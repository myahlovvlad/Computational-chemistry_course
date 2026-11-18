"""Register a user Jupyter kernel that starts via uv for this checkout.

Run: uv run --frozen python tools/register_uv_kernel.py
Notebook metadata selects this kernel; no activation cell is needed.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parents[1]
NAME='chemistry-course-uv'


def main():
    if sys.platform!='linux':
        raise SystemExit('Use Ubuntu/WSL for the full course environment including PySCF.')
    uv=shutil.which('uv')
    if not uv:raise SystemExit('uv not found in PATH')
    if Path(sys.prefix).resolve() != (ROOT/'.venv').resolve():
        raise SystemExit('Run with uv run from this project to select its .venv')
    spec={
        'argv':[uv,'run','--frozen','--project',str(ROOT),'python','-m','ipykernel_launcher','-f','{connection_file}'],
        'display_name':'Chemistry course (uv / WSL / Python 3.12)',
        'language':'python',
        'env':{'VIRTUAL_ENV':str(ROOT/'.venv'),'UV_PROJECT_ENVIRONMENT':str(ROOT/'.venv'),
               'PYTHONNOUSERSITE':'1','PYTHONPATH':'','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},
        'metadata':{'debugger':True},
    }
    # Per-user registration; replace only this named course kernel.
    with tempfile.TemporaryDirectory(prefix='course-kernel-') as folder:
        (Path(folder)/'kernel.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        path=KernelSpecManager().install_kernel_spec(folder,kernel_name=NAME,user=True)
    print(json.dumps({'kernel':NAME,'path':path,'project':str(ROOT),'argv':spec['argv']},indent=2))


if __name__=='__main__':main()
