"""Regression checks for scientific and input contracts."""
import unittest
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from chemistry import standardize, screen, descriptors, p_activity
from pipeline import process_csv
from h2_scf import rhf_h2
from docking import mapped_rmsd

DATA=Path(__file__).resolve().parents[1]/'data'


class LaboratoryContracts(unittest.TestCase):
    def test_salt_and_covalent_halogen(self):
        self.assertEqual(standardize('CC(=O)[O-].[Na+]').parent_smiles,'CC(=O)O')
        self.assertIn('Cl',standardize('Clc1ccccc1').parent_smiles)

    def test_stereo_and_tautomer_policy(self):
        self.assertNotEqual(standardize('C[C@H](O)C(=O)O').parent_smiles,
                            standardize('C[C@@H](O)C(=O)O').parent_smiles)
        a,b='O=c1cccc[nH]1','Oc1ccccn1'
        self.assertNotEqual(standardize(a).parent_smiles,standardize(b).parent_smiles)
        self.assertEqual(standardize(a,True).parent_smiles,standardize(b,True).parent_smiles)

    def test_units_and_invalid_numbers(self):
        self.assertEqual(p_activity(100,'nM'),7)
        self.assertEqual(p_activity(0.1,'uM'),7)
        for value in [0,-1,math.nan]:
            with self.assertRaises(ValueError):p_activity(value,'M')

    def test_structural_alert_is_not_verdict(self):
        self.assertEqual(screen('Oc1ccccc1O')['status'],'review')
        self.assertIn('unknown',screen('CCO')['reason'])

    def test_complete_table_contract(self):
        data=DATA.joinpath('molecules.csv').read_bytes()
        rows,passport=process_csv(data)
        self.assertEqual(len(rows),12)
        self.assertEqual(sum(row['status']=='invalid' for row in rows),2)
        self.assertEqual(passport['rows'],12)

    def test_schema_duplicate_and_limit(self):
        for data in [b'id,wrong\nX,CCO\n',b'id,smiles\nX,CCO\nX,CCN\n']:
            with self.assertRaises(ValueError):process_csv(data)
        with self.assertRaises(ValueError):process_csv(b'id,smiles\nA,CCO\nB,CCN\n',max_rows=1)

    def test_tautomer_option_reaches_the_table_policy(self):
        data=b'id,smiles\nA,O=c1cccc[nH]1\nB,Oc1ccccn1\n'
        separate,passport=process_csv(data)
        merged,canonical_passport=process_csv(data,canonical_tautomer=True)
        self.assertNotEqual(separate[0]['parent_smiles'],separate[1]['parent_smiles'])
        self.assertEqual(merged[0]['parent_smiles'],merged[1]['parent_smiles'])
        self.assertIn('tautomer=False',passport['policy'])
        self.assertIn('tautomer=True',canonical_passport['policy'])

    def test_rhf_physical_reference(self):
        result=rhf_h2(.74)
        self.assertTrue(result['converged'])
        self.assertAlmostEqual(result['energy_hartree'],-1.116759307,places=6)
        with self.assertRaises(ValueError):rhf_h2(0)

    def test_pose_reference(self):
        data=DATA/'docking'
        rmsd=mapped_rmsd(data/'1iep_ligand.pdbqt',data/'1iep_ligand_vina_out.pdbqt')
        self.assertAlmostEqual(rmsd,0.9067287654,places=5)


if __name__=='__main__':unittest.main()
