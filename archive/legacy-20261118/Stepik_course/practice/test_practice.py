"""Scientific regression checks for the teaching examples."""

import csv
import math
import unittest
from pathlib import Path

from chemistry import (curate_activity, descriptors, optimize_conformer,
                       p_activity, parse, screen, similarity, standardize)
from stepik_tasks import enrichment, tanimoto, z_prime
from stepik_tasks import p_activity as stepik_p_activity


class ChemistryTests(unittest.TestCase):
    def test_equivalent_serializations(self):
        self.assertEqual(standardize("CCO").parent_smiles, standardize("OCC").parent_smiles)

    def test_salt_retains_raw_and_matches_acid_parent(self):
        salt = "CC(=O)[O-].[Na+]"
        result = standardize(salt)
        self.assertEqual(result.raw_smiles, salt)
        self.assertEqual(result.parent_smiles, standardize("CC(=O)O").parent_smiles)
        self.assertNotIn("Na", result.parent_smiles)

    def test_covalent_chlorine_survives(self):
        mol = parse(standardize("Clc1ccccc1").parent_smiles)
        self.assertTrue(any(atom.GetSymbol() == "Cl" for atom in mol.GetAtoms()))

    def test_stereochemistry_not_collapsed(self):
        self.assertNotEqual(standardize("C[C@H](O)C(=O)O").parent_smiles,
                            standardize("C[C@@H](O)C(=O)O").parent_smiles)

    def test_tautomer_canonicalization_is_explicit(self):
        pair = ("O=c1cccc[nH]1", "Oc1ccccn1")
        self.assertNotEqual(*(standardize(s).parent_smiles for s in pair))
        self.assertEqual(*(standardize(s, canonical_tautomer=True).parent_smiles for s in pair))

    def test_invalid_and_empty(self):
        for smiles in ("not_a_smiles", "", " "):
            with self.subTest(smiles=smiles):
                self.assertEqual(screen(smiles)["status"], "invalid")

    def test_expected_descriptors(self):
        self.assertAlmostEqual(descriptors("CCO")["MolWt"], 46.069, places=2)
        self.assertEqual(descriptors("c1ccccc1")["TPSA"], 0.0)
        self.assertEqual(descriptors("CCO")["ro5_violations"], 0)

    def test_all_four_ro5_conditions(self):
        # Twelve hydroxyls cause both HBD and HBA violations; MW and logP do not.
        result = descriptors("OC(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)CO")
        self.assertGreater(result["HBD"], 5)
        self.assertGreater(result["HBA"], 10)
        self.assertEqual(result["ro5_violations"], 2)

    def test_pains_is_review(self):
        result = screen("Oc1ccccc1O")
        self.assertTrue(result["alerts"])
        self.assertEqual(result["status"], "review")

    def test_no_alert_is_not_activity(self):
        result = screen("CCO")
        self.assertEqual(result["status"], "eligible")
        self.assertIn("unknown", result["reason"])

    def test_morgan_properties(self):
        self.assertEqual(similarity("CCO", "OCC"), 1.0)
        self.assertAlmostEqual(similarity("CCO", "CCN"), similarity("CCN", "CCO"))
        self.assertTrue(0 <= similarity("CCO", "c1ccccc1") <= 1)

    def test_conformer(self):
        result = optimize_conformer("CCCC")
        self.assertEqual(result["n_conformers"], 1)
        self.assertTrue(result["converged"])
        self.assertTrue(math.isfinite(result["energy_kcal_mol"]))

    def test_activity_units_and_failures(self):
        for function in (p_activity, stepik_p_activity):
            self.assertAlmostEqual(function(100, "nM"), 7)
            self.assertAlmostEqual(function(0.1, "uM"), 7)
            for value, unit in ((0, "nM"), (-1, "M"), (1, "bad"), (math.nan, "M")):
                with self.assertRaises(ValueError):
                    function(value, unit)

    def test_curated_rows(self):
        with Path(__file__).with_name("activities.csv").open(encoding="utf-8") as handle:
            output = [curate_activity(row) for row in csv.DictReader(handle)]
        included = [row for row in output if row["status"] == "included"]
        self.assertEqual([row["record_id"] for row in included], ["R01", "R02"])
        self.assertTrue(all(row["pIC50"] == 7 for row in included))
        self.assertEqual(len(output), 8)


class PurePythonTests(unittest.TestCase):
    def test_tanimoto_cases(self):
        self.assertEqual(tanimoto({1, 2, 3}, {2, 3, 4}), 0.5)
        self.assertEqual(tanimoto(set(), set()), 1.0)
        self.assertEqual(tanimoto({1}, {2}), 0.0)

    def test_enrichment(self):
        self.assertEqual(enrichment(1000, 20, 50, 5), 5)
        for args in ((100, 0, 10, 0), (100, 10, 0, 0), (10, 8, 9, 1)):
            with self.assertRaises(ValueError):
                enrichment(*args)

    def test_z_prime(self):
        self.assertAlmostEqual(z_prime(100, 10, 5, 5), 2 / 3)
        self.assertLess(z_prime(100, 10, 20, 20), 0)
        with self.assertRaises(ValueError):
            z_prime(10, 10, 1, 1)


if __name__ == "__main__":
    unittest.main()
