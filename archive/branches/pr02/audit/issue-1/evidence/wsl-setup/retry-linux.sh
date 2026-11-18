#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/miakhlov/.local/bin:$PATH"
cd /home/miakhlov/Computational-chemistry_course
cp '/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/uv-wsl-notebooks-20261117/tools/register_uv_kernel.py' tools/
uv run --frozen python tools/register_uv_kernel.py
uv run --frozen python '/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/practice-audit-issue1-20261117/audit/issue-1/linux_runner.py' --root /home/miakhlov/Computational-chemistry_course --output /home/miakhlov/course-evidence-linux-02
