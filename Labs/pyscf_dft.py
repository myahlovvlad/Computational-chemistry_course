"""Optional PySCF extension; requires a supported Linux/macOS/WSL environment.

This script has NOT been executed in the verified native Windows environment.
It never silently substitutes an RHF energy for a DFT result.
"""
from __future__ import annotations
import json
from pathlib import Path


def run(output: Path) -> dict:
    try:
        import pyscf
        from pyscf import gto,scf,dft
    except ImportError as error:
        raise RuntimeError('Install PySCF in a supported environment; see Labs/extensions/README.md') from error
    mol=gto.M(atom='H 0 0 0; H 0 0 0.74',unit='Angstrom',basis='sto-3g',charge=0,spin=0,verbose=0)
    hf=scf.RHF(mol)
    hf.conv_tol=1e-10
    hf_energy=hf.kernel()
    ks=dft.RKS(mol)
    ks.xc='PBE'
    ks.conv_tol=1e-10
    ks.grids.level=4
    dft_energy=ks.kernel()
    if not hf.converged or not ks.converged:
        raise RuntimeError('An electronic calculation did not converge')
    result={'pyscf':pyscf.__version__,'geometry_A':'H 0 0 0; H 0 0 0.74','basis':'sto-3g',
            'charge':0,'spin_Nalpha_minus_Nbeta':0,'functional':'PBE','grid_level':4,
            'RHF_energy_hartree':float(hf_energy),'DFT_energy_hartree':float(dft_energy),
            'HF_converged':bool(hf.converged),'DFT_converged':bool(ks.converged),
            'scope':'single points, no optimization, frequencies or thermochemical corrections'}
    output.mkdir(parents=True,exist_ok=True)
    (output/'pyscf_dft.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    print(json.dumps(run(Path(__file__).with_name('results')/'dft'),indent=2))
