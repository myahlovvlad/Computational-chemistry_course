"""Numerical, source-integrity and learner-data safeguards; runtime is separate."""
import ast
import json
import math
from pathlib import Path
import statistics
import sys
import tempfile
import unittest

import nbformat

MODULE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(MODULE))
from m01 import (META,checksum,create_dossier,format_feedback,locate_snapshot,
                 metric_invariants,prepare_import_case,read_rows,verify)
from formative import feedback


class NotebookTests(unittest.TestCase):
    def test_schema_compilation_and_minimal_imports(self):
        for name in ('01_guided_case.ipynb','02_independent_lab.ipynb'):
            with self.subTest(notebook=name):
                book=nbformat.read(MODULE/name,as_version=4)
                nbformat.validate(book)
                self.assertEqual(len(book.cells),len({c.id for c in book.cells}))
                self.assertEqual(book.metadata.kernelspec.name,'course-m01-evidence')
                for cell in book.cells:
                    if cell.cell_type!='code':continue
                    compile(cell.source,name,'exec')
                    for node in ast.walk(ast.parse(cell.source)):
                        imports=([n.name for n in node.names] if isinstance(node,ast.Import)
                                 else [node.module or ''] if isinstance(node,ast.ImportFrom) else [])
                        for item in imports:
                            self.assertNotIn(item.split('.')[0],{'rdkit','pandas','numpy','instructor'})

    def test_independent_does_not_import_reference_solution(self):
        book=nbformat.read(MODULE/'02_independent_lab.ipynb',as_version=4)
        for cell in book.cells:
            if cell.cell_type=='code':
                self.assertNotIn('solution.py',cell.source)
                self.assertNotIn('instructor/',cell.source)


class SourceAndCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=locate_snapshot();cls.rows=read_rows(cls.source)

    def test_pinned_bytes_and_schema(self):
        self.assertEqual(checksum(self.source),META['sha256'])
        self.assertEqual(self.source.stat().st_size,96699)
        self.assertEqual(len(self.rows),1128)
        self.assertEqual([r['row_id'] for r in self.rows],list(range(1128)))

    def test_corrupted_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            altered=Path(folder)/'altered.csv'
            altered.write_bytes(self.source.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'SHA256'):verify(altered)

    def test_preallocated_records_are_disjoint_not_chemical_split(self):
        subsets=[{r['row_id'] for r in self.rows if r['row_id']%4==k} for k in (0,1)]
        self.assertEqual([len(x) for x in subsets],[282,282])
        self.assertFalse(subsets[0]&subsets[1])

    def test_guided_numeric_reference(self):
        rows=[r for r in self.rows if r['row_id']%4==0]
        errors=[r['predicted']-r['measured'] for r in rows]
        self.assertAlmostEqual(statistics.mean(map(abs,errors)),.7690035460992907,12)
        self.assertAlmostEqual(math.sqrt(statistics.mean(e*e for e in errors)),1.0037640277496775,12)
        worst=max(rows,key=lambda r:abs(r['predicted']-r['measured']))
        self.assertEqual(worst['row_id'],852)
        self.assertAlmostEqual(worst['predicted']-worst['measured'],3.389,12)

    def test_independent_numeric_reference(self):
        rows=[r for r in self.rows if r['row_id']%4==1]
        errors=[r['predicted']-r['measured'] for r in rows]
        self.assertAlmostEqual(statistics.mean(map(abs,errors)),.6410035460992908,12)
        self.assertAlmostEqual(math.sqrt(statistics.mean(e*e for e in errors)),.8536171742308398,12)
        self.assertEqual(max(rows,key=lambda r:abs(r['predicted']-r['measured']))['row_id'],733)

    def test_fault_repair_restores_values_without_mutating_source(self):
        before=checksum(self.source)
        rows=[r for r in self.rows if r['row_id']%4==1]
        original=json.dumps(rows,sort_keys=True)
        fault=prepare_import_case(rows)
        self.assertIn('synthetic',fault['metadata']['kind'])
        for src,dst in zip(rows,fault['rows']):
            self.assertEqual(src['row_id'],dst['row_id'])
            self.assertEqual(src['measured'],dst['measured'])
            self.assertAlmostEqual(math.log10(dst['reported_logS']),src['predicted'],12)
        self.assertEqual(json.dumps(rows,sort_keys=True),original)
        self.assertEqual(checksum(self.source),before)


class LearnerSafeguardsTests(unittest.TestCase):
    def test_formative_empty_choice_is_not_completion(self):
        for prompt in ['P04','P06','P09']:
            self.assertEqual(feedback(prompt,None)['status'],'NOT_RUN')

    def test_formative_choices_distinguish_misconceptions(self):
        for prompt,right in [('P04','B'),('P06','C'),('P09','A')]:
            self.assertEqual(feedback(prompt,right)['status'],'COMPONENT_CORRECT')
            messages=[]
            for wrong in set('ABC')-{right}:
                response=feedback(prompt,wrong)
                self.assertEqual(response['status'],'RECONSIDER');messages.append(response['message'])
            self.assertNotEqual(*messages)
            self.assertIn('not assessed',feedback(prompt,right)['scope'])

    def test_formative_invalid_choice_does_not_crash_or_pass(self):
        for choice in ['D','',3,{}]:
            self.assertEqual(feedback('P04',choice)['status'],'RETRY')

    def test_empty_and_format_only_are_distinct(self):
        self.assertEqual(format_feedback(None,['claim'])['status'],'NOT_RUN')
        self.assertEqual(format_feedback({},['claim'])['status'],'FAIL')
        feedback=format_feedback({'claim':'an unsupported claim'},['claim'])
        self.assertEqual(feedback['status'],'PASS')
        self.assertEqual(feedback['scientific_review'],'NOT_RUN')

    def test_arithmetic_invariants_reject_wrong_numbers(self):
        self.assertEqual(metric_invariants([1,-3],2,math.sqrt(5))['status'],'PASS')
        self.assertEqual(metric_invariants([1,-3],0,0)['status'],'FAIL')
        self.assertEqual(metric_invariants([float('nan')],0,0)['status'],'FAIL')
        self.assertEqual(metric_invariants(None,None,None)['status'],'NOT_RUN')

    def test_dossier_creation_preserves_existing_student_work(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=create_dossier(Path(folder)/'my_research')
            file=dest/'decisions.md';file.write_text('My original decision',encoding='utf-8')
            create_dossier(dest)
            self.assertEqual(file.read_text(encoding='utf-8'),'My original decision')
            self.assertTrue((dest/'concept_map.json').is_file())


if __name__=='__main__':unittest.main()
