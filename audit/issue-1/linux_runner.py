"""Run existing notebooks unchanged under a Linux venv; retain fresh evidence.

Usage: python linux_runner.py --root /path/to/course --output /path/to/new/evidence
No fallback from missing Vina/PySCF to a claimed full pass.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve();out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a new evidence directory')
    out.mkdir(parents=True)
    def dump(path,data):
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    env=dict(os.environ)
    env.pop('PYTHONPATH',None)
    env.update(PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLBACKEND='Agg')
    # Inherited by each kernel. User/global PYTHONPATH must not affect this run.
    os.environ.pop('PYTHONPATH',None)
    os.environ.update(env)
    packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    dump(out/'environment.json',{'python':sys.version,'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,
          'isolated':sys.prefix!=sys.base_prefix,'platform':platform.platform(),'packages':dict(sorted(packages.items())),
          'thread_environment':{k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MPLBACKEND']},
          'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()})
    (out/'uv-pip-freeze.txt').write_text(subprocess.check_output(['uv','pip','freeze','--python',sys.executable],text=True),encoding='utf-8')
    (out/'uv-version.txt').write_text(subprocess.check_output(['uv','--version'],text=True),encoding='utf-8')
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    dump(out/'source-sha256.json',[{'path':name,'sha256':hashfile(root/name)} for name in tracked if name])
    runs=[]
    def command(name,argv):
        folder=out/name;folder.mkdir()
        start=time.perf_counter();utc=datetime.now(timezone.utc).isoformat()
        with (folder/'stdout.txt').open('w') as stdout,(folder/'stderr.txt').open('w') as stderr:
            try:
                p=subprocess.run(argv,cwd=root,env=env,stdout=stdout,stderr=stderr,timeout=1200)
                code=p.returncode;status='PASS' if code==0 else 'FAIL'
            except subprocess.TimeoutExpired:
                code=None;status='BLOCKED'
        record={'id':name,'argv':argv,'cwd':str(root),'started_utc':utc,'duration_seconds':time.perf_counter()-start,
                'exit_code':code,'status':status,'environment':'../environment.json'}
        dump(folder/'run.json',record);runs.append(record);print(name,status,flush=True)
        return folder
    command('core-tests',[sys.executable,'-m','unittest','discover','-s','Stepik_course/practice','-p','test_practice.py','-v'])
    command('labs-tests',[sys.executable,'-m','unittest','discover','-s','Labs','-p','test_labs.py','-v'])
    if shutil.which('vina'):
        folder=command('vina-version',['vina','--version'])
        dump(folder/'binary.json',{'path':shutil.which('vina'),'sha256':hashfile(Path(shutil.which('vina')))})
    from nbclient import NotebookClient
    import nbformat
    kernel='chemistry-course-uv'
    # Provisioning registers this kernel through uv, not a direct interpreter.
    command('kernel',[sys.executable,'-m','jupyter','kernelspec','list','--json'])
    books=[root/'Stepik_course/practice/quickstart.ipynb']+sorted((root/'Labs/notebooks').glob('lab*.ipynb'))+[root/'Labs/extensions/dft_pyscf.ipynb']
    for source in books:
        name=source.stem;folder=out/name;folder.mkdir()
        book=nbformat.read(source,as_version=4)
        for cell in book.cells:
            if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
        start=time.perf_counter();utc=datetime.now(timezone.utc).isoformat();status='PASS';error=''
        try:
            NotebookClient(book,timeout=900,kernel_name=kernel,resources={'metadata':{'path':str(root)}}).execute()
        except Exception as exc:
            status='FAIL';error=str(exc)
        nbformat.write(book,folder/'executed.ipynb')
        (folder/'stdout.txt').write_text('\n'.join(o.get('text','') for c in book.cells if c.cell_type=='code' for o in c.outputs),encoding='utf-8')
        (folder/'stderr.txt').write_text(error,encoding='utf-8')
        record={'id':name,'status':status,'source':source.relative_to(root).as_posix(),'input_sha256':hashfile(source),
                'started_utc':utc,'duration_seconds':time.perf_counter()-start,'cwd':str(root),'kernel':kernel,
                'driver_argv':sys.argv,'environment':'../environment.json','scope':'fresh reference execution, not learner transfer/interpretation',
                'code_cells':sum(c.cell_type=='code' for c in book.cells),'error':error}
        dump(folder/'run.json',record);runs.append(record);print(name,status,flush=True)
    # Execute the exact original PySCF fence, not a substitute calculation.
    text=(root/'Stepik_course/modules/12_quantum.md').read_text(encoding='utf-8')
    code=next(x for x in re.findall(r'```python\s*\n(.*?)```',text,re.S) if 'pyscf' in x)
    snippet=out/'module12-pyscf.py';snippet.write_text(code,encoding='utf-8')
    command('module12-pyscf',[sys.executable,str(snippet)])
    if (root/'Labs/results').exists():shutil.copytree(root/'Labs/results',out/'labs-results')
    # Missing Vina is an explicit scientific blocker even if a notebook can analyse a prepared pose.
    docking=root/'Labs/results/lab10/docking.json'
    mode=json.loads(docking.read_text())['mode'] if docking.exists() else None
    dump(out/'summary.json',{'status':'PASS' if all(r['status']=='PASS' for r in runs) and mode=='executed-vina' else 'BLOCKED' if mode!='executed-vina' else 'FAIL',
         'runs':[{'id':r['id'],'status':r['status']} for r in runs],'docking_mode':mode,'notebooks':len(books),
         'scope':'existing reference notebooks/tests; no Stepik or independent learner evidence'})


if __name__=='__main__':main()
