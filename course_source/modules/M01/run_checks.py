"""Retain bounded M01 runtime evidence; do not overwrite learner artifacts."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

MODULE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def execute_book(source,output):
    import nbformat
    from nbclient import NotebookClient
    book=nbformat.read(source,as_version=4)
    for cell in book.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    try:
        NotebookClient(book,timeout=180,resources={'metadata':{'path':str(MODULE)}}).execute()
    finally:nbformat.write(book,output)
    text='\n'.join(str(o.get('text','')) for cell in book.cells if cell.cell_type=='code' for o in cell.outputs)
    if source.name.startswith('02_'):
        assert text.count("'status': 'NOT_RUN'")==3,'Empty scaffold must not report solved cases'
    else:
        pngs=[o for cell in book.cells if cell.cell_type=='code' for o in cell.outputs if 'image/png' in o.get('data',{})]
        assert len(pngs)>=2,'Both actual plots must be embedded in the guided notebook, including under Agg'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    parser.add_argument('--book',type=Path)
    parser.add_argument('--executed',type=Path)
    args=parser.parse_args()
    if args.book:
        execute_book(args.book,args.executed);return
    if args.output is None:parser.error('--output is required')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    from m01 import locate_snapshot,META
    source=locate_snapshot()
    environment={'python':sys.version,'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,
                 'platform':platform.platform(),'rdkit_installed':importlib.util.find_spec('rdkit') is not None,
                 'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions()))}
    from jupyter_client.kernelspec import KernelSpecManager
    kernel=KernelSpecManager().get_kernel_spec('course-m01-evidence')
    environment['kernel']={'argv':kernel.argv,'env':kernel.env,'resource_dir':kernel.resource_dir}
    environment['uv_version']=subprocess.check_output([kernel.argv[0],'--version'],text=True).strip()
    environment['audit_argv']=[sys.executable,*sys.argv]
    (output/'environment.json').write_text(json.dumps(environment,indent=2),encoding='utf-8')
    if environment['rdkit_installed']:raise RuntimeError('Use the dedicated minimal M01 uv environment, not the full chemistry kernel')
    files=[MODULE/name for name in ['data/provenance.json','data/evidence_cards.json','m01.py','instructor/solution.py',
            'uv.lock','pyproject.toml','build_notebooks.py','run_checks.py','register_kernel.py','tests/test_notebooks.py',
            '01_guided_case.ipynb','02_independent_lab.ipynb']]+[source]
    input_manifest=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
    (output/'inputs.json').write_text(json.dumps(input_manifest,indent=2),encoding='utf-8')
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8',MPLBACKEND='Agg',M01_ASSERT_MINIMAL='1',
             M01_WORK_DIR=str(output/'learner_work'))
    env.pop('PYTHONPATH',None)
    records=[]
    def command(identifier,argv,scope):
        folder=output/identifier;folder.mkdir();start=time.perf_counter();utc=datetime.now(timezone.utc).isoformat()
        with (folder/'stdout.txt').open('w',encoding='utf-8') as stdout,(folder/'stderr.txt').open('w',encoding='utf-8') as stderr:
            try:
                p=subprocess.run(argv,cwd=MODULE,env=env,stdout=stdout,stderr=stderr,timeout=600,check=False)
                code=p.returncode;status='PASS' if code==0 else 'FAIL'
            except subprocess.TimeoutExpired:code=None;status='BLOCKED'
        record={'id':identifier,'argv':argv,'cwd':str(MODULE),'started_utc':utc,'seconds':time.perf_counter()-start,
                'exit_code':code,'status':status,'scope':scope,'environment':'../environment.json','data_sha256':META['sha256'],
                'M01_WORK_DIR':env['M01_WORK_DIR']}
        (folder/'run.json').write_text(json.dumps(record,indent=2),encoding='utf-8');records.append(record)
        print(identifier,status,flush=True)
    command('unit-tests',[sys.executable,'-m','unittest','discover','-s',str(MODULE/'tests'),'-p','test_*.py','-v'],'source, numeric and safeguard tests, not pedagogy certification')
    for name,scope in [('01_guided_case.ipynb','full guided reference execution'),('02_independent_lab.ipynb','empty scaffold execution; learner tasks NOT_RUN')]:
        path=MODULE/name;folder=output/path.stem
        command(path.stem,[sys.executable,str(Path(__file__).resolve()),'--book',str(path),'--executed',str(folder/'executed.ipynb')],scope)
        (folder/'input.ipynb').write_bytes(path.read_bytes())
    command('instructor',[sys.executable,str(MODULE/'instructor/solution.py'),'--output',str(output/'instructor/artifacts')],'author numeric solutions C1/C2; learner/independent scientific review C3 NOT_RUN')
    if sha(source)!=META['sha256']:raise AssertionError('Source changed during execution')
    summary={'status':'PASS' if all(r['status']=='PASS' for r in records) else 'FAIL','runs':records,
             'scope':'M01 technical and author-reference validation only','learner_cases':'NOT_RUN',
             'student_pilot':'NOT_RUN','independent_scientific_review':'NOT_RUN','source_rights':'See RESEARCH_SOURCE.md; new full CSV not redistributed'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    if summary['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
