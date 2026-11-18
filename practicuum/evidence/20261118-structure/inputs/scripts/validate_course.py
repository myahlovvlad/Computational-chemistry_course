"""Проверить структуру, связи и генерацию подготовленных уроков; не сертифицирует обучение."""
import argparse,hashlib,json,re,sys
from pathlib import Path
from urllib.parse import unquote,urlsplit
import nbformat
from build_notebooks import cells_from_step

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--release',action='store_true')
    args=parser.parse_args();course=json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'))
    errors=[];prepared=[];planned=[];ids=[];hours=0
    if len(course['modules'])!=14:errors.append('Ожидаются 14 модулей')
    for number,module in enumerate(course['modules'],1):
      if module['id']!=f'M{number:02}':errors.append('Нарушен порядок модулей')
      for lesson in module['lessons']:
        ids.append(lesson['id']);hours+=lesson['hours']
        if lesson['profile'] not in ['base','chem','quantum']:errors.append('Неизвестный профиль '+lesson['id'])
        config_path=ROOT/lesson['practice']/'lesson.json'
        if not config_path.is_file():
          planned.append(lesson['id'])
          if lesson['status']!='PLANNED':errors.append('Нет исходников объявленного урока '+lesson['id'])
          continue
        prepared.append(lesson['id'])
        theory=list((ROOT/lesson['theory']).glob('*.md'))
        if len(theory)<3:errors.append('Недостаточно отдельных теоретических шагов '+lesson['id'])
        config=json.loads(config_path.read_text(encoding='utf-8'))
        for role,key,steps in [('case','case_notebook','case_steps'),('lab','lab_notebook','lab_steps')]:
          target=ROOT/lesson[key];expected=[]
          try:
            for i,relative in enumerate(config[steps],1):
              source=(ROOT/relative).resolve();source.relative_to(ROOT)
              expected+=cells_from_step(source,target,f"{lesson['id']}-{role}-{i}")
            book=nbformat.read(target,as_version=4);nbformat.validate(book)
            if [(c.cell_type,c.source) for c in expected]!=[(c.cell_type,c.source) for c in book.cells]:
              errors.append('Notebook отстаёт от MD '+lesson['id']+' '+role)
            if book.metadata.kernelspec.name!='course-v2-'+lesson['profile']:errors.append('Неверное ядро '+str(target))
          except Exception as error:errors.append(str(error))
    if len(ids)!=len(set(ids)):errors.append('Повторены ID уроков')
    if len(ids)!=28:errors.append('Ожидаются 28 исследовательских уроков')
    if hours!=course['core_hours_planned'] or not 100<=hours<=140:errors.append('Несогласованная нагрузка')
    folders=['programm','skills','scripts','media','web-training','theory','practicuum','parser']
    for name in folders:
      if not (ROOT/name).is_dir():errors.append('Отсутствует область '+name)
    # Проверяем локальные ссылки действующих текстов, архив сохраняет исторический контекст.
    for folder in folders+['.']:
      documents=(ROOT/folder).glob('*.md') if folder=='.' else (ROOT/folder).rglob('*.md')
      for path in documents:
        if any(part.startswith('.') or part in ['evidence','workspace','dist','cache'] for part in path.relative_to(ROOT).parts):continue
        for reference in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
          parts=urlsplit(reference.strip('<>'))
          if parts.scheme or not parts.path:continue
          target=(path.parent/unquote(parts.path)).resolve()
          if not target.exists():errors.append('Неразрешённая ссылка '+str(path.relative_to(ROOT))+' → '+reference)
    release_blockers=planned+(['independent scientific review NOT_RUN','student pilot NOT_RUN'] if prepared else [])
    report={'status':'FAIL' if errors else ('BLOCKED' if args.release and release_blockers else 'PASS'),
      'scope':'structure/source consistency only; no new calculation or scientific review',
      'modules':len(course['modules']),'lessons':len(ids),'hours_planned':hours,'prepared_lessons':prepared,
      'planned_lessons':planned,'errors':errors,'release_blockers':release_blockers}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report['status']!='PASS':raise SystemExit(2 if report['status']=='BLOCKED' else 1)

if __name__=='__main__':main()
