"""Compare real disk-backed CAM/TDDFT with/without lossless integral compression."""
from contextlib import nullcontext
import hashlib,json,sys,tempfile
from pathlib import Path
import h5py
import numpy as np
from pyscf import gto,dft,lib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'practicuum/shared'))
from lossless_scratch import compressed_scratch


def main():
    (ROOT/'tmp').mkdir(exist_ok=True)
    lib.num_threads(1);runs=[];ledger=[]
    original=h5py.Group.create_dataset
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='lossless-check-') as temporary:
        root=Path(temporary)
        for compressed in [False,True]:
            folder=root/str(compressed);folder.mkdir()
            context=compressed_scratch(folder,minimum_free_bytes=1024**3,ledger=ledger,minimum_dataset_bytes=128*1024) if compressed else nullcontext()
            with context:
                mol=gto.M(atom='O 0 0 0; H 0 .757 .587; H 0 -.757 .587',basis='def2-tzvp',verbose=0,max_memory=1000)
                mf=dft.RKS(mol).density_fit();mf.xc='CAM-B3LYP';mf.with_df._cderi_to_save=str(folder/'integrals.h5')
                mf=mf.PCM();mf.with_solvent.method='C-PCM';mf.with_solvent.eps=78.3553;mf.with_solvent.eps_optical=1.78
                mf.with_solvent.lebedev_order=17;mf.conv_tol=1e-10
                energy=mf.kernel();td=mf.TDDFT();td.nstates=3;td.conv_tol=1e-7;td.with_solvent.equilibrium_solvation=False
                excitation,_=td.kernel()
                if not mf.converged or not np.all(td.converged):raise RuntimeError('Calibration calculation did not converge')
                arrays={}
                with h5py.File(folder/'integrals.h5','r') as stream:
                    def collect(name,obj):
                        if isinstance(obj,h5py.Dataset):arrays[name]=obj[...]
                    stream.visititems(collect)
                runs.append({'energy':float(energy),'excitations':excitation.copy(),'integrals':arrays,
                             'file_size':(folder/'integrals.h5').stat().st_size})
        if not ledger or h5py.Group.create_dataset is not original:raise RuntimeError('Compression not exercised or patch not restored')
        if runs[0]['integrals'].keys()!=runs[1]['integrals'].keys():raise RuntimeError('Different DF integral datasets')
        bitwise=all(np.array_equal(runs[0]['integrals'][k],runs[1]['integrals'][k]) for k in runs[0]['integrals'])
        energy_change=abs(runs[0]['energy']-runs[1]['energy']);excitation_change=float(max(abs(runs[0]['excitations']-runs[1]['excitations'])))
        if not bitwise or energy_change>1e-10 or excitation_change>1e-9:raise RuntimeError('Lossless control failed')
        print(json.dumps({'status':'PASS','scope':__doc__,'bitwise_DF_integrals_equal':bitwise,
            'SCF_energy_difference_Eh':energy_change,'max_excitation_difference_Eh':excitation_change,
            'file_sizes_bytes':[r['file_size'] for r in runs],
            'compression_ledger':ledger,'target_drug_spectrum_validation':'NOT_CLAIMED'}))


if __name__=='__main__':main()
