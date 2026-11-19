"""Verify preserved data from retired branch tips without needing those branches."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest = json.loads((ROOT/'archive/branch-datasets/manifest.json').read_text(encoding='utf-8'))
    checked = set()
    for row in manifest['records']:
        path = (ROOT/row['preserved_path']).resolve()
        path.relative_to(ROOT)
        key = (str(path), row['sha256'])
        if key in checked:
            continue
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != row['sha256']:
            raise ValueError('Changed preserved data: '+row['preserved_path'])
        blob = hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
        if blob != row['git_blob']:
            raise ValueError('Original Git blob differs: '+row['source_path'])
        checked.add(key)
    print(json.dumps({'status':'PASS', 'branch_dataset_records':len(manifest['records']),
                      'unique_files_checked':len(checked)}, indent=2))

if __name__ == '__main__':
    main()
