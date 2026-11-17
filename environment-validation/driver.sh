#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/miakhlov/.local/bin:$PATH"
cd /home/miakhlov/course-notebooks
cp '/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/uv-wsl-notebooks-20261117/tools/check_notebook_environment.py' tools/
uv run --frozen python tools/check_notebook_environment.py --all --output tmp/kernel-smoke-all-02
cp tmp/kernel-smoke-all-02/results.json '/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/uv-wsl-notebooks-20261117/environment-validation/kernel-all.json'
