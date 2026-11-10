"""Execute each laboratory in a fresh real Jupyter kernel and record evidence."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time

import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--only",type=int)
    parser.add_argument("--kernel",default="course-chemistry")
    args=parser.parse_args()
    os.environ['JUPYTER_PATH']=str(Path(sys.prefix)/'share/jupyter')
    evidence=ROOT/'Labs/benchmarks/execution.json'
    reports=json.loads(evidence.read_text(encoding='utf-8'))['runs'] if args.only and evidence.exists() else []
    for path in sorted((ROOT/'Labs/notebooks').glob('lab*.ipynb')):
        number=int(path.stem[3:])
        if args.only and number!=args.only:continue
        start=time.perf_counter()
        notebook=nbformat.read(path,as_version=4)
        client=NotebookClient(notebook,timeout=900,kernel_name=args.kernel,
                              resources={'metadata':{'path':str(path.parent)}})
        try:
            client.execute()
            # Publish actual outputs with the notebook; no hidden synthetic success.
            nbformat.write(notebook,path)
            record=json.loads((ROOT/f'Labs/results/lab{number:02d}/benchmark.json').read_text(encoding='utf-8'))
            result={'lab':number,'status':'passed','notebook_wall_seconds':time.perf_counter()-start,
                    'calculation':record}
        except Exception as error:
            nbformat.write(notebook,ROOT/f'Labs/results/failed-lab{number:02d}.ipynb')
            result={'lab':number,'status':'failed','error':str(error)[-2500:]}
        reports=[entry for entry in reports if entry['lab']!=number]+[result]
        reports.sort(key=lambda entry:entry['lab'])
        print(json.dumps({'lab':number,'status':result['status'],'error':result.get('error')},ensure_ascii=True),flush=True)
        (ROOT/'Labs/benchmarks/execution.json').write_text(json.dumps({
            'python':platform.python_version(),'platform':platform.platform(),'runs':reports
        },ensure_ascii=False,indent=2),encoding='utf-8')
    if any(record['status']=='failed' for record in reports):raise SystemExit(1)


if __name__=='__main__':main()
