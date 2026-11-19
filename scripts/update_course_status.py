"""Build an evidence-scoped readiness register; authored files never imply research acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value.rstrip()+'\n',encoding='utf-8',newline='\n')


def proof(path):
    source=ROOT/path
    if not source.is_file():return {'status':'NOT_RUN','expected_evidence':path}
    result=read(path)
    return {'status':result.get('status','REVIEW'),'evidence':path,
            'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--observed-on',required=True)
    args=parser.parse_args();course=read('programm/course.json')
    windows='practicuum/evidence/20261118-full-course-windows/summary.json'
    linux='practicuum/evidence/20261118-full-course-linux/summary.json'
    # Later source revisions supersede individual runs, never overwrite the old logs.
    supplementary={'M08-L02':('practicuum/evidence/20261118-ir-distribution-safe-windows/summary.json',
                               'practicuum/evidence/20261118-ir-distribution-safe-linux/summary.json'),
                   'M13-L01':('practicuum/evidence/20261118-process-source-windows/summary.json',None),
                   'M13-L02':('practicuum/evidence/20261118-process-source-windows/summary.json',None)}
    for id in ['M09-L01','M09-L02']:
        supplementary[id]=('practicuum/evidence/20261119-professional-kinetics-windows-corrected/summary.json',
                            'practicuum/evidence/20261119-professional-kinetics-linux/summary.json')
    for id in ['M12-L01','M12-L02']:
        supplementary[id]=('practicuum/evidence/20261119-professional-QSAR-windows/summary.json',
                            'practicuum/evidence/20261119-professional-QSAR-linux/summary.json')
    for id in ['M10-L01','M10-L02']:
        supplementary[id]=('practicuum/evidence/20261119-professional-chromatography-windows/summary.json',
                            'practicuum/evidence/20261119-professional-chromatography-linux/summary.json')
    for id in ['M11-L01','M11-L02']:
        supplementary[id]=('practicuum/evidence/20261119-professional-docking-windows/summary.json',
                            'practicuum/evidence/20261119-professional-docking-linux/summary.json')
    baseline={}
    for label,path in [('Windows',windows),('Linux/WSL',linux)]:
        for r in read(path)['runs']:baseline[(r['lesson_id'],r['role'],label)]={'status':r['status'],'evidence':path}
    for lesson,(win,lin) in supplementary.items():
        for label,path in [('Windows',win),('Linux/WSL',lin)]:
            if path and (ROOT/path).is_file():
                for r in read(path)['runs']:
                    if r['lesson_id']==lesson:baseline[(lesson,r['role'],label)]={'status':r['status'],'evidence':path}
    research={
      'HPLC':proof('practicuum/evidence/20261118-hplc-research-statistics/result.json'),
      'atorvastatin_kinetic_parameter_audit':proof('practicuum/evidence/20261118-statin-kinetics-solubility-research/result.json'),
      'xanthine_primary_kinetic_data':proof('practicuum/evidence/20261119-caffeine-rate-law-research/result.json'),
      'xanthine_UHPLC':proof('practicuum/evidence/20261119-xanthine-UHPLC-research/result.json'),
      'A2A_redocking':proof('practicuum/evidence/20261118-A2A-professional-redocking/result.json'),
      'HMGCR_preparation':proof('practicuum/evidence/20261118-HMGCR-target-preparation-repair-audited/failure.json'),
      'coarse_DFT_geometry':proof('practicuum/evidence/research-quantum-istradefylline-cpcm-20261118/conformer-000/optimize/result.json'),
      'coarse_DFT_quadrature':proof('practicuum/evidence/research-quantum-istradefylline-cpcm-20261118/conformer-000/numerical_convergence/failure.json'),
      'A2A_QSAR':proof('practicuum/evidence/20261119-research-A2A-QSAR/result.json'),
      'A2A_QSAR_audit':proof('practicuum/evidence/20261119-research-A2A-QSAR-audit/result.json'),
      'HMGCR_QSAR':proof('practicuum/evidence/20261119-research-HMGCR-QSAR/result.json')}
    research['A2A_redocking']['scientific_acceptance']='FAIL: top-ranked pose recovery 0/9; finding a correct lower-ranked pose does not validate ranking'
    research['coarse_DFT_geometry']['scientific_acceptance']='NOT_ACCEPTED: quadrature gate failed; minimum not confirmed by Hessian'
    research['A2A_QSAR']['scientific_acceptance']='REVIEW_REQUIRED: target-drug chemical domain and independent prospective assay validation'
    requirements={
      'M04-L02':['atorvastatin_kinetic_parameter_audit'],
      'M06-L01':['conformer_ensemble_with_identity_and_convergence'],
      'M06-L02':['DFT_minima_and_conformer_free_energy_uncertainty'],
      'M07-L01':['converged_target_DFT_geometry_and_Hessian'],
      'M07-L02':['quadrature_basis_and_solvent_controls'],
      'M08-L01':['target_TDDFT_and_vibrational_results'],
      'M08-L02':['instrument_response_and_experimental_specificity'],
      'M09-L01':['atorvastatin_kinetic_parameter_audit','xanthine_primary_kinetic_data'],
      'M09-L02':['identifiable_kinetic_fit_to_raw_time_series'],
      'M10-L01':['HPLC','no_invented_peak_widths_or_measured_Rs'],
      'M10-L02':['HPLC','prospective_analytical_method_validation'],
      'M11-L01':['target_identity_assay_and_construct_curation'],
      'M11-L02':['A2A_redocking','HMGCR_preparation','independent_pose_validation'],
      'M12-L01':['A2A_QSAR','HMGCR_QSAR'],
      'M12-L02':['domain_uncertainty_and_external_endpoint_validation'],
      'M13-L01':['published_routes_with_stereochemistry_and_stage_provenance'],
      'M13-L02':['real_process_material_balance_and_missing_input_audit'],
      'M14-L01':['versioned_dossier_and_graph_provenance'],
      'M14-L02':['defended_scientific_argument_and_independent_verification']}
    modules=[]
    for module in course['modules']:
        lessons=[]
        for lesson in module['lessons']:
            id=lesson['id'];notebooks={}
            for role,key in [('case','case_notebook'),('lab','lab_notebook')]:
                path=ROOT/lesson[key]
                notebooks[role]={'path':lesson[key],'authored':path.is_file(),
                  'current_sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
                  'baseline_execution':{os:baseline.get((id,role,os),{'status':'NOT_RUN'}) for os in ['Windows','Linux/WSL']},
                  'scope':'guided demonstration' if role=='case' else 'empty student scaffold; student solutions NOT_RUN'}
            lessons.append({'id':id,'title':lesson['title'],'authoring':'DEVELOPED_DRAFT',
                'professional_computation_requirements':requirements.get(id,['reproducible_foundational_research_contract']),
                'professional_acceptance':'REVIEW_REQUIRED','scientific_review':'NOT_RUN','pedagogical_validation':'NOT_RUN',
                'stepik_testing':'NOT_RUN','release_readiness':'BLOCKED','notebooks':notebooks})
        modules.append({'id':module['id'],'title':module['title'],'lessons':lessons})
    state={'schema_version':'2.0','observed_on':args.observed_on,
      'scope':'draft lesson coverage and actual evidence; professional delivery remains incomplete',
      'program':{'modules':14,'lessons':28,'notebooks':56,'projected_hours':122,'hours_validated':False},
      'quality_requirement':'Professional calculations on target chemical forms; educational toy controls are not accepted substitutes',
      'modules':modules,'research':research,
      'global_release_blockers':['uncompleted target QM/IR/UV and numerical convergence',
       'failed A2A top-pose redocking recovery; HMGCR pocket preparation requires scientific resolution',
       'endpoint-specific QSAR validation and small-data limitation of HMGCR',
       'professional research outputs must replace simplified mandatory demonstrations where still present',
       'independent scientific review NOT_RUN','student pilot and observed workload NOT_RUN','Stepik API/grader testing NOT_RUN'],
      'release_readiness':'BLOCKED'}
    write('course-status.json',json.dumps(state,ensure_ascii=False,indent=2))
    write('PROJECT_STATUS.md',f'''# Фактическое состояние курса — {args.observed_on}

Подготовлены исходники **28 уроков и 56 Notebook** по утверждённым 14 модулям. Это авторская вычислительная редакция: после требования автора о профессиональных расчётах она **не считается завершённым профессиональным курсом**. Упрощённые обязательные демонстрации должны быть заменены целевыми исследованиями; единичные учебные контроли не заменяют их.

## Подтверждено

- Селективно сохранены 704 файла из PR #2/#3/#5; 42 старых задания сопоставлены по компетенциям. Проверены рабочие файлы и Git blobs. [Матрица](migration-matrix.json), [перенос](CONSOLIDATION_REPORT.md).
- Базовая редакция: 56 Notebook исполнялись на Windows и те же 56 в Linux/WSL. Это проверка исполнения разобранных примеров и **пустых каркасов B**, не научный выпуск и не решения студентов. Позднейшие изменения и исследовательские маршруты учитываются отдельно.
- Выполнены профессиональные статистические проверки семи HPLC-откликов по 20 опубликованным опытам: pure error, lack-of-fit, исключение целого режима с повторами, условные интервалы и диагностика. M10 использует также реальные UHPLC данные ксантинов: %RSD, условные интервалы, ранг OFAT и неидентифицируемость взаимодействий.
- Выполнен аудит реальных параметров кинетики/растворимости аторвастатина. M09 использует пять опубликованных кинетических условий кофеина, OLS/остатки/LOOCV и структурную идентифицируемость B; недостающие временные ряды не выдуманы.
- Выполнен target-specific QSAR A2A на 4546 структурах: nested scaffold CV, отдельная calibration, test 854; RMSE 0.74459 pKi, bootstrap CI95 [0.68720, 0.80377]. Аудит не выявил пересечений каркасов. M12 заново анализирует сохранённые прогнозы и область применения, не выдавая это за новое обучение. HMGCR: 57 структур, обучение BLOCKED по заранее заданному протоколу.
- Реальный redocking истрадефиллина в 8RW0: девять поисков, независимые начальные конформации, симметрийный RMSD в системе рецептора. **Геометрический критерий top-1 не пройден: 0/9.** M11 заново анализирует координаты/poses и диагностирует HMGCR BLOCKED; сохранённые результаты не объявляются новым docking.
- Геометрия истрадефиллина B3LYP-D3(BJ)/def2-SVP/C-PCM сошлась; coarse-grid проверка не прошла. Плотная сетка — отдельный новый прогон, не переименование прежнего результата.

## Требует завершения

Полные QM/UV/IR, численная/методическая сходимость, исследовательские ансамбли форм B; пригодная подготовка HMGCR; QSAR и область применимости; замена упрощённых обязательных расчётов профессиональными исходниками/outputs. Полный список и ссылки — [реестр](course-status.json) и [научный отчёт](SCIENTIFIC_VALIDATION_REPORT.md).

Независимая научная рецензия, студенческий пилот, фактические часы и Stepik grader **NOT_RUN**. Выпуск и слияние в main **BLOCKED**. Существующие пользовательские изменения сохранены; автоматическое закрытие PR/Issues не выполняется.
''')
    write('ROADMAP.md','''# Оставшаяся работа

1. Завершить целевые DFT-расчёты с доказанной численной сходимостью, проверкой минимума по Hessian и раздельными формами аторвастатина. Получить TDDFT/IR при явно заданных методе, растворителе и ограничениях.
2. Разобрать отрицательный результат A2A redocking, проверить протокол на независимом структурном контроле. Для HMGCR устранить искусственное восстановление атомов у кармана на научно обоснованной модели; не обходить этот gate удалением проблемных остатков.
3. Выполнен target-specific QSAR A2A по полным страницам ChEMBL_37, аудит split/метрик и перенос в M12. Требуются внешняя endpoint-валидация, анализ assay/document/time shift и обоснование области лекарственного запроса. Небольшую выборку HMGCR не объявлять достаточной; обучение остаётся BLOCKED. Разделять Ki и IC50.
4. Интегрировать профессиональные расчёты, реальные данные, негативные результаты и решения в все затронутые уроки A/B. Учебные синтетические контроли не оставлять заменой основного исследования.
5. Проверить преподавательские ориентиры, задания/рубрики и передачу в версионное досье. Выполнить независимую научную рецензию и студенческий пилот.
6. Повторить сборку полного локального пакета Stepik уже из профессиональной редакции; проверить portable data/resources. Проверить реальную платформу и grader в тестовом курсе.
7. Обновить PR #8 фактическими доказательствами. Слияние в main, закрытие PR/Issues и любые разрушительные операции требуют отдельного разрешения.

Выполненные этапы консолидации и исходной генерации не выдаются за выполнение этих научных критериев. [Статусы](course-status.json).
''')
    write('SCIENTIFIC_VALIDATION_REPORT.md','''# Научные вычисления: результаты и пределы

| Компонент | Фактический результат | Допуск к научному выводу |
|---|---|---|
| HPLC, 20 опубликованных опытов | 7 RSM-моделей; pure error/LOF, grouped CV, диагностические графики и интервалы | Расчёт выполнен; независимая валидация метода отсутствует |
| Удерживание p-ATO / лактона | Ошибка исключённого режима 0.28254 / 0.23236 min | Не экстраполировать на другой pH/колонку; measured Rs не вычисляется без ширин |
| Аторвастатин, опубликованная кинетика | При pH 4.5 отдельно приведённые показатели убыли/образования различаются в 10 раз | Без исходных рядов нельзя выдать совместный fit и новые интервалы параметров |
| Истpaдефиллин, DFT | B3LYP-D3(BJ)/def2-SVP/C-PCM оптимизация сошлась | До Hessian не подтверждён минимум; coarse surface quadrature изменила E на 2.78e-4 Eh при допуске 1e-4 Eh |
| SMD-ветвь | Реальные попытки, остановленные недостатком памяти WSL | Нет принятого результата оптимизации; старый STO-3G не подставлен |
| A2A/8RW0 redocking | 9 реальных поисков, exhaustiveness 64, 3 начальные геометрии × 3 seed; top-1 recovery 0/9, средний top-1 RMSD 9.5593 Å | **FAIL ранжирования**; найденные ниже позы с RMSD <2 Å не меняют этот итог |
| HMGCR/1HWK | Gate остановил подготовку: смещение атомов кармана 2.311 Å и новый OXT на 3.79 Å от лиганда | BLOCKED до проверки структуры/обработки неполных концов; не запускать docking на заведомо неподходящем входе |
| Кофеин, кинетика | Пять опубликованных k_exp при 100 °C; slope 0.695, origin-constrained k₂ 0.71273 L mol⁻¹ min⁻¹; LOOCV RMSE 0.008266 min⁻¹ | OLS-интервалы условны; сырые временные ряды/ошибки повторов отсутствуют; это не кинетика истрадефиллина |
| Ксантины, UHPLC | Семь опубликованных режимов; %RSD переведён в условный SD; ранг полного квадратичного OFAT-плана 7/10 | Взаимодействия неидентифицируемы; внутриусловная повторяемость не подтверждает полную устойчивость; исходные средние округлены |
| QSAR A2A | 4546 структур, 1807 каркасов; nested 5×3 CV; train/cal/test 2848/844/854; test RMSE 0.74459 pKi, baseline 1.24215 | Аудит split/метрик PASS; ближайший training Tanimoto истрадефиллина 0.373; prospective assay validation NOT_RUN |
| QSAR HMGCR | 57 структур, 28 каркасов, endpoint pIC50 | BLOCKED для заранее заданного порога ≥80; обучение NOT_RUN, pIC50 не смешивается с pKi |

Доказательства и SHA: [реестр](course-status.json), `practicuum/evidence`. Независимая рецензия **NOT_RUN**. Ни SCF-сходимость, ни docking score, ни корреляция не подтверждают эффективность, доставку или экспериментальную точность.

Профессиональный протокол требует отдельно назвать химическую форму, заряд/spin, геометрию, solvent model, базис/функционал, дисперсию, сетки и допуски, статус минимумов, исходники, параметры приборного/статистического метода, неопределённость и независимую проверку. C-PCM и SMD не смешиваются как один метод. Газофазные прежние B3LYP/STO-3G результаты остаются историческим учебным контролем.
''')
    write('PEDAGOGICAL_REVIEW_REPORT.md','''# Педагогическая проверка

Существуют 28 пар MD/Notebook, предварительные знания, научные вопросы, математические модели, задания трёх уровней и отдельные преподавательские ориентиры. Профессиональные маршруты после уточнения автора интегрируются; наличие структуры не подтверждает достаточную глубину каждого урока.

Внутренняя проверка: ID, исходные MD → Notebook, локальные ссылки, раздельные A/B, открытые ответы отдельно от ограниченных численных контрактов; сохранение версий досье и происхождения вывода. Пустой B имеет NOT_RUN для решения студента, даже если каркас запустился.

Требует предметного редактирования: замена коротких условных моделей в обязательных научных исследованиях, раскрытие профессиональных алгоритмов небольшими осмысленными блоками, интерпретация негативных результатов, постепенность нагрузки, самостоятельность выбора метода B и полноценные открытые авторские решения.

**NOT_RUN:** независимая научно-методическая рецензия, согласование оценок преподавателей, студенческий пилот, фактическая трудоёмкость и измерение переноса навыка. 122 часа — проектный ориентир. Машинная генерация рубрик не является проверкой педагогической эффективности.
''')
    write('STEPIK_RELEASE_REPORT.md','''# Подготовка к Stepik

Локальная черновая сборка `parser/dist/full-course-20261118` содержала 28 уроков, 56 Notebook, 142 текстовых шага и 25 stdlib-проверок ограниченных численных полей. Целостность этой редакции проверена локально. Это **не профессиональный релиз** и не публикация.

Сборщик включает shared/data и закреплённую среду; исключает преподавательские решения, личный workspace и NIST raw cache. Notebook исполняются в локальном Jupyter/WSL, а не предполагаемом RDKit grader Stepik. Права/атрибуция сохраняются.

После интеграции профессиональных вычислений требуется новая неизменяемая сборка и проверка portable-пакета. **NOT_RUN:** загрузка assets/доступность ссылок, API-объекты тестового курса, отображение формул, полный round-trip решений и реальный Stepik grader. Для доказательства платформенной пригодности локального запуска недостаточно.

Выпуск **BLOCKED** научными критериями и отсутствием проверки платформы. Запись в действующий курс и merge в main не выполняются.
''')
    print('Updated evidence-scoped register for',len(modules),'modules; release BLOCKED')


if __name__=='__main__':main()
