from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,time
import psutil
R=Path(__file__).resolve().parents[1]
run=R/'practicuum/evidence/20261119-istradefylline-CAM-TZVP-lossless-water'
plan=R/'practicuum/evidence/20261119-lossless-TDDFT-postprocess-plan';plan.mkdir(exist_ok=False)
source=R/'scripts/analyze_electronic_checkpoint.py';frozen=plan/'planned-auditor-source.py';frozen.write_bytes(source.read_bytes())
audited=R/'practicuum/evidence/20261119-istradefylline-CAM-TZVP-electronic-audit'
target_pid=20420;maximum=24*3600;started=time.monotonic()
record={'created_utc':datetime.now(timezone.utc).isoformat(),'watcher_pid':os.getpid(),'target_pid':target_pid,
 'run':str(run),'auditor_sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'output':str(audited),
 'maximum_wait_seconds':maximum,'scope':'Only analyze a completed PASS checkpoint; no new SCF, no new TDDFT, no publishing',
 'on_numerical_failure':'Record BLOCKED; do not invent missing transition data'}
(plan/'plan.json').write_text(json.dumps(record,indent=2)+'\n');(plan/'watcher-source.py').write_bytes(Path(__file__).read_bytes())
receipt={'status':'BLOCKED','scope':record['scope']}
while time.monotonic()-started<maximum:
 if (run/'result.json').is_file():
  try:result=json.loads((run/'result.json').read_text())
  except ValueError:result=None
  if result is not None:
   if result['status']=='PASS':
    command=[sys.executable,str(frozen),'--run',str(run),'--out',str(audited)]
    with (R/'tmp/vertical-electronic-audit.log').open('wb') as log:
     process=subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT)
    receipt.update(status='PASS' if process.returncode==0 else 'FAIL',exit_code=process.returncode,argv=command)
   else:receipt['reason']='Numerical run not PASS'
   break
 if (run/'failure.json').is_file() or (run/'blocked.json').is_file():
  receipt['reason']='Target numerical calculation stopped without a completed spectrum';break
 try:
  p=psutil.Process(target_pid);active=p.is_running() and run.name in ' '.join(p.cmdline())
 except psutil.Error:active=False
 if not active:receipt['reason']='Target process ended without completed result';break
 time.sleep(10)
else:receipt['reason']='24-hour checkpoint wait expired; no calculation was terminated'
receipt.update(finished_utc=datetime.now(timezone.utc).isoformat(),waited_seconds=time.monotonic()-started)
with (R/'practicuum/evidence/20261119-lossless-TDDFT-postprocess-execution.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(receipt['status'],receipt.get('reason','completed independent checkpoint analysis'),flush=True)
