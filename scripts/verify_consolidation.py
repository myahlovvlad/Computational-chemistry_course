"""Verify selective archives against their immutable migration digests."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    matrix=json.loads((ROOT/'migration-matrix.json').read_text(encoding='utf-8'))
    count=0
    for record in matrix['components']:
        if 'sha256' not in record:continue
        path=(ROOT/record['destination']).resolve();path.relative_to(ROOT)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Changed historical bytes: '+record['destination'])
        count+=1
    mapping=json.loads((ROOT/'programm/LEGACY_CASE_MAPPING.json').read_text(encoding='utf-8'))
    if len(mapping)!=42 or len({r['source_case'] for r in mapping})!=42:
        raise ValueError('Legacy task loss or duplication')
    course=json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'))
    lessons={r['id'] for m in course['modules'] for r in m['lessons']}
    if any(not set(r['target_lessons'])<=lessons for r in mapping):raise ValueError('Unknown mapping target')
    print(json.dumps({'status':'PASS','archived_files':count,'mapped_cases':len(mapping),
      'scope':'exact historical byte preservation and mapping integrity; historical runs not re-certified'},indent=2))


if __name__=='__main__':main()
