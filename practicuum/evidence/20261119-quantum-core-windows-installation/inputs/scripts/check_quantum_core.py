"""Small installation check: water SCF and nonequilibrium TDDFT, not a drug case."""
import json
import numpy as np
from pyscf import gto,dft,lib


def main():
    lib.num_threads(2)
    mol=gto.M(atom='O 0 0 0; H 0 .757 .587; H 0 -.757 .587',basis='def2-svp',verbose=3,max_memory=1000)
    mf=dft.RKS(mol).density_fit();mf.xc='CAM-B3LYP';mf=mf.PCM()
    mf.with_solvent.method='C-PCM';mf.with_solvent.eps=78.3553;mf.with_solvent.eps_optical=1.78
    mf.with_solvent.lebedev_order=17;mf.conv_tol=1e-9
    energy=mf.kernel();electrons=float(np.einsum('ij,ji',mf.make_rdm1(),mf.get_ovlp()))
    if not mf.converged or not np.isfinite(energy) or abs(electrons-10)>1e-6:
        raise RuntimeError('Installation SCF/electron-count check failed')
    td=mf.TDDFT();td.nstates=3;td.conv_tol=1e-6;td.with_solvent.equilibrium_solvation=False
    states,_=td.kernel();osc=td.oscillator_strength(gauge='length')
    if len(states)!=3 or not np.all(td.converged) or not np.isfinite(states).all() or min(states)<=0:
        raise RuntimeError('Installation TDDFT check failed')
    if not np.isfinite(osc).all() or min(osc)<-1e-8:raise RuntimeError('Invalid oscillator strength')
    print(json.dumps({'status':'PASS','scope':__doc__,'energy_Eh':float(energy),
        'excitation_energies_Eh':states.tolist(),'oscillator_strengths':osc.tolist(),'density_electrons':electrons}))


if __name__=='__main__':main()
