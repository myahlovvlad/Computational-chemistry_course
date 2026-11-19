"""Copy immutable WSL calculation evidence, retaining large checkpoints in Linux."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True)
    parser.add_argument('--distro',default='Ubuntu-24.04')
    parser.add_argument('--names',nargs='+',required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    if any(not re.fullmatch(r'[A-Za-z0-9_.-]+',name) for name in args.names):raise ValueError('Only evidence directory basenames accepted')
    code='''import sys,tarfile
from pathlib import Path
root=Path(SOURCE_ROOT).resolve()/'practicuum/evidence'
names=NAMES
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
 for name in names:
  folder=(root/name).resolve();folder.relative_to(root)
  if not folder.is_dir():raise FileNotFoundError(folder)
  for path in sorted(folder.rglob('*')):
   if path.is_symlink():raise ValueError('Symlink in evidence')
   if not path.is_file() or path.suffix in {'.h5','.chk'}:continue
   if '__pycache__' in path.parts:continue
   archive.add(path,arcname=path.relative_to(root).as_posix(),recursive=False)
'''.replace('SOURCE_ROOT',repr(args.source_root)).replace('NAMES',repr(args.names))
    destination=ROOT/'practicuum/evidence';hashes={}
    with tempfile.TemporaryFile() as bundle:
        process=subprocess.run(['wsl','-d',args.distro,'--','python3','-'],input=code.encode('utf-8'),stdout=bundle,stderr=subprocess.PIPE)
        if process.returncode:raise RuntimeError(process.stderr.decode('utf-8',errors='replace'))
        bundle.seek(0)
        with tarfile.open(fileobj=bundle,mode='r:gz') as archive:
            members=archive.getmembers()
            for member in members:
                target=(destination/member.name).resolve();target.relative_to(destination.resolve())
                if not member.isfile():raise ValueError('Only regular calculation artifacts expected')
            for member in members:
                target=destination/member.name;data=archive.extractfile(member).read();digest=hashlib.sha256(data).hexdigest()
                if target.exists() and target.read_bytes()!=data:raise ValueError('Refuse to change prior evidence: '+member.name)
                target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():target.write_bytes(data)
                hashes[member.name]=digest
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    with args.receipt.open('x',encoding='utf-8') as stream:
        json.dump({'status':'PASS','collected_utc':datetime.now(timezone.utc).isoformat(),'source_root':args.source_root,
                   'distro':args.distro,'files_sha256':hashes,'excluded':'HDF5/checkpoint files remain in original Linux run; no source artifacts removed'},stream,indent=2)
    print('Collected',len(hashes),'immutable artifacts from',len(args.names),'calculation directories')


if __name__=='__main__':main()
