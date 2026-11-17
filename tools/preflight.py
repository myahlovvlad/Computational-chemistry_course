"""Check the complete Linux/uv teaching environment without starting a server."""
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    checks=[]
    def record(name,ok,actual):checks.append({'id':name,'status':'PASS' if ok else 'BLOCKED','actual':actual})
    record('linux',sys.platform=='linux',sys.platform)
    record('python-3.12',sys.version_info[:2]==(3,12),sys.version)
    record('project-venv',Path(sys.prefix).resolve()==(ROOT/'.venv').resolve(),sys.executable)
    for package in ['rdkit','numpy','pandas','scikit-learn','nbformat','nbclient','ipykernel','jupyterlab','pyscf','streamlit']:
        try:version=importlib.metadata.version(package);record(package,True,version)
        except importlib.metadata.PackageNotFoundError:record(package,False,'not installed')
    for binary in ['uv','vina']:
        path=shutil.which(binary)
        if path:
            p=subprocess.run([path,'--version'],capture_output=True,text=True,timeout=15)
            record(binary,p.returncode==0,{'path':path,'version':p.stdout.strip()})
        else:record(binary,False,'not on PATH')
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'BLOCKED','platform':platform.platform(),
            'scope':'environment preflight only, not completed exercises','checks':checks}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)

if __name__=='__main__':main()
