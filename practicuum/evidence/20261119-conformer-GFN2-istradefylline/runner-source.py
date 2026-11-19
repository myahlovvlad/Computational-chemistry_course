"""Seeded whole-molecule conformer search, GFN2/ALPB re-ranking, optimization and Hessian audit."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib,importlib.metadata,json,math,os,platform,re,shutil,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np
from rdkit import Chem,rdBase
from rdkit.Chem import AllChem
from run_research_quantum import structure

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from conformer_ensemble import aligned_conformer_rmsd,geometry_identity,projected_frequencies
HARTREE_KCAL=627.5094740631


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def single_conformer(mol,id):
    result=Chem.Mol(mol);result.RemoveAllConformers();result.AddConformer(Chem.Conformer(mol.GetConformer(id)),assignId=True)
    return result


def xtb_job(folder,molecule,kind,manifest,exe):
    p=manifest['protocol'];charge=Chem.GetFormalCharge(molecule)
    if folder.exists():raise FileExistsError('Immutable calculation directory already exists: '+str(folder))
    folder.mkdir(parents=True)
    xyz=Chem.MolToXYZBlock(molecule,precision=12)
    (folder/'input.xyz').write_text(xyz,encoding='ascii')
    control='$gbsa\n grid='+p['solvent_grid']+'\n$end\n'
    if kind=='hessian':control+='$hess\n step='+str(p['hessian_displacement_bohr'])+'\n$end\n'
    (folder/'control.inp').write_text(control,encoding='ascii')
    command=['xtb','input.xyz','--gfn','2','--alpb',p['solvent'],p['solution_reference_state'],
             '--chrg',str(charge),'--uhf','0','--parallel',str(p['resources']['threads_per_job']),
             '--input','control.inp','--json']
    if kind=='optimize':command+=['--opt',p['optimization_level'],'--acc',str(p['optimization_accuracy']),'--cycles',str(p['optimization_max_cycles'])]
    else:command+=['--acc',str(p['hessian_accuracy'] if kind=='hessian' else p['singlepoint_accuracy'])]
    if kind=='hessian':command+=['--hess']
    # Separate executable/argv[0] keeps native Windows xTB's JSON program-call
    # metadata free of unescaped absolute Windows path separators.
    save(folder/'command.json',{'argv':command,'executable':str(exe),'executable_sha256':manifest['executable_sha256'],
                              'input_sha256':sha(folder/'input.xyz'),'protocol_sha256':manifest['protocol_sha256']})
    env=dict(os.environ,PATH=str(exe.parent)+os.pathsep+os.environ.get('PATH',''),
             OMP_NUM_THREADS=str(p['resources']['threads_per_job']),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_STACKSIZE='256M')
    start=time.perf_counter()
    try:
        with (folder/'stdout.log').open('wb') as a,(folder/'stderr.log').open('wb') as b:
            process=subprocess.run(command,executable=str(exe),cwd=folder,env=env,stdout=a,stderr=b,
                     timeout=p['resources']['timeout_seconds_per_job'],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if process.returncode:raise RuntimeError('xTB exit '+str(process.returncode))
        output=(folder/'stdout.log').read_text(errors='replace')
        if 'normal termination of xtb' not in (folder/'stderr.log').read_text(errors='replace')+output:
            raise RuntimeError('Normal termination marker absent')
        result=read(folder/'xtbout.json')
        if result['method']!='GFN2-xTB' or not result['xtb version'].startswith(p['xtb_version']):raise ValueError('Different Hamiltonian/version')
        if abs(sum(result['partial charges'])-charge)>1e-5:raise ValueError('Charge sum mismatch')
        valence={1:1,6:4,7:5,8:6,9:7,15:5,16:6,17:7}
        electrons=sum(valence[a.GetAtomicNum()] for a in molecule.GetAtoms())-charge
        if result['number of electrons']!=electrons or result['number of unpaired electrons']!=0:
            raise ValueError('Valence electron/spin mismatch')
        energies=re.findall(r'TOTAL ENERGY\s+([-+0-9.EDed]+)\s+Eh',output)
        if not energies:raise ValueError('Final full-precision energy unavailable')
        energy=float(energies[-1].replace('D','E'))
        if not math.isfinite(energy) or abs(energy-result['total energy'])>1e-7:raise ValueError('Energy output inconsistency')
        report={'status':'PASS','kind':kind,'energy_hartree':energy,'valence_electrons':electrons,'charge':charge,
                'seconds':time.perf_counter()-start,'JSON_sha256':sha(folder/'xtbout.json')}
        optimized=molecule
        if kind=='optimize':
            if 'GEOMETRY OPTIMIZATION CONVERGED' not in output or (folder/'NOT_CONVERGED').exists():
                raise RuntimeError('Geometry optimization not accepted')
            optimized=geometry_identity(molecule,(folder/'xtbopt.xyz').read_text(),charge)
            report['geometry_sha256']=sha(folder/'xtbopt.xyz');report['minimum_verified']=False
            report['scope']='stationary conformer; Hessian required separately'
        if kind=='hessian':
            n=molecule.GetNumAtoms()
            text=' '.join(line for line in (folder/'hessian').read_text().splitlines() if not line.startswith('$'))
            H=np.fromstring(text,sep=' ').reshape(3*n,3*n)
            projected=projected_frequencies(H,molecule.GetConformer().GetPositions(),[a.GetMass() for a in molecule.GetAtoms()])
            native=np.asarray(result['vibrational frequencies / rcm']);rigid=projected['rigid_mode_rank']
            if len(native)!=3*n:raise ValueError('Native frequency count mismatch')
            internal=np.sort(np.delete(native,np.argsort(abs(native))[:rigid]))
            if not np.allclose(internal,projected['frequencies_cm1'],rtol=p['native_frequency_check_relative_tolerance'],atol=p['native_frequency_check_absolute_tolerance_cm1']):
                raise ValueError('Native and independently projected Hessian modes disagree')
            save(folder/'projected_hessian.json',projected)
            report.update(minimum_verified=projected['minimum_verified'],lowest_frequency_cm1=projected['lowest_frequency_cm1'],
                          internal_mode_count=projected['internal_mode_count'],native_projected_mode_max_difference_cm1=float(np.max(abs(internal-projected['frequencies_cm1']))))
            if not projected['minimum_verified']:report.update(status='FAIL',reason='Nonpositive internal curvature; no clipping accepted')
        save(folder/'result.json',report)
        return report,optimized
    except Exception as error:
        report={'status':'FAIL','kind':kind,'seconds':time.perf_counter()-start,'error':str(error),'traceback':traceback.format_exc()}
        save(folder/'failure.json',report);return report,None


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--name',required=True,choices=['istradefylline','atorvastatin','atorvastatin_anion','atorvastatin_lactone'])
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--protocol',type=Path,default=ROOT/'practicuum/protocols/conformer-gfn2-alpb.json')
    parser.add_argument('--installation',type=Path,default=ROOT/'scripts/bin/xtb-6.8.0')
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    p=read(args.protocol);installed=read(args.installation/'installation.json');exe=(args.installation/installed['executable']).resolve()
    if sha(exe)!=installed['executable_sha256'] or installed['version']!=p['xtb_version']:raise ValueError('Tool installation/version changed')
    molecule,record=structure(args.name)
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'name':args.name,'structure':record,
        'canonical_state_smiles':Chem.MolToSmiles(Chem.RemoveHs(molecule),isomericSmiles=True),
        'charge':Chem.GetFormalCharge(molecule),'protocol':p,'protocol_sha256':sha(args.protocol),
        'script_sha256':sha(__file__),'structure_helper_sha256':sha(ROOT/'scripts/run_research_quantum.py'),
        'geometry_helper_sha256':sha(ROOT/'practicuum/shared/conformer_ensemble.py'),
        'compound_source_sha256':sha(ROOT/'practicuum/shared/data/compounds.json'),
        'executable_sha256':sha(exe),'installation':installed,'python':sys.version,'platform':platform.platform(),
        'rdkit':rdBase.rdkitVersion,'versions':{n:importlib.metadata.version(n) for n in ['numpy','scipy','rdkit']},
        'scope':'actual finite conformer search; final DFT and equilibrium populations require separate validation'}
    save(out/'manifest.json',manifest);(out/'protocol.json').write_bytes(args.protocol.read_bytes())
    (out/'runner-source.py').write_bytes(Path(__file__).read_bytes());(out/'geometry-helper-source.py').write_bytes((ROOT/'practicuum/shared/conformer_ensemble.py').read_bytes())
    inputs=[];batches=[]
    for seed in p['seeds']:
        mol=Chem.Mol(molecule);params=AllChem.ETKDGv3();params.randomSeed=seed;params.numThreads=2
        ids=list(AllChem.EmbedMultipleConfs(mol,numConfs=p['conformers_per_seed'],params=params))
        if not ids:raise RuntimeError('No embedded structures for seed '+str(seed))
        if not AllChem.MMFFHasAllMoleculeParams(mol):raise ValueError('MMFF parameters missing')
        values=AllChem.MMFFOptimizeMoleculeConfs(mol,numThreads=2,maxIters=p['forcefield_max_iterations'],mmffVariant=p['forcefield'])
        for id,(status,energy) in zip(ids,values):
            item={'id':len(inputs),'seed':seed,'seed_conformer_id':int(id),'MMFF_status':int(status),'MMFF_energy_kcal_mol':float(energy)}
            inputs.append((item,single_conformer(mol,id)))
        batches.append({'seed':seed,'attempted':p['conformers_per_seed'],'embedded':len(ids),'MMFF_converged':sum(s==0 for s,e in values)})
        print(args.name,'prepared seed',seed,'embedded',len(ids),flush=True)
    save(out/'embedding_batches.json',batches)
    with Chem.SDWriter(str(out/'initial_ensemble.sdf')) as writer:
        for item,mol in inputs:
            for key,value in item.items():mol.SetProp(key,str(value))
            writer.write(mol)
    results={}
    with ThreadPoolExecutor(max_workers=p['resources']['simultaneous_jobs']) as pool:
        futures={pool.submit(xtb_job,out/f"singlepoints/{item['id']:04}",mol,'singlepoint',manifest,exe):(item,mol) for item,mol in inputs}
        for done,future in enumerate(as_completed(futures),1):
            item,mol=futures[future];result,_=future.result();results[item['id']]={**item,**result}
            if done%25==0:print(args.name,'GFN2/ALPB singlepoints',done,'/',len(inputs),flush=True)
    save(out/'singlepoint_results.json',list(results.values()))
    good=sorted((r for r in results.values() if r['status']=='PASS'),key=lambda r:r['energy_hartree'])
    if not good:raise RuntimeError('No accepted GFN2 singlepoint')
    selected=[];lookup={item['id']:mol for item,mol in inputs}
    for row in good:
        if (row['energy_hartree']-good[0]['energy_hartree'])*HARTREE_KCAL>p['selection_energy_window_kcal_mol']:continue
        if any(aligned_conformer_rmsd(lookup[row['id']],lookup[old['id']])<p['selection_heavy_atom_RMSD_A'] for old in selected):continue
        selected.append(row)
        if len(selected)>=p['max_optimization_candidates']:break
    save(out/'optimization_selection.json',selected);optimized=[]
    with ThreadPoolExecutor(max_workers=p['resources']['simultaneous_jobs']) as pool:
        futures={pool.submit(xtb_job,out/f"optimize/{row['id']:04}",lookup[row['id']],'optimize',manifest,exe):row for row in selected}
        for future in as_completed(futures):
            row=futures[future];result,mol=future.result();optimized.append(({**row,**result},mol))
            print(args.name,'optimization',row['id'],result['status'],flush=True)
    accepted=sorted([(r,m) for r,m in optimized if r['status']=='PASS'],key=lambda pair:pair[0]['energy_hartree'])
    unique=[]
    for row,mol in accepted:
        if not any(aligned_conformer_rmsd(mol,old_mol)<p['selection_heavy_atom_RMSD_A'] for old,old_mol in unique):unique.append((row,mol))
    with Chem.SDWriter(str(out/'optimized_conformers.sdf')) as writer:
        for row,mol in unique:
            mol.SetProp('GFN2_ALPB_energy_hartree',str(row['energy_hartree']));mol.SetProp('source_id',str(row['id']));writer.write(mol)
    hessians=[]
    for row,mol in unique[:p['hessian_candidates']]:
        result,_=xtb_job(out/f"hessian/{row['id']:04}",mol,'hessian',manifest,exe)
        hessians.append({'source_id':row['id'],**result});print(args.name,'Hessian',row['id'],result['status'],flush=True)
    all_pass=all(r['status']=='PASS' for r in results.values()) and len(accepted)==len(selected) and hessians and all(r['status']=='PASS' for r in hessians)
    report={'status':'PASS' if all_pass else 'FAIL','scope':manifest['scope'],'name':args.name,'protocol_sha256':manifest['protocol_sha256'],
        'batches':batches,'singlepoints_attempted':len(inputs),'singlepoints_converged':len(good),
        'optimization_candidates':len(selected),'optimization_converged':len(accepted),'distinct_optimized_conformers':len(unique),
        'optimized_records':[r for r,m in optimized],'lowest_energy_hartree':None if not unique else unique[0][0]['energy_hartree'],
        'per_seed_lowest_singlepoint_hartree':{str(seed):min((r['energy_hartree'] for r in good if r['seed']==seed),default=None) for seed in p['seeds']},
        'hessian_results':hessians,'sampling_exhaustiveness':'NOT_PROVEN: finite seeded search and candidate cap',
        'DFT_minimum_verification':'NOT_RUN in this semiempirical pipeline','scientific_review':'NOT_RUN',
        'limitations':p['limitations']}
    save(out/'result.json',report);print(args.name,'completed',report['status'],'distinct conformers',len(unique),flush=True)
    if not all_pass:raise SystemExit(2)


if __name__=='__main__':main()
