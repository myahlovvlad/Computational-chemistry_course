#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
VINA_VERSION="${VINA_VERSION:-1.2.7}"
RUN_ALL=0
WITH_PYSCF=0

usage() {
  cat <<'EOF'
Usage: bash tools/setup_wsl.sh [--run-all] [--with-pyscf]

  --run-all       Execute all 14 main laboratory notebooks after setup.
  --with-pyscf    Create a separate PySCF environment and run the DFT extension.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-all) RUN_ALL=1 ;;
    --with-pyscf) WITH_PYSCF=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "NOTE: WSL was not detected. The script can still work on a compatible Linux host."
fi

echo "==> Installing Linux prerequisites"
sudo apt-get update
sudo apt-get install -y ca-certificates curl git build-essential libgomp1

mkdir -p "$HOME/.local/bin"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
if ! grep -Fqx "$PATH_LINE" "$HOME/.bashrc" 2>/dev/null; then
  printf '\n%s\n' "$PATH_LINE" >> "$HOME/.bashrc"
fi
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Installing managed Python ${PYTHON_VERSION}"
uv python install "$PYTHON_VERSION"

BASE_ENV="$ROOT/.venv-course"
echo "==> Creating base course environment at $BASE_ENV"
rm -rf "$BASE_ENV"
uv venv --python "$PYTHON_VERSION" "$BASE_ENV"
uv pip install --python "$BASE_ENV/bin/python" -r "$ROOT/Labs/requirements.txt"

echo "==> Registering Jupyter kernel course-chemistry"
"$BASE_ENV/bin/python" -m ipykernel install   --prefix "$BASE_ENV"   --name course-chemistry   --display-name "Chemistry course (WSL)"

echo "==> Installing AutoDock Vina ${VINA_VERSION}"
case "$(uname -m)" in
  x86_64|amd64)
    VINA_ASSET="vina_${VINA_VERSION}_linux_x86_64"
    ;;
  aarch64|arm64)
    VINA_ASSET="vina_${VINA_VERSION}_linux_aarch64"
    ;;
  *)
    echo "Unsupported architecture for the prebuilt Vina binary: $(uname -m)" >&2
    exit 1
    ;;
esac

VINA_URL="https://github.com/forlilab/AutoDock-Vina/releases/download/v${VINA_VERSION}/${VINA_ASSET}"
curl -fL --retry 3 "$VINA_URL" -o "$HOME/.local/bin/vina"
chmod +x "$HOME/.local/bin/vina"

echo "==> Environment versions"
"$BASE_ENV/bin/python" --version
uv --version
vina --version
"$BASE_ENV/bin/python" - <<'PY'
import numpy, pandas, scipy, sklearn, streamlit
import rdkit
print("rdkit", rdkit.__version__)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scipy", scipy.__version__)
print("scikit-learn", sklearn.__version__)
print("streamlit", streamlit.__version__)
PY

echo "==> Running regression tests"
"$BASE_ENV/bin/python" -m unittest discover -s Labs -p test_labs.py -v

echo "==> Validating course package"
"$BASE_ENV/bin/python" tools/validate_course.py

if [[ "$WITH_PYSCF" -eq 1 ]]; then
  PYSCF_ENV="$ROOT/.venv-pyscf"
  echo "==> Creating isolated PySCF environment at $PYSCF_ENV"
  rm -rf "$PYSCF_ENV"
  uv venv --python "$PYTHON_VERSION" "$PYSCF_ENV"
  uv pip install --python "$PYSCF_ENV/bin/python" pyscf ase ipykernel
  "$PYSCF_ENV/bin/python" -m ipykernel install     --prefix "$PYSCF_ENV"     --name course-pyscf     --display-name "Chemistry course PySCF (WSL)"
  echo "==> Running optional PySCF DFT extension"
  "$PYSCF_ENV/bin/python" Labs/pyscf_dft.py
fi

if [[ "$RUN_ALL" -eq 1 ]]; then
  echo "==> Executing all 14 main laboratory notebooks"
  "$BASE_ENV/bin/python" tools/run_labs.py
else
  echo "==> Smoke-running laboratory 1"
  "$BASE_ENV/bin/python" tools/run_labs.py --only 1
  echo
  echo "Base setup is ready."
  echo "Run all main labs with:"
  echo "  .venv-course/bin/python tools/run_labs.py"
  echo "Verify real Vina execution with:"
  echo "  .venv-course/bin/python tools/run_labs.py --only 10"
fi
