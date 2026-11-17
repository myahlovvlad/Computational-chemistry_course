"""Execute reference notebooks and empty scaffolds; never overwrite learner files."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',type=int,choices=range(1,15))
    parser.add_argument('--role',choices=['worked','practice','both'],default='both')
    parser.add_argument('--output',type=Path,default=ROOT/'Labs/executed/paired-v1')
    args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLBACKEND='Agg',PYTHONNOUSERSITE='1')
    os.environ.pop('PYTHONPATH',None)
    records=[]
    manifest=json.loads((ROOT/'course-manifest.json').read_text(encoding='utf-8'))
    env={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
         'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions()))}
    (output/'environment.json').write_text(json.dumps(env,indent=2),encoding='utf-8')
    for item in manifest:
        if args.only and item['module']!=args.only:continue
        for role,key in [('worked','worked_notebook'),('practice','practice_notebook')]:
            if args.role!='both' and args.role!=role:continue
            source=ROOT/item[key];book=nbformat.read(source,as_version=4)
            for cell in book.cells:
                if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
            started=time.perf_counter();utc=datetime.now(timezone.utc).isoformat();error='';status='PASS'
            try:NotebookClient(book,timeout=900,resources={'metadata':{'path':str(ROOT)}}).execute()
            except Exception as exc:
                error=str(exc)
                status='BLOCKED' if any(t in error for t in ['BLOCKED:','No module named','Install PySCF']) else 'FAIL'
            target=output/source.name;nbformat.write(book,target)
            record={'module':item['module'],'role':role,'status':status,
                    'scope':'worked reference execution' if role=='worked' else 'scaffold infrastructure only; learner cases NOT_RUN',
                    'source':item[key],'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'kernel':book.metadata.kernelspec.name,'started_utc':utc,'wall_seconds':time.perf_counter()-started,
                    'executed_copy':str(target.relative_to(output)),'error':error}
            records.append(record);print(f"M{item['module']:02d} {role}: {status}",flush=True)
            (output/'execution.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    from paired_reference_checks import run as check_references
    reference=check_references(output,only=args.only)
    summary={'scope':'author reference and scaffold checks; no learner grading','argv':sys.argv,'cwd':str(ROOT),
             'environment':'environment.json','notebooks':records,'reference_cases':reference,
             'learner_cases':{'status':'NOT_RUN','count':3 if args.only else 42}}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
    if any(r['status']!='PASS' for r in records) or any(r['status']=='FAIL' for r in reference):raise SystemExit(1)

if __name__=='__main__':main()
