"""Build an evidence-scoped readiness register; authored files never imply research acceptance."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCUMENTS=json.loads((ROOT/'docs/layout.json').read_text(encoding='utf-8'))['moved_documents']


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):
    path=ROOT/DOCUMENTS.get(path,path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.suffix=='.md':
        # Templates use repository-root targets; emitted links follow the document.
        def relocate(match):
            target=match[1]
            if ':' in target or target.startswith('#'):return match[0]
            return ']('+os.path.relpath(ROOT/DOCUMENTS.get(target,target),path.parent).replace('\\','/')+')'
        value=re.sub(r'\]\(([^)]+)\)',relocate,value)
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
    configs={lesson['id']:read(lesson['practice']+'/lesson.json')
             for module in course['modules'] for lesson in module['lessons']}
    text_step_count=sum(len(list((ROOT/lesson['theory']).glob('*.md')))
                        +len(configs[lesson['id']]['case_steps'])+len(configs[lesson['id']]['lab_steps'])
                        for module in course['modules'] for lesson in module['lessons'])
    hashes={}
    def current_hash(relative):
        path=(ROOT/relative).resolve();path.relative_to(ROOT)
        if relative not in hashes:hashes[relative]=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return hashes[relative]
    def execution_entry(run,path):
        config=configs[run['lesson_id']];steps=config['case_steps' if run['role']=='case' else 'lab_steps']
        observed_steps=run.get('step_sha256',{});observed_inputs=run.get('data_sha256',{})
        return {'status':run['status'],'evidence':path,
          'current_step_sources_match':set(observed_steps)==set(steps)
              and all(observed_steps[name]==current_hash(name) for name in steps),
          'current_declared_inputs_match':all(observed_inputs.get(name)==current_hash(name) for name in config.get('inputs',[]))}
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
    for id in ['M04-L01','M04-L02']:
        supplementary[id]=('practicuum/evidence/20261119-professional-solubility-windows/summary.json',
                            'practicuum/evidence/20261119-professional-solubility-linux/summary.json')
    for id in ['M06-L01','M06-L02']:
        supplementary[id]=('practicuum/evidence/20261119-professional-conformers-reproduced-windows/summary.json',
                            'practicuum/evidence/20261119-professional-conformers-reproduced-linux/summary.json')
    baseline={}
    for label,path in [('Windows',windows),('Linux/WSL',linux)]:
        for r in read(path)['runs']:baseline[(r['lesson_id'],r['role'],label)]=execution_entry(r,path)
    for lesson,(win,lin) in supplementary.items():
        for label,path in [('Windows',win),('Linux/WSL',lin)]:
            if path and (ROOT/path).is_file():
                for r in read(path)['runs']:
                    if r['lesson_id']==lesson:baseline[(lesson,r['role'],label)]=execution_entry(r,path)
    # Consolidation and later main edits supersede older worktree runs only for the actual executed OS.
    for path in ['practicuum/evidence/20261119-main-unification/notebooks/summary.json',
                 'practicuum/evidence/20261119-main-method-article-reviews/summary.json',
                 'practicuum/evidence/20261119-main-method-article-final/summary.json',
                 'practicuum/evidence/20261119-main-metric-meaning/summary.json',
                 'practicuum/evidence/20261120-refactor-course/notebook-summary.json',
                 'practicuum/evidence/20261120-editorial-execution/notebook-summary.json']:
        if (ROOT/path).is_file():
            for r in read(path)['runs']:baseline[(r['lesson_id'],r['role'],'Windows')]=execution_entry(r,path)
    research={
      'HPLC':proof('practicuum/evidence/20261118-hplc-research-statistics/result.json'),
      'atorvastatin_kinetic_parameter_audit':proof('practicuum/evidence/20261118-statin-kinetics-solubility-research/result.json'),
      'xanthine_primary_kinetic_data':proof('practicuum/evidence/20261119-caffeine-rate-law-research/result.json'),
      'xanthine_UHPLC':proof('practicuum/evidence/20261119-xanthine-UHPLC-research/result.json'),
      'istradefylline_solubility':proof('practicuum/evidence/20261119-istradefylline-solubility-research-checked/result.json'),
      'A2A_redocking':proof('practicuum/evidence/20261118-A2A-professional-redocking/result.json'),
      'HMGCR_preparation':proof('practicuum/evidence/20261118-HMGCR-target-preparation-repair-audited/failure.json'),
      'coarse_DFT_geometry':proof('practicuum/evidence/research-quantum-istradefylline-cpcm-20261118/conformer-000/optimize/result.json'),
      'coarse_DFT_quadrature':proof('practicuum/evidence/research-quantum-istradefylline-cpcm-20261118/conformer-000/numerical_convergence/failure.json'),
      'A2A_QSAR':proof('practicuum/evidence/20261119-research-A2A-QSAR/result.json'),
      'A2A_QSAR_audit':proof('practicuum/evidence/20261119-research-A2A-QSAR-audit/result.json'),
      'HMGCR_QSAR':proof('practicuum/evidence/20261119-research-HMGCR-QSAR/result.json')}
    for name in ['istradefylline','atorvastatin','atorvastatin_anion','atorvastatin_lactone']:
        key='GFN2_conformers_'+name
        research[key]=proof('practicuum/evidence/20261119-conformer-GFN2-'+name+'/result.json')
        research[key]['scientific_acceptance']='LOCAL_GFN2_MINIMA_ONLY: three positive projected Hessians; exhaustive sampling, DFT and solution populations not established'
    for name in ['istradefylline','atorvastatin']:
        research['GFN2_numerics_'+name]=proof('practicuum/evidence/20261119-conformer-GFN2-'+name+'-numerics/result.json')
    research['CAM_TZVP_on_GFN2']=proof('practicuum/evidence/20261119-istradefylline-CAM-TZVP-on-GFN2-water/result.json')
    research['GFN2_istradefylline_actual_linux']=proof('practicuum/evidence/20261119-conformer-GFN2-istradefylline-linux/result.json')
    research['GFN2_complete_basin_set_reproduction']=proof('practicuum/evidence/20261119-GFN2-cross-platform-reproduction/result.json')
    research['GFN2_fixed_geometry_platform_diagnosis']=proof('practicuum/evidence/20261119-GFN2-cross-platform-diagnosis/result.json')
    research['CAM_TZVP_on_GFN2_failed_attempt']=proof('practicuum/evidence/20261119-istradefylline-CAM-TZVP-on-GFN2-water/failure.json')
    research['CAM_TZVP_scratch_preflight']=proof('practicuum/evidence/20261119-istradefylline-CAM-TZVP-scratch-preflight/blocked.json')
    research['refined_DFT_progress_snapshot']=proof('practicuum/evidence/20261119-refined-DFT-progress-snapshot/progress.json')
    research['lossless_HDF5_quantum_control']=proof('practicuum/evidence/20261119-lossless-quantum-control/check.json')
    research['lossless_HDF5_guard_control']=proof('practicuum/evidence/20261119-lossless-scratch-guards/check.json')
    research['lossless_HDF5_quantum_control_linux']=proof('practicuum/evidence/20261119-lossless-quantum-control-linux/check.json')
    research['lossless_HDF5_guard_control_linux']=proof('practicuum/evidence/20261119-lossless-scratch-guards-linux/check.json')
    research['electronic_checkpoint_control']=proof('practicuum/evidence/20261119-electronic-checkpoint-controls/summary.json')
    research['CAM_TZVP_lossless_progress_snapshot']=proof('practicuum/evidence/20261119-lossless-TDDFT-progress-snapshot/progress.json')
    research['CAM_TZVP_lossless_result']=proof('practicuum/evidence/20261119-istradefylline-CAM-TZVP-lossless-water/result.json')
    research['current_main_research_runtime']=proof('practicuum/evidence/20261119-main-research-runtime/summary.json')
    research['current_main_research_runtime']['observation_role']='Historical state before the later main-root cached restart'
    research['main_cached_restart_control']=proof('practicuum/evidence/20261119-main-electronic-restart-guarded-calculation/result.json')
    research['main_cached_restart_input_compatibility']=proof('practicuum/evidence/20261119-main-CAM-cache-preflight/restart-validation.json')
    research['main_cached_restart_input_compatibility']['scientific_acceptance']='INPUTS_ONLY: does not certify SCF, TDDFT or physical accuracy'
    research['main_cached_restart_progress_snapshot']=proof('practicuum/evidence/20261119-main-CAM-restarted-progress/progress.json')
    research['main_cached_restart_spectrum']=proof('practicuum/evidence/20261119-main-CAM-TZVP-restarted/result.json')
    research['main_cached_restart_independent_audit']=proof('practicuum/evidence/20261119-main-CAM-TZVP-restarted-audit/result.json')
    research['main_cached_restart_scf_snapshot']=proof('practicuum/evidence/20261120-refactor-runtime/scf.json')
    research['main_cached_restart_scf_snapshot']['scientific_acceptance']='SCF_ONLY: TDDFT spectrum and independent checkpoint audit remain separate gates'
    research['CAM_TZVP_on_GFN2']['scientific_acceptance']='REVIEW_REQUIRED: composite geometry; stability, sensitivity and experimental matching remain required'
    research['A2A_redocking']['scientific_acceptance']='FAIL: top-ranked pose recovery 0/9; finding a correct lower-ranked pose does not validate ranking'
    research['coarse_DFT_geometry']['scientific_acceptance']='NOT_ACCEPTED: quadrature gate failed; minimum not confirmed by Hessian'
    research['A2A_QSAR']['scientific_acceptance']='REVIEW_REQUIRED: target-drug chemical domain and independent prospective assay validation'
    research['istradefylline_solubility']['scientific_acceptance']='REVIEW_REQUIRED: source concentration-basis inconsistencies and aqueous analytical-domain questions; no accepted pKa/intrinsic S0/thermodynamic enthalpy'
    requirements={
      'M04-L01':['istradefylline_solubility','atorvastatin_kinetic_parameter_audit'],
      'M04-L02':['istradefylline_solubility','atorvastatin_kinetic_parameter_audit'],
      'M06-L01':['GFN2_conformers_istradefylline','GFN2_conformers_atorvastatin','GFN2_conformers_atorvastatin_anion','GFN2_conformers_atorvastatin_lactone','finite_sampling_budget_audit'],
      'M06-L02':['GFN2_numerics_istradefylline','GFN2_numerics_atorvastatin','low_mode_RRHO_and_subset_population_limitations'],
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
      'program':{'modules':14,'lessons':28,'notebooks':56,'text_steps':text_step_count,'projected_hours':122,'hours_validated':False},
      'repository':{'canonical_branch':'main','canonical_location':'repository root',
        'documentation':'docs/README.md',
        'dataset_preservation':'archive/branch-datasets/manifest.json'},
      'pedagogy':{'narrative_openings':28,'lesson_transitions':28,'article_reviews':14,
        'reading_route':'programm/ARTICLE_READING.md','student_pilot':'NOT_RUN'},
      'current_main_execution':proof('practicuum/evidence/20261120-refactor-course/notebook-summary.json'),
      'latest_editorial_execution':proof('practicuum/evidence/20261120-editorial-execution/notebook-summary.json'),
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
- M04 использует 60 реальных температурных и восемь pH-значений истрадефиллина, визуально сверенные с первичными PDF. Выполнены conditional Van't Hoff fits и аудит согласованности: source acceptance REVIEW_REQUIRED, pKa/intrinsic S0/thermodynamic enthalpy не объявлены измеренными.
- M06 использует реальные GFN2-xTB/ALPB water расчёты четырёх целых химических форм: 1200 singlepoints, 91 оптимизация, 12 гессианов. Положительные внутренние частоты подтверждают локальные минимумы этой модели. Контроль сетки/шага для A и кислоты выполнен; тонкий порядок двух конформеров A меняется. Независимый Linux-поиск A: ещё 300 singlepoints/19 оптимизаций/3 Hessian. Полное совпадение basin sets REVIEW (7/10 назначений прошли оба допуска); 10 идентичных геометрий на каждой платформе дали max ΔE ≈1.01e-12 Eh. Полнота ансамбля, DFT-минимумы и растворные populations не установлены. Четыре Notebook M06, все 28 преподавательских ориентиров и 47 shared-тестов прошли Windows и Linux/WSL.
- Выполнен target-specific QSAR A2A на 4546 структурах: nested scaffold CV, отдельная calibration, test 854; RMSE 0.74459 pKi, bootstrap CI95 [0.68720, 0.80377]. Аудит не выявил пересечений каркасов. M12 заново анализирует сохранённые прогнозы и область применения, не выдавая это за новое обучение. HMGCR: 57 структур, обучение BLOCKED по заранее заданному протоколу.
- Реальный redocking истрадефиллина в 8RW0: девять поисков, независимые начальные конформации, симметрийный RMSD в системе рецептора. **Геометрический критерий top-1 не пройден: 0/9.** M11 заново анализирует координаты/poses и диагностирует HMGCR BLOCKED; сохранённые результаты не объявляются новым docking.
- Геометрия истрадефиллина B3LYP-D3(BJ)/def2-SVP/C-PCM сошлась; coarse-grid проверка не прошла. Плотная сетка — отдельный новый прогон, не переименование прежнего результата.

## Требует завершения

Полные QM/UV/IR, численная/методическая сходимость, исследовательские ансамбли форм B; пригодная подготовка HMGCR; QSAR и область применимости; замена упрощённых обязательных расчётов профессиональными исходниками/outputs. Полный список и ссылки — [реестр](course-status.json) и [научный отчёт](SCIENTIFIC_VALIDATION_REPORT.md).

Независимая научная рецензия, студенческий пилот, фактические часы и Stepik grader **NOT_RUN**. Научный выпуск **BLOCKED**. Репозиторий консолидирован в `main` по прямому поручению автора от 19.11.2026; это не снимает научные критерии выпуска. См. [отчёт об объединении](MAIN_UNIFICATION_REPORT.md).
''')
    write('ROADMAP.md','''# Оставшаяся работа

1. Завершить целевые DFT-расчёты с доказанной численной сходимостью, проверкой минимума по Hessian и раздельными формами аторвастатина. Получить TDDFT/IR при явно заданных методе, растворителе и ограничениях.
2. Разобрать отрицательный результат A2A redocking, проверить протокол на независимом структурном контроле. Для HMGCR устранить искусственное восстановление атомов у кармана на научно обоснованной модели; не обходить этот gate удалением проблемных остатков.
3. Выполнен target-specific QSAR A2A по полным страницам ChEMBL_37, аудит split/метрик и перенос в M12. Требуются внешняя endpoint-валидация, анализ assay/document/time shift и обоснование области лекарственного запроса. Небольшую выборку HMGCR не объявлять достаточной; обучение остаётся BLOCKED. Разделять Ki и IC50.
4. Интегрировать профессиональные расчёты, реальные данные, негативные результаты и решения в все затронутые уроки A/B. Учебные синтетические контроли не оставлять заменой основного исследования.
5. Проверить преподавательские ориентиры, задания/рубрики и передачу в версионное досье. Выполнить независимую научную рецензию и студенческий пилот.
6. Повторить сборку полного локального пакета Stepik уже из профессиональной редакции; проверить portable data/resources. Проверить реальную платформу и grader в тестовом курсе.
7. Поддерживать единственную ветку `main` и проверяемые доказательства. Консолидация и удаление прежних веток поручены автором 19.11.2026; [отчёт](MAIN_UNIFICATION_REPORT.md). Новые научные результаты принимать по прежним критериям.

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
| GFN2-xTB / ALPB water | 4 формы × 300 singlepoints; 19+24+24+24 оптимизаций, 12 гессианов; число различных геометрий 10/24/23/24 | Локальные минимумы в GFN2, не DFT; finite sampling, разные составы/заряды не ранжируются по абсолютной энергии |
| Численная проверка GFN2 | Для A/кислоты solvent grid 974→2030 и Hessian step 0.005→0.0025 bohr; знаки частот устойчивы | Близкие уровни A меняют порядок; прохождение абсолютного допуска не подтверждает тонкое ранжирование или физическую точность |
| Независимый Linux GFN2 | Новый полный поиск A: 300 singlepoints/19 оптимизаций/3 Hessian, локальные gates PASS; полное сопоставление 10 бассейнов REVIEW | 20/300 MMFF-refined starting geometries отличаются >0.01 Å; 7/10 назначений прошли geometric/energy допуски. На десяти идентичных XYZ max разность энергий Windows/Linux ≈1.01e-12 Eh: эту воспроизводимость нельзя переносить на полноту поиска |
| CAM-B3LYP/def2-TZVP//GFN2 | Реальный Windows-запуск остановлен ENOSPC при построении DF/RSH интегралов; незавершённый временный кэш 13.6 GB удалён с receipt, входы/логи сохранены | Спектр не получен. Повторный preflight BLOCKED: свободно ≈17 GiB при консервативном резерве 50 GiB; базис не уменьшен. Геометрия остаётся GFN2, stability/sensitivity/эксперимент ещё требуют проверки |
| Lossless HDF5 контроль | Disk-backed H2O CAM/def2-TZVP: DF-интегралы совпали побитово, SCF/TD excitation differences 0; файл 1715448→922294 bytes | Проверено изменение хранения, не точность спектра лекарства. Диск guard/path isolation/exception restoration PASS |
| Повтор целевого CAM с lossless IO | Та же электронная модель, 1012 AO и 30 запрошенных состояний; gzip/shuffle/Fletcher32, остановка при резерве диска <4 GiB | Progress snapshot не является спектром. До result.json numerical completion NOT_RUN; минимальный резерв для попытки 16 GiB не гарантирует завершение |
| Анализ электронного checkpoint | На настоящем H2O checkpoint независимо восстановлены density, MO metric и oscillator strengths; намеренно неверный electron count отклонён | Для целевого run поставлена отдельная проверка только после numerical PASS. X-only SVD character игнорирует Y, его вклад сообщается отдельно; physical assignments REVIEW_REQUIRED |
| Проверка main перед возобновлением | `20261119-main-research-runtime/summary.json`: в момент проверки соответствующих процессов не было, финальных target результатов нет, checkpoint сохранены | Исторический BLOCKED. Причина остановки не установлена; промежуточная SCF-энергия не является принятым результатом |
| Read-only restart из main | H2O SCF/TDDFT parity PASS; неверная геометрия/повреждённый тензор отвергнуты. Целевые 204 electrons/1012 AO и 12 sampled AO pairs каждого full/LR блока совместимы; max Gram errors 1.08e-14/2.78e-16 | Это проверка входов, не спектр. Новый SCF/30-state TDDFT запущен из main; snapshot IN_PROGRESS и ожидаемые result/audit учитываются отдельно. Тензоры не перестраиваются, старый SCF PASS не наследуется |
| A2A/8RW0 redocking | 9 реальных поисков, exhaustiveness 64, 3 начальные геометрии × 3 seed; top-1 recovery 0/9, средний top-1 RMSD 9.5593 Å | **FAIL ранжирования**; найденные ниже позы с RMSD <2 Å не меняют этот итог |
| HMGCR/1HWK | Gate остановил подготовку: смещение атомов кармана 2.311 Å и новый OXT на 3.79 Å от лиганда | BLOCKED до проверки структуры/обработки неполных концов; не запускать docking на заведомо неподходящем входе |
| Кофеин, кинетика | Пять опубликованных k_exp при 100 °C; slope 0.695, origin-constrained k₂ 0.71273 L mol⁻¹ min⁻¹; LOOCV RMSE 0.008266 min⁻¹ | OLS-интервалы условны; сырые временные ряды/ошибки повторов отсутствуют; это не кинетика истрадефиллина |
| Ксантины, UHPLC | Семь опубликованных режимов; %RSD переведён в условный SD; ранг полного квадратичного OFAT-плана 7/10 | Взаимодействия неидентифицируемы; внутриусловная повторяемость не подтверждает полную устойчивость; исходные средние округлены |
| Истрадефиллин, растворимость | 60 строк Table S1, восемь pH-значений; conditional fits и source-basis audit | Для метанола slopes по x/mass ≈66.23/35.22 kJ/mol; source acceptance REVIEW_REQUIRED. Физические параметры и новая экспериментальная точность не приняты |
| QSAR A2A | 4546 структур, 1807 каркасов; nested 5×3 CV; train/cal/test 2848/844/854; test RMSE 0.74459 pKi, baseline 1.24215 | Аудит split/метрик PASS; ближайший training Tanimoto истрадефиллина 0.373; prospective assay validation NOT_RUN |
| QSAR HMGCR | 57 структур, 28 каркасов, endpoint pIC50 | BLOCKED для заранее заданного порога ≥80; обучение NOT_RUN, pIC50 не смешивается с pKi |

Доказательства и SHA: [реестр](course-status.json), `practicuum/evidence`. Независимая рецензия **NOT_RUN**. Ни SCF-сходимость, ни docking score, ни корреляция не подтверждают эффективность, доставку или экспериментальную точность.

Снимок 20.11.2026: возобновлённый CAM-B3LYP/def2-TZVP/C-PCM SCF истрадефиллина сошёлся (E = −1296.410267893305 Eh; Tr(DS) ≈ 204). Сохранён неизменяемый `practicuum/evidence/20261120-refactor-runtime/scf.json`. Расчёт 30 состояний TDDFT ещё выполняется; итогового спектра и отдельного checkpoint-аудита нет. Геометрия GFN2 не объявляется DFT-минимумом.

Профессиональный протокол требует отдельно назвать химическую форму, заряд/spin, геометрию, solvent model, базис/функционал, дисперсию, сетки и допуски, статус минимумов, исходники, параметры приборного/статистического метода, неопределённость и независимую проверку. C-PCM и SMD не смешиваются как один метод. Газофазные прежние B3LYP/STO-3G результаты остаются историческим учебным контролем.
''')
    write('PEDAGOGICAL_REVIEW_REPORT.md','''# Педагогическая проверка

Существуют 28 пар MD/Notebook, предварительные знания, научные вопросы, математические модели, задания трёх уровней и отдельные преподавательские ориентиры. Профессиональные маршруты после уточнения автора интегрируются; наличие структуры не подтверждает достаточную глубину каждого урока.

Внутренняя проверка: ID, исходные MD → Notebook, локальные ссылки, раздельные A/B, открытые ответы отдельно от ограниченных численных контрактов; сохранение версий досье и происхождения вывода. Пустой B имеет NOT_RUN для решения студента, даже если каркас запустился.

Требует предметного редактирования: замена коротких условных моделей в обязательных научных исследованиях, раскрытие профессиональных алгоритмов небольшими осмысленными блоками, интерпретация негативных результатов, постепенность нагрузки, самостоятельность выбора метода B и полноценные открытые авторские решения.

20.11.2026: выполнен структурный редакторский аудит 28 уроков и подробный ручной разбор шести случаев. Глубоко переработаны A/B и рубрика M02-L01; в 13 других разборах общие переходы заменены пояснениями к конкретным вычислениям. [Редакторский отчёт](docs/maintenance/PRACTICUM_EDITORIAL_REVIEW.md) отделяет выполненную правку от ещё открытых предметных задач. Это не внешний педагогический пилот и не подтверждение научной достаточности контролей M07/M08.

**NOT_RUN:** независимая научно-методическая рецензия, согласование оценок преподавателей, студенческий пилот, фактическая трудоёмкость и измерение переноса навыка. 122 часа — проектный ориентир. Машинная генерация рубрик не является проверкой педагогической эффективности.
''')
    package_proof='practicuum/evidence/20261120-editorial-package/check.json'
    if (ROOT/package_proof).is_file() and read(package_proof).get('status')=='PASS':
        package_name='parser/dist/editorial-20261120'
    else:
        package_name='parser/dist/refactor-20261120'
        package_proof='practicuum/evidence/20261120-refactor-package/check.json'
    write('STEPIK_RELEASE_REPORT.md',f'''# Подготовка к Stepik

Действующая программа main содержит 28 уроков, 56 Notebook и {text_step_count} текстовых шагов, включая переходы и задания по статьям. Сборка `{package_name}` проверена локально (`{package_proof}`); 25 stdlib-проверок относятся к ограниченным численным полям. Редакторские изменения 14 пар Notebook проверены отдельно (`practicuum/evidence/20261120-editorial-execution/notebook-summary.json`); прежние проверки восьми Notebook и смысла метрик M12 сохранены как исторические свидетельства. Это **не профессиональный релиз** и не публикация.

Сборщик включает shared/data и закреплённую среду; исключает преподавательские решения, личный workspace и NIST raw cache. Notebook исполняются в локальном Jupyter/WSL, а не предполагаемом RDKit grader Stepik. Права/атрибуция сохраняются.

После дальнейших изменений M07/M08 потребуется следующая неизменяемая сборка. **NOT_RUN:** загрузка assets/доступность ссылок, API-объекты тестового курса, отображение формул, полный round-trip решений и реальный Stepik grader. Для доказательства платформенной пригодности локального запуска недостаточно.

Выпуск **BLOCKED** научными критериями и отсутствием проверки платформы. Репозиторий консолидирован в `main` по поручению автора; публикация в действующий Stepik-курс не выполняется.

Дополнительная сборка `parser/dist/professional-quantum-io-20261119` включает lossless scratch/guard controls и самостоятельный electronic checkpoint analyzer. Её локальная целостность проверяется отдельно от состояния ожидающих расчётов; метод хранения не меняет научные критерии выпуска.
''')
    print('Updated evidence-scoped register for',len(modules),'modules; release BLOCKED')


if __name__=='__main__':main()
