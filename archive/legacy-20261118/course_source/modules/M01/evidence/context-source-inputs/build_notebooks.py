"""Generate the M01 pair from authored narrative and explicit runnable code cells."""
import json
from pathlib import Path
import re
import nbformat

ROOT=Path(__file__).resolve().parent
MARKER=re.compile(r'<!--\s*(cell|code):\s*([a-z0-9-]+)\s*-->')

def build():
    codes=json.loads((ROOT/'lesson_code.json').read_text(encoding='utf-8'))
    for stem,role in [('01_guided_case','guided'),('02_independent_lab','independent')]:
        text=(ROOT/'content'/(stem+'.md')).read_text(encoding='utf-8')
        markers=list(MARKER.finditer(text));cells=[]
        if text[:markers[0].start()].strip():raise ValueError('Text before first cell marker')
        for i,match in enumerate(markers):
            kind,identifier=match.groups()
            tail=text[match.end():markers[i+1].start() if i+1<len(markers) else len(text)].strip()
            if kind=='code':
                if tail:raise ValueError('Unmarked text following code '+identifier)
                cell=nbformat.v4.new_code_cell(codes[identifier])
                if identifier in {'g-setup','l-setup'}:cell.metadata['jupyter']={'source_hidden':True}
            else:
                if not tail:raise ValueError('Empty markdown cell '+identifier)
                cell=nbformat.v4.new_markdown_cell(tail.replace('](../',']('))
            cell.id=f'm01-{role}-{identifier}';cells.append(cell)
        book=nbformat.v4.new_notebook(cells=cells,metadata={
          'kernelspec':{'name':'course-m01-evidence','display_name':'M01 · scientific evidence · uv (no RDKit)','language':'python'},
          'language_info':{'name':'python'},
          'course':{'module':'M01','role':role,'version':'research-v2-context',
                    'narrative_source':'content/'+stem+'.md','code_source':'lesson_code.json'}})
        nbformat.validate(book)
        nbformat.write(book,ROOT/(stem+'.ipynb'))
        print(stem, len(cells),'cells')

if __name__=='__main__':build()
