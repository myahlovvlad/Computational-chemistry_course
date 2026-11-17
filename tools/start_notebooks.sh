#!/usr/bin/env bash
set -euo pipefail
course_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$course_root"
if ! command -v uv >/dev/null 2>&1; then
  export PATH="$HOME/.local/bin:$PATH"
fi
uv sync --frozen
uv run --frozen python tools/register_uv_kernel.py
exec uv run --frozen jupyter lab --ip=127.0.0.1 --no-browser
