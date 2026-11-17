"""Verify metadata and launch two representative notebooks, or all with --all."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parents[1]
NAME='chemistry-course-uv'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--all',action='store_true',help='Execute all active paired notebooks by stored kernel name')
    parser.add_argument('--output',default='tmp/kernel-smoke')
    args=parser.parse_args()
    target=ROOT/args.output
    target.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((ROOT/'course-manifest.json').read_text())
    paths=[ROOT/item[key] for item in manifest for key in ['worked_notebook','practice_notebook']]
    checks=[]
    for path in paths:
        book=nbformat.read(path,as_version=4)
        actual=book.metadata.kernelspec.name
        checks.append({'source':path.relative_to(ROOT).as_posix(),'kernel':actual,'status':'PASS' if actual==NAME else 'FAIL'})
    assert len(paths)==28 and all(x['status']=='PASS' for x in checks),checks
    spec=KernelSpecManager().get_kernel_spec(NAME)
    assert spec.argv[1:3]==['run','--frozen'],spec.argv
    assert spec.env['UV_PROJECT_ENVIRONMENT']==str(ROOT/'.venv'),spec.env
    selected=paths if args.all else [ROOT/'Labs/notebooks/lab02.ipynb',ROOT/'Labs/notebooks/lab12.ipynb']
    for path in selected:
        book=nbformat.read(path,as_version=4)
        for cell in book.cells:
            if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
        book.cells.insert(0,nbformat.v4.new_code_cell('import sys\nfrom pathlib import Path\nprint(sys.executable)\nassert Path(sys.prefix).resolve() == Path('+repr(str(ROOT/'.venv'))+').resolve()'))
        # No kernel_name override: resolve exactly what opening this notebook selects.
        NotebookClient(book,timeout=180,resources={'metadata':{'path':str(ROOT)}}).execute()
        nbformat.write(book,target/(path.stem+'.ipynb'))
        checks.append({'source':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'status':'PASS','check':'metadata-selected kernel, isolated interpreter and original notebook assertions'})
    result={'status':'PASS','argv':sys.argv,'interpreter':sys.executable,'kernel_argv':spec.argv,'checks':checks}
    (target/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
