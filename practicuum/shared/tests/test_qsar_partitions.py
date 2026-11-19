from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_target_qsar import validate_partitions


class PartitionAuditTests(unittest.TestCase):
    def test_disjoint_rows_do_not_allow_shared_scaffolds(self):
        parts={'training':{'row_ids':[0],'scaffolds':['A']},'test':{'row_ids':[1],'scaffolds':['A']}}
        with self.assertRaisesRegex(ValueError,'Scaffold leakage'):validate_partitions(['A','A'],parts)

    def test_missing_rows_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'cover'):
            validate_partitions(['A','B'],{'training':{'row_ids':[0],'scaffolds':['A']}})

    def test_duplicate_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_partitions(['A'],{'training':{'row_ids':[0,0],'scaffolds':['A']}})

    def test_ledger_must_match_molecular_scaffolds(self):
        with self.assertRaisesRegex(ValueError,'ledger'):
            validate_partitions(['A'],{'training':{'row_ids':[0],'scaffolds':['WRONG']}})

    def test_valid_groups_pass(self):
        validate_partitions(['A','A','B'],{'training':{'row_ids':[0,1],'scaffolds':['A']},
                                         'test':{'row_ids':[2],'scaffolds':['B']}})
