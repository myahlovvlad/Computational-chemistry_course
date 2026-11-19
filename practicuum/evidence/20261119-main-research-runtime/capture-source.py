from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[1];out=R/'practicuum/evidence/20261119-main-research-runtime';out.mkdir(exist_ok=False)
native=R/'practicuum/evidence/20261119-istradefylline-CAM-TZVP-lossless-water'
ps="Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Where-Object { $_.CommandLine -match 'run_vertical_tddft.py|run_research_quantum.py|watch_vertical_checkpoint.py' } | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
raw=subprocess.check_output(['powershell','-NoProfile','-Command',ps]);processes=json.loads(raw.decode('utf-8-sig')) if raw.strip() else []
if isinstance(processes,dict):processes=[processes]
code=r'''
from pathlib import Path
import subprocess,json
r=Path('/home/miakhlov/course-production-verified-20261118/practicuum/evidence/research-quantum-istradefylline-cpcm-refined-20261119')
active=[line for line in subprocess.check_output(['ps','-eo','pid,etime,%cpu,rss,args'],text=True).splitlines() if 'scripts/run_research_quantum.py --name' in line]
completed={str(p.relative_to(r)):json.loads(p.read_text()) for p in r.rglob('result.json')}
print(json.dumps({'processes':active,'completed_stages':completed,'source':str(r),'checkpoints':[str(p.relative_to(r)) for p in r.rglob('*.h5')]}))
'''
p=subprocess.run(['wsl','-d','Ubuntu-24.04','--','python3','-'],input=code.encode(),capture_output=True,check=True)
linux=json.loads(p.stdout);log=(native/'pyscf.log').read_bytes();text=log.decode('utf-8',errors='replace')
cycles=re.findall(r'cycle=\s*(\d+)\s+E=\s*([-+0-9.]+)',text)
summary={'utc':datetime.now(timezone.utc).isoformat(),'status':'BLOCKED' if not processes and not linux['processes'] else 'IN_PROGRESS',
 'scope':'Current execution state on main; historical progress snapshots remain unchanged',
 'windows_processes':processes,'linux':linux,'native_final_result_present':(native/'result.json').exists(),
 'native_checkpoint_preserved':(native/'checkpoint.h5').exists(),'native_log_sha256':hashlib.sha256(log).hexdigest(),
 'native_last_logged_SCF_cycle':cycles[-1] if cycles else None,'native_log_reports_SCF_convergence':'converged SCF energy' in text,
 'accepted_target_spectrum':False,'accepted_refined_DFT_minimum':False,
 'reason_if_inactive':'No matching process and no completed result. Cause not established; stored checkpoint and intermediate energies are not accepted converged results.',
 'restart_requirement':'New main-root run with new output directory; validate geometry, charge, basis and cached tensor provenance; reuse density only as initial guess and reconverge all gates.'}
(out/'pyscf-log-snapshot.log').write_bytes(log);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(out/'capture-source.py').write_bytes(Path(__file__).read_bytes())
print(summary['status'],'current processes',len(processes)+len(linux['processes']),'completed Linux stages',len(linux['completed_stages']))
