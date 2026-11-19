"""Fixed identical XYZ bytes isolate xTB compiler/platform effects from sampling."""
from datetime import datetime,timezone
import argparse,hashlib,json,os,platform,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    p=read(args.inputs/'protocol.json');install=read(ROOT/'scripts/bin/xtb-6.8.0/installation.json')
    exe=(ROOT/'scripts/bin/xtb-6.8.0'/install['executable']).resolve()
    if sha(exe)!=install['executable_sha256']:raise ValueError('Executable changed')
    save(out/'manifest.json',{'utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
        'runner_sha256':sha(__file__),'protocol':p,'protocol_sha256':sha(args.inputs/'protocol.json'),'installation':install})
    shutil.copyfile(__file__,out/'runner-source.py');rows=[]
    for name,digest in p['geometry_sha256'].items():
        source=args.inputs/name
        if sha(source)!=digest:raise ValueError('Fixed geometry changed')
        folder=out/Path(name).stem;folder.mkdir();(folder/'input.xyz').write_bytes(source.read_bytes())
        (folder/'control.inp').write_bytes(b'$gbsa\n grid=tight\n$end\n')
        command=['xtb','input.xyz','--gfn','2','--alpb','water','gsolv','--chrg','0','--uhf','0','--parallel','1','--acc','0.01','--input','control.inp','--json']
        save(folder/'command.json',{'argv':command,'executable':str(exe),'input_sha256':sha(folder/'input.xyz')})
        env=dict(os.environ,PATH=str(exe.parent)+os.pathsep+os.environ.get('PATH',''),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_STACKSIZE='256M')
        started=time.perf_counter()
        with (folder/'stdout.log').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
            completed=subprocess.run(command,executable=str(exe),cwd=folder,env=env,stdout=stdout,stderr=stderr,timeout=1800,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if completed.returncode:raise RuntimeError('Fixed geometry calculation failed')
        native=read(folder/'xtbout.json');text=(folder/'stdout.log').read_text(errors='replace')
        final=re.findall(r'TOTAL ENERGY\s+([-+0-9.EDed]+)\s+Eh',text)
        if not final:raise ValueError('No energy output')
        e=float(final[-1].replace('D','E'))
        if native['method']!='GFN2-xTB' or not native['xtb version'].startswith('6.8.0') or abs(e-native['total energy'])>1e-7:
            raise ValueError('Method/version/energy gate failed')
        if native['number of electrons']!=148 or abs(sum(native['partial charges']))>1e-5:raise ValueError('State changed')
        rows.append({'geometry':name,'input_sha256':digest,'energy_Eh':e,'seconds':time.perf_counter()-started})
    save(out/'result.json',{'status':'PASS','scope':__doc__,'protocol_sha256':sha(args.inputs/'protocol.json'),'singlepoints':rows})
    print('Fixed geometry singlepoints PASS',len(rows),flush=True)
if __name__=='__main__':main()
