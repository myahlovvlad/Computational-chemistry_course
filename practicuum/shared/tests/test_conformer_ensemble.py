from pathlib import Path
import sys,unittest
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from conformer_ensemble import aligned_conformer_rmsd,projected_frequencies


class ConformerControls(unittest.TestCase):
    def test_alignment_is_allowed_for_isolated_conformers(self):
        reference=Chem.AddHs(Chem.MolFromSmiles('CCO'));AllChem.EmbedMolecule(reference,randomSeed=11)
        moved=Chem.Mol(reference);conf=moved.GetConformer()
        for i in range(moved.GetNumAtoms()):
            p=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(-p.y+2,p.x-3,p.z+1))
        self.assertLess(aligned_conformer_rmsd(reference,moved),1e-6)

    def test_diatomic_spring_has_one_internal_mode_and_correct_units(self):
        H=np.zeros((6,6));k=.1;H[0,0]=H[3,3]=k;H[0,3]=H[3,0]=-k
        result=projected_frequencies(H,[[0,0,0],[1,0,0]],[12.,16.])
        self.assertEqual(result['rigid_mode_rank'],5)
        self.assertEqual(result['internal_mode_count'],1)
        self.assertAlmostEqual(result['lowest_frequency_cm1'],result['unit_factor_cm1']*np.sqrt(k*(1/12+1/16)),places=9)
        self.assertTrue(result['minimum_verified'])

    def test_negative_internal_curvature_is_not_clipped(self):
        H=np.zeros((6,6));H[0,0]=H[3,3]=-.1;H[0,3]=H[3,0]=.1
        result=projected_frequencies(H,[[0,0,0],[1,0,0]],[12.,16.])
        self.assertFalse(result['minimum_verified']);self.assertLess(result['lowest_frequency_cm1'],0)
