"""Real staged DFT research, strict convergence, immutable outputs and resumable stages.

No surrogate values and no fallback to the educational STO-3G archive.
Run prepare once, then selected stages or all; successful stages are reused only
when their immutable input protocol and script hashes match the run manifest.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def structure(name):
    from rdkit import Chem
    records=load(ROOT/'practicuum/shared/data/compounds.json')
    if name=='atorvastatin_anion':
        record=next(r for r in records if r['name']=='atorvastatin_calcium')
        parent=Chem.MolFromSmiles(record['smiles'])
        fragments=Chem.GetMolFrags(parent,asMols=True)
        organic=[m for m in fragments if Chem.GetFormalCharge(m)==-1]
        if len(organic)!=2 or Chem.MolToSmiles(organic[0])!=Chem.MolToSmiles(organic[1]):
            raise ValueError('Unexpected calcium salt stoichiometry or anion identity')
        molecule=organic[0]
        record={**record,'derived_name':name,'transformation':'one of two identical organic anions from calcium salt; counterion excluded explicitly'}
    else:
        record=next(r for r in records if r['name']==name)
        molecule=Chem.MolFromSmiles(record['smiles'])
    if molecule is None or len(Chem.GetMolFrags(molecule))!=1:
        raise ValueError('QM requires one explicitly chosen molecular form')
    if any(a.GetAtomicNum() not in {1,6,7,8,9,15,16,17} for a in molecule.GetAtoms()):
        raise ValueError('Element outside this organic protocol')
    return Chem.AddHs(molecule),record


def prepare(args,protocol):
    import numpy as np
    from rdkit import Chem,rdBase
    from rdkit.Chem import AllChem,rdMolAlign
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    molecule,record=structure(args.name)
    p=protocol['conformers'];params=AllChem.ETKDGv3()
    params.randomSeed=p['seed'];params.numThreads=protocol['resources']['threads']
    ids=list(AllChem.EmbedMultipleConfs(molecule,numConfs=p['attempted'],params=params))
    if not ids:raise RuntimeError('No conformers embedded')
    if not AllChem.MMFFHasAllMoleculeParams(molecule):raise RuntimeError('MMFF parameters missing')
    raw=AllChem.MMFFOptimizeMoleculeConfs(molecule,numThreads=protocol['resources']['threads'],
        maxIters=p['max_iterations'],mmffVariant=p['forcefield'])
    values=[{'id':int(i),'status':int(s),'energy_kcal_mol':float(e)} for i,(s,e) in zip(ids,raw)]
    good=sorted([r for r in values if r['status']==0 and np.isfinite(r['energy_kcal_mol'])],key=lambda r:r['energy_kcal_mol'])
    if not good:raise RuntimeError('No converged prescreen conformer')
    heavy=[a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum()>1]
    selected=[]
    for row in good:
        if row['energy_kcal_mol']-good[0]['energy_kcal_mol']>p['energy_window_kcal_mol']:continue
        if any(rdMolAlign.GetBestRMS(Chem.RemoveHs(Chem.Mol(molecule)),Chem.RemoveHs(Chem.Mol(molecule)),
                 prbId=row['id'],refId=previous['id'])<p['heavy_atom_rmsd_angstrom'] for previous in selected):continue
        selected.append(row)
        if len(selected)>=p['qm_candidates']:break
    charge=Chem.GetFormalCharge(molecule);electrons=sum(a.GetAtomicNum() for a in molecule.GetAtoms())-charge
    if electrons%2:raise ValueError('Open-shell species requires a separately justified protocol')
    with Chem.SDWriter(str(out/'prescreen.sdf')) as writer:
        for row in values:
            molecule.SetProp('MMFF_status',str(row['status']));molecule.SetProp('MMFF_energy_kcal_mol',str(row['energy_kcal_mol']))
            writer.write(molecule,confId=row['id'])
    for number,row in enumerate(selected):
        folder=out/f'conformer-{number:03}';folder.mkdir()
        conf=molecule.GetConformer(row['id'])
        atoms=[(a.GetSymbol(),list(conf.GetAtomPosition(a.GetIdx()))) for a in molecule.GetAtoms()]
        dump_new(folder/'initial_geometry.json',atoms)
        dump_new(folder/'selection.json',row)
    manifest={'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),'name':args.name,
       'protocol':protocol,'protocol_sha256':digest(args.protocol),'script_sha256':digest(__file__),
       'structure_source_sha256':digest(ROOT/'practicuum/shared/data/compounds.json'),
       'record':record,'charge':charge,'spin_2S':0,'electrons':electrons,'atom_count':molecule.GetNumAtoms(),
       'prescreen':values,'selected':selected,'python':sys.version,'platform':platform.platform(),
       'versions':{n:importlib.metadata.version(n) for n in ['pyscf','geometric','pyscf-dispersion','rdkit','numpy','scipy']},
       'scope':'actual computed molecular states, method validation pending','scientific_review':'NOT_RUN'}
    dump_new(out/'manifest.json',manifest)
    (out/'protocol.json').write_bytes(args.protocol.read_bytes())
    (out/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    print('Prepared',args.name,'embedded',len(ids),'converged',len(good),'QM candidates',len(selected),flush=True)
    return manifest


def build_mf(atoms,settings,manifest,log,checkpoint):
    from pyscf import gto,dft,lib
    resources=manifest['protocol']['resources'];lib.num_threads(resources['threads'])
    system=gto.M(atom=atoms,basis=settings['basis'],unit='Angstrom',charge=manifest['charge'],
       spin=manifest['spin_2S'],max_memory=resources['memory_MB'],verbose=4,output=str(log))
    if system.nelectron!=manifest['electrons']:raise ValueError('Electron count changed')
    mf=dft.RKS(system).density_fit();mf.xc=settings['functional']
    if settings.get('dispersion'):mf.disp=settings['dispersion']
    mf=mf.SMD();mf.with_solvent.solvent=settings['solvent']
    # Memory controls change block sizes, never the basis or electronic model.
    mf.max_memory=resources['memory_MB'];mf.with_solvent.max_memory=resources['memory_MB']
    mf.with_solvent.lebedev_order=protocol_order=manifest['protocol'].get('surface_lebedev_order',41)
    mf.grids.level=settings['grid_level'];mf.conv_tol=settings['scf_tolerance_hartree']
    mf.conv_tol_grad=settings['density_tolerance'];mf.max_cycle=settings['max_scf_cycles']
    mf.chkfile=str(checkpoint)
    return mf


def solve(mf):
    import numpy as np
    energy=mf.kernel()
    if not mf.converged or not np.isfinite(energy):raise RuntimeError('SCF not converged; no fallback accepted')
    # N is evaluated in the nonorthogonal AO metric, never by tracing D alone.
    trace=float(np.einsum('ij,ji',mf.make_rdm1(),mf.get_ovlp()))
    if abs(trace-mf.mol.nelectron)>1e-6:raise RuntimeError('Density electron-count regression')
    return float(energy)


def geometry_json(system):
    return [(system.atom_symbol(i),system.atom_coord(i,unit='Angstrom').tolist()) for i in range(system.natm)]


def stage(folder,stage_name,manifest):
    import numpy as np
    protocol=manifest['protocol'];target=folder/stage_name
    if (target/'result.json').exists():
        result=load(target/'result.json')
        if result['status']!='PASS':raise RuntimeError('Existing stage not accepted')
        print(folder.name,stage_name,'already PASS',flush=True);return
    if target.exists():raise FileExistsError('Incomplete stage retained. Inspect it and choose a new attempt/run: '+str(target))
    target.mkdir()
    started=time.perf_counter()
    dump_new(target/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'stage':stage_name,
      'script_sha256':manifest['script_sha256'],'protocol_sha256':manifest['protocol_sha256']})
    try:
        if stage_name=='optimize':
            from pyscf.geomopt.geometric_solver import kernel
            atoms=load(folder/'initial_geometry.json');settings=protocol['geometry']
            mf=build_mf(atoms,settings,manifest,target/'pyscf.log',target/'checkpoint.h5')
            trajectory=[]
            def callback(env):
                g=np.asarray(env['gradients']);entry={'step':len(trajectory)+1,'energy_hartree':float(env['energy']),
                    'gradient_rms':float(np.sqrt(np.mean(g*g))),'gradient_max':float(abs(g).max())}
                trajectory.append(entry);dump_new(target/f"step-{len(trajectory):04}.json",{**entry,'geometry':geometry_json(env['mol'])})
                print(manifest['name'],folder.name,'DFT optimization',entry,flush=True)
            converged,system=kernel(mf,maxsteps=settings['max_geometry_steps'],callback=callback,
                convergence_energy=settings['energy_change_hartree'],convergence_grms=settings['gradient_rms_hartree_bohr'],
                convergence_gmax=settings['gradient_max_hartree_bohr'],convergence_drms=settings['step_rms_angstrom'],
                convergence_dmax=settings['step_max_angstrom'])
            if not converged:raise RuntimeError('Geometry optimization not converged')
            atoms=geometry_json(system);dump_new(target/'geometry.json',atoms)
            check=build_mf(atoms,settings,manifest,target/'final-scf.log',target/'final-checkpoint.h5')
            energy=solve(check);gradient=check.nuc_grad_method().kernel()
            # geomeTRIC uses rms/max over vector magnitudes of per-atom gradients.
            norms=np.linalg.norm(gradient,axis=1);grms=float(np.sqrt(np.mean(norms**2)));gmax=float(norms.max())
            if grms>settings['gradient_rms_hartree_bohr'] or gmax>settings['gradient_max_hartree_bohr']:
                raise RuntimeError('Independent final gradient check failed')
            result={'energy_hartree':energy,'geometry_sha256':digest(target/'geometry.json'),
                'gradient_rms_hartree_bohr':grms,'gradient_max_hartree_bohr':gmax,'trajectory':trajectory,
                'minimum_verified':False,'next_required':'projected Hessian at same model'}
        else:
            geometry=folder/'optimize/geometry.json'
            if not geometry.is_file():raise FileNotFoundError('Accepted optimized geometry required')
            atoms=load(geometry)
            if stage_name=='frequencies':
                from pyscf.hessian import thermo
                settings=protocol['geometry'];mf=build_mf(atoms,settings,manifest,target/'pyscf.log',target/'checkpoint.h5')
                energy=solve(mf);hessian=mf.Hessian().kernel()
                if not np.all(np.isfinite(hessian)):raise RuntimeError('Nonfinite Hessian')
                symmetry=float(np.max(abs(hessian-hessian.transpose(1,0,3,2))))
                np.save(target/'hessian_hartree_bohr2.npy',hessian)
                if symmetry>1e-5:raise RuntimeError('Hessian not symmetric within tolerance')
                modes=thermo.harmonic_analysis(mf.mol,hessian,imaginary_freq=False)
                frequencies=np.asarray(modes['freq_wavenumber'],dtype=float)
                np.save(target/'normal_modes.npy',modes['norm_mode'])
                dump_new(target/'frequencies_cm1.json',frequencies.tolist())
                if len(frequencies)!=3*mf.mol.natm-6:raise RuntimeError('Unexpected mode count for nonlinear molecule')
                if np.any(frequencies<=0):raise RuntimeError('Not a verified minimum: nonpositive projected vibrational modes')
                thermal=thermo.thermo(mf,modes['freq_au'],temperature=protocol['vibrations']['temperature_K'],pressure=protocol['vibrations']['pressure_Pa'])
                thermochemistry={key:{'value':np.asarray(value[0]).tolist(),'unit':value[1]} for key,value in thermal.items()}
                dump_new(target/'RRHO_thermochemistry.json',thermochemistry)
                result={'energy_hartree':energy,'geometry_sha256':digest(geometry),'minimum_verified':True,
                    'mode_count':len(frequencies),'lowest_frequency_cm1':float(frequencies.min()),'hessian_symmetry_error':symmetry,
                    'standard_state':'RRHO 1 atm; solution free energies need explicit standard-state and low-mode treatment'}
            elif stage_name=='numerical_convergence':
                import copy
                trials=[]
                for surface_order,grid_level in [(23,4),(29,4),(35,4),(29,5)]:
                    variant=copy.deepcopy(manifest);variant['protocol']['surface_lebedev_order']=surface_order
                    settings={**protocol['geometry'],'grid_level':grid_level}
                    mf=build_mf(atoms,settings,variant,target/f'surface-{surface_order}-grid-{grid_level}.log',target/f'surface-{surface_order}-grid-{grid_level}.h5')
                    energy=solve(mf)
                    trial={'surface_lebedev_order':surface_order,'DFT_grid_level':grid_level,'energy_hartree':energy}
                    trials.append(trial);dump_new(target/f'surface-{surface_order}-grid-{grid_level}.json',trial)
                baseline=trials[1]['energy_hartree']
                deltas=[abs(t['energy_hartree']-baseline) for t in trials[2:]]
                threshold=protocol['numerical_convergence']['energy_tolerance_hartree']
                if max(deltas)>threshold:raise RuntimeError('Quadrature convergence not demonstrated at requested tolerance')
                result={'trials':trials,'max_reference_change_hartree':max(deltas),'acceptance_hartree':threshold,
                        'geometry_sha256':digest(geometry),'scope':'electronic and surface quadrature only; not basis-set error'}
            elif stage_name=='singlepoint':
                settings=protocol['singlepoint'];mf=build_mf(atoms,settings,manifest,target/'pyscf.log',target/'checkpoint.h5')
                energy=solve(mf)
                result={'energy_hartree':energy,'geometry_sha256':digest(geometry),'basis_functions':mf.mol.nao_nr(),
                    'settings':settings,'energy_kind':'electronic plus SMD and specified D3; not a Gibbs free energy'}
            elif stage_name=='uv':
                from scipy.constants import physical_constants
                settings=protocol['excitation'];mf=build_mf(atoms,settings,manifest,target/'pyscf.log',target/'checkpoint.h5')
                energy=solve(mf);td=mf.TDDFT();td.nstates=settings['states'];td.conv_tol=settings['tolerance_hartree'];td.max_cycle=150
                td.with_solvent.equilibrium_solvation=settings['equilibrium_solvation']
                excitations,_=td.kernel()
                if len(excitations)!=settings['states'] or not all(td.converged):raise RuntimeError('Incomplete TDDFT convergence')
                oscillator=td.oscillator_strength(gauge='length');vel=td.oscillator_strength(gauge='velocity')
                transitions=[]
                for i,(e,f,v) in enumerate(zip(excitations,oscillator,vel),1):
                    eV=float(e*physical_constants['Hartree energy in eV'][0])
                    if eV<=0 or not np.isfinite([eV,f,v]).all():raise RuntimeError('Invalid electronic transition')
                    transitions.append({'state':i,'energy_eV':eV,'wavelength_nm':1239.8419843320026/eV,
                        'oscillator_strength_length':float(f),'oscillator_strength_velocity':float(v)})
                result={'SCF_energy_hartree':energy,'geometry_sha256':digest(geometry),'transitions':transitions,
                    'solvent_response':'nonequilibrium vertical','absolute_measured_absorbance':'NOT_INFERRED',
                    'settings':settings,'converged_states':len(transitions)}
            elif stage_name=='ir':
                from scipy.constants import Avogadro,epsilon_0,c,physical_constants
                if not load(folder/'frequencies/result.json')['minimum_verified']:raise RuntimeError('Verified minimum required for IR')
                modes=np.load(folder/'frequencies/normal_modes.npy')
                frequencies=load(folder/'frequencies/frequencies_cm1.json')
                settings=protocol['geometry'];reference=build_mf(atoms,settings,manifest,target/'reference.log',target/'reference.h5');solve(reference)
                coords=reference.mol.atom_coords(unit='Bohr');step=protocol['vibrations']['IR_mass_weighted_step_bohr_sqrt_amu']
                # PySCF normal modes are mass-unweighted Cartesian vectors in amu^-1/2.
                # Central differences produce d(mu/e*a0)/d(Q/a0*sqrt(amu)).
                ea0=physical_constants['atomic unit of electric dipole mom.'][0]
                bohr=physical_constants['Bohr radius'][0];amu=physical_constants['atomic mass constant'][0]
                conversion=ea0/(bohr*np.sqrt(amu))
                intensity_factor=Avogadro/(12*epsilon_0*c*c)/1000
                lines=[]
                for i,mode in enumerate(modes):
                    dipoles=[]
                    for sign in [-1,1]:
                        displaced=reference.mol.copy();displaced.set_geom_(coords+sign*step*mode,unit='Bohr')
                        geom=geometry_json(displaced)
                        trial=build_mf(geom,settings,manifest,target/f'mode-{i:04}-{sign}.log',target/f'mode-{i:04}-{sign}.h5')
                        solve(trial);dipoles.append(np.asarray(trial.dip_moment(unit='AU',verbose=0)))
                    derivative=(dipoles[1]-dipoles[0])/(2*step)
                    intensity=float(intensity_factor*np.sum((derivative*conversion)**2))
                    line={'mode':i+1,'frequency_cm1':frequencies[i],'intensity_km_mol':intensity,
                          'dipole_derivative_au_per_mass_weighted_Q':derivative.tolist()}
                    lines.append(line);dump_new(target/f'mode-{i:04}.json',line)
                    print(manifest['name'],'IR mode',i+1,'of',len(modes),flush=True)
                result={'modes':lines,'geometry_sha256':digest(geometry),'intensity_units':'km/mol',
                    'derivative':'central finite difference of self-consistent SMD dipoles',
                    'step_bohr_sqrt_amu':step,'frequency_scale':1.0,'experimental_calibration':'NOT_RUN'}
            else:raise ValueError(stage_name)
        result.update(status='PASS',kind='calculated',seconds=time.perf_counter()-started,scientific_review='NOT_RUN')
        dump_new(target/'result.json',result);print(manifest['name'],folder.name,stage_name,'PASS',flush=True)
    except BaseException as error:
        dump_new(target/'failure.json',{'status':'FAIL','error':str(error),'traceback':traceback.format_exc(),
            'seconds':time.perf_counter()-started,'no_substitute_result':True})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',choices=['caffeine','istradefylline','atorvastatin','atorvastatin_anion','atorvastatin_lactone'],required=True)
    parser.add_argument('--protocol',type=Path,default=ROOT/'practicuum/protocols/research-quantum.json')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--stage',choices=['prepare','optimize','numerical_convergence','frequencies','singlepoint','uv','ir','all'],required=True)
    parser.add_argument('--candidate',type=int,help='Run one selected QM conformer; default all selected')
    args=parser.parse_args();protocol=load(args.protocol)
    if args.stage=='prepare':prepare(args,protocol);return
    manifest=load(args.out/'manifest.json')
    if manifest['name']!=args.name or manifest['protocol_sha256']!=digest(args.protocol) or manifest['script_sha256']!=digest(__file__):
        raise ValueError('Run identity, protocol or script changed; create a new run rather than mixing methods')
    indices=range(len(manifest['selected'])) if args.candidate is None else [args.candidate]
    for i in indices:
        if not 0<=i<len(manifest['selected']):raise ValueError('Unknown selected conformer')
        folder=args.out/f'conformer-{i:03}'
        stages=['optimize','numerical_convergence','frequencies','singlepoint','uv','ir'] if args.stage=='all' else [args.stage]
        for name in stages:stage(folder,name,manifest)


if __name__=='__main__':main()
