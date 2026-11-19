"""Conformer comparison, geometry identity and mass-weighted Hessian controls."""
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdDetermineBonds,rdMolAlign
from scipy import constants


def geometry_identity(template,xyz,charge):
    candidate=Chem.MolFromXYZBlock(xyz)
    if candidate is None:raise ValueError('Invalid XYZ geometry')
    if [a.GetSymbol() for a in candidate.GetAtoms()]!=[a.GetSymbol() for a in template.GetAtoms()]:
        raise ValueError('XYZ atom identity/order changed')
    rdDetermineBonds.DetermineBonds(candidate,charge=charge,embedChiral=True)
    expected=Chem.MolToSmiles(Chem.RemoveHs(template),isomericSmiles=True)
    observed=Chem.MolToSmiles(Chem.RemoveHs(candidate),isomericSmiles=True)
    if expected!=observed:raise ValueError('Optimized geometry changed connectivity, protonation or stereochemistry')
    return candidate


def aligned_conformer_rmsd(reference,pose):
    reference=Chem.RemoveHs(reference);pose=Chem.RemoveHs(pose)
    if Chem.MolToSmiles(reference,isomericSmiles=True)!=Chem.MolToSmiles(pose,isomericSmiles=True):
        raise ValueError('Different molecular states cannot be clustered together')
    mappings=pose.GetSubstructMatches(reference,uniquify=False,useChirality=True,maxMatches=10000)
    if not mappings or len(mappings)>=10000:raise ValueError('Unambiguous symmetry enumeration required')
    return min(rdMolAlign.GetAlignmentTransform(pose,reference,
               atomMap=[(pi,ri) for ri,pi in enumerate(mapping)],reflect=False)[0] for mapping in mappings)


def projected_frequencies(hessian,coordinates_angstrom,masses_amu):
    masses=np.asarray(masses_amu,dtype=float);xyz=np.asarray(coordinates_angstrom,dtype=float)
    H=np.asarray(hessian,dtype=float);n=len(masses)
    if H.shape!=(3*n,3*n) or xyz.shape!=(n,3) or n<2:raise ValueError('Hessian/geometry/mass shape mismatch')
    if not (np.isfinite(H).all() and np.isfinite(xyz).all() and np.isfinite(masses).all() and (masses>0).all()):
        raise ValueError('Finite Hessian and positive masses required')
    symmetry=float(np.max(abs(H-H.T)))
    if symmetry>1e-5:raise ValueError('Hessian symmetry gate failed')
    xyz=xyz-np.sum(xyz*masses[:,None],axis=0)/masses.sum();sqrt_mass=np.sqrt(masses)
    rigid=[]
    for axis in np.eye(3):rigid.append((sqrt_mass[:,None]*np.broadcast_to(axis,(n,3))).ravel())
    for axis in np.eye(3):rigid.append((sqrt_mass[:,None]*np.cross(axis,xyz)).ravel())
    U,s,_=np.linalg.svd(np.column_stack(rigid),full_matrices=True)
    rank=int(np.sum(s>s.max()*1e-10));Q=U[:,rank:]
    if rank not in {5,6}:raise ValueError('Unexpected translation/rotation rank')
    weight=np.repeat(sqrt_mass,3);F=(H+H.T)/2/np.outer(weight,weight)
    eigenvalues=np.linalg.eigvalsh(Q.T@F@Q)
    Eh=constants.physical_constants['Hartree energy'][0]
    bohr=constants.physical_constants['Bohr radius'][0]
    amu=constants.physical_constants['atomic mass constant'][0]
    factor=np.sqrt(Eh/(amu*bohr**2))/(2*np.pi*constants.c*100)
    frequencies=np.sign(eigenvalues)*np.sqrt(abs(eigenvalues))*factor
    return {'frequencies_cm1':frequencies.tolist(),'rigid_mode_rank':rank,'internal_mode_count':len(frequencies),
            'minimum_verified':bool(np.all(frequencies>0)),'lowest_frequency_cm1':float(frequencies.min()),
            'Hessian_symmetry_error':symmetry,'unit_factor_cm1':float(factor),
            'mass_basis':'explicit supplied atomic masses in u; Cartesian Hessian Eh/Bohr^2',
            'projection':'mass-weighted translation/rotation subspace removed by SVD; no deletion of an arbitrary six eigenvalues'}
