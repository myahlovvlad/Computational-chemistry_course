"""Собрать Notebook из канонических Markdown-шагов; не исполняет и не оценивает задания."""
import json
import argparse
from pathlib import Path
import re
from urllib.parse import quote,unquote,urlsplit
import nbformat

ROOT=Path(__file__).resolve().parents[1]
PYTHON=re.compile(r'^```python\s*\n(.*?)^```\s*$',re.M|re.S)

def local_links(text,source,destination):
    def replace(match):
        original=match.group(1);parts=urlsplit(original)
        if parts.scheme or not parts.path:return match.group(0)
        target=(source.parent/unquote(parts.path)).resolve()
        import os
        relative=os.path.relpath(target,destination.parent).replace('\\','/')
        return ']('+quote(relative,safe='/._-')+('#'+parts.fragment if parts.fragment else '')+')'
    return re.sub(r'\]\(([^)]+)\)',replace,text)

def cells_from_step(source,destination,prefix):
    text=source.read_text(encoding='utf-8');cells=[];position=0
    for index,match in enumerate(PYTHON.finditer(text)):
        before=text[position:match.start()].strip()
        if before:cells.append(nbformat.v4.new_markdown_cell(local_links(before,source,destination)))
        cells.append(nbformat.v4.new_code_cell(match.group(1).rstrip()+'\n'))
        position=match.end()
    tail=text[position:].strip()
    if tail:cells.append(nbformat.v4.new_markdown_cell(local_links(tail,source,destination)))
    for index,cell in enumerate(cells):cell.id=(prefix+'-'+str(index))[:64]
    return cells

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',nargs='*');args=parser.parse_args()
    course=json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'))
    count=0
    for module in course['modules']:
        for lesson in module['lessons']:
            if args.only and lesson['id'] not in args.only:continue
            config_path=ROOT/lesson['practice']/'lesson.json'
            if not config_path.exists():raise FileNotFoundError('Урок ещё не подготовлен: '+str(config_path))
            config=json.loads(config_path.read_text(encoding='utf-8'))
            for role,key,steps in [('case','case_notebook','case_steps'),('lab','lab_notebook','lab_steps')]:
                target=ROOT/lesson[key];target.parent.mkdir(parents=True,exist_ok=True);cells=[]
                for number,relative in enumerate(config[steps],1):
                    source=(ROOT/relative).resolve();source.relative_to(ROOT)
                    cells.extend(cells_from_step(source,target,f"{lesson['id']}-{role}-{number}"))
                book=nbformat.v4.new_notebook(cells=cells,metadata={
                   'kernelspec':{'name':'course-v2-'+lesson['profile'],'display_name':'Курс химии v2 · '+lesson['profile']+' · uv','language':'python'},
                   'language_info':{'name':'python'},'course':{'course_version':course['version'],'lesson_id':lesson['id'],
                   'role':role,'source_steps':config[steps],'scientific_review':'NOT_RUN'}})
                nbformat.validate(book);nbformat.write(book,target);count+=1
    print('Собрано Notebook:',count,'; outputs отсутствуют до фактического исполнения')

if __name__=='__main__':main()
