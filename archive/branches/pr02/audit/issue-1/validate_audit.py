"""Validate evidence links/counts and unchanged teaching sources, not course readiness."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'audit/issue-1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows=list(csv.DictReader((ROOT/'practice-audit.csv').open(encoding='utf-8-sig',newline='')))
    checks=[]
    def check(name, condition, details=None):
        checks.append({'id':name,'status':'PASS' if condition else 'FAIL','details':details})
    check('unique-ids',len(rows)==len({r['exercise_id'] for r in rows}),len(rows))
    check('all-14-modules',{r['module_id'] for r in rows}=={str(i) for i in range(1,15)})
    check('valid-statuses',all(r['status'] in {'PASS','FAIL','BLOCKED','NOT_RUN'} for r in rows))
    check('control-questions-42',sum(bool(re.fullmatch(r'M\d\d-Q[123]',r['exercise_id'])) for r in rows)==42)
    check('reference-notebooks-14',sum(bool(re.fullmatch(r'LAB\d\d-REFERENCE',r['exercise_id'])) and r['status']=='PASS' for r in rows)==14)
    check('transfer-actions-42',sum('TRANSFER' in r['exercise_id'] for r in rows)==42)
    summary=json.loads((BASE/'registry-summary.json').read_text(encoding='utf-8'))
    check('summary-matches',summary['rows']==len(rows) and summary['statuses']==dict(Counter(r['status'] for r in rows)))
    broken=[]
    for r in rows:
        path=r['source'].split(':')[0]
        if not (ROOT/path).is_file():broken.append([r['exercise_id'],'source',path])
        if r['status'] in {'PASS','FAIL'}:
            evidence=r['evidence'].split(';')[0]
            if not evidence or not (ROOT/evidence).is_file():broken.append([r['exercise_id'],'evidence',evidence])
            else:
                directory=(ROOT/evidence).parent
                for name in ['stdout.txt','stderr.txt']:
                    if not (directory/name).is_file():broken.append([r['exercise_id'],name])
            if not r['test_command'] or not (ROOT/r['environment']).is_file():broken.append([r['exercise_id'],'command/environment'])
    check('executable-evidence-and-source-links',not broken,broken)
    check('no-text-only-pass',all(r['status']!='PASS' or r['status_scope'] not in {'learner_action','learner_prediction_or_transfer','case_rubric_obligation','learner_interpretation'} for r in rows))
    source=json.loads((BASE/'evidence/source-inventory.json').read_text(encoding='utf-8'))
    changed=[x['path'] for x in source['files'] if not (ROOT/x['path']).is_file() or sha(ROOT/x['path'])!=x['sha256']]
    check('original-tracked-files-unchanged',not changed,changed)
    # Freeze a compact delivery manifest. Validate again after git add to check packaging.
    files=[ROOT/'practice-audit.csv',ROOT/'PRACTICE_AUDIT_REPORT.md',ROOT/'PRACTICE_AUDIT_FIXES.md']
    files += [p for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in {'file-manifest.json','validation.json'}]
    manifest=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]
    (BASE/'file-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','scope':'audit packaging/integrity only','checks':checks,'manifest_files':len(manifest)}
    (BASE/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))
    sys.exit(0 if result['status']=='PASS' else 1)


if __name__=='__main__':main()
