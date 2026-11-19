from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
import psutil
R=Path(__file__).resolve().parents[1];run=R/'practicuum/evidence/20261119-istradefylline-CAM-TZVP-lossless-water'
out=R/'practicuum/evidence/20261119-lossless-TDDFT-progress-snapshot';out.mkdir(exist_ok=False)
files={}
for name in ['manifest.json','runner-source.py','io-helper-source.py','input.xyz','scratch-preflight.json','pyscf.log']:
 p=run/name
 if p.is_file():
  b=p.read_bytes();(out/name).write_bytes(b);files[name]=hashlib.sha256(b).hexdigest()
processes=[]
for p in psutil.process_iter(['pid','cmdline','memory_info']):
 try:
  command=' '.join(p.info['cmdline'] or [])
  if 'run_vertical_tddft.py' in command and run.name in command:
   processes.append({'pid':p.pid,'cmdline':p.info['cmdline'],'RSS_bytes':p.info['memory_info'].rss})
 except psutil.Error:pass
status='IN_PROGRESS' if processes else 'REVIEW'
failure=run/'failure.json'
if failure.exists():status=json.loads(failure.read_text())['status']
record={'status':status,'utc':datetime.now(timezone.utc).isoformat(),'scope':'Frozen progress observation, not a converged SCF or spectrum',
 'processes':processes,'files_sha256':files,'free_disk_bytes':shutil.disk_usage(R).free,
 'completed_result_present':(run/'result.json').is_file(),'SCF_result_present':(run/'scf.json').is_file(),
 'numerical_method':'CAM-B3LYP/def2-TZVP//GFN2, C-PCM water, 30 singlet TDDFT states',
 'storage_change_only':'lossless gzip/shuffle/Fletcher32; calibrated against uncompressed integrals',
 'space_reserve_GiB':4,'postprocessing_plan':'practicuum/evidence/20261119-lossless-TDDFT-postprocess-plan/plan.json'}
(out/'progress.json').write_text(json.dumps(record,indent=2)+'\n');(out/'capture-source.py').write_bytes(Path(__file__).read_bytes())
print(status,'SCF complete',record['SCF_result_present'],'spectrum complete',record['completed_result_present'])
