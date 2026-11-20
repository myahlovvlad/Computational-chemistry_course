"""Inventory evidence without deleting files or treating unlinked data as disposable."""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try: output_name=args.out.resolve().relative_to(ROOT).as_posix()
    except ValueError: output_name=None
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    consumers = []
    for name in tracked:
        p = ROOT/name
        if (not name or name==output_name or name.startswith(('archive/', 'practicuum/evidence/'))
                or p.suffix not in {'.py', '.md', '.json', '.yml', '.ipynb'}
                or not p.is_file() or p.stat().st_size > 5_000_000): continue
        consumers.append((name, p.read_text(encoding='utf-8', errors='replace')))
    preserved = json.loads((ROOT/'archive/branch-datasets/manifest.json').read_text(encoding='utf-8'))
    protected = {r['preserved_path'] for r in preserved['records']}
    folders = []
    total = 0
    for directory in sorted((ROOT/'practicuum/evidence').iterdir()):
        if not directory.is_dir(): continue
        files = []
        for parent, dirs, names in os.walk(directory, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(parent)/d).is_symlink()]
            for name in names:
                p = Path(parent)/name
                if p.is_file() and not p.is_symlink(): files.append(p)
        size = sum(p.stat().st_size for p in files)
        total += size
        refs = [name for name, text in consumers if directory.name in text]
        immutable = sum(p.relative_to(ROOT).as_posix() in protected for p in files)
        cache = [p for p in files if '__pycache__' in p.parts or p.suffix in {'.pyc', '.pyo'}]
        notebooks = [p for p in files if p.name == 'executed.ipynb']
        checkpoints = [p for p in files if p.suffix in {'.h5', '.chk'} or p.name == 'xtbrestart']
        folders.append({'directory':directory.relative_to(ROOT).as_posix(), 'bytes':size,
                        'files':len(files), 'explicit_consumers':refs,
                        'protected_by_branch_manifest':immutable,
                        'bytecode_cache_files':len(cache),
                        'bytecode_cache_bytes':sum(p.stat().st_size for p in cache),
                        'executed_notebooks':len(notebooks),
                        'executed_notebook_bytes':sum(p.stat().st_size for p in notebooks),
                        'checkpoints':len(checkpoints),
                        'retention':'KEEP: branch history' if immutable else
                            ('KEEP: explicit consumer' if refs else 'REVIEW: absence of a literal reference is not proof of non-use')})
    report = {'status':'PASS', 'observed_utc':datetime.now(timezone.utc).isoformat(), 'scope':'Read-only size/reference inventory; no scientific acceptance or deletion authorization',
              'folders':len(folders), 'bytes':total,
              'bytecode_cache_bytes':sum(r['bytecode_cache_bytes'] for r in folders),
              'executed_notebook_bytes':sum(r['executed_notebook_bytes'] for r in folders),
              'inventory':sorted(folders, key=lambda r:r['bytes'], reverse=True)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='inventory'}, indent=2))
    for item in report['inventory'][:10]:
        print(round(item['bytes']/1024**2, 2), 'MiB', item['directory'])


if __name__ == '__main__': main()
