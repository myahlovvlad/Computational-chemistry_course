from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,shutil
import psutil
R=Path(__file__).resolve().parents[1];run=R/'practicuum/evidence/20261119-main-CAM-TZVP-restarted'
out=R/'practicuum/evidence/20261119-main-CAM-restarted-progress';out.mkdir(exist_ok=False)
def optional(name):
 try:return json.loads((run/name).read_text(encoding='utf-8'))
 except (FileNotFoundError,json.JSONDecodeError):return None
processes=[]
for p in psutil.process_iter(['pid','cmdline','memory_info']):
 try:
  command=' '.join(p.info['cmdline'] or [])
  if 'run_vertical_tddft.py' in command and run.name in command:
   processes.append({'pid':p.pid,'cmdline':p.info['cmdline'],'RSS_bytes':p.info['memory_info'].rss})
 except psutil.Error:pass
result=optional('result.json');failure=optional('failure.json');scf=optional('scf.json');validation=optional('restart-validation.json')
status='PASS' if result and result.get('status')=='PASS' else ('IN_PROGRESS' if processes else 'BLOCKED')
if failure:status=failure['status']
files={}
for name in ['manifest.json','runner-source.py','restart-helper-source.py','io-helper-source.py','input.xyz',
             'basis.json','scratch-preflight.json','restart-validation.json','pyscf.log','scf.json']:
 p=run/name
 if p.is_file():
  payload=p.read_bytes();(out/name).write_bytes(payload);files[name]=hashlib.sha256(payload).hexdigest()
record={'utc':datetime.now(timezone.utc).isoformat(),'status':status,
 'scope':'Frozen observation of a fresh main-root SCF/TDDFT run; not independent scientific validation',
 'single_numerical_run':True,'os_process_matches_including_venv_shims':processes,
 'input_compatibility':validation.get('status') if validation else 'NOT_RUN',
 'SCF_completed':bool(scf and scf.get('status')=='PASS'),'target_spectrum_completed':bool(result and result.get('status')=='PASS'),
 'scientific_acceptance':'REVIEW_REQUIRED','geometry_DFT_minimum':'NOT_CLAIMED',
 'files_sha256':files,'free_disk_bytes':shutil.disk_usage(R).free,
 'plan':'practicuum/evidence/20261119-main-CAM-TZVP-restart-plan/plan.json',
 'expected_final_result':'practicuum/evidence/20261119-main-CAM-TZVP-restarted/result.json',
 'expected_independent_audit':'practicuum/evidence/20261119-main-CAM-TZVP-restarted-audit/result.json'}
(out/'progress.json').write_text(json.dumps(record,indent=2)+'\n');(out/'capture-source.py').write_bytes(Path(__file__).read_bytes())
print(status,'compatibility',record['input_compatibility'],'SCF complete',record['SCF_completed'],'spectrum complete',record['target_spectrum_completed'])
