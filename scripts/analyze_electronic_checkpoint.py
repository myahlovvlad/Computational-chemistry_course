"""Independent density/TD-vector audit of a completed composite excitation run.

NTO-like weights below use normalized X only, matching PySCF's documented CIS
interpretation. Y is retained and its size reported; no full-TDM claim is made.
"""
from datetime import datetime,timezone
import argparse,hashlib,importlib.metadata,json,shutil,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();parent=read(args.run/'manifest.json');result=read(args.run/'result.json')
    if result['status']!='PASS':raise ValueError('Completed numerical excitation result required')
    save(out/'manifest.json',{'utc':datetime.now(timezone.utc).isoformat(),'argv':sys.argv,'auditor_sha256':sha(__file__),
        'parent_manifest_sha256':sha(args.run/'manifest.json'),'parent_result_sha256':sha(args.run/'result.json'),
        'checkpoint_sha256':sha(args.run/'checkpoint.h5'),'PySCF':importlib.metadata.version('pyscf'),
        'scope':__doc__})
    shutil.copyfile(__file__,out/'auditor-source.py')
    try:
        from pyscf import dft,lib
        lib.num_threads(2)
        mol=lib.chkfile.load_mol(str(args.run/'checkpoint.h5'))
        scf=lib.chkfile.load(str(args.run/'checkpoint.h5'),'scf')
        e=np.asarray(lib.chkfile.load(str(args.run/'checkpoint.h5'),'tddft/e'))
        xy=lib.chkfile.load(str(args.run/'checkpoint.h5'),'tddft/xy')
        C=np.asarray(scf['mo_coeff']);occ=np.asarray(scf['mo_occ']);S=mol.intor_symmetric('int1e_ovlp')
        density=(C*occ)@C.conj().T;electrons=float(np.einsum('ij,ji',density,S).real)
        metric_error=float(np.max(abs(C.conj().T@S@C-np.eye(C.shape[1]))))
        idempotency=float(np.linalg.norm(density@S@density-2*density)/np.linalg.norm(density))
        if abs(electrons-parent['all_electrons'])>1e-6 or metric_error>1e-7 or idempotency>1e-6:
            raise ValueError('Density/orthonormality/idempotency gate failed')
        if mol.nelectron!=parent['all_electrons'] or set(occ)!={0.,2.}:raise ValueError('Closed-shell state changed')
        xyz=np.array([[float(v) for v in line.split()[1:]] for line in (args.run/'input.xyz').read_text().splitlines()[2:] if line.strip()])
        if np.max(abs(xyz-mol.atom_coords(unit='Angstrom')))>1e-9:raise ValueError('Checkpoint geometry changed')
        mf=dft.RKS(mol).density_fit();mf.xc=parent['protocol']['functional'];mf=mf.PCM()
        mf.with_solvent.method='C-PCM';mf.with_solvent.eps=parent['protocol']['static_dielectric']
        mf.with_solvent.eps_optical=parent['protocol']['optical_dielectric']
        for key in ['mo_coeff','mo_occ','mo_energy','e_tot']:setattr(mf,key,scf[key])
        td=mf.TDDFT();td.e=e;td.xy=xy;td.with_solvent.equilibrium_solvation=False
        f=td.oscillator_strength(gauge='length');v=td.oscillator_strength(gauge='velocity')
        expected=np.array([r['oscillator_strength_length'] for r in result['transitions']])
        expected_v=np.array([r['oscillator_strength_velocity'] for r in result['transitions']])
        if not np.allclose(f,expected,rtol=1e-6,atol=1e-8) or not np.allclose(v,expected_v,rtol=1e-6,atol=1e-8):
            raise ValueError('Independent oscillator-strength reconstruction failed')
        from scipy.constants import physical_constants
        ev=e*physical_constants['Hartree energy in eV'][0]
        if not np.allclose(ev,[r['energy_eV'] for r in result['transitions']],rtol=1e-10,atol=1e-9):
            raise ValueError('Excitation energy/checkpoint mismatch')
        states=[];nocc=int(np.count_nonzero(occ==2));nto_orbitals={}
        export=set([0,*np.argsort(f)[-3:].tolist()])
        for index,(X,Y) in enumerate(xy):
            X=np.asarray(X);Y=np.asarray(Y);x2=float(np.vdot(X,X).real);y2=float(np.vdot(Y,Y).real)
            norm=2*(x2-y2)
            if abs(norm-1)>1e-6:raise ValueError('TDDFT symplectic normalization failed')
            # Work on a new normalized array: native get_nto normalizes X in-place.
            U,s,Vh=np.linalg.svd(X/np.sqrt(x2),full_matrices=False);weights=s*s
            if abs(weights.sum()-1)>1e-10:raise ValueError('X-only SVD normalization failed')
            indices=np.unravel_index(np.argsort(abs(X).ravel())[-5:][::-1],X.shape)
            pairs=[{'occupied_MO_1based':int(i+1),'virtual_MO_1based':int(nocc+j+1),
                    'normalized_X_squared_weight':float(abs(X[i,j])**2/x2)} for i,j in zip(*indices)]
            states.append({'state':index+1,'energy_eV':float(ev[index]),'oscillator_strength_length':float(f[index]),
                'TDDFT_norm_2_X2_minus_Y2':norm,'X_norm_squared':x2,'Y_norm_squared':y2,
                'X_only_NTO_weights':weights[:10].tolist(),'dominant_X_MO_pairs':pairs,
                'interpretation':'CIS-like X-only character; de-excitation contribution not incorporated into this SVD'})
            if index in export:
                nto_orbitals[f'state_{index+1}_hole_AO']=C[:,occ==2]@U[:,0]
                nto_orbitals[f'state_{index+1}_particle_AO']=C[:,occ==0]@Vh[0,:].conj()
        np.savez_compressed(out/'electronic_wavefunction.npz',mo_coeff=C,mo_occ=occ,mo_energy=scf['mo_energy'],
            transition_energies_Eh=e,X=np.asarray([p[0] for p in xy]),Y=np.asarray([p[1] for p in xy]),**nto_orbitals)
        save(out/'result.json',{'status':'PASS','scope':__doc__,'density_electrons':electrons,
            'MO_metric_max_error':metric_error,'closed_shell_density_idempotency_relative_error':idempotency,
            'orbital_gap_eV_not_excitation':float((scf['mo_energy'][nocc]-scf['mo_energy'][nocc-1])*physical_constants['Hartree energy in eV'][0]),
            'states':states,'wavefunction_sha256':sha(out/'electronic_wavefunction.npz'),
            'SCF_stability':'NOT_RUN','geometry_DFT_minimum':'NOT_CLAIMED','scientific_acceptance':'REVIEW_REQUIRED',
            'seconds':time.perf_counter()-start})
        print('PASS independent density/transition reconstruction; physical validation REVIEW_REQUIRED')
    except Exception as error:
        save(out/'failure.json',{'status':'FAIL','type':type(error).__name__,'message':str(error),'seconds':time.perf_counter()-start})
        raise


if __name__=='__main__':main()
