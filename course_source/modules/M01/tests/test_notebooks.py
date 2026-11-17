"""Пилотные проверки структуры и модели Jupyter-кейса М01.

Запуск из корня репозитория:
python -m unittest discover -s course_source/modules/M01/tests -p "test_*.py" -v

При RUN_NOTEBOOK_EXECUTION=1 выполняет обе книги в отдельном временном каталоге;
без флага проверяет только JSON и численную модель (не свидетельство исполнения).
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
FILES = ("01_guided_case.ipynb", "02_independent_lab.ipynb")


class NotebookStructureTests(unittest.TestCase):
    def test_notebook_schema_and_unique_cell_ids(self):
        for name in FILES:
            with self.subTest(notebook=name):
                nb = nbformat.read(ROOT / name, as_version=4)
                nbformat.validate(nb)
                self.assertGreaterEqual(len(nb.cells), 10)
                ids = [cell["id"] for cell in nb.cells]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(any(c.cell_type == "markdown" for c in nb.cells))
                self.assertTrue(any(c.cell_type == "code" for c in nb.cells))

    def test_guided_has_results_and_scientific_limits(self):
        nb = nbformat.read(ROOT / FILES[0], as_version=4)
        text = "\n".join(c.source for c in nb.cells)
        for required in ("наблюдени", "взаимодейств", "степен", "МПа", "синтетичес"):
            with self.subTest(fragment=required):
                self.assertIn(required.lower(), text.lower())

    def test_facultative_arithmetic_reference(self):
        # Derived from explicit 2x2 toy dataset, independently of notebook output.
        y = {(-1,-1):43.0, (+1,-1):47.0, (-1,+1):37.0, (+1,+1):73.0}
        effect_a = (y[(1,-1)] + y[(1,1)] - y[(-1,-1)] - y[(-1,1)]) / 2
        effect_b = (y[(-1,1)] + y[(1,1)] - y[(-1,-1)] - y[(1,-1)]) / 2
        effect_ab = (y[(-1,-1)] + y[(1,1)] - y[(1,-1)] - y[(-1,1)]) / 2
        self.assertEqual((effect_a,effect_b,effect_ab), (20.0,10.0,16.0))

    @unittest.skipUnless(os.getenv("RUN_NOTEBOOK_EXECUTION") == "1", "Set RUN_NOTEBOOK_EXECUTION=1 for kernel execution")
    def test_run_both_notebooks(self):
        from nbclient import NotebookClient
        with tempfile.TemporaryDirectory(prefix="course-m01-") as folder:
            for name in FILES:
                with self.subTest(notebook=name):
                    nb = nbformat.read(ROOT / name, as_version=4)
                    NotebookClient(
                        nb, timeout=180, kernel_name="python3",
                        resources={"metadata":{"path":folder}},
                        allow_errors=False,
                    ).execute()


if __name__ == "__main__":
    unittest.main()
