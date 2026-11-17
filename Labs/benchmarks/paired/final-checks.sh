#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/miakhlov/.local/bin:$PATH"
repo='/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/paired-case-notebooks-20261117'
cd /home/miakhlov/course-notebooks
for name in tools/run_labs.py tools/validate_course.py tools/check_notebook_environment.py Labs/test_practice_contracts.py Labs/SETUP.md Labs/datasets/README.md Labs/datasets/manifest.json NOTEBOOK_ENVIRONMENT.md; do
  cp "$repo/$name" "$name"
done
uv run --frozen python tools/validate_course.py
uv run --frozen python -m unittest discover -s Labs -p 'test_*.py' -v
uv run --frozen python -m unittest discover -s Stepik_course/practice -p test_practice.py -v
uv run --frozen python tools/preflight.py
