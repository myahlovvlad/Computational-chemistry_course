"""Actual water SCF/TDDFT cache-restart controls, including incompatible inputs."""
import argparse,json,shutil,sys
from pathlib import Path
import h5py
import numpy as np
from pyscf import gto,dft,lib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'practicuum/shared'))
from electronic_restart import density_guess,verify_and_attach_df,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,out/'control-source.py');lib.num_threads(1)
    mol=gto.M(atom='O 0 0 0; H 0 .757 .587; H 0 -.757 .587',basis='def2-svp',verbose=0,max_memory=1000)
    def build(label):
        mf=dft.RKS(mol).density_fit();mf.xc='CAM-B3LYP';mf.with_df._cderi_to_save=str(out/(label+'-integrals.h5'))
        mf=mf.PCM();mf.with_solvent.method='C-PCM';mf.with_solvent.eps=78.3553;mf.with_solvent.eps_optical=1.78
        mf.with_solvent.lebedev_order=17;mf.conv_tol=1e-10;mf.conv_tol_grad=1e-7;mf.chkfile=str(out/(label+'-checkpoint.h5'))
        return mf
    def excitation(mf):
        td=mf.TDDFT();td.nstates=3;td.conv_tol=1e-7;td.with_solvent.equilibrium_solvation=False
        e,_=td.kernel()
        if not np.all(td.converged):raise ValueError('Control excitations did not converge')
        return e,td.oscillator_strength(gauge='length')
    first=build('reference');e1=first.kernel();x1,f1=excitation(first)
    if not first.converged:raise ValueError('Reference SCF failed')
    cache=out/'reference-integrals.h5';checkpoint=out/'reference-checkpoint.h5';before=sha(cache)
    second=build('restarted');D,density_report=density_guess(second.mol,checkpoint)
    cache_report=verify_and_attach_df(second,cache);e2=second.kernel(dm0=D);x2,f2=excitation(second)
    if not second.converged or abs(e2-e1)>1e-9 or not np.allclose(x1,x2,atol=1e-8,rtol=1e-8) or not np.allclose(f1,f2,atol=1e-7,rtol=1e-6):
        raise ValueError('Restart SCF/TDDFT parity failed')
    if (out/'restarted-integrals.h5').exists() or sha(cache)!=before:raise ValueError('Cache was rebuilt or changed')
    wrong=mol.copy();coords=wrong.atom_coords();coords[0,0]+=.01;wrong.set_geom_(coords,unit='Bohr')
    rejected_geometry=False
    try:density_guess(wrong,checkpoint)
    except ValueError:rejected_geometry=True
    corrupt=out/'deliberately-corrupted-integrals.h5';shutil.copyfile(cache,corrupt)
    with h5py.File(corrupt,'a') as f:f['j3c/0'][0,0]+=0.1
    rejected_corruption=False
    try:verify_and_attach_df(build('negative'),corrupt)
    except ValueError as error:rejected_corruption='compatibility failed' in str(error)
    if not rejected_geometry or not rejected_corruption:raise ValueError('Invalid restart input was accepted')
    report={'status':'PASS','scope':__doc__,'SCF_energy_difference_Eh':float(e2-e1),
      'max_TDDFT_energy_difference_Eh':float(max(abs(x2-x1))),
      'max_oscillator_strength_difference':float(max(abs(f2-f1))),
      'density':density_report,'cache':cache_report,'cache_unchanged':True,
      'wrong_geometry':'REJECTED_AS_EXPECTED','corrupted_tensor':'REJECTED_AS_EXPECTED',
      'target_drug_result':'NOT_CLAIMED'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
