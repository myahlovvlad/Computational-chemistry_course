"""Check rendered markup and local links; does not certify scientific understanding."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote,urlsplit

import nbformat
from nbconvert import HTMLExporter

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();checks=[];inputs=[]
    for name in ['01_guided_case.ipynb','02_independent_lab.ipynb']:
        path=ROOT/name;book=nbformat.read(path,as_version=4)
        inputs.append({'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        missing=[]
        for cell in book.cells:
            if cell.cell_type!='markdown':continue
            for target in re.findall(r'\]\(([^)]+)\)',cell.source):
                link=urlsplit(target)
                if not link.scheme and link.path and not (ROOT/unquote(link.path)).exists():missing.append(target)
        html,_=HTMLExporter().from_notebook_node(book)
        result={'file':name,'missing_local_links':missing,'html_bytes':len(html.encode('utf-8'))}
        assert not missing,missing
        if name.startswith('01_'):
            result['embedded_pngs']=html.count('data:image/png;base64,')
            result['tex_preserved']=r'\frac{S}{1\;\mathrm{mol\,L^{-1}}}' in html and '$$' in html
            assert result['embedded_pngs']>=2 and result['tex_preserved']
        checks.append(result)
    report={'status':'PASS','argv':[sys.executable,*sys.argv],'utc':datetime.now(timezone.utc).isoformat(),
       'versions':{'python':sys.version,'nbconvert':importlib.metadata.version('nbconvert')},
       'scope':'local links, embedded images and TeX markup retention; no browser typesetting, remote-link validation or learner assessment',
       'inputs':inputs,'checks':checks}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
