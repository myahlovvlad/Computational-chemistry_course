"""Build exactly two active notebooks per module without rewriting theory."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
import nbformat as n
from lab_materials import LABS
from paired_lab_materials import CASES,EXPLAIN,SPLITS

ROOT=Path(__file__).resolve().parents[1]
KERNEL={'name':'chemistry-course-uv','display_name':'Chemistry course (uv / WSL / Python 3.12)','language':'python'}

BOOT='''from pathlib import Path
import sys, json, math, csv, time, hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'Labs/chemistry.py').is_file())
for folder in [ROOT/'Stepik_course/practice', ROOT/'Labs']:
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
DATA = ROOT/'Labs/datasets'
OUT = ROOT/'Labs/results/MODULE_DIR'
OUT.mkdir(parents=True, exist_ok=True)
started = time.perf_counter()
print('Python:', sys.executable)
'''

CUSTOM={
8:[
'''from chemistry import screen
from metrics import z_prime, enrichment
raw=pd.read_csv(DATA/'molecules.csv',keep_default_na=False)
records=[{'id':r.id,**screen(r.smiles)} for r in raw.itertuples()]
table=pd.DataFrame(records)
display(table[['id','status','reason']])
assert len(table)==12
''',
'''good=z_prime(100,10,5,5)
bad=z_prime(100,10,20,20)
ef=enrichment(1000,20,50,5)
print({'Z_good':good,'Z_bad':bad,'EF_50':ef})
assert math.isclose(good,2/3) and math.isclose(bad,-1/3)
assert ef==5
''',
'''assert screen('Oc1ccccc1O')['status']=='review'
assert screen('')['status']=='invalid'
table.to_csv(OUT/'decisions.csv',index=False)
artifact={'Z_prime':good,'EF_at_50':ef,'statuses':table.status.value_counts().to_dict()}
'''],
10:[
'''from docking import first_pose, mapped_rmsd
import shutil, subprocess
docking_data=DATA/'docking'
provenance=json.loads((docking_data/'provenance.json').read_text())
print(json.dumps(provenance,indent=2))
print((docking_data/'1iep_receptor.box.txt').read_text())
reference=docking_data/'1iep_ligand.pdbqt'
official=docking_data/'1iep_ligand_vina_out.pdbqt'
''',
'''binary=shutil.which('vina')
if binary is None:
    raise RuntimeError('BLOCKED: установите Linux Vina в PATH; готовый output не заменяет запуск')
pose=OUT/'redocked.pdbqt'
command=[binary,'--receptor',str(docking_data/'1iep_receptor.pdbqt'),
         '--ligand',str(reference),'--config',str(docking_data/'1iep_receptor.box.txt'),
         '--seed','42','--cpu','1','--exhaustiveness','8','--num_modes','9','--out',str(pose)]
print('argv:',command)
process=subprocess.run(command,capture_output=True,text=True,timeout=600)
(OUT/'vina-stdout.txt').write_text(process.stdout)
(OUT/'vina-stderr.txt').write_text(process.stderr)
process.check_returncode()
assert pose.is_file()
''',
'''a,_=first_pose(reference)
b,score=first_pose(pose)
assert a.keys()==b.keys(), 'Нужно явное сопоставление атомов'
# WHY: do not align the ligand separately; preserve receptor coordinates.
rmsd=float(np.sqrt(np.mean([np.sum((a[k]-b[k])**2) for k in sorted(a)])))
assert math.isfinite(rmsd) and math.isfinite(score)
artifact={'mode':'executed-vina','score':score,'rmsd_angstrom':rmsd,
          'rmsd_definition':'heavy atom serials, receptor frame, no symmetry correction',
          'official_reference_rmsd_angstrom':mapped_rmsd(reference,official),
          'command':command,'binary_sha256':hashlib.sha256(Path(binary).read_bytes()).hexdigest()}
(OUT/'docking.json').write_text(json.dumps(artifact,indent=2))
print(artifact)
'''],
11:[
'''from train_esol import load, run, TARGET
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
records=load(DATA/'esol.csv')
x=np.array([r['x'] for r in records]); y=np.array([r['y'] for r in records])
groups=[r['identity'] for r in records]
train,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=42).split(x,y,groups))
assert not set(groups[i] for i in train)&set(groups[i] for i in test)
print('Target:',TARGET,'rows:',len(records),'train/test:',len(train),len(test))
''',
'''models={'baseline':make_pipeline(SimpleImputer(strategy='median'),DummyRegressor()),
        'RF':make_pipeline(SimpleImputer(strategy='median'),RandomForestRegressor(
            n_estimators=200,min_samples_leaf=2,random_state=42,n_jobs=1))}
for name,model in models.items():
    model.fit(x[train],y[train])  # WHY: no fit/imputation on test.
    predicted=model.predict(x[test])
    print(name,'MAE logS:',mean_absolute_error(y[test],predicted))
# The full reference protocol also saves scaffold split, baseline and membership.
result=run(DATA/'esol.csv',OUT)
assert result['rows']==1128 and result['unique_identity']==1117
display(pd.json_normalize(result['splits'],sep='.'))
''',
'''predictions=pd.read_csv(OUT/'scaffold_predictions.csv')
predictions['absolute_error']=abs(predictions.measured_logS-predictions.predicted)
display(predictions.nlargest(5,'absolute_error'))
plt.scatter(predictions.measured_logS,predictions.predicted,alpha=.6)
plt.plot([-10,2],[-10,2],'k--');plt.xlabel('Measured logS');plt.ylabel('Predicted logS')
plt.savefig(OUT/'parity.png',dpi=150);plt.show()
artifact=result
'''],
12:[
'''from h2_scf import rhf_h2
result=rhf_h2(.74)
print(result)
assert result['converged']
assert abs(result['energy_hartree']+1.116759307)<5e-5
display(pd.DataFrame(result['trace']))
''',
'''assert math.isclose(-.010*2625.5,-26.255,abs_tol=1e-9)
scan=pd.DataFrame([{'R_A':float(r),'E_hartree':rhf_h2(float(r))['energy_hartree']}
                   for r in np.linspace(.5,2.5,11)])
scan.to_csv(OUT/'h2_scan.csv',index=False)
plt.plot(scan.R_A,scan.E_hartree,'o-');plt.xlabel('H–H, angstrom');plt.ylabel('RHF/STO-3G E, Hartree')
plt.savefig(OUT/'h2_energy.png',dpi=150);plt.show()
''',
'''from pyscf import gto, scf, dft
import pyscf
mol=gto.M(atom='H 0 0 0; H 0 0 .74',unit='Angstrom',basis='sto-3g',charge=0,spin=0,verbose=4)
hf=scf.RHF(mol);hf.conv_tol=1e-10;eh=hf.kernel()
ks=dft.RKS(mol);ks.xc='PBE';ks.grids.level=4;ks.conv_tol=1e-10;ed=ks.kernel()
assert hf.converged and ks.converged
assert abs(eh-result['energy_hartree'])<5e-5
artifact={'geometry_angstrom':'H 0 0 0; H 0 0 .74','charge':0,'spin':0,'basis':'sto-3g',
          'pyscf':pyscf.__version__,'functional':'PBE','grid_level':4,
          'RHF_energy_hartree':float(eh),'PBE_energy_hartree':float(ed),
          'HF_converged':bool(hf.converged),'DFT_converged':bool(ks.converged),
          'scope':'single-point electronic energies, not free energies or barriers'}
(OUT/'pyscf_dft.json').write_text(json.dumps(artifact,indent=2))
print(artifact)
'''],
14:[
'''from pipeline import process_csv
data=(DATA/'molecules.csv').read_bytes()
rows,passport=process_csv(data)
display(pd.DataFrame(rows)[['id','raw_smiles','parent_smiles','status','reason']])
assert len(rows)==12 and sum(r['status']=='invalid' for r in rows)==2
''',
'''negative_inputs=[b'id,wrong\\nX,CCO\\n',b'id,smiles\\nX,CCO\\nX,CCN\\n']
errors=[]
for invalid_csv in negative_inputs:
    try:
        process_csv(invalid_csv)
    except ValueError as error:
        errors.append(str(error))
    else:
        raise AssertionError('Нарушение CSV контракта принято')
print(errors)
assert len(errors)==2
assert any('unique' in error for error in errors)
''',
'''assert passport['input_sha256']==hashlib.sha256(data).hexdigest()
assert len({r['id'] for r in rows})==len(rows)
print(passport)
artifact={'rows':len(rows),'passport':passport,'negative_input_errors':errors,
          'scope':'reference core only; application development and tests take place in IDE'}
'''],
}

def code_sections(number):
    if number in CUSTOM:return CUSTOM[number]
    code=LABS[number]['code']
    cuts=[0]+[code.index(marker) for marker in SPLITS[number]]+[len(code)]
    chunks=[code[a:b] for a,b in zip(cuts,cuts[1:])]
    for chunk in chunks:ast.parse(chunk)
    return chunks

def write_book(path,cells,number,role):
    book=n.v4.new_notebook(cells=cells)
    book.metadata={'kernelspec':KERNEL,'language_info':{'name':'python'},
                   'course':{'module':number,'role':role,'version':'paired-v1'}}
    # Stable IDs keep rebuilding reviewable. Old outputs are never copied into new code.
    for index,cell in enumerate(book.cells):cell.id=f'm{number:02d}-{role}-{index:02d}'
    if role=='worked' and path.exists():
        previous=n.read(path,as_version=4)
        prior={cell.id:cell for cell in previous.cells}
        for cell in book.cells:
            old=prior.get(cell.id)
            if cell.cell_type=='code' and old and old.cell_type=='code' and old.source==cell.source:
                cell.outputs=old.outputs
                cell.execution_count=old.execution_count
    n.write(book,path)

def build():
    manifest=json.loads((ROOT/'course-manifest.json').read_text(encoding='utf-8'))
    public=[];rubrics=[]
    for module in manifest:
        number=module['module'];lab=dict(LABS[number]);tag=f'lab{number:02d}'
        if number==12:
            lab.update(title='Электронная энергия H2: RHF и DFT/PBE',
                       purpose='Проследить RHF-расчёт и сравнить HF/PBE при одинаковых геометрии и базисе.',
                       workflow='Геометрия/заряд/spin → RHF → кривая → PySCF HF/PBE → сходимость и ограничения.',
                       benchmark='RHF/STO-3G при 0,74 Å: −1,116759307±5e−5 Hartree. Пакетные HF/PBE должны сходиться; HF согласуется с собственной реализацией. E не является G или барьером.')
        if number==10:lab['benchmark']='Полный Vina run обязателен: argv, новые позы и logs, конечные score/RMSD. Без бинарника BLOCKED; значения seed42 не являются универсальным эталоном.'
        module['title']=lab['title']
        module.update(notebook=f'Labs/notebooks/{tag}.ipynb',worked_notebook=f'Labs/notebooks/{tag}.ipynb',
                      practice_notebook=f'Labs/notebooks/{tag}_practice.ipynb',practice_cases=[f'M{number:02d}-C{i}' for i in range(1,4)])
        passport=f"**Модуль {number}. Автор/аффилиация:** автор курса уточняет перед публикацией. **Среда:** WSL/uv/Python 3.12. **Данные:** {lab['data']}"
        cells=[n.v4.new_markdown_cell(f"# Модуль {number}. Разбор кейсов: {lab['title']}\n\n{passport}\n\n{lab['purpose']}\n\n**Workflow:** {lab['workflow']}\n\n**Результаты обучения:** объяснить вход/политику; воспроизвести расчёт и отрицательный контроль; ограничить научный вывод.\n\nОцените результат до запуска. После разбора переходите во [второй notebook]({tag}_practice.ipynb). [Установка среды](../SETUP.md).\n\n[Связанная глава](../../{quote(module['theory'])})."),
               n.v4.new_markdown_cell('## 0. Подготовка и паспорт запуска\n\nЗапускайте ячейки сверху вниз после Restart Kernel. Путь Python должен указывать на проектную `.venv`; устанавливать пакеты в ячейке не нужно. Эта ячейка только определяет пути и создаёт отдельный каталог результатов разбора.'),
               n.v4.new_code_cell(BOOT.replace('MODULE_DIR',f'{tag}/worked'))]
        chunks=code_sections(number)
        for i,((title,text),code) in enumerate(zip(EXPLAIN[number],chunks),1):
            cells += [n.v4.new_markdown_cell(f'## {i}. {title}\n\n{text}\n\n**Перед запуском:** {lab["steps"][i-1]}'),n.v4.new_code_cell(code)]
            cells.append(n.v4.new_markdown_cell(f'**После запуска:** сверьте промежуточные переменные и объясните, какое условие проверено. {EXPLAIN[number][i-1][0]} — часть протокола; успешная ячейка не оценивает самостоятельный ответ.'))
        cells += [n.v4.new_markdown_cell('## 4. Артефакт и граница доказательства\n\n'+lab['benchmark']+'\n\nСледующая ячейка сохраняет именно новый запуск и хеши входов. Отсутствующее вычисление нельзя заменять старым output. Время относится к этому компьютеру и не является обещанием производительности.'),
                  n.v4.new_code_cell("record={'module':"+str(number)+",'scope':'worked reference execution','python':sys.executable,'elapsed_seconds':time.perf_counter()-started,'result':artifact}\n(OUT/'benchmark.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))\nprint(OUT/'benchmark.json')")]
        if number==14:
            cells.append(n.v4.new_markdown_cell('## 5. Разработка приложения — в IDE\n\nОткройте корень проекта в VS Code WSL. Создайте `student_work/module14/cli.py` и `app.py`; отладчик, терминал и тесты запускайте там. Полная [инструкция IDE](../ide/README.md). Здесь сервер не запускается. Во втором notebook запишите команды, результаты и ссылки на исходники.'))
        sources=[f'Исходный вычислительный пример: [Labs/chemistry.py](../chemistry.py), [описание данных](../datasets/README.md).',
                 '[RDKit: Getting Started](https://www.rdkit.org/docs/GettingStartedInPython.html).',
                 '[scikit-learn: common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).' if number==11 else '[PySCF: Quickstart](https://pyscf.org/quickstart.html).' if number==12 else '[Vina: basic docking](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html).' if number==10 else '[Карта чтения](../../Literature/READING_MAP.md).']
        cells.append(n.v4.new_markdown_cell('## Источники и следующий шаг\n\n'+'\n'.join(f'{i}. {s}' for i,s in enumerate(sources,1))+f'\n\nПерейдите к [{tag}_practice.ipynb]({tag}_practice.ipynb). Через неделю повторите первый кейс без просмотра ключа.'))
        write_book(ROOT/module['notebook'],cells,number,'worked')

        tasks=[n.v4.new_markdown_cell(f"# Модуль {number}. Самостоятельный лабораторный практикум\n\n{passport}\n\n**Назначение:** решить три кейса самостоятельно, сохранив код, входы, результат и ограничение. Разбор находится в [{tag}.ipynb]({tag}.ipynb). Ответы здесь не подставляются.\n\nДля каждого кейса: прогноз → собственное решение → контроль → артефакт → интерпретация. Перезапуск незаполненного notebook лишь проверяет каркас, а не выполнение лабораторной. Для задач IDE код пишется в файлах проекта. [Окружение](../SETUP.md)."),
               n.v4.new_code_cell(BOOT.replace('MODULE_DIR',f'{tag}/student')+f"\nfrom practice_checks import check_case\nall_inputs=json.loads((DATA/'practice_cases.json').read_text())\ncase_inputs=all_inputs['modules']['{number}']\nchecks=[]\n")]
        key=[f"# Ключ преподавателя: модуль {number}\n\nРешения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.\n"]
        for i,c in enumerate(CASES[number],1):
            cid=f'M{number:02d}-C{i}';kind=c.get('mode','auto')
            rubrics.append({'id':cid,'module':number,'title':c['title'],'mode':kind,'expected':c['expected'],'tolerance':.01 if number==4 and i==1 else 1e-6})
            public.append({'id':cid,'module':number,'title':c['title'],'mode':kind,'input':c['input'],'dataset_kind':'fictional teaching scenario; referenced ESOL/docking retain original passports','requirements':c['tasks']})
            body=f"## Кейс {i}. {c['title']}\n\n**ID:** {cid}. **Место работы:** {'IDE; notebook — журнал результатов' if kind=='ide' else 'Jupyter Notebook'}.\n\n{c['story']}\n\n**Вход:** словарь `input_{i}` ниже; файловые входы разрешаются относительно `DATA`.\n\n**Задачи:**\n"+'\n'.join(f'{j}. {t}' for j,t in enumerate(c['tasks'],1))
            body+='\n\n**Сдача:** собственный код/файлы, исходные ID и параметры, фактический результат, контрольный случай и обоснованный вывод. Численный checker проверяет только возвращаемый контракт; сохранённые файлы и научный вывод оцениваются отдельно.'
            if kind!='auto':body+='\n\n**Проверка:** требуется рецензия по критериям задачи. Автозапуск не присваивает PASS.'
            tasks += [n.v4.new_markdown_cell(body),n.v4.new_code_cell(f"input_{i}=case_inputs[{i-1}]\ndisplay(input_{i})"),
                      n.v4.new_markdown_cell('### Собственное решение\n\nСначала запишите прогноз и причину ожидаемого результата. В ячейке ниже напишите своё решение; готовый алгоритм не вставлен. Для исследовательского/IDE-кейса можно вернуть словарь ссылок на файлы и наблюдений, но это не заменяет сам артефакт.'),
                      n.v4.new_code_cell(f"# TODO: собственный код или журнал выполненной работы.\nanswer_{i}=None"),
                      n.v4.new_markdown_cell('### Проверка контракта и интерпретация\n\nЕсли решение отсутствует, статус NOT_RUN. PASS означает только совпадение численного контракта, а не освоение темы. Не меняйте эталон ради прохождения. Ниже дополните три предложения: наблюдение; ограничение; следующий контроль.'),
                      n.v4.new_code_cell(f"check_{i}=check_case('{cid}',answer_{i})\nchecks.append(check_{i})\nprint(check_{i})"),
                      n.v4.new_markdown_cell('**Моё наблюдение:** …\n\n**Ограничение вывода:** …\n\n**Следующий контроль:** …')]
            key += [f"\n## {cid}. {c['title']}\n\n{c['interpretation']}\n"]
            if c['solution']:
                key += ['\n```python\ncase_input = '+repr(c['input'])+'\n'+c['solution']+'\n```\n', '\nОжидаемый численный контракт: `'+json.dumps(c['expected'],ensure_ascii=False)+'`.\n']
            else:key += ['\nРубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.\n']
        tasks += [n.v4.new_markdown_cell('## Сохранение и сдача\n\nСохраните свой notebook отдельной копией вместе с файлами из каталога student. JSON ниже — журнал вызовов checker, не удостоверение выполнения всех требований. За каждый кейс: 1 балл за постановку/входы, 2 за решение/контроль и 1 за интерпретацию; всего 12. Для review/IDE требуется преподаватель. Исследовательские баллы не выставляются по наличию ключевых слов.'),
                  n.v4.new_code_cell("(OUT/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))\nprint('Результаты проверок:',checks)"),
                  n.v4.new_markdown_cell(f'[Ключ после попытки](../solutions/{tag}.md). Через неделю повторите кейс 1 на изменённом входе и сравните ход рассуждений.')]
        write_book(ROOT/module['practice_notebook'],tasks,number,'practice')
        (ROOT/module['solutions']).write_text('\n'.join(key),encoding='utf-8')
        guide=f"# Модуль {number}: {lab['title']}\n\n## Сущность и назначение\n\n{lab['purpose']}\n\n## Данные и workflow\n\n{lab['data']}\n\n{lab['workflow']}\n\n[Паспорт данных](../datasets/README.md); [установка](../SETUP.md).\n\n## Два этапа работы\n\n1. [Разбор кейсов и кода](../notebooks/{tag}.ipynb): пояснение → короткая ячейка → интерпретация.\n2. [Самостоятельные кейсы](../notebooks/{tag}_practice.ipynb): три условия, входы, места для собственного решения, проверки и рубрика.\n\n{lab['benchmark']}\n\nИсторический benchmark относится к прежней редакции. Свежие результаты парного формата публикуются отдельно в paired-execution.json. Пустые задания имеют NOT_RUN, даже если notebook запускается без ошибок.\n\n[Ключ преподавателя](../solutions/{tag}.md). Приложения создаются и отлаживаются в [IDE](../ide/README.md).\n"
        (ROOT/module['lab']).write_text(guide,encoding='utf-8')
    grouped={str(i):[c['input'] for c in CASES[i]] for i in range(1,15)}
    dataset=ROOT/'Labs/datasets/practice_cases.json'
    dataset.write_text(json.dumps({'version':'paired-v1','provenance':'Authored fictional exercises, 2026-11-17. Referenced real datasets keep their own passports.','modules':grouped},ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'Labs/practice_contracts.json').write_text(json.dumps(rubrics,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'Labs/practice-case-registry.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'course-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    path=ROOT/'Labs/datasets/manifest.json';data=json.loads(path.read_text(encoding='utf-8'))
    data=[x for x in data if x['path']!='practice_cases.json']
    for entry in data:
        if entry['path']=='README.md':
            readme=ROOT/'Labs/datasets/README.md'
            entry.update(bytes=readme.stat().st_size,sha256=hashlib.sha256(readme.read_bytes()).hexdigest())
    data.append({'path':'practice_cases.json','bytes':dataset.stat().st_size,'sha256':hashlib.sha256(dataset.read_bytes()).hexdigest()})
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')
    header='# Практикум: два notebook на модуль\n\n[Установка и настройка среды](SETUP.md). [Разработка приложений через IDE](ide/README.md).\n\nПервый notebook сочетает пояснения с исполняемыми короткими шагами. Второй содержит три самостоятельных кейса без подставленных решений. Работа над приложением ведётся в IDE; notebook сохраняет постановку и доказательства.\n\n| Модуль | Разбор | Самостоятельный практикум | Руководство |\n|---|---|---|---|\n'
    for m in manifest:
        t=f"lab{m['module']:02d}";header+=f"| {m['module']}. {m['title']} | [{t}](notebooks/{t}.ipynb) | [{t}_practice](notebooks/{t}_practice.ipynb) | [Guideline](guides/{t}.md) |\n"
    header+='\n## Проверяемость\n\n[Свежие запуски](benchmarks/paired-execution.json) разделяют исполнение разбора, проверку незаполненного каркаса и авторскую проверку эталонных решений. NOT_RUN у самостоятельного задания означает, что ученик его ещё не решил. PASS численного контракта не оценивает интерпретацию, приложение или защиту. Исторический аудит Issue #1 относится к исходному commit и не сертифицирует эту новую редакцию.\n\nQuickstart в Stepik_course/practice и старое DFT-дополнение — вспомогательные материалы прежней версии; действующий маршрут состоит ровно из 28 notebooks в этой таблице. DFT включён в основной разбор модуля 12.\n'
    (ROOT/'Labs/README.md').write_text(header,encoding='utf-8')
    print('Built 14 pairs / 28 notebooks / 42 independent cases; theory untouched')

if __name__=='__main__':build()
