"""Freeze historical data versions before evolving canonical files on main.

Only storage locations change: branch/commit/path/blob/SHA lineage is preserved.
An existing archive object is never overwritten or repaired silently.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true');parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.relative_to(ROOT)
    if out.exists():raise FileExistsError('Choose a new immutable receipt: '+str(out))
    path=ROOT/'archive/branch-datasets/manifest.json';before=path.read_bytes();manifest=json.loads(before)
    changes={};checked=set()
    for row in manifest['records']:
        key=(row['preserved_path'],row['sha256'],row['git_blob'])
        if key in checked:continue
        checked.add(key);source=(ROOT/key[0]).resolve();source.relative_to(ROOT)
        if source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==key[1]:continue
        if source.is_relative_to(ROOT/'archive/branch-datasets/objects'):
            raise ValueError('Immutable archive object changed: '+key[0])
        if not re.fullmatch('[0-9a-f]{40}',key[2]):raise ValueError('Invalid original blob identifier')
        payload=subprocess.check_output(['git','cat-file','blob',key[2]],cwd=ROOT)
        sha=hashlib.sha256(payload).hexdigest()
        blob=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
        if (sha,blob)!=(key[1],key[2]):raise ValueError('Original bytes could not be recovered')
        target=ROOT/'archive/branch-datasets/objects'/(blob+source.suffix)
        if target.exists() and target.read_bytes()!=payload:raise ValueError('Archive destination differs')
        changes[key]=(target,payload)
    moves=[]
    if args.apply:
        for key,(target,payload) in changes.items():
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                with target.open('xb') as stream:stream.write(payload)
        for row in manifest['records']:
            key=(row['preserved_path'],row['sha256'],row['git_blob'])
            if key in changes:row['preserved_path']=changes[key][0].relative_to(ROOT).as_posix()
        if changes:path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for key,(target,payload) in changes.items():
        moves.append({'previous_storage':key[0],'preserved_path':target.relative_to(ROOT).as_posix(),
            'sha256':key[1],'git_blob':key[2],'bytes':len(payload)})
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as stream:json.dump({'status':'PASS','applied':args.apply,
        'scope':'Historical payloads verified against original SHA256 and Git blobs; lineage fields unchanged',
        'manifest_sha256_before':hashlib.sha256(before).hexdigest(),
        'manifest_sha256_after':hashlib.sha256(path.read_bytes()).hexdigest(),'moves':moves},stream,indent=2);stream.write('\n')
    print('Historical versions requiring separate storage:',len(moves),'applied:',args.apply)


if __name__=='__main__':main()
