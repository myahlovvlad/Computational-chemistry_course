"""Register a dedicated, minimal M01 uv kernel on Windows or Linux."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parent
NAME='course-m01-evidence'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--uv');args=parser.parse_args()
    binary=args.uv or shutil.which('uv')
    if not binary:raise SystemExit('Install uv or pass --uv /absolute/path/to/uv')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise SystemExit('Run this script with uv run --project M01')
    spec={'argv':[str(binary),'run','--frozen','--project',str(ROOT),'python','-m','ipykernel_launcher','-f','{connection_file}'],
          'display_name':'M01 · scientific evidence · uv (no RDKit)','language':'python',
          'env':{'UV_PROJECT_ENVIRONMENT':str(ROOT/'.venv'),'PYTHONNOUSERSITE':'1','PYTHONPATH':'','MPLBACKEND':'Agg'}}
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder)/'kernel.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        installed=KernelSpecManager().install_kernel_spec(folder,kernel_name=NAME,user=True)
    print(json.dumps({'kernel':NAME,'path':installed,'project':str(ROOT),'argv':spec['argv']},indent=2))
