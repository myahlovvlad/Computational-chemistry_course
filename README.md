# Введение в хемоинформатику и вычислительную химию

**Операция «Химера»: от молекулярной записи к проверяемому вычислительному решению.**

Основной текст курса находится в `Module_theory/`: 14 последовательно переработанных глав, 112 нумерованных разделов, объяснение методов и границ применимости, разобранные примеры и ссылки на книги. В `Labs/` каждой главе соответствует лабораторная работа с guideline, dataset, исполняемым notebook, заданиями и ответами.

Подача сохранена как разговор коллег у лабораторного стола: начинаем с прикладного вопроса, объясняем физику/математику, проверяем результат и только затем принимаем решение. Уверенный вывод не подменяет контроль.

## Читать и выполнять

| № | Теория | Руководство | Разбор кейсов | Самостоятельные кейсы |
|---|---|---|---|---|
| 1 | [Модуль 1. Вычислительный эксперимент: от красивого результата к решению лаборатории](Module_theory/Module%201_SDLC.md) | [Guideline](Labs/guides/lab01.md) | [Разбор](Labs/notebooks/lab01.ipynb) | [Практикум](Labs/notebooks/lab01_practice.ipynb) |
| 2 | [Модуль 2. Цифровой верстак: от установки к первому проверенному результату](Module_theory/Module%202_Setup%20Workharness.md) | [Guideline](Labs/guides/lab02.md) | [Разбор](Labs/notebooks/lab02.ipynb) | [Практикум](Labs/notebooks/lab02_practice.ipynb) |
| 3 | [Модуль 3. Молекула в компьютере: от строки к химической идентичности](Module_theory/Module%203_compound%20and%20reaction-representation.md) | [Guideline](Labs/guides/lab03.md) | [Разбор](Labs/notebooks/lab03.ipynb) | [Практикум](Labs/notebooks/lab03_practice.ipynb) |
| 4 | [Модуль 4. Дескрипторы: от структуры к признакам с физическим смыслом](Module_theory/Module%204_Descriptor.md) | [Guideline](Labs/guides/lab04.md) | [Разбор](Labs/notebooks/lab04.ipynb) | [Практикум](Labs/notebooks/lab04_practice.ipynb) |
| 5 | [Модуль 5. Поиск аналогов: от отпечатка к проверяемой гипотезе](Module_theory/Module%205_Fingerprinter_Farmacophore.md) | [Guideline](Labs/guides/lab05.md) | [Разбор](Labs/notebooks/lab05.ipynb) | [Практикум](Labs/notebooks/lab05_practice.ipynb) |
| 6 | [Модуль 6. Конформеры: от плоской формулы к проверенной геометрии](Module_theory/Module%206_Moleculr%20mechanics.md) | [Guideline](Labs/guides/lab06.md) | [Разбор](Labs/notebooks/lab06.ipynb) | [Практикум](Labs/notebooks/lab06_practice.ipynb) |
| 7 | [Модуль 7. Химические данные: от скачанной таблицы к сопоставимым измерениям](Module_theory/Module%207_Database.md) | [Guideline](Labs/guides/lab07.md) | [Разбор](Labs/notebooks/lab07.ipynb) | [Практикум](Labs/notebooks/lab07_practice.ipynb) |
| 8 | [Модуль 8. Воронка скрининга: от предупреждения к обоснованной проверке](Module_theory/Module%208_Screening.md) | [Guideline](Labs/guides/lab08.md) | [Разбор](Labs/notebooks/lab08.ipynb) | [Практикум](Labs/notebooks/lab08_practice.ipynb) |
| 9 | [Модуль 9. Научный отчёт: от эффектной картинки к понятному решению](Module_theory/Module%209_Visualization.md) | [Guideline](Labs/guides/lab09.md) | [Разбор](Labs/notebooks/lab09.ipynb) | [Практикум](Labs/notebooks/lab09_practice.ipynb) |
| 10 | [Модуль 10. Докинг: от рейтинга score к проверке протокола](Module_theory/Module%2010_docking.md) | [Guideline](Labs/guides/lab10.md) | [Разбор](Labs/notebooks/lab10.ipynb) | [Практикум](Labs/notebooks/lab10_practice.ipynb) |
| 11 | [Модуль 11. QSAR/QSPR: от красивой метрики к честной оценке переноса](Module_theory/Module%2011_QSAR.md) | [Guideline](Labs/guides/lab11.md) | [Разбор](Labs/notebooks/lab11.ipynb) | [Практикум](Labs/notebooks/lab11_practice.ipynb) |
| 12 | [Модуль 12. Квантовая химия: от энергии в файле к физическому выводу](Module_theory/Module%2012_quatium%20chemistry.md) | [Guideline](Labs/guides/lab12.md) | [Разбор](Labs/notebooks/lab12.ipynb) | [Практикум](Labs/notebooks/lab12_practice.ipynb) |
| 13 | [Модуль 13. Ретросинтез: от предложенной стрелки к проверяемому маршруту](Module_theory/Module%2013_retrosynthesis.md) | [Guideline](Labs/guides/lab13.md) | [Разбор](Labs/notebooks/lab13.ipynb) | [Практикум](Labs/notebooks/lab13_practice.ipynb) |
| 14 | [Модуль 14. Передача инструмента: от рабочего ноутбука к воспроизводимому решению](Module_theory/Module%2014_SDLS-workflow%20development_web%20app.md) | [Guideline](Labs/guides/lab14.md) | [Разбор](Labs/notebooks/lab14.ipynb) | [Практикум](Labs/notebooks/lab14_practice.ipynb) |

## С чего начать

1. Прочитать главу 1 и заполнить паспорт задачи.
2. Установить среду по [инструкции практикума](Labs/README.md).
3. Выполнить ЛР 1–3 с прогнозом до запуска и отрицательным контролем.
4. Продолжить по номерам; докинг и квантовая химия имеют отдельные предпосылки. Завершить передачей конвейера в главе 14.

Действующий практикум состоит из 14 пар / 28 notebooks: объяснённые расчёты и 42 самостоятельных кейса. DFT входит в разбор модуля 12. Приложения модуля 14 создаются в [IDE](Labs/ide/README.md). [Журнал новой редакции](Labs/benchmarks/paired-execution.json) отделяет запуск разбора, пустого каркаса и авторскую проверку эталонных решений; самостоятельное выполнение учениками не заявляется.

Полный маршрут использует WSL/Ubuntu, Python 3.12 и uv с `uv.lock`. [Инструкция установки](Labs/SETUP.md) включает Jupyter и IDE. Для Vina нужен отдельный Linux-бинарник в PATH. Наборы данных и их hash опубликованы с [паспортами](Labs/datasets/README.md). Искусственные значения не выдаются за экспериментальные измерения.

## Книги и визуальные материалы

[Карта чтения](Literature/READING_MAP.md) связывает семь книг/источников из локальной библиотеки с главами курса. PDF преобразованы установленным навыком pdf-to-markdown: 2657 страниц Markdown, 767 извлечённых иллюстраций, 2657 факсимиле страниц. [Описание конвертации](Literature/README.md) объясняет покрытие и ограничение OCR.

Полные книги и конвертации остаются в локальной `Literature/converted/` и исключены из публичного Git. На GitHub находятся авторские учебные тексты, библиографическая карта, исходный код, учебные datasets и проверенные notebooks. Рисунки в notebook построены кодом практикума.

## Для автора курса

- [Согласованная программа для Stepik](Stepik_course/02_PROGRAM.md) и [инструкция сборки шагов](Stepik_course/03_STEPIK.md).
- [Интерактив и сценарии видео](Stepik_course/05_MEDIA.md), [локальный тренажёр](Stepik_course/media/interactive.html).
- `course-manifest.json` — машинная связь глава → guideline → notebook → ответы.
- `tools/build_course.py` — сборка основной редакции; `tools/run_labs.py` — исполнение; `tools/validate_course.py` — проверка пакета.

`Stepik_course/` — предыдущий редакторский пакет; действующая теория и практикум находятся в `Module_theory/` и `Labs/`. В `archive/source-drafts/` сохранены заполненные исходные черновики. Старые файлы `Couse organistaions.md` и `Programm/Matrix-course.md` оставлены как история замысла; их неподтверждённые цифры и примеры не являются рекомендациями текущей редакции.

## Проверки

```text
python -m unittest discover -s Labs -p test_labs.py -v
python tools/validate_course.py
python tools/run_labs.py
```

Перед публикацией на Stepik остаются ручная сборка шагов, выбор режима оценки, пилот нагрузки и запись видео. Размещение исходников на GitHub не означает публикацию курса в LMS.
