"""Append immutable, traceable evidence versions without replacing learner files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import uuid

KINDS = {'measured', 'literature', 'calculated', 'simulation', 'hypothesis'}


def validate_graph(nodes, edges, *, calculation=True):
    """Concept maps may cycle; calculation dependency graphs may not."""
    ids = [n['id'] for n in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate node ID')
    known = set(ids)
    outgoing = {n: [] for n in ids}
    for a, b in edges:
        if a not in known or b not in known:
            raise ValueError('Dangling dependency')
        outgoing[a].append(b)
    if calculation:
        # Kahn traversal avoids recursion limits on large dossiers.
        degree = {n: 0 for n in ids}
        for children in outgoing.values():
            for child in children:
                degree[child] += 1
        ready = [n for n in ids if degree[n] == 0]
        visited = 0
        while ready:
            node = ready.pop()
            visited += 1
            for child in outgoing[node]:
                degree[child] -= 1
                if degree[child] == 0:
                    ready.append(child)
        if visited != len(ids):
            raise ValueError('Calculation dependency cycle')
    return True


def append_record(dossier, lesson_id, role, result, root, *, inputs=(),
                  method='see canonical lesson source', conditions=None,
                  uncertainty='see lesson limitations; independent validation pending',
                  decision='retain calculation; scientific conclusion requires review'):
    if not re.fullmatch(r'M\d{2}-L\d{2}', lesson_id):
        raise ValueError('Invalid lesson ID')
    if role not in {'A', 'B', 'instructor'}:
        raise ValueError('Invalid role')
    if result.get('kind') not in KINDS:
        raise ValueError('Explicit evidence kind required')
    root = Path(root).resolve()
    hashes = {}
    for relative in inputs:
        path = (root / relative).resolve()
        path.relative_to(root)
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    practice = root / 'practicuum/modules' / lesson_id[:3] / 'lessons' / lesson_id[-3:]
    sources = [practice/'lesson.json', *sorted((practice/'steps').glob('*.md'))]
    sources += sorted((root/'practicuum/shared').glob('*.py'))
    source_hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sources if p.is_file()}
    record = {
        'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'lesson_id': lesson_id, 'role': role, 'kind': result['kind'],
        'input_sha256': hashes, 'algorithm_sha256': source_hashes,
        'python': platform.python_version(), 'method': method,
        'conditions': conditions or {'scope': 'educational computation; see lesson'},
        'uncertainty': uncertainty, 'decision': decision,
        'result': result, 'scientific_review': 'NOT_RUN',
    }
    payload = json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)
    folder = Path(dossier) / 'evidence' / lesson_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+role+'-'+uuid.uuid4().hex+'.json')
    with target.open('x', encoding='utf-8') as stream:
        stream.write(payload+'\n')
    return target
