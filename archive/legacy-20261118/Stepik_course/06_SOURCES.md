# Источники и границы проведённого чтения

## 6.1. Материалы проекта

Полностью прочитаны все шесть непустых исходных Markdown: `SYSTEM_PROMPT.md`, `skills/storytelling.md`, `Couse organistaions.md`, `Programm/Matrix-course.md` и два заполненных файла в `Module_theory/`. Остальные **14 из 20** исходных Markdown пусты; `INSTRUCTIONS.md` входит в их число.

Пустые файлы учтены в инвентаризации. Существующего `graphify-out/graph.json` нет; небольшой корпус авторских текстов проверен непосредственным чтением, новый граф не создавался.

## 6.2. Библиотека PDF

Из всех семи PDF извлечён доступный текст всех страниц. Всего 2657 страниц, текст извлечён с 2605. Пустая извлечённая страница не обязательно пустая визуально. Изучены начальные разделы/оглавления и тематические фрагменты; книги целиком последовательно не прочитаны и не проходили визуальную постраничную проверку. Для некоторых шрифтов extractor сообщил предупреждения: формулы и символы нельзя считать проверенными по извлечённому тексту. В курс не переносились непроверенные формулы из таких фрагментов.

| Файл / издание | Страниц PDF / с текстом | Как использовать |
|---|---:|---|
| Kulkarni et al., *Artificial Intelligence for Chemical Sciences*, 2025 | 413 / 399 | Дополнительный обзор применений и представлений; не предпосылка курса |
| Bajorath (ed.), *Chemoinformatics: Concepts, Methods, and Tools for Drug Discovery*, Methods in Molecular Biology 275 | 538 / 528 | Основы представлений и сходства для модулей 3–5; программные API проверять по современной документации |
| Mollick, *Co-Intelligence*, 2024 | 226 / 216 | Факультатив о сотрудничестве с ИИ; не источник химической валидации |
| Young, *Computational Chemistry: A Practical Guide*, 2001 | 434 / 434 | Главы о силовых полях, выборе модели и проверке результатов; команды старого ПО не копировать |
| Cramer, *Essentials of Computational Chemistry*, 2nd ed., 2004 | 607 / 606 | Механика, электронная структура, DFT и термохимия для 6/12 |
| Leardi, *Experimental design in chemistry: A tutorial*, ACA 652 (2009), 161–172 | 12 / 12 | Взаимодействие факторов и план эксперимента, кейс H |
| Ильяхов, Сарычева, *Пиши, сокращай 2025*, выходные данные в файле: 2024 | 427 / 410 | Работа с конкретикой, предложением и задачей читателя; не источник химических утверждений |

Рабочие извлечения находятся в `tmp/pdfs/`, это вспомогательные файлы анализа, не материалы для публикации студентам. Длинные выдержки и изображения страниц в курс не включены. Для студенческой библиографии нужны легальные ссылки/экземпляры; имеющиеся имена файлов не являются рекомендацией источника скачивания.

## 6.3. Проверенные внешние первичные источники

Проверка выполнена 10 ноября 2026. Документация меняется; перед записью видео и настройкой grader нужно повторить техническую проверку.

- [Stepik: структура курса](https://help.stepik.org/article/54734) — уровни курса, урока и шага.
- [Stepik: конструктор и типы заданий](https://teach.stepik.org/blog/constructor-kursov) — выбор формата шага.
- [Stepik: справочный центр](https://help.stepik.org/search) — доступность функций; точный тариф аккаунта не проверялся.
- [RDKit: руководство](https://www.rdkit.org/docs/GettingStartedInPython.html), [установка](https://www.rdkit.org/docs/Install.html), [MolStandardize](https://www.rdkit.org/docs/source/rdkit.Chem.MolStandardize.rdMolStandardize.html), [FilterCatalog](https://www.rdkit.org/docs/cppapi/classRDKit_1_1FilterCatalogParams.html) — API, различие преобразований и объединение PAINS.
- [Assay Guidance Manual: assay artifacts](https://www.ncbi.nlm.nih.gov/books/NBK326708/), [chemical reactivity](https://www.ncbi.nlm.nih.gov/sites/books/NBK326709/), [How to Triage PAINS-Full Research](https://pmc.ncbi.nlm.nih.gov/articles/PMC4841006/) — интерференция и ограничения фильтров.
- [Microsoft: что такое WSL](https://learn.microsoft.com/en-us/windows/wsl/about), [установка](https://learn.microsoft.com/en-us/windows/wsl/install) — архитектура и права для стандартного сценария установки.
- [Python venv](https://docs.python.org/3/library/venv.html) — изолированные среды.
- [ChEMBL: схема и SQL](https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/schema-questions-and-sql-examples) — структура таблиц и поля активности.
- [MoleculeNet](https://deepchem.readthedocs.io/en/latest/api_reference/moleculenet.html) — различие ESOL, BBBP, ClinTox; выбор задачи.
- [scikit-learn: common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) — Pipeline и предотвращение утечки.
- [AutoDock Vina: basic docking](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html) — подготовка и 1IEP tutorial.
- [PySCF: DFT](https://pyscf.org/user/dft.html), [geometry optimization](https://pyscf.org/user/geomopt.html) — различие электронной задачи и оптимизации.
- [AiZynthFinder](https://molecularai.github.io/aizynthfinder/) — необходимость модели и stock для автоматического ретросинтеза.

Некоторые дополнительные ссылки в модулях — навигация по официальной документации, а не отдельные доказательства проведённого запуска. Фактически выполненные запуски перечислены в `07_VALIDATION.md`.

## 6.4. Что исключено из исходной библиографии

Ссылка на «Oleg Merkulev, Cheminformatics in Practice», названия обзоров с неполной атрибуцией и точные номера глав у неподтверждённых изданий не перенесены как установленная библиография. Для курса недостаточно пометы «или аналогичные пособия». HuBMAP не предлагается как основной молекулярный benchmark растворимости. Цифры стоимости миллиона дескрипторных расчётов и заявления о гарантированном ускорении исключены до реального бенчмарка.
