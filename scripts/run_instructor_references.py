"""Run each authored numerical reference in a separate process, preserving failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(ROOT/'practicuum/shared'))
    from research_checks import check
    records=[]
    for path in sorted((ROOT/'practicuum/modules').glob('*/lessons/*/instructor/reference.py')):
        id=path.parents[3].name+'-'+path.parents[1].name
        folder=out/id;folder.mkdir()
        env=dict(os.environ,PYTHONUTF8='1',COURSE_WORK_DIR=str(out/'workspace'),MPLBACKEND='Agg',OMP_NUM_THREADS='1')
        start=time.perf_counter()
        record={'lesson_id':id,'source':path.relative_to(ROOT).as_posix(),
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'python':sys.executable,
                'scope':'author numerical reference; open argument requires review'}
        (folder/'reference.py').write_bytes(path.read_bytes())
        try:
            process=subprocess.run([sys.executable,str(path)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=600)
            (folder/'stdout.txt').write_text(process.stdout,encoding='utf-8')
            (folder/'stderr.txt').write_text(process.stderr,encoding='utf-8')
            if process.returncode:raise RuntimeError('Reference exit '+str(process.returncode))
            answer=json.loads(process.stdout)
            try:feedback=check(id,answer)
            except ValueError:feedback={'status':'NOT_APPLICABLE','scope':'legacy reference contains its own assertions'}
            record.update(status='FAIL' if feedback['status']=='FAIL' else 'PASS',contract=feedback)
            (folder/'answer.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as error:record.update(status='FAIL',error=str(error))
        record['seconds']=time.perf_counter()-start
        records.append(record);print(id,record['status'],flush=True)
    summary={'status':'PASS' if records and all(r['status']=='PASS' for r in records) else 'FAIL','runs':records,
             'learner_solutions':'NOT_RUN','scientific_review':'NOT_RUN'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    if summary['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
