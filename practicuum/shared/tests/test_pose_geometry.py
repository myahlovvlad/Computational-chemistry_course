from pathlib import Path
import sys,unittest
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pose_geometry import rmsd_without_alignment


class PoseGeometryTests(unittest.TestCase):
    def molecule(self,smiles='CCO'):
        mol=Chem.AddHs(Chem.MolFromSmiles(smiles));AllChem.EmbedMolecule(mol,randomSeed=11)
        return Chem.RemoveHs(mol)

    def test_translation_remains_visible(self):
        reference=self.molecule();shifted=Chem.Mol(reference);conf=shifted.GetConformer()
        for i in range(shifted.GetNumAtoms()):
            xyz=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(xyz.x+1,xyz.y,xyz.z))
        self.assertAlmostEqual(rmsd_without_alignment(reference,shifted),1.,places=10)

    def test_atom_reordering_does_not_change_pose(self):
        reference=self.molecule()
        reordered=Chem.RenumberAtoms(reference,list(reversed(range(reference.GetNumAtoms()))))
        self.assertAlmostEqual(rmsd_without_alignment(reference,reordered),0.,places=12)

    def test_changed_bond_graph_is_not_full_graph_isomorphism(self):
        with self.assertRaises(ValueError):rmsd_without_alignment(self.molecule('CCC'),self.molecule('C1CC1'))

    def test_changed_stereochemistry_is_rejected(self):
        with self.assertRaises(ValueError):rmsd_without_alignment(self.molecule('F[C@H](Cl)Br'),self.molecule('F[C@@H](Cl)Br'))
