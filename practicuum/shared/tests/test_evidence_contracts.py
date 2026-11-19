import json
from pathlib import Path
import sys
import tempfile
import unittest

SHARED = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SHARED))
from dossier_records import append_record, validate_graph
from research_checks import check


class EvidenceContracts(unittest.TestCase):
    def test_previous_versions_survive_and_hashes_follow_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'input.csv').write_bytes(b'x\n1\n')
            dossier = root/'dossier'
            a = append_record(dossier, 'M01-L02', 'B', {'kind': 'calculated', 'value': 1}, root, inputs=['input.csv'])
            original = a.read_bytes()
            (root/'input.csv').write_bytes(b'x\n2\n')
            b = append_record(dossier, 'M01-L02', 'B', {'kind': 'calculated', 'value': 2}, root, inputs=['input.csv'])
            self.assertNotEqual(a, b)
            self.assertEqual(a.read_bytes(), original)
            self.assertNotEqual(json.loads(original)['input_sha256'], json.loads(b.read_bytes())['input_sha256'])

    def test_nonfinite_and_unlabelled_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for result in [{'value': 1}, {'kind': 'calculated', 'value': float('nan')}]:
                with self.assertRaises(ValueError):
                    append_record(tmp, 'M01-L02', 'B', result, tmp)
            self.assertFalse(list(Path(tmp).rglob('*.json')))

    def test_dependency_errors_and_concept_cycles(self):
        nodes = [{'id': 'a'}, {'id': 'b'}]
        self.assertTrue(validate_graph(nodes, [('a', 'b')]))
        for edges in [[('missing', 'b')], [('a', 'b'), ('b', 'a')], [('a', 'a')]]:
            with self.assertRaises(ValueError):
                validate_graph(nodes, edges)
        self.assertTrue(validate_graph(nodes, [('a', 'b'), ('b', 'a')], calculation=False))

    def test_empty_boolean_and_nonfinite_submissions(self):
        self.assertEqual(check('M01-L02', None)['status'], 'NOT_RUN')
        for value in [True, float('nan'), float('inf'), '226', 225]:
            self.assertEqual(check('M01-L02', {'n': value})['status'], 'FAIL')
        self.assertEqual(check('M01-L02', {'n': 226})['reasoning'], 'NOT_REVIEWED')
        self.assertEqual(check('M02-L01', {'same_object': 1})['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
