from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
code=r'''
import json,subprocess
from pathlib import Path
r=Path('/home/miakhlov/course-production-verified-20261118')
run=r/'practicuum/evidence/research-quantum-istradefylline-cpcm-refined-20261119'
rows=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  args=(p/'cmdline').read_bytes().decode().replace('\0',' ')
  if 'scripts/run_research_quantum.py --name istradefylline --protocol practicuum/protocols/research-quantum-cpcm-refined.json' in args:
   rows.append({'pid':int(p.name),'argv':args,'process_status':(p/'status').read_text()})
 except (OSError,UnicodeDecodeError):pass
files={}
for p in run.rglob('result.json'):
 try:files[str(p.relative_to(run))]=json.loads(p.read_text())
 except (OSError,ValueError):pass
print(json.dumps({'processes':rows,'completed_stage_results':files,'scope':'live process and completed stage inspection; not an accepted DFT minimum'}))
'''
p=subprocess.run(['wsl','-d','Ubuntu-24.04','--','python3','-'],input=code.encode(),capture_output=True,check=True)
receipt=json.loads(p.stdout);receipt['utc']=datetime.now(timezone.utc).isoformat()
receipt['status']='IN_PROGRESS' if receipt['processes'] else 'REVIEW'
out=R/'practicuum/evidence/20261119-refined-DFT-progress-snapshot';out.mkdir(exist_ok=False)
b=(R/'tmp/research-quantum-refined.log').read_bytes();(out/'driver-log-snapshot.log').write_bytes(b)
receipt['driver_log_snapshot_sha256']=hashlib.sha256(b).hexdigest()
(out/'progress.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(out/'capture-source.py').write_bytes(Path(__file__).read_bytes())
print(receipt['status'],'processes',len(receipt['processes']),'completed stages',list(receipt['completed_stage_results']))
