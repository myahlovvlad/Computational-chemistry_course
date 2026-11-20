# Документация курса

Учебный маршрут находится в [программе](../programm/COURSE_BLUEPRINT.md), теория — в `theory`, практические уроки — в `practicuum/modules`.

| Задача | Документ |
|---|---|
| Узнать текущее состояние | [Статус](status/PROJECT_STATUS.md), [машинный реестр](status/course-status.json) |
| Проверить научные ограничения | [Научный отчёт](status/SCIENTIFIC_VALIDATION_REPORT.md) |
| Проверить обучение и оценивание | [Педагогическая проверка](status/PEDAGOGICAL_REVIEW_REPORT.md) |
| Подготовить Stepik | [Состояние экспорта](status/STEPIK_RELEASE_REPORT.md) |
| Перенести курс через API | [Пошаговая инструкция](maintenance/STEPIK_API_GUIDE.md) |
| Выбрать следующую работу | [План](status/ROADMAP.md), [реестр долга](maintenance/DEBT_REGISTER.md) |
| Понять структуру | [Архитектура](architecture/ARCHITECTURE.md), [карта переноса](layout.json) |
| Открыть курс в WSL | [Единственный источник](maintenance/WSL_SINGLE_SOURCE.md) |
| Сопровождать репозиторий | [Правила очистки](maintenance/REPOSITORY_MAINTENANCE.md), [роль автора](maintenance/SYSTEM_PROMPT.md) |
| Проверить историю консолидации | [Объединение main](history/MAIN_UNIFICATION_REPORT.md), [продолжение](history/MAIN_CONTINUATION_REPORT.md), [матрица](history/MIGRATION_MATRIX.md) |
| Проверить этот рефакторинг | [Отчёт](maintenance/REFACTOR_20261120.md) |
| Разобраться в папке evidence | [Что хранить и что можно сокращать](maintenance/EVIDENCE_RETENTION.md), [инвентарь](maintenance/EVIDENCE_INVENTORY.json) |
| Оценить подачу практикума | [Редакторская проверка](maintenance/PRACTICUM_EDITORIAL_REVIEW.md), [метрики](maintenance/PRACTICUM_AUDIT.json) |
| Читать углублённые объяснения | [Новая редакция всех 28 разборов](maintenance/REASONING_REVISION.md) |

`status` обновляется генератором `scripts/update_course_status.py`. `history` сохраняет описание прежних этапов и не удостоверяет текущее состояние курса. JSON-пути к научным данным в реестрах считаются от корня репозитория. Перемещение документа не является повторным выполнением проверки.
