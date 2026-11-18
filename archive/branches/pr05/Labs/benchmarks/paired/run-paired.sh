#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/miakhlov/.local/bin:$PATH"
python3 '/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/wsl-setup/sync-paired.py'
cd /home/miakhlov/course-notebooks
uv run --frozen python tools/register_uv_kernel.py
uv run --frozen python tools/preflight.py
uv run --frozen python tools/validate_course.py
uv run --frozen python -m unittest discover -s Labs -p 'test_*.py' -v
uv run --frozen python -m unittest discover -s Stepik_course/practice -p test_practice.py -v
uv run --frozen python tools/run_labs.py --output Labs/executed/paired-v1-01
