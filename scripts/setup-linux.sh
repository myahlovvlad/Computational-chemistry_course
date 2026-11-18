#!/usr/bin/env bash
set -euo pipefail
course_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
course_profile="${1:-base}"
case "$course_profile" in base|chem|quantum) ;; *) printf '%s\n' 'Профиль: base, chem или quantum'; exit 2;; esac
export PYTHONUTF8=1 PYTHONNOUSERSITE=1
if command -v uv >/dev/null 2>&1; then
  course_uv="$(command -v uv)"
else
  course_bootstrap="$course_script_dir/environment/.uv-bootstrap"
  if [ ! -x "$course_bootstrap/bin/python" ]; then
    python3 -m venv "$course_bootstrap"
  fi
  "$course_bootstrap/bin/python" -m pip install uv==0.13.8
  course_uv="$course_bootstrap/bin/uv"
fi
python3 "$course_script_dir/setup_environment.py" --profile "$course_profile" --uv "$course_uv"
