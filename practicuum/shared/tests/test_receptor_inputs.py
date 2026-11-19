from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from receptor_inputs import normalize_pqr


class ReceptorInputs(unittest.TestCase):
    def test_four_digit_residue_does_not_merge_into_chain(self):
        line='ATOM    3195  N    ALA A1001     -18.801  -34.987  122.881 -0.4157 1.8240'
        fields=normalize_pqr(line).split()
        self.assertEqual(fields[4:6],['A','1001'])
        self.assertEqual(fields[-5:],['-18.801','-34.987','122.881','-0.4157','1.8240'])

    def test_small_residue_and_chainless_records_preserve_values(self):
        a='ATOM       1  N    ALA A   0       2.695   21.659  138.872  0.1414 1.8240'
        b='ATOM 1 N ALA 42 2.695 21.659 138.872 0.1414 1.8240'
        self.assertEqual(normalize_pqr(a).split()[4:6],['A','0'])
        self.assertEqual(normalize_pqr(b).split()[4],'42')

    def test_malformed_or_nonfinite_input_rejected(self):
        for text in ['ATOM 1 N ALA A1001 bad', 'ATOM 1 N ALA A1001 nan 0 0 -.4 1.8']:
            with self.assertRaises(ValueError):normalize_pqr(text)

    def test_forcefield_zero_hydrogen_radius_preserved(self):
        line='ATOM 2 HA ALA A 1 0 0 0 .1 0.0000'
        self.assertEqual(normalize_pqr(line).split()[-1],'0.0000')

    def test_histidine_alias_does_not_change_protons_or_charges(self):
        line='ATOM 2 HD1 HID A 861 0 0 0 .354 1.2'
        fields=normalize_pqr(line,canonical_resnames=True).split()
        self.assertEqual(fields[3],'HIS')
        self.assertEqual(fields[2],'HD1')
        self.assertEqual(fields[-2:],['.354','1.2'])
