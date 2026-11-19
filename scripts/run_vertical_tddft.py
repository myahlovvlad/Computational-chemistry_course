"""Actual composite CAM//GFN2 vertical excitation run with immutable provenance.

Use quantum-core on Windows or quantum on Linux. This route does not require
dispersion or an optimizer and never certifies the input as a DFT minimum.
"""
from datetime import datetime, timezone
from contextlib import ExitStack
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'practicuum/shared'))


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):value.update(block)
    return value.hexdigest()
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'practicuum/shared/data/conformer_research/istradefylline')
    parser.add_argument('--protocol',type=Path,default=ROOT/'practicuum/protocols/uv-cam-gfn2-water.json')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--initial-checkpoint',type=Path)
    parser.add_argument('--df-cache',type=Path)
    parser.add_argument('--restart-source',type=Path,help='Original run whose geometry/protocol produced the inputs')
    parser.add_argument('--validate-restart-only',action='store_true')
    parser.add_argument('--scratch',type=Path,default=ROOT/'tmp/pyscf-scratch',help='Volume with sufficient free space; no existing files are removed')
    args=parser.parse_args()
    restart=any([args.initial_checkpoint,args.df_cache,args.restart_source])
    if restart and not all([args.initial_checkpoint,args.df_cache,args.restart_source]):
        parser.error('Restart requires --initial-checkpoint, --df-cache and --restart-source together')
    if args.validate_restart_only and not restart:parser.error('--validate-restart-only requires restart inputs')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();p=read(args.protocol);source=read(args.data/'manifest.json');result=read(args.data/'result.json')
    if result['status']!='PASS':raise ValueError('Parent research did not pass its local gates')
    accepted=[r for r in result['hessian_results'] if r['status']=='PASS' and r['minimum_verified']]
    selected=min(accepted,key=lambda r:r['energy_hartree'])
    geometry=args.data/f"geometry_{selected['source_id']:04}.xyz"
    from rdkit import Chem
    from run_research_quantum import structure
    from conformer_ensemble import geometry_identity
    template,_=structure(source['name'])
    if Chem.MolToSmiles(Chem.RemoveHs(template),isomericSmiles=True)!=source['canonical_state_smiles']:
        raise ValueError('Source chemical state no longer matches the structure builder')
    molecule=geometry_identity(template,geometry.read_text(),source['charge'])
    electrons=sum(a.GetAtomicNum() for a in molecule.GetAtoms())-source['charge']
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'argv':sys.argv,'platform':platform.platform(),
        'python':sys.version,'protocol':p,'protocol_sha256':sha(args.protocol),'runner_sha256':sha(__file__),
        'helper_sha256':sha(ROOT/'practicuum/shared/conformer_ensemble.py'),
        'structure_builder_sha256':sha(ROOT/'scripts/run_research_quantum.py'),
        'parent_manifest_sha256':sha(args.data/'manifest.json'),'parent_result_sha256':sha(args.data/'result.json'),
        'geometry_sha256':sha(geometry),'geometry_source_id':selected['source_id'],
        'geometry_model':'GFN2-xTB 6.8.0 / ALPB water gsolv, independently projected positive Hessian',
        'canonical_state_smiles':source['canonical_state_smiles'],'charge':source['charge'],'spin_2S':0,
        'all_electrons':electrons,'packages':{k:importlib.metadata.version(k) for k in ['pyscf','numpy','scipy','rdkit','h5py']}}
    if p.get('scratch_compression'):
        manifest['IO_helper_sha256']=sha(ROOT/'practicuum/shared/lossless_scratch.py')
        shutil.copyfile(ROOT/'practicuum/shared/lossless_scratch.py',out/'io-helper-source.py')
    if restart:
        manifest['restart_inputs']={'source_run':str(args.restart_source.resolve()),
            'source_manifest_sha256':sha(args.restart_source/'manifest.json'),
            'checkpoint':str(args.initial_checkpoint.resolve()),'cache':str(args.df_cache.resolve()),
            'helper_sha256':sha(ROOT/'practicuum/shared/electronic_restart.py'),
            'prior_convergence_accepted':False}
        shutil.copyfile(ROOT/'practicuum/shared/electronic_restart.py',out/'restart-helper-source.py')
    save(out/'manifest.json',manifest);shutil.copyfile(__file__,out/'runner-source.py');shutil.copyfile(geometry,out/'input.xyz')
    scratch=None;mf=None;td=None;io_stack=ExitStack();io_ledger=[];initial_density=None;restart_audit=None
    try:
        args.scratch.mkdir(parents=True,exist_ok=True)
        free=shutil.disk_usage(args.scratch).free
        required_GiB=(p['resources'].get('scratch_reserve_GiB',4)+1) if restart else p['resources']['minimum_scratch_free_GiB']
        required=required_GiB*1024**3
        save(out/'scratch-preflight.json',{'path':str(args.scratch.resolve()),'free_bytes':free,'required_free_bytes':required,
            'mode':'read-only cache reuse, subject to all compatibility gates' if restart else 'new integral construction',
            'basis_AO_and_auxiliary_tensor_size':'Conservative storage reserve, not a change of electronic method'})
        if free<required:
            save(out/'blocked.json',{'status':'BLOCKED','reason':'Insufficient free scratch space before SCF',
                'free_bytes':free,'required_free_bytes':required,'SCF':'NOT_RUN','TDDFT':'NOT_RUN'})
            raise SystemExit(2)
        scratch=tempfile.TemporaryDirectory(prefix='vertical-',dir=args.scratch)
        import numpy as np
        from pyscf import gto,dft,lib
        from scipy.constants import physical_constants
        lib.param.TMPDIR=scratch.name
        if p.get('scratch_compression'):
            if p['scratch_compression']!='gzip1-shuffle-fletcher32':raise ValueError('Unsupported scratch compression')
            from lossless_scratch import compressed_scratch
            io_stack.enter_context(compressed_scratch(scratch.name,
                minimum_free_bytes=p['resources']['scratch_reserve_GiB']*1024**3,ledger=io_ledger))
        lib.num_threads(p['resources']['threads'])
        mol=gto.M(atom='\n'.join(geometry.read_text().splitlines()[2:]),basis=p['basis'],unit='Angstrom',
            charge=source['charge'],spin=0,max_memory=p['resources']['memory_MB'],verbose=4,output=str(out/'pyscf.log'))
        if mol.nelectron!=electrons:raise ValueError('All-electron count mismatch')
        mf=dft.RKS(mol).density_fit();mf.xc=p['functional']
        mf.with_df._cderi_to_save=str(Path(scratch.name)/'integrals.h5')
        mf=mf.PCM()
        mf.with_solvent.method=p['solvent_model'];mf.with_solvent.eps=p['static_dielectric']
        mf.with_solvent.eps_optical=p['optical_dielectric'];mf.with_solvent.lebedev_order=p['surface_lebedev_order']
        mf.with_solvent.max_memory=p['resources']['memory_MB'];mf.grids.level=p['grid_level']
        mf.conv_tol=p['scf_energy_tolerance_Eh'];mf.conv_tol_grad=p['scf_orbital_gradient_tolerance']
        mf.max_cycle=p['scf_max_cycles'];mf.chkfile=str(out/'checkpoint.h5')
        save(out/'basis.json',{'AO_count':mol.nao_nr(),'orbital_basis':mol._basis,
            'requested_auxiliary_basis':mf.with_df.auxbasis,'resolved_auxiliary_basis_status':'recorded after SCF'})
        if restart:
            old=read(args.restart_source/'manifest.json')
            for key in ['functional','basis','density_fitting','grid_level','solvent_model','static_dielectric',
                        'optical_dielectric','surface_lebedev_order','equilibrium_solvation']:
                if old['protocol'][key]!=p[key]:raise ValueError('Restart protocol differs: '+key)
            for key in ['charge','spin_2S','all_electrons','geometry_sha256']:
                if old[key]!=manifest[key]:raise ValueError('Restart state/geometry differs: '+key)
            for key in ['pyscf','numpy','scipy']:
                if old['packages'][key]!=manifest['packages'][key]:raise ValueError('Restart engine version differs: '+key)
            if sha(args.restart_source/'input.xyz')!=manifest['geometry_sha256']:
                raise ValueError('Original input geometry bytes changed')
            from electronic_restart import density_guess,verify_and_attach_df
            initial_density,density_report=density_guess(mol,args.initial_checkpoint)
            print('Validating full and range-separated cached integrals against direct sampled integrals',flush=True)
            cache_report=verify_and_attach_df(mf,args.df_cache)
            restart_audit={'status':'PASS','scope':'Input compatibility only; previous SCF convergence not accepted',
                'density':density_report,'cache':cache_report,'validation_only':args.validate_restart_only}
            save(out/'restart-validation.json',restart_audit)
            if args.validate_restart_only:
                print('PASS input compatibility; SCF/TDDFT NOT_RUN in validation-only mode',flush=True);return
        print('Starting actual CAM//GFN2 SCF',mol.natm,'atoms',mol.nao_nr(),'AO',flush=True)
        energy=mf.kernel(dm0=initial_density)
        density_electrons=float(np.einsum('ij,ji',mf.make_rdm1(),mf.get_ovlp()))
        if not mf.converged or not np.isfinite(energy) or abs(density_electrons-electrons)>1e-6:
            raise RuntimeError('SCF or density electron-count gate failed')
        save(out/'scf.json',{'status':'PASS','energy_Eh':float(energy),'density_electrons':density_electrons,
            'converged':bool(mf.converged),'seconds':time.perf_counter()-started,
            'auxiliary_basis':mf.with_df.auxmol._basis,'stability':'NOT_RUN'})
        print('SCF converged; starting',p['singlet_states'],'full TDDFT states',flush=True)
        td=mf.TDDFT();td.nstates=p['singlet_states'];td.conv_tol=p['tddft_tolerance_Eh']
        td.max_cycle=p['tddft_max_cycles'];td.max_space=p['tddft_max_space']
        td.with_solvent.equilibrium_solvation=p['equilibrium_solvation']
        excitations,_=td.kernel()
        if len(excitations)!=p['singlet_states'] or not np.all(td.converged):raise RuntimeError('TDDFT state convergence failed')
        length=td.oscillator_strength(gauge='length');velocity=td.oscillator_strength(gauge='velocity')
        transitions=[]
        for i,(e,f,v) in enumerate(zip(excitations,length,velocity),1):
            ev=float(e*physical_constants['Hartree energy in eV'][0])
            if not np.isfinite([ev,f,v]).all() or ev<=0 or min(f,v)<-1e-8:raise ValueError('Invalid transition')
            transitions.append({'state':i,'energy_eV':ev,'wavelength_nm':1239.8419843320026/ev,
                'oscillator_strength_length':float(f),'oscillator_strength_velocity':float(v)})
        if restart and sha(args.df_cache)!=restart_audit['cache']['cache_sha256']:
            raise ValueError('Read-only integral cache changed during calculation')
        save(out/'result.json',{'status':'PASS','scope':p['scope'],'scientific_acceptance':'REVIEW_REQUIRED',
            'SCF_energy_Eh':float(energy),'transitions':transitions,'converged_states':len(transitions),
            'geometry_sha256':sha(geometry),'seconds':time.perf_counter()-started,
            'required_follow_up':p['required_follow_up'],'limitations':p['limitations']})
        print('PASS numerical SCF/TDDFT gates; scientific acceptance REVIEW_REQUIRED',flush=True)
    except Exception as error:
        save(out/'failure.json',{'status':'BLOCKED' if type(error).__name__=='ScratchSpaceError' else 'FAIL',
            'type':type(error).__name__,'message':str(error),'seconds':time.perf_counter()-started})
        raise
    finally:
        if scratch is not None:
            import gc
            mf=None;td=None;gc.collect()
            io_stack.close()
            save(out/'scratch-io.json',{'compression':p.get('scratch_compression'),'datasets':io_ledger,
                'scope':'Lossless storage only; no integral rounding or model change'})
            try:scratch.cleanup()
            except OSError as error:
                save(out/'scratch-retained.json',{'path':scratch.name,'reason':str(error),
                    'scope':'temporary integral cache; inspect handles before removing, never a scientific result'})


if __name__=='__main__':main()
