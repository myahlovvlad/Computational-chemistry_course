"""Исполнить одну проверку и сохранить команду, входы, версии и фактический лог."""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.metadata,json,os,platform,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--input',action='append',default=[])
    parser.add_argument('--scope',required=True)
    parser.add_argument('--blocked-exit',type=int)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command:parser.error('Нужна команда после --')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs={}
    for relative in args.input:
        path=(ROOT/relative).resolve();path.relative_to(ROOT)
        inputs[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        target=out/'inputs'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(path.read_bytes())
    record={'argv':command,'cwd':str(ROOT),'scope':args.scope,
      'started_utc':datetime.now(timezone.utc).isoformat(),'inputs_sha256':inputs,
      'capture_python':sys.version,'platform':platform.platform(),
      'capture_packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions()))}
    start=time.perf_counter()
    try:
      result=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONUTF8='1'),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',errors='replace',check=False)
      status='PASS' if result.returncode==0 else ('BLOCKED' if result.returncode==args.blocked_exit else 'FAIL')
      record.update(exit_code=result.returncode,status=status)
      (out/'stdout.log').write_text(result.stdout,encoding='utf-8')
      (out/'stderr.log').write_text(result.stderr,encoding='utf-8')
    except FileNotFoundError as error:record.update(status='BLOCKED',error=str(error))
    record['seconds']=time.perf_counter()-start
    (out/'check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(record['status'],args.scope)
    if record['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
