"""Continue verified-cache vertical research, then audit its completed checkpoint.

Run in quantum-core/quantum. Frozen plans are separate from evolving run logs.
Nothing is published and no prior numerical convergence is inherited.
"""
from datetime import datetime,timezone
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ['source-run','initial-checkpoint','df-cache','protocol','run-out','analysis-out','plan','receipt']:
        parser.add_argument('--'+flag,type=Path,required=True)
    args=parser.parse_args()
    for path in [args.run_out,args.analysis_out,args.plan,args.receipt]:
        path=path.resolve();path.relative_to(ROOT)
        if path.exists():raise FileExistsError('Choose a new result/plan path: '+str(path))
    args.plan.mkdir(parents=True,exist_ok=False)
    solver=ROOT/'scripts/run_vertical_tddft.py';auditor=ROOT/'scripts/analyze_electronic_checkpoint.py'
    settings=json.loads(args.protocol.read_text(encoding='utf-8'))
    command=[sys.executable,str(solver),'--protocol',str(args.protocol.resolve()),
        '--restart-source',str(args.source_run.resolve()),'--initial-checkpoint',str(args.initial_checkpoint.resolve()),
        '--df-cache',str(args.df_cache.resolve()),'--out',str(args.run_out.resolve())]
    analysis=[sys.executable,str(auditor),'--run',str(args.run_out.resolve()),'--out',str(args.analysis_out.resolve())]
    code=[solver,auditor,ROOT/'practicuum/shared/electronic_restart.py',ROOT/'practicuum/shared/lossless_scratch.py']
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in code}
    for p in code:shutil.copyfile(p,args.plan/p.name)
    shutil.copyfile(__file__,args.plan/'launcher-source.py')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() if (ROOT/'.git').exists() else None
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip() if (ROOT/'.git').exists() else None
    save(args.plan/'plan.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),
        'code_commit':commit,'branch':branch,'code_sha256':hashes,'solver_argv':command,'analysis_argv':analysis,
        'scope':'Fresh SCF/TDDFT after compatibility gates, then independent checkpoint audit; no publication',
        'scientific_acceptance':'REVIEW_REQUIRED even after numerical PASS'})
    env=dict(os.environ,PYTHONUTF8='1',OMP_NUM_THREADS=str(settings['resources']['threads']),
             OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS=str(settings['resources']['threads']))
    logdir=ROOT/'tmp';logdir.mkdir(exist_ok=True)
    solver_log=logdir/(args.run_out.name+'.launcher.log');analysis_log=logdir/(args.analysis_out.name+'.launcher.log')
    if any(sha(ROOT/name)!=digest for name,digest in hashes.items()):raise ValueError('Planned source changed')
    with solver_log.open('xb') as stream:process=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    record={'finished_utc':datetime.now(timezone.utc).isoformat(),'solver_exit_code':process.returncode,
        'scope':'Numerical execution and independent audit only','scientific_acceptance':'REVIEW_REQUIRED'}
    if process.returncode:
        record.update(status='BLOCKED',reason='Solver did not complete numerical gates; inspect immutable run failure')
    elif any(sha(ROOT/name)!=digest for name,digest in hashes.items()):
        record.update(status='BLOCKED',reason='Source changed after plan; explicit audit continuation required')
    else:
        result=json.loads((args.run_out/'result.json').read_text())
        if result['status']!='PASS':raise ValueError('Completed numerical PASS required before analysis')
        with analysis_log.open('xb') as stream:checked=subprocess.run(analysis,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record.update(status='PASS' if checked.returncode==0 else 'FAIL',analysis_exit_code=checked.returncode)
    args.receipt.parent.mkdir(parents=True,exist_ok=True);save(args.receipt,record)
    print(record['status'],record.get('reason','Numerical result and checkpoint audit completed'),flush=True)
    if record['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
