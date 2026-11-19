"""Chemical-identity-preserving pose comparisons in the receptor coordinate frame."""
import numpy as np
from rdkit import Chem


def rmsd_without_alignment(reference,pose,conf_id=0):
    reference=Chem.RemoveHs(reference);pose=Chem.RemoveHs(pose)
    if Chem.MolToSmiles(reference,isomericSmiles=True)!=Chem.MolToSmiles(pose,isomericSmiles=True):
        raise ValueError('Reference/pose chemical identity mismatch')
    matches=pose.GetSubstructMatches(reference,uniquify=False,useChirality=True,maxMatches=10000)
    if not matches:raise ValueError('No stereochemistry-preserving graph isomorphism')
    if len(matches)>=10000:raise RuntimeError('Symmetry enumeration truncated; explicit mapping required')
    target=np.asarray(reference.GetConformer().GetPositions());coordinates=np.asarray(pose.GetConformer(conf_id).GetPositions())
    return min(float(np.sqrt(np.mean(np.sum((coordinates[list(mapping)]-target)**2,axis=1)))) for mapping in matches)
