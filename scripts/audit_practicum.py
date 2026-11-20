"""Collect editorial indicators; counts are not a scientific or pedagogical grade."""
import argparse
from collections import defaultdict
import json
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--revision', help='Read canonical steps from this Git revision')
    args = parser.parse_args()
    revision = subprocess.check_output(['git','rev-parse',args.revision],cwd=ROOT,text=True).strip() if args.revision else None
    course = json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'))
    def read(relative):
        if args.revision:
            return subprocess.check_output(['git','show',revision+':'+relative],cwd=ROOT).decode('utf-8')
        return (ROOT/relative).read_text(encoding='utf-8')
    rows = []
    repeated = defaultdict(set)
    for module in course['modules']:
        for lesson in module['lessons']:
            cfg = json.loads(read(lesson['practice']+'/lesson.json'))
            case = '\n'.join(read(p) for p in cfg['case_steps'])
            lab = '\n'.join(read(p) for p in cfg['lab_steps'])
            blocks = re.findall(r'```python\s*\n(.*?)```',case,re.S)
            prose = re.sub(r'```.*?```','',case,flags=re.S)
            for para in re.split(r'\n\s*\n', re.sub(r'```.*?```','',case+'\n'+lab,flags=re.S)):
                if len(para.strip())>100: repeated[para.strip()].add(lesson['id'])
            rows.append({'lesson':lesson['id'],'title':lesson['title'],
                         'case_sources':cfg['case_steps'],'lab_sources':cfg['lab_steps'],
                         'normalized_source_sha256':{p:hashlib.sha256(read(p).encode('utf-8')).hexdigest()
                             for p in cfg['case_steps']+cfg['lab_steps']},
                         'case_prose_words':len(prose.split()),'code_blocks':len(blocks),
                         'longest_code_lines':max((len(b.splitlines()) for b in blocks),default=0),
                         'lab_none_placeholders':len(re.findall(r'task_\d\s*=\s*None',lab))})
    result = {'scope':'Automated editorial indicators for all 28 lessons; no learner observation, external scientific review or automatic quality score',
              'revision':revision or 'working tree', 'lessons':rows,
              'repeated_paragraphs':[{'text':text,'lesson_count':len(ids),'lessons':sorted(ids)}
                  for text,ids in sorted(repeated.items(),key=lambda item:len(item[1]),reverse=True) if len(ids)>=3]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Audited',len(rows),'lessons;',len(result['repeated_paragraphs']),'paragraphs repeat in >=3 lessons')


if __name__ == '__main__': main()
