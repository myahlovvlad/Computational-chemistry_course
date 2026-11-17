from pyscf import gto, dft
mol = gto.M(atom="H 0 0 0; H 0 0 0.74", unit="Angstrom",
            basis="sto-3g", charge=0, spin=0)
mf = dft.RKS(mol)
mf.xc = "pbe"
energy = mf.kernel()
print(mf.converged, energy)