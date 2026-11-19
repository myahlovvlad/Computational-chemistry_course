"""Paired GFN2 gas/ALPB, solvent-grid and Hessian-step checks at fixed geometries."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
import numpy as np
from run_research_quantum import structure
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from conformer_ensemble import geometry_identity,projected_frequencies


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--installation',type=Path,default=ROOT/'scripts/bin/xtb-6.8.0')
    args=parser.parse_args();run=args.run.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    parent=read(run/'manifest.json');result=read(run/'result.json');installed=read(args.installation/'installation.json')
    exe=(args.installation/installed['executable']).resolve()
    if sha(exe)!=parent['executable_sha256']:raise ValueError('Numerical comparison requires the same binary')
    selected=result['hessian_results'];template,_=structure(parent['name']);charge=parent['charge']
    protocol={'scope':'paired fixed-geometry controls; no global sampling or final DFT claim',
              'source_manifest_sha256':sha(run/'manifest.json'),'source_result_sha256':sha(run/'result.json'),
              'executable_sha256':sha(exe),'singlepoint_accuracy':.01,'solvent_grids':['tight','verytight'],
              'ALPB_reference_state':'gsolv','Hessian_steps_bohr':[.005,.0025],
              'absolute_grid_energy_change_tolerance_Eh':1e-5,'Hessian_mode_change_tolerance_cm1':2.,
              'minimum_gate':'all internal frequencies positive in both step calculations'}
    save(out/'protocol.json',protocol);(out/'auditor-source.py').write_bytes(Path(__file__).read_bytes())
    env=dict(os.environ,PATH=str(exe.parent)+os.pathsep+os.environ.get('PATH',''),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_STACKSIZE='256M')
    def calculate(label,source,grid=None,hessian=False):
        folder=out/label;folder.mkdir();shutil.copyfile(source,folder/'input.xyz')
        control=('$gbsa\n grid='+grid+'\n$end\n') if grid else ''
        if hessian:control+='$hess\n step=0.0025\n$end\n'
        (folder/'control.inp').write_text(control,encoding='ascii')
        command=['xtb','input.xyz','--gfn','2','--chrg',str(charge),'--uhf','0','--acc','0.01','--parallel','1','--json']
        if grid:command+=['--alpb','water','gsolv']
        if control:command+=['--input','control.inp']
        if hessian:command+=['--hess']
        save(folder/'command.json',{'argv':command,'executable':str(exe),'geometry_sha256':sha(source)})
        with (folder/'stdout.log').open('wb') as a,(folder/'stderr.log').open('wb') as b:
            completed=subprocess.run(command,executable=str(exe),cwd=folder,env=env,stdout=a,stderr=b,
                        timeout=1800,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if completed.returncode:raise RuntimeError('Audit calculation failed '+label)
        j=read(folder/'xtbout.json')
        if j['method']!='GFN2-xTB' or not j['xtb version'].startswith('6.8.0'):raise ValueError('Different method/version')
        if abs(sum(j['partial charges'])-charge)>1e-5:raise ValueError('Charge mismatch')
        text=(folder/'stdout.log').read_text(errors='replace');energies=re.findall(r'TOTAL ENERGY\s+([-+0-9.EDed]+)\s+Eh',text)
        if not energies:raise ValueError('Energy absent')
        energy=float(energies[-1].replace('D','E'))
        if not np.isfinite(energy) or abs(energy-j['total energy'])>1e-7:raise ValueError('Inconsistent energy')
        report={'status':'PASS','energy_hartree':energy,'solvent_model':'ALPB water, '+grid if grid else 'gas phase',
                'same_geometry_sha256':sha(source)}
        if hessian:
            molecule=geometry_identity(template,(folder/'input.xyz').read_text(),charge);n=molecule.GetNumAtoms()
            matrix=np.fromstring(' '.join(line for line in (folder/'hessian').read_text().splitlines() if not line.startswith('$')),sep=' ').reshape(3*n,3*n)
            report['projected_hessian']=projected_frequencies(matrix,molecule.GetConformer().GetPositions(),[a.GetMass() for a in molecule.GetAtoms()])
        save(folder/'result.json',report);return report
    paired=[]
    for row in selected:
        id=row['source_id'];xyz=run/f'optimize/{id:04}/xtbopt.xyz'
        tight=calculate(f'{id:04}-tight',xyz,'tight');dense=calculate(f'{id:04}-verytight',xyz,'verytight')
        gas=calculate(f'{id:04}-gas',xyz)
        paired.append({'source_id':id,'tight_energy_Eh':tight['energy_hartree'],'verytight_energy_Eh':dense['energy_hartree'],
                       'gas_energy_Eh':gas['energy_hartree'],'fixed_geometry_ALPB_minus_gas_Eh':tight['energy_hartree']-gas['energy_hartree'],
                       'surface_grid_energy_change_Eh':dense['energy_hartree']-tight['energy_hartree']})
    first=selected[0]['source_id'];old=read(run/f'hessian/{first:04}/projected_hessian.json')
    new=calculate('hessian-half-step',run/f'optimize/{first:04}/xtbopt.xyz','tight',True)['projected_hessian']
    difference=float(np.max(abs(np.array(old['frequencies_cm1'])-new['frequencies_cm1'])))
    grid=np.array([r['surface_grid_energy_change_Eh'] for r in paired])
    numerical_pass=bool(np.max(abs(grid))<=1e-5 and difference<=2 and old['minimum_verified'] and new['minimum_verified'])
    report={'status':'PASS' if numerical_pass else 'FAIL','scope':protocol['scope'],'paired_fixed_geometry_results':paired,
            'max_surface_energy_change_Eh':float(np.max(abs(grid))),
            'max_relative_energy_grid_sensitivity_kcal_mol':float(np.ptp(grid)*627.5094740631),
            'Hessian_step_max_frequency_change_cm1':difference,
            'half_step_lowest_frequency_cm1':new['lowest_frequency_cm1'],'minimum_sign_stable':old['minimum_verified'] and new['minimum_verified'],
            'fine_conformer_ordering':'REVIEW: compare pairwise gaps with numerical sensitivity; this is not an uncertainty bound on the Hamiltonian',
            'limitations':['Gas singlepoints use ALPB-optimized geometries; solvent-induced geometry relaxation is not isolated',
                           'GFN2/ALPB controls do not establish DFT convergence or experimental populations','Finite difference/grid comparisons do not quantify all physical model error'],
            'scientific_review':'NOT_RUN'}
    save(out/'result.json',report);print(json.dumps(report,indent=2))
    if not numerical_pass:raise SystemExit(2)


if __name__=='__main__':main()
