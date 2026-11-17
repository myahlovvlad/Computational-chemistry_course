"""Verify published capture hashes and code correspondence without running a kernel."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    folder=ROOT/'evidence'
    manifest=json.loads((folder/'artifact-manifest.json').read_text(encoding='utf-8'))
    for record in manifest:
        path=folder/record['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Artifact bytes changed: '+record['path'])
    for name in ['01_guided_case.ipynb','02_independent_lab.ipynb']:
        active=json.loads((ROOT/name).read_text(encoding='utf-8'))
        for platform in ['windows-20261117','linux-20261117']:
            captured=json.loads((folder/platform/Path(name).stem/'input.ipynb').read_text(encoding='utf-8'))
            if [(c['cell_type'],c['source']) for c in active['cells']]!=[(c['cell_type'],c['source']) for c in captured['cells']]:
                raise ValueError(f'Lesson code changed since capture: {name}, {platform}')
    print(f'PASS: {len(manifest)} artifact hashes; lesson cells match captured inputs on both platforms')
    print('Scope: capture integrity only, not a new execution or scientific assessment')

if __name__=='__main__':main()
