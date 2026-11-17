"""Check published course links, notebooks, manifest and dataset hashes."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote
import nbformat

ROOT=Path(__file__).resolve().parents[1]


def main() -> None:
    errors=[]
    manifest=json.loads((ROOT/'course-manifest.json').read_text(encoding='utf-8'))
    if len(manifest)!=14:errors.append('Expected 14 module mappings')
    paired_paths=[item[key] for item in manifest for key in ['worked_notebook','practice_notebook']]
    if len(set(paired_paths))!=28:errors.append('Notebook mappings must be distinct')
    if {item['module'] for item in manifest}!=set(range(1,15)):errors.append('Expected module IDs 1..14')
    candidates=[ROOT/'README.md',*(ROOT/'Module_theory').glob('*.md'),
                *(ROOT/'Labs').rglob('*.md'),*(ROOT/'Literature').glob('*.md')]
    for path in candidates:
        text=path.read_text(encoding='utf-8')
        # A reaction SMARTS in a fenced code block is not a Markdown link.
        text=re.sub(r'```.*?```','',text,flags=re.S)
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('http:','https:','#','mailto:')):continue
            target=unquote(target.split('#')[0])
            if not (path.parent/target).exists():errors.append(f'{path.relative_to(ROOT)} -> {target}')
    for module in manifest:
        for key in ['theory','lab','notebook','worked_notebook','practice_notebook','solutions']:
            if not (ROOT/module[key]).exists():errors.append(module[key])
        for key,role in [('worked_notebook','worked'),('practice_notebook','practice')]:
            notebook=nbformat.read(ROOT/module[key],as_version=4);nbformat.validate(notebook)
            if notebook.metadata.get('course',{}).get('role')!=role:errors.append(f'Role: {module[key]}')
            if notebook.metadata.get('course',{}).get('module')!=module['module']:errors.append(f'Module ID: {module[key]}')
            if notebook.metadata.kernelspec.name!='chemistry-course-uv':errors.append(f'Kernel: {module[key]}')
            for cell in notebook.cells:
                if cell.cell_type=='code':
                    compile(cell.source,module[key],'exec')
                    if any(out.output_type=='error' for out in cell.outputs):errors.append(f"Notebook error: {module[key]}")
                elif cell.cell_type=='markdown':
                    text=re.sub(r'```.*?```','',cell.source,flags=re.S)
                    for target in re.findall(r'\]\(([^)]+)\)',text):
                        if target.startswith(('http:','https:','#','mailto:')):continue
                        target=unquote(target.split('#')[0])
                        if not ((ROOT/module[key]).parent/target).exists():errors.append(f"{module[key]} -> {target}")
        theory=(ROOT/module['theory']).read_text(encoding='utf-8')
        sections=re.findall(r'^## (\d+\.\d+)\.',theory,re.M)
        if sections!=[f"{module['module']}.{n}" for n in range(1,9)]:errors.append(f"Section sequence: {module['theory']}")
    for entry in json.loads((ROOT/'Labs/datasets/manifest.json').read_text(encoding='utf-8')):
        path=ROOT/'Labs/datasets'/entry['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:errors.append(f"Dataset hash: {entry['path']}")
    if errors:
        print('\n'.join(errors));raise SystemExit(1)
    active=list((ROOT/'Labs/notebooks').glob('lab*.ipynb'))
    if len(active)!=28:errors.append(f'Expected 28 active notebooks, got {len(active)}')
    if errors:print('\n'.join(errors));raise SystemExit(1)
    print('PASS: 14 pairs / 28 notebooks, 112 theory sections, schema/code, links, dataset hashes')


if __name__=='__main__':main()
