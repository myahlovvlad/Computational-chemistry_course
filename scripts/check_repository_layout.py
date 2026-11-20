"""Check documentation locations and links without modifying course files."""
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
from validate_course import markdown_references

ROOT = Path(__file__).resolve().parents[1]


def main():
    layout = json.loads((ROOT/'docs/layout.json').read_text(encoding='utf-8'))
    errors = []
    for old, new in layout['moved_documents'].items():
        if (ROOT/old).exists(): errors.append('Retired document location exists: '+old)
        if not (ROOT/new).is_file(): errors.append('Missing document: '+new)
    unexpected = {p.name for p in ROOT.glob('*.md')} - set(layout['root_markdown'])
    errors.extend('Unexpected root document: '+p for p in sorted(unexpected))
    for path in (ROOT/'docs').rglob('*.md'):
        for ref in markdown_references(path.read_text(encoding='utf-8')):
            parts = urlsplit(ref.strip('<>'))
            if not parts.scheme and parts.path and not (path.parent/unquote(parts.path)).exists():
                errors.append(str(path.relative_to(ROOT))+' -> '+ref)
    state = json.loads((ROOT/'docs/status/course-status.json').read_text(encoding='utf-8'))
    if state['repository']['canonical_branch'] != 'main': errors.append('Canonical branch changed')
    print(json.dumps({'status':'FAIL' if errors else 'PASS',
                      'moved_documents':len(layout['moved_documents']), 'errors':errors}, indent=2))
    if errors: raise SystemExit(1)


if __name__ == '__main__': main()
