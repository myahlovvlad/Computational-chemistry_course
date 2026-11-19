"""Собрать локальный пакет текстовых шагов; сетевой публикации и grader здесь нет."""
import argparse,hashlib,json,shutil,sys,subprocess
from pathlib import Path
from nbconvert.filters import markdown2html

ROOT=Path(__file__).resolve().parents[1]

def copy_resource(out,relative):
    source=(ROOT/relative).resolve();source.relative_to(ROOT)
    target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)

def grader_source(lesson_id,contract):
    # Standalone stdlib checker; platform adapter and execution remain NOT_RUN.
    return ('import json, math\nEXPECTED='+repr(contract)+'\n\n'
      'def check(reply):\n'
      '    try:\n'
      '        value=json.loads(reply)\n'
      '        if not isinstance(value,dict):return False\n'
      '        for key,expected in EXPECTED.items():\n'
      '            actual=value.get(key)\n'
      '            if isinstance(expected,bool):\n'
      '                if type(actual) is not bool or actual != expected:return False\n'
      '            elif isinstance(expected,(int,float)):\n'
      '                if type(actual) not in (int,float) or not math.isfinite(actual):return False\n'
      '                if not math.isclose(actual,expected,rel_tol=1e-5,abs_tol=1e-7):return False\n'
      '            elif actual != expected:return False\n'
      '        return True\n'
      '    except (ValueError,TypeError,OverflowError):return False\n')
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
    contracts_path=ROOT/'practicuum/shared/research_contracts.json'
    contracts=json.loads(contracts_path.read_text(encoding='utf-8')) if contracts_path.exists() else {}
    # Portable notebook distribution retains the same root layout. No instructor,
    # archive, user workspace, ignored cache, or unrelated local downloads included.
    copy_resource(out,'programm/course.json')
    for source in (ROOT/'practicuum/shared').glob('*.py'):
        copy_resource(out,source.relative_to(ROOT))
    for source in (ROOT/'practicuum/shared').glob('*.json'):
        copy_resource(out,source.relative_to(ROOT))
    tracked=subprocess.check_output(['git','ls-files','-z','practicuum/shared/data'],cwd=ROOT).decode('utf-8').split('\0')
    for relative in tracked:
        if relative and (ROOT/relative).is_file():copy_resource(out,relative)
    for relative in ['scripts/environment/pyproject.toml','scripts/environment/uv.lock',
        'scripts/setup_environment.py','scripts/setup-windows.ps1','scripts/setup-linux.sh',
        'scripts/README.md','THIRD_PARTY_NOTICES.md']:
        copy_resource(out,relative)
    # Resource-heavy research is a separate explicit CLI route. Include its real
    # inputs and code so the notebook's training command works after unpacking.
    for name in ['fetch_target_qsar.py','train_target_qsar.py','audit_target_qsar.py',
                 'fetch_research_structures.py','prepare_target_docking.py','run_target_redocking.py',
                 'run_research_quantum.py','analyze_hplc_research.py','analyze_statin_research.py',
                 'analyze_caffeine_kinetics.py','analyze_xanthine_chromatography.py',
                 'analyze_istradefylline_solubility.py']:
        copy_resource(out,'scripts/'+name)
    for source in (ROOT/'practicuum/protocols').glob('*.json'):
        copy_resource(out,source.relative_to(ROOT))
    for target in ['A2A','HMGCR']:
        for name in ['dataset.json','curated.csv']:
            copy_resource(out,f'practicuum/evidence/20261119-research-{target}-dataset/{name}')
    for name in ['crystals-12-00917.pdf','crystals-12-00917-s001.zip','provenance.json']:
        copy_resource(out,'practicuum/evidence/20261119-istradefylline-solubility-source/'+name)
    for source in (ROOT/'web-training').rglob('*'):
        if source.is_file() and source.suffix in {'.html','.js','.css','.json','.svg','.png'} and not any(p in {'node_modules','workspace','__pycache__'} for p in source.parts):
            copy_resource(out,source.relative_to(ROOT))
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
      if lesson['id'] in contracts:
        grader=folder/'numeric_grader.py'
        grader.write_text(grader_source(lesson['id'],contracts[lesson['id']]),encoding='utf-8')
        payload['assessment']={'format':'JSON numerical subset + separate expert rubric',
          'contract':contracts[lesson['id']],'checker':grader.relative_to(out).as_posix(),
          'platform_adapter':'NOT_RUN','reasoning_grading':'manual',
          'prompt':'Выполните задания B в Notebook. Отправьте JSON с указанными численными полями; обоснование приложите отдельно.'}
      else:
        payload['assessment']={'format':'expert rubric','platform_adapter':'NOT_RUN'}
      (folder/'lesson.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
      items.append({'id':lesson['id'],'file':lesson['id']+'/lesson.json','steps':len(steps)})
    (out/'README.md').write_text('''# Локальный пакет курса для проверки перед Stepik

28 уроков и 56 Notebook находятся в структуре исходного курса. Для выполнения распакуйте весь пакет и установите base/chem по scripts/README.md; одиночный Notebook без shared/data недостаточен. PySCF повторяется отдельно в Linux/WSL. Установщики и uv.lock сохранены. Интерактивные инструменты запускаются локальным HTTP-сервером из web-training.

Численные stdlib checkers предназначены для локальной проверки ограниченного JSON-контракта. Они не оценивают научную аргументацию. Интеграция checker с конкретным Stepik block, загрузка assets и тестовый курс NOT_RUN. HTML-ссылки требуют asset mapping при публикации. Лабораторные Notebook выполняются локально/JupyterLab, не внутри stdlib grader.

Полные преподавательские решения не включены. NIST raw JCAMP не распространяется. Сторонние права, ChEMBL CC BY-SA и источники — THIRD_PARTY_NOTICES.md и паспорта data. Пакет не является подтверждённой публикацией в Stepik.
''',encoding='utf-8')
    for path in out.rglob('*'):
      if path.is_file():manifest[path.relative_to(out).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    report={'format':'local-stepik-review-package-v1','partial':bool(missing),'lessons':items,'not_ready':missing,
      'files_sha256':manifest,'scope':'local build; HTML links require publication asset mapping',
      'stepik_api_integration':'NOT_RUN','stepik_grader':'NOT_RUN'}
    (out/'package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS local build:',len(items),'lessons;',len(missing),'not ready; Stepik integration NOT_RUN')

if __name__=='__main__':main()
