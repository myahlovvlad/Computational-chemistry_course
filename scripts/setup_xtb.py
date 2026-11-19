"""Install a SHA256-pinned official xTB binary locally; no global environment changes."""
import argparse
from datetime import datetime,timezone
import hashlib,json,os,platform,subprocess,tarfile,tempfile,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RELEASE='6.8.0'
ASSETS={
    ('Windows','AMD64'):('xtb-6.8.0-windows-x86_64-openblas.zip','abd7f74d60908925a7e88a030f83d448253ff4e087451f9b13aeda755eb7b98d'),
    ('Linux','x86_64'):('xtb-6.8.0-linux-x86_64-ifx-mkl.tar.xz','db090333361749ae0d9ccf0ce7c0035c0000f2ebad0847f6d77191d1954f4d68')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'scripts/bin'/('xtb-'+RELEASE))
    args=parser.parse_args();key=(platform.system(),platform.machine())
    if key not in ASSETS:raise RuntimeError('This exact release asset is not pinned for '+str(key))
    name,digest=ASSETS[key];destination=args.out.resolve()
    if destination.exists():
        receipt=destination/'installation.json'
        if not receipt.is_file():raise FileExistsError('Existing installation is not ours: '+str(destination))
        record=json.loads(receipt.read_text(encoding='utf-8'));executable=destination/record['executable']
        if hashlib.sha256(executable.read_bytes()).hexdigest()!=record['executable_sha256']:
            raise ValueError('Installed executable changed')
        print('Verified existing xTB',executable);return
    url=f'https://github.com/grimme-lab/xtb/releases/download/v{RELEASE}/{name}'
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='xtb-download-',dir=destination.parent) as temporary:
        archive=Path(temporary)/name
        with urllib.request.urlopen(url,timeout=60) as response,archive.open('xb') as stream:
            while chunk:=response.read(1024*1024):stream.write(chunk)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:raise ValueError('Official release SHA256 mismatch')
        destination.mkdir()
        if name.endswith('.zip'):
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.infolist():
                    (destination/member.filename).resolve().relative_to(destination)
                bundle.extractall(destination)
        else:
            with tarfile.open(archive) as bundle:bundle.extractall(destination,filter='data')
    matches=list(destination.rglob('xtb.exe' if key[0]=='Windows' else 'xtb'))
    matches=[p for p in matches if p.is_file() and p.parent.name=='bin']
    if len(matches)!=1:raise RuntimeError('No unambiguous xTB executable in the verified asset')
    executable=matches[0]
    env=dict(os.environ,PATH=str(executable.parent)+os.pathsep+os.environ.get('PATH',''),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    process=subprocess.run([str(executable),'--version'],env=env,capture_output=True,timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    version=(process.stdout+process.stderr).decode('utf-8',errors='replace')
    if process.returncode or RELEASE not in version:raise RuntimeError('Installed binary failed its version check: '+version)
    record={'status':'PASS','version':RELEASE,'created_utc':datetime.now(timezone.utc).isoformat(),
            'download_url':url,'archive_sha256':digest,'executable':executable.relative_to(destination).as_posix(),
            'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),'version_output':version,
            'platform':platform.platform(),'scope':'local pinned tool installation; no scientific calculation yet'}
    (destination/'installation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Installed and verified xTB',executable)


if __name__=='__main__':main()
