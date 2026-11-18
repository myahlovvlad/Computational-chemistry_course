# MIGRATION_MATRIX — селективная консолидация

**Цель:** одна архитектура PR #8, без полного merge старых PR. Статусы: KEEP (оставить действующим), ADAPT (селективно перенести/переработать), ARCHIVE (исторически сохранить), REPLACE (в новой архитектуре заменить), REVIEW (сначала проверить).

| Источник | Компонент/путь | Действие | Обоснование и проверка |
|---|---|---|---|
| #8 `course/unified-research-structure` | `programm/COURSE_BLUEPRINT.md`, `programm/BRIEF_TRACEABILITY.md`, `programm/CONCEPT_TO_CASE_MATRIX.md` | KEEP | Единственный целевой syllabus, 14/28 |
| #8 | `theory/modules/M01,L03` (точно `M01`, `M03`), `practicuum/modules/M01,M03` | KEEP | 3 подготовленных урока; выполнить повторную регрессию после миграции |
| #8 | `practicuum/shared`, `practicuum/evidence`, `scripts/environment`, `parser` | KEEP | Канонические инструменты/данные/история; не объявлять Stepik релиз |
| #8 | `web-training/trainers/hplc` | KEEP | Ограниченный HPLC-прототип, не завершённый M10 |
| #8 | `archive/legacy-20261118` | KEEP/ARCHIVE | История main и PR #7, не текущий курс |
| #7 `practice/issue4-research-m01` | `course_source/modules/M01/01_guided_case.ipynb`, `02_independent_lab.ipynb`, глоссарий, вопросы, вычислительные ориентиры | REVIEW/ADAPT | Исходный кейс ESOL и наставнические приёмы могут использоваться в M01-L02; часть уже архивирована #8; проверить SHA и семантические различия |
| #7 | `course_source/modules/M01/evidence`, `verify_evidence.py` | ARCHIVE | 220 старых хешей проверялись, но не являются активной проверкой нового курса |
| #5 `practice/paired-case-notebooks` (base #3) | `Labs/notebooks/labXX.ipynb`, `labXX_practice.ipynb`, `Labs/guides` | ADAPT | 14 пар/28 notebook ≠ 28 целевых уроков/56 notebook; перенос по учебному результату, не по номеру |
| #5 | `Labs/practice-case-registry.json`, `Labs/practice_contracts.json`, `Labs/practice_checks.py` | REVIEW/ADAPT | Уникальные checkers/схемы; отделить численную проверку от оценки научного аргумента |
| #5 | `Labs/benchmarks/paired/M*-C*/reference.py`, `paired-execution.json`, `PAIRED_REPORT.md` | ADAPT/ARCHIVE | 25 авторских reference PASS, 42 ученических решения NOT_RUN; импорт эталонов только с контрольными хешами/входами |
| #5 | `Labs/ide/README.md` и IDE-часть M14 | ADAPT | Оставить разработку CLI/Streamlit в IDE, а не выдавать Notebook за готовое приложение |
| #5 | Старые индексы, `course-manifest.json`, генератор прежнего syllabus | REPLACE | Пересборка должна исходить из `programm` и `parser` #8 |
| #3 `setup/uv-wsl-notebooks` | `pyproject.toml`, `uv.lock`, `tools/register_uv_kernel.py`, `tools/check_notebook_environment.py`, `NOTEBOOK_ENVIRONMENT.md` | REVIEW/ADAPT | Сравнить с `scripts/environment` #8; переносить только недостающие требования, не второе глобальное окружение |
| #3 | `.vscode/settings.json`, `.vscode/extensions.json`, `tools/start_notebooks.sh` | REVIEW/ADAPT | Пользовательские редакторские подсказки после проверки портируемости Windows/Linux |
| #3 | `environment-validation/executed`, `kernel-all.json` | ARCHIVE | Старые доказательства 16 Notebook; не новая программа |
| #2 `audit/issue-1-practice-evidence` | `PRACTICE_AUDIT_REPORT.md`, `PRACTICE_AUDIT_FIXES.md`, `audit/issue-1/build_registry.py`, `check.py` | ADAPT | Переиспользовать методику реестра и доказательной проверки без старых критериев готовности |
| #2 | `audit/issue-1/evidence`, `practice-audit.csv` | ARCHIVE | 513 вхождений действий, не независимые 513 тестов и не процент готовности |
| main | `Module_theory`, `Stepik_course`, `Programm` | ARCHIVE/ADAPT | Использовать как сырьё для новых уроков; не держать две опубликованные программы |
| main | `Labs/datasets`, `Labs/solutions`, `Literature`, `THIRD_PARTY_NOTICES.md` | REVIEW/KEEP | Сверить лицензии, SHA, исходные методы и права на публикацию; книги не переносить без разрешения |
| main | `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` | REVIEW/ADAPT | Эталонные расчёты полезны для будущих M07/M11/M12, но не эквивалентны кейсам A/B |

## Границы достоверности
Сравнение через GitHub `compare` вернуло максимум 300 файлов для крупных изменений #5/#8; это **не полная построчная проверка 770 изменённых файлов PR #8**. Перед любым фактическим переносом обязательно выполнить локальный `git diff --name-status`, `git diff --find-renames`, SHA256 всех бинарных входов и отдельный отчёт покрытия каждого файла. Не применять автоматический cherry-pick массовых коммитов.

## Порядок выбора
1. Сначала искать реализацию в канонической структуре #8.
2. Если отсутствует — сверить SHA и назначение в архиве #8.
3. Затем только уникальную семантическую часть брать из источника; отдельно сохранить исторические доказательства.
4. При противоречии научных исходных данных оставлять REVIEW и не переписывать эталон.
5. После адаптации запустить новую регрессию Windows/Linux, проверку ссылок, лицензий, provenance, исполнения и качества заданий.
