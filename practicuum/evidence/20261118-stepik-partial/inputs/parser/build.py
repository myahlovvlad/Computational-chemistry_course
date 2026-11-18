"""Собрать локальный пакет текстовых шагов; сетевой публикации и grader здесь нет."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
from nbconvert.filters import markdown2html

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args()
    course=json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'))
    ready=[];missing=[]
    for module in course['modules']:
      for lesson in module['lessons']:
        if (ROOT/lesson['practice']/'lesson.json').is_file():ready.append((module,lesson))
        else:missing.append(lesson['id'])
    if missing and not args.allow_partial:
      print('BLOCKED: полный курс не подготовлен:',','.join(missing));raise SystemExit(2)
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);items=[];manifest={}
    for module,lesson in ready:
      folder=out/lesson['id'];folder.mkdir()
      config=json.loads((ROOT/lesson['practice']/'lesson.json').read_text(encoding='utf-8'))
      sources=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/lesson['theory']).glob('*.md'))]
      sources+=config['case_steps']+config['lab_steps']
      steps=[]
      for i,relative in enumerate(sources,1):
        path=ROOT/relative;text=path.read_text(encoding='utf-8')
        # Каждый MD остаётся отдельным шагом; lesson/section ID выдаёт платформа при публикации.
        steps.append({'local_id':lesson['id']+f'-S{i:02}','position':i,'source':relative,
          'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'block':{'name':'text','text':markdown2html(text)}})
        target=out/'sources'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
      for key in ['case_notebook','lab_notebook']:
        path=ROOT/lesson[key];target=out/path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
      payload={'module_id':module['id'],'lesson_id':lesson['id'],'title':lesson['title'],'steps':steps,
        'notebooks':[lesson['case_notebook'],lesson['lab_notebook']],
        'publication_status':'NOT_RUN','grader_status':'NOT_RUN'}
      (folder/'lesson.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
      items.append({'id':lesson['id'],'file':lesson['id']+'/lesson.json','steps':len(steps)})
    for path in out.rglob('*'):
      if path.is_file():manifest[path.relative_to(out).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    report={'format':'local-stepik-review-package-v1','partial':bool(missing),'lessons':items,'not_ready':missing,
      'files_sha256':manifest,'scope':'local build; HTML links require publication asset mapping',
      'stepik_api_integration':'NOT_RUN','stepik_grader':'NOT_RUN'}
    (out/'package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS local build:',len(items),'lessons;',len(missing),'not ready; Stepik integration NOT_RUN')

if __name__=='__main__':main()
