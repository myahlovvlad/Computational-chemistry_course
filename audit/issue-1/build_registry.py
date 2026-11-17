"""Occurrence-level inventory. PASS is assigned only to bounded run evidence.

Explicit learner actions stay NOT_RUN even when a worked answer is printed.
Repeated occurrences have independent IDs and related_ids, not silent dedup.
"""
from __future__ import annotations
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import runpy

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"audit/issue-1"
EVIDENCE=BASE/"evidence"
ROWS=[]
COVERAGE=[]

SCIENCE={
1:"Цель, объект, модель и независимый контроль; факторный эффект не равен коэффициенту; без повторов нет оценки ошибки.",
2:"Единицы, изоляция интерпретатора, версии; химический результат проверяется отдельно от импорта.",
3:"Сериализация не равна таутомеризации; parent не тождествен физическому образцу; сохранить raw, Cl и стереохимию.",
4:"MW g/mol, TPSA Å²; logP не logD(pH); четыре условия Ro5 не доказывают эффективность/безопасность.",
5:"Танимото относится к выбранным признакам; указать radius/fpSize/chirality; сходство не равно активности.",
6:"ETKDG/MMFF, параметры и status; локальный минимум не глобальный; энергии сравнивать для одной системы.",
7:"Положительная концентрация в М перед логарифмом; знак границы меняется; IC50/Ki/ассеи не смешивать.",
8:"PAINS — сигнал риска, не доказанный механизм; Z′ и EF измеряют разные свойства, нужна истинная разметка.",
9:"ID, единицы и происхождение точки; статический график/таблица не подтверждают 3D, неопределённость и доступность.",
10:"Vina score не Kd/экспериментальная ΔG; serial-mapped RMSD к prepared reference не symmetry-corrected RMSD к независимо сверенной кристаллографии.",
11:"Измеренный logS, только train fit, непересекающиеся identity/scaffold-группы; holdout не доказывает калибровку применимости.",
12:"Заряд, Nalpha−Nbeta, базис, метод и сходимость; RHF не DFT; ΔE не ΔG и не барьер.",
13:"Один ester SMARTS не универсальный ретросинтез; выходы перемножаются лишь в оговорённой модели; цены вымышлены.",
14:"Сохранение ID/ошибочных строк, hash/политики; reference CLI/GUI не самостоятельное досье, transfer или защита.",
}


def source_span(path, start=1, end=None):
    p=ROOT/path
    lines=p.read_text(encoding="utf-8").splitlines()
    return f"{path}:L{start}-L{end or start}"


def locate(path, needle, occurrence=0):
    text=(ROOT/path).read_text(encoding="utf-8")
    matches=list(re.finditer(re.escape(needle),text))
    if len(matches)<=occurrence: return source_span(path)
    index=matches[occurrence].start()
    return source_span(path,text.count('\n',0,index)+1,text.count('\n',0,index+len(needle))+1)


def record(module, identifier, prompt, source, kind="conceptual", lesson=None,
           expected=None, input_data=None, run=None, result=None, status=None,
           reason=None, scope="learner_action", related="", partial="", requirement="required-or-editorial-decision-needed"):
    row={"module_id":str(module),"lesson_id":lesson or f"{module}.cross",
         "exercise_id":identifier,"learning_outcome":re.sub(r'\s+',' ',prompt).strip(),
         "source":source,"input":input_data or "Условие и контекст в указанном source; отдельный fixture не определён",
         "expected_output":expected or "Обоснованный ответ/артефакт по условию; эталон в Markdown не является проверкой",
         "science_check":SCIENCE[module],"test_command":"NOT_RUN — выполняемой команды/оценки этого действия нет",
         "environment":"NOT_RUN / требуется методическая или платформенная проверка",
         "status":status or "NOT_RUN","evidence":"","reviewer":"Codex audit: execution/static inspection; external scientific/learner review NOT_RUN",
         "blockers":reason or "Нет самостоятельного выполнения/рубрики с фактическим оцениванием этого действия",
         "exercise_type":kind,"status_scope":scope,"requirement":requirement,
         "related_ids":related,"partial_evidence":partial,"actual_output":result or "Не наблюдался",
         "source_commit":"75e9e8606972f49f9a380588ee9c1db1c10d90fa"}
    if run:
        meta=json.loads((EVIDENCE/run/"run.json").read_text(encoding="utf-8"))
        row["test_command"]=meta["command_windows"]
        stage = "core" if run.startswith(("02-", "03-", "04-", "05-", "06-", "07-")) else "labs"
        row["environment"]=f"audit/issue-1/evidence/{stage}-environment/stdout.txt"
        row["evidence"]=f"audit/issue-1/evidence/{run}/run.json; stdout.txt; stderr.txt" 
        if status is None:row["status"]=meta["status"]
        if row["status"]=="PASS":row["blockers"]="Только указанный scope; научная экспертиза всей темы и оценивание ученика не подтверждены"
    ROWS.append(row)
    return row


def lesson_at(text, position, module):
    headings=list(re.finditer(r'^## (\d+\.\d+)\.',text[:position],re.M))
    return headings[-1][1] if headings else f"{module}.intro"


def module_actions():
    cue=re.compile(r'Быстрый результат|Практика:|В скелете|Задание «скелет»|Самостоятельн|Повторение|Три проверки|Три обязательные|Контроль\.|Контроль Stepik|Затем замените|Разберите список|Рассчитайте|Сравните|Запишите|Сначала студент|Студент дописывает|Практика ESOL|Сдать исходный|На защите',re.I)
    for path in sorted((ROOT/'Stepik_course/modules').glob('*.md')):
        rel=path.relative_to(ROOT).as_posix();module=int(path.name[:2]);text=path.read_text(encoding='utf-8')
        blocks=list(re.finditer(r'(?ms)^```[^\n]*\n.*?^```',text))
        counter=0
        for paragraph in re.finditer(r'(?m)^[^\n]+(?:\n(?!\n)[^\n]+)*',text):
            value=paragraph[0]
            if any(b.start()<=paragraph.start()<b.end() for b in blocks):continue
            if value.startswith(('#','Источники:','|')) or not cue.search(value):continue
            counter+=1
            ref=source_span(rel,text.count('\n',0,paragraph.start())+1,text.count('\n',0,paragraph.end())+1)
            identifier=f"M{module:02d}-ACT-{counter:02d}"
            is_control=bool(re.search(r'\*\*Контроль(?: Stepik)?[. ]',value))
            if is_control:
                pairs=list(re.finditer(r'«([^»]+)»[.!?]?\s*\*\*Ответ:\*\*\s*(.*?)(?=«[^»]+»[.!?]?\s*\*\*Ответ:|$)',value))
                if len(pairs)!=3:raise ValueError(f"Control parsing requires review: {rel}: {value}")
                for i,pair in enumerate(pairs,1):
                    record(module,f"M{module:02d}-Q{i}",pair[1],ref,lesson=lesson_at(text,paragraph.start(),module),expected=pair[2].strip(),
                           related=identifier,scope="learner_interpretation")
                COVERAGE.append({"source":ref,"action_paragraph":value,"registered_ids":[f"M{module:02d}-Q{i}" for i in range(1,4)]})
                continue
            kind="programming" if re.search(r'код|скрипт|функци|notebook|python|CSV|скелет|\.fit',value,re.I) else "calculation" if re.search(r'рассч|посчитать|вычисл|MAE|Z′|EF|энерги|Танимото|перемнож',value,re.I) else "research" if re.search(r'проект|паспорт|следующ|эксперимент|сравните|защит',value,re.I) else "conceptual"
            blocked=bool(re.search(r'В скелете|Скелет задания|Задание «скелет»',value))
            record(module,identifier,value,ref,kind,lesson_at(text,paragraph.start(),module),
                   status="BLOCKED" if blocked else "NOT_RUN",
                   reason="Отдельный исполняемый starter с пропусками не идентифицирован; решения/полный код не подтверждают этот вариант задания" if blocked else None,
                   partial=f"LAB{module:02d}-REFERENCE (другая, более узкая проверка)")
            ids=[identifier]
            checks=re.search(r'Три проверки(?: кода)?:\s*(.*?)(?:\. |$)',value)
            if checks:
                for i,condition in enumerate(checks[1].split(';'),1):
                    child=f"{identifier}-QC{i}"
                    record(module,child,condition.strip(),ref,kind,lesson_at(text,paragraph.start(),module),related=identifier,
                           scope="acceptance_condition_not_auto_execution",partial=f"LAB{module:02d}-REFERENCE")
                    ids.append(child)
            COVERAGE.append({"source":ref,"action_paragraph":value,"registered_ids":ids})
        for i,match in enumerate(re.finditer(r'```python\n(.*?)```',text,re.S)):
            details=json.loads((EVIDENCE/'07-module-examples/results.json').read_text(encoding='utf-8'))['checks']
            observed=next(r for r in details if r['module']==module and r['index']==i+1)
            record(module,f"M{module:02d}-CODE{i+1}","Выполнить существующий Python-пример без правки эталона",
                   source_span(rel,text.count('\n',0,match.start())+1,text.count('\n',0,match.end())+1),"programming",lesson_at(text,match.start(),module),
                   input_data=match[1],expected="Пример выполняется в доступной среде; для PySCF требуется поддерживаемая среда",
                   run='07-module-examples',status=observed['status'],result=json.dumps(observed,ensure_ascii=False),scope='source_snippet_execution',
                   reason=observed.get('reason'))
            import subprocess
            ROWS[-1]['test_command']=subprocess.list2cmdline(observed['argv'])


def labs():
    material=runpy.run_path(str(ROOT/'tools/lab_materials.py'))['LABS']
    for n,lab in material.items():
        path=f"Labs/guides/lab{n:02d}.md"
        run=f"lab-{n:02d}"
        record(n,f"LAB{n:02d}-REFERENCE",f"Исполнить готовый notebook: {lab['title']}",f"Labs/notebooks/lab{n:02d}.ipynb:code-cells",
               'programming',input_data=lab['data'],expected=lab['benchmark'],run=run,
               result=f"audit/issue-1/evidence/{run}/executed.ipynb; Labs/results/lab{n:02d}/benchmark.json copied into evidence/13-artifacts/labs-results",
               scope='reference_notebook_execution_only')
        for tag,key in [('STEP','steps'),('TRANSFER','tasks')]:
            for i,prompt in enumerate(lab[key],1):
                record(n,f"LAB{n:02d}-{tag}{i}",prompt,locate(path,prompt),
                       'research' if tag=='TRANSFER' else 'conceptual',input_data=lab['data'],
                       expected=lab['answers'][i-1] if tag=='TRANSFER' else lab['benchmark'],
                       partial=f"LAB{n:02d}-REFERENCE",scope='learner_transfer' if tag=='TRANSFER' else 'guided_action_with_interpretation')
        # Each embedded assertion is a bounded check, not a whole learning outcome.
        code=lab['code'];tree=ast.parse(code)
        for i,node in enumerate((node for node in ast.walk(tree) if isinstance(node,ast.Assert)),1):
            statement=ast.get_source_segment(code,node)
            record(n,f"LAB{n:02d}-ASSERT{i}",statement,f"Labs/notebooks/lab{n:02d}.ipynb:execution-cell:L{node.lineno}",
                   'programming',input_data=lab['data'],expected="Assertion evaluates True in the actual reference execution",
                   run=run,scope='executed_reference_assertion',result="Notebook executed after historical outputs were stripped; see executed cell outputs")
        for i,prompt in enumerate(['Сформулировать наблюдаемый результат','Сформулировать недопустимое обобщение','Предложить следующий контроль/эксперимент'],1):
            record(n,f"LAB{n:02d}-CONCLUSION{i}",prompt,f"Labs/notebooks/lab{n:02d}.ipynb:final-markdown-cell",'research',scope='learner_conclusion',partial=f"LAB{n:02d}-REFERENCE")


def cases_and_tasks():
    source='Stepik_course/04_CASES.md';text=(ROOT/source).read_text(encoding='utf-8')
    headings=list(re.finditer(r'^## ([A-H])\. (.+)$',text,re.M))
    modules={'A':3,'B':7,'C':8,'D':10,'E':11,'F':12,'G':13,'H':1}
    for index,heading in enumerate(headings):
        letter=heading[1];module=modules[letter]
        section=text[heading.end():headings[index+1].start() if index+1<len(headings) else text.index('## Общая схема помощи')]
        ref=source_span(source,text.count('\n',0,heading.start())+1,text.count('\n',0,heading.end()+len(section))+1)
        record(module,f"CASE-{letter}",heading[2],ref,'research',input_data=section.split('\n\n')[1] if '\n\n' in section else section,
               expected=section,partial=f"LAB{module:02d}-REFERENCE; 04-audit-numerics where applicable",scope='case_interpretation_and_rubric')
        # Preserve the rubric's distinct obligations, rather than counting a
        # whole case as solved because one number was recomputed.
        criteria={
          'A':['Сохранить raw и ID','Сохранить ошибочные записи','Назвать политику parent','Сохранить ковалентный Cl','Не объединить стереопару','Обосновать отличие соли и кислоты как физических образцов'],
          'B':['Проверить единицы','Проверить endpoint','Сохранить цензурирование','Проверить target/assay контекст','Сохранить полный журнал'],
          'C':['Разделить совпадение паттерна и механизм','Выбрать уместный контрскрининг','Обсудить цену ложного отказа'],
          'D':['Сравнить геометрию двух вымышленных поз','Разделить score и экспериментальную аффинность','Определить RMSD и соответствие атомов','Предложить диагностические действия для протокола'],
          'E':['Сгруппировать identity до split','Сравнить с baseline','Обучать преобразования только на train','Сохранить отдельный test','Объяснить пределы применимости'],
          'F':['Проверить знак ΔE','Перевести Hartree в кДж/моль','Проверить согласованность состава и метода','Различить E и G','Не объявлять разность минимумов барьером'],
          'G':['Перемножить последовательные выходы','Сравнить нормированные затраты','Проверить допущения об одинаковой загрузке','Назвать недостающие параметры маршрута'],
          'H':['Вычислить эффекты A/B/AB','Отличить эффект от коэффициента','Указать отсутствие оценки ошибки без повторов','Предложить следующий план повторов/дополнительных точек']}
        for i,criterion in enumerate(criteria[letter],1):
            record(module,f'CASE-{letter}-CRITERION{i}',criterion,ref,'research',related=f'CASE-{letter}',scope='case_rubric_obligation',partial=f'LAB{module:02d}-REFERENCE; NUM-* for arithmetic only')
        # The case explicitly asks two separate questions in E.
        if letter=='E':
            record(11,'CASE-E-Q2','Объяснить разницу вымышленных R²=0,94 и 0,42 без приписывания одной причине',locate(source,'**Вопрос 2:**'),'conceptual',scope='learner_interpretation')
    numeric=json.loads((EVIDENCE/'04-audit-numerics/results.json').read_text(encoding='utf-8'))['checks']
    for item in numeric:
        identifier=item['id']
        if identifier.startswith('P'):
            number=int(identifier[1]);module={1:7,2:5,3:8,4:8}[number]
            ref=locate('Stepik_course/03_STEPIK.md',f'**P{number},')
        else:
            letter=identifier[0];module=modules[letter];ref=locate(source,f'## {letter}.')
        record(module,'NUM-'+identifier,'Вычислить численный эталон '+identifier,ref,'calculation',
               expected=json.dumps(item['expected']),input_data=json.dumps(item['input']),run='04-audit-numerics',
               status=item['status'],result=json.dumps(item['actual']),scope='audit_numeric_recomputation_only',related=f"CASE-{identifier[0]}" if not identifier.startswith('P') else identifier.split('-')[0])
    for n,module in {1:7,2:5,3:8,4:8}.items():
        ref=locate('Stepik_course/03_STEPIK.md',f'**P{n},')
        record(module,f'P{n}-LEARNER',f'Написать самостоятельное решение задачи P{n}, соблюдая stdin/stdout контракт',ref,'programming',
               partial=f'NUM-P{n}-*',scope='learner_program_submission')
        record(module,f'P{n}-GRADER',f'Проверить P{n} в целевом Stepik grader',ref,'programming',status='BLOCKED',
               reason='Нет ID тестового курса/шага, grader-конфигурации, submission и grade trace',scope='lms_acceptance')
    for item in json.loads((EVIDENCE/'17-case-checks/results.json').read_text(encoding='utf-8'))['checks']:
        module=7 if item['id'].startswith('B-') else 8
        record(module,'CHECK-CASE-'+item['id'],'Проверить конкретный reference результат кейса '+item['id'],locate(source,'## '+item['id'][0]+'.'),
               'programming' if module==7 else 'calculation',input_data=json.dumps(item['input'],ensure_ascii=False),expected=json.dumps(item['expected'],ensure_ascii=False),
               run='17-case-checks',status=item['status'],result=json.dumps(item['actual'],ensure_ascii=False),scope='case_reference_output_only')


def software_and_tests():
    source='Stepik_course/practice/test_practice.py'
    mapping={'equivalent_serializations':3,'salt_retains_raw_and_matches_acid_parent':3,'covalent_chlorine_survives':3,'stereochemistry_not_collapsed':3,'tautomer_canonicalization_is_explicit':3,'invalid_and_empty':3,'expected_descriptors':4,'all_four_ro5_conditions':4,'pains_is_review':8,'no_alert_is_not_activity':8,'morgan_properties':5,'conformer':6,'activity_units_and_failures':7,'curated_rows':7,'tanimoto_cases':5,'enrichment':8,'z_prime':8}
    for path,run in [(source,'02-core-tests'),('Labs/test_labs.py','11-labs-tests')]:
        text=(ROOT/path).read_text(encoding='utf-8');tree=ast.parse(text)
        labmap={'salt_and_covalent_halogen':3,'stereo_and_tautomer_policy':3,'units_and_invalid_numbers':7,'structural_alert_is_not_verdict':8,'complete_table_contract':14,'schema_duplicate_and_limit':14,'rhf_physical_reference':12,'pose_reference':10}
        for node in ast.walk(tree):
            if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
                name=node.name[5:];module=(mapping if path==source else labmap)[name]
                record(module,('TEST-CORE-' if path==source else 'TEST-LABS-')+name,node.name,
                       source_span(path,node.lineno,node.end_lineno),'programming',
                       input_data=ast.get_source_segment(text,node),expected='Все существующие assertions этого метода проходят',
                       run=run,scope='existing_unit_test_method',result='Executed suite transcript; no test failures and expected test count')
    for module,ident,path,run in [(2,'EXEC-CHEMISTRY','Stepik_course/practice/chemistry.py','03-chemistry'),
                                  (2,'EXEC-QUICKSTART','Stepik_course/practice/quickstart.ipynb','10-quickstart'),
                                  (11,'EXEC-ESOL','Stepik_course/practice/train_esol.py','05-esol')]:
        record(module,ident,'Повторить существующий вычислительный пример',source_span(path), 'programming',
               run=run,scope='reference_script_execution',expected='Новый запуск без правки входов/эталонов; результаты сохранены',result=f'Outputs retained in audit/issue-1/evidence/{run}')
    for path,related in [('Stepik_course/practice/chemistry.py','EXEC-CHEMISTRY'),('Stepik_course/practice/stepik_tasks.py','NUM-P1-*; NUM-P2-*; NUM-P3-*; NUM-P4-*'),('Stepik_course/practice/train_esol.py','EXEC-ESOL')]:
        text=(ROOT/path).read_text(encoding='utf-8');tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.FunctionDef) and node.col_offset==0:
                module=11 if 'esol' in path else 7 if node.name in {'p_activity','curate_activity','z_prime','enrichment'} else 6 if node.name=='optimize_conformer' else 5 if node.name in {'similarity','tanimoto'} else 3
                if node.name in {'screen','pains_alerts'}:module=8
                record(module,'API-'+Path(path).stem+'-'+node.name,'Реализованная reference-функция '+node.name,source_span(path,node.lineno,node.end_lineno),'programming',
                       partial=related,scope='reference_api_contract_inventory',reason='Наличие реализации не является полным тестом API; фактически проверенные случаи зарегистрированы отдельно')
    path='Stepik_course/practice/quickstart.ipynb'
    book=json.loads((ROOT/path).read_text(encoding='utf-8'))
    bindings={'intro':2,'environment':2,'predict-parent':3,'parent':3,'screen-question':8,'screen':8,
              'units-question':7,'units':7,'geometry-question':6,'geometry':6,'transfer':3}
    for cell in book['cells']:
        key=cell['id'];module=bindings[key]
        text=''.join(cell['source']) if isinstance(cell['source'],list) else cell['source']
        if cell['cell_type']=='code':
            record(module,'QUICK-'+key,'Исполнить ячейку '+key,f'{path}:cell={key}','programming',
                   input_data=text,expected='Успешное исполнение нового ядра и имеющихся assert',run='10-quickstart',scope='reference_notebook_cell_execution',result='Executed copy: audit/issue-1/evidence/10-quickstart/executed.ipynb')
        else:
            record(module,'QUICK-'+key,text,f'{path}:cell={key}','research' if key=='transfer' else 'conceptual',
                   partial='EXEC-QUICKSTART',scope='learner_prediction_or_transfer')
    for module,ident,prompt in [(7,'MEDIA-UNITS','Изменить концентрацию/единицу/отношение и объяснить pIC50'),
                                 (5,'MEDIA-TANIMOTO','Переключить биты A/B и объяснить изменившееся сходство'),
                                 (8,'MEDIA-PAINS','Выбрать решение при предупреждении PAINS и обосновать')]:
        record(module,ident,prompt,source_span('Stepik_course/media/interactive.html'),'conceptual',scope='browser_interaction_and_learner_explanation',
               reason='В текущем прогоне браузерная интеракция и самостоятельное объяснение ученика не проверялись; исторические заявления не перенесены в PASS')
    for item in json.loads((EVIDENCE/'18-gui/results.json').read_text(encoding='utf-8'))['checks']:
        record(14,'APP14-'+item['id'],item['expected'],locate('Stepik_course/modules/14_delivery.md','## 14.2.'),'programming',
               expected=item['expected'],input_data=item.get('input','Labs/datasets/molecules.csv; AppTest + mocked uploader'),
               run='18-gui',status=item['status'],result=json.dumps(item['actual'],ensure_ascii=False),scope='app_reference_acceptance_bounded',
               reason='Выполненная проверка не находит заявленного в ТЗ переключателя таутомеризации; химическая политика не менялась' if item['status']=='FAIL' else None)


def gaps_and_map():
    entries=[(7,'GAP-API-CACHE','Реальный API/cache или подтверждённый metadata fixture','Stepik_course/modules/07_databases.md','Нет существующего клиента пагинации/cache и реального activity metadata fixture в Stepik; искусственный CSV/ESOL это не заменяет'),
             (10,'GAP-VINA-PREPARATION','Подготовка сырого комплекса и independently checked experimental RMSD','Stepik_course/modules/10_docking.md','Vina можно исполнить на готовых tutorial-файлах; подготовка из сырого PDB, независимое сопоставление экспериментальной позы и symmetry correction этим не проверены'),
             (12,'GAP-PYSCF','Выполнить PySCF DFT или проверить полный reference packet','Labs/extensions/dft_pyscf.ipynb','PySCF не установлен в изолированной Windows-среде; готового полного DFT output/reference packet не найдено; RHF отдельно'),
             (14,'GAP-PROJECT-EXAMPLE','Полное исследовательское досье с provenance, неопределённостью, ограничениями и следующим экспериментом','Stepik_course/modules/14_delivery.md','Reference CSV CLI не является сквозным образцовым научным досье с QM/docking/QSPR/map и применённой рубрикой'),
             (14,'GAP-PROJECT-DEFENSE','Независимый перенос и защита итоговой работы','Stepik_course/modules/14_delivery.md','Нет студенческой работы и проведённого оценивания; автоматизация reference не доказывает перенос')]
    for m,i,p,s,r in entries:
        record(m,i,p,source_span(s),'research',status='NOT_RUN' if i.endswith('DEFENSE') else 'BLOCKED',reason=r,scope='release_evidence_gap',
               partial='LAB10-REFERENCE' if m==10 else 'LAB12-REFERENCE' if m==12 else 'LAB14-REFERENCE' if m==14 else 'LAB07-REFERENCE')
    source='Stepik_course/09_EVOLVING_CONCEPT_MAP.md'
    # The document explicitly does NOT bind this progression to the 14 numbers.
    # Inventory the six cross-course actions once; do not invent 14 assignments.
    for i,prompt in enumerate(['Ответить на прогнозирующий вопрос о выборе модели','Разобрать опорный фрагмент и неверную связь','Создать/исправить 1–3 обоснованных направленных связи','Проверить связь на контрпримере','Привязать связь к источнику/результату/формуле/ограничению','Вернуться к прежнему утверждению и уточнить его'],1):
        record(14,f'MAP-CYCLE{i}',prompt,locate(source,'## 5. Учебное действие'),'research',lesson='cross-course.map',scope='specified_cross_course_learner_action',requirement='required-cross-course; per-module binding not specified')
    for tag,prompt in [('EDITOR','Построить и отредактировать карту в автономном веб-редакторе'),('JSON','Экспортировать и повторно прочитать переносимый JSON'),('TEXT','Выполнить эквивалентное задание текстом/клавиатурой')]:
        record(14,'MAP-GATE-'+tag,prompt,locate(source,'## 7. Публикация на Stepik'),'programming',status='BLOCKED',scope='concept_map_acceptance',reason='Есть спецификация, но нет реализованного редактора/контрольного экспорта и подтверждённого доступного пути')


def linux_supplement():
    directory=EVIDENCE/'wsl-linux'
    if not directory.exists():return
    import shlex
    def observed_row(module,identifier,prompt,source,name,scope):
        meta=json.loads((directory/name/'run.json').read_text(encoding='utf-8'))
        row=record(module,identifier,prompt,source,'programming',status=meta['status'],scope=scope)
        driver=meta.get('driver_argv')
        argv=meta.get('argv') or [json.loads((directory/'environment.json').read_text())['executable'],*driver]
        row.update(test_command=shlex.join(argv),environment='audit/issue-1/evidence/wsl-linux/environment.json',
                   evidence=f'audit/issue-1/evidence/wsl-linux/{name}/run.json; stdout.txt; stderr.txt',
                   input=f"Unmodified source at base commit; SHA256 {meta.get('input_sha256','see source-sha256.json')}",
                   expected_output='Fresh notebook/code execution and original assertions succeed in uv-managed WSL kernel',
                   actual_output=json.dumps(meta,ensure_ascii=False),
                   blockers='Only bounded reference execution; learner explanation/transfer and full scientific review remain unproven')
        return row
    for n in range(1,15):
        observed_row(n,f'WSL-LAB{n:02d}-REFERENCE',f'Исполнить ЛР {n} в WSL/uv',f'Labs/notebooks/lab{n:02d}.ipynb:code-cells',f'lab{n:02d}','reference_notebook_execution_linux_uv')
    observed_row(2,'WSL-QUICKSTART','Исполнить quickstart в WSL/uv','Stepik_course/practice/quickstart.ipynb:code-cells','quickstart','reference_notebook_execution_linux_uv')
    observed_row(12,'WSL-DFT-REFERENCE','Исполнить PySCF RHF/PBE notebook в WSL/uv','Labs/extensions/dft_pyscf.ipynb:code-cells','dft_pyscf','pyscf_notebook_execution_linux_uv')
    observed_row(12,'WSL-M12-CODE1','Исполнить неизменённую PySCF-вставку модуля 12 в Linux',locate('Stepik_course/modules/12_quantum.md','from pyscf import gto, dft'),'module12-pyscf','source_snippet_execution_linux_uv')
    gap=next(r for r in ROWS if r['exercise_id']=='GAP-PYSCF')
    executed=next(r for r in ROWS if r['exercise_id']=='WSL-DFT-REFERENCE')
    for key in ['test_command','environment','status','evidence','actual_output','blockers']:
        gap[key]=executed[key]
    gap['status_scope']='pyscf_reference_evidence_gap_closed_linux_only'
    gap['partial_evidence']='WSL-DFT-REFERENCE; WSL-M12-CODE1; original Windows BLOCKED retained'
    windows=next(r for r in ROWS if r['exercise_id']=='M12-CODE1')
    windows['blockers']='Native Windows attempt lacks PySCF; successful later Linux execution is recorded separately in WSL-M12-CODE1'
    windows['partial_evidence']='WSL-M12-CODE1'
    windows['status_scope']='source_snippet_execution_native_windows'


def main():
    module_actions();labs();cases_and_tasks();software_and_tests();gaps_and_map();linux_supplement()
    ids=[r['exercise_id'] for r in ROWS]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate exercise IDs')
    for row in ROWS:
        if row['status']=='PASS' and not row['evidence']:raise ValueError('Unproven PASS '+row['exercise_id'])
    with (ROOT/'practice-audit.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(ROWS[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(ROWS)
    (BASE/'source-action-coverage.json').write_text(json.dumps(COVERAGE,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'rows':len(ROWS),'statuses':dict(Counter(r['status'] for r in ROWS)),
             'types':dict(Counter(r['exercise_type'] for r in ROWS)),
             'modules':{str(n):dict(Counter(r['status'] for r in ROWS if r['module_id']==str(n))) for n in range(1,15)}}
    (BASE/'registry-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
