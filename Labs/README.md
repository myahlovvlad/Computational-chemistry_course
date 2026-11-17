# Лабораторный практикум «Операция Химера»

У каждой главы есть руководство, рабочий Jupyter notebook, три задания для переноса навыка и ключ ответов. Основные notebooks содержат фактически выполненные выходы. [Benchmark](benchmarks/REPORT.md) отделяет результат запуска от обещаний точности метода. Искусственные данные, реальные измерения ESOL и подготовленный пример 1IEP имеют разные паспорта.

## Установка и первый запуск

Для полного локального прогона под Windows через WSL 2 используйте [WSL-инструкцию](WSL_SETUP.md). Она создаёт базовую Python 3.12 среду, устанавливает Linux AutoDock Vina 1.2.7 и при необходимости отдельный PySCF-контур. Автоматизация: `bash tools/setup_wsl.sh` из корня репозитория.

В корне репозитория, Python 3.12:

```powershell
python -m venv .venv-course
.venv-course\Scripts\python.exe -m pip install -r Labs/requirements.txt
.venv-course\Scripts\python.exe -m ipykernel install --prefix .venv-course --name course-chemistry --display-name "Chemistry course"
.venv-course\Scripts\python.exe tools/run_labs.py --only 1
```

Для Linux/macOS используйте `python3` и `.venv-course/bin/python`. Среда проверена на Windows x64; совместимость всех комбинаций платформ и будущих версий не заявляется. В VS Code/Jupyter выберите установленное ядро этой среды. При отдельной установке JupyterLab добавьте его в ту же среду; он не нужен для автоматического запуска через nbclient.

Запуск всех основных работ: `python tools/run_labs.py`. Каждая работа использует новое ядро. Для интерактивного изучения открывайте `notebooks/labXX.ipynb` и выполняйте сверху вниз. Автоматический запуск перезаписывает выходы учебных notebooks; свой вариант сохраните отдельным файлом.

Проверка ядра: `python -m unittest discover -s Labs -p test_labs.py -v`. Проверка ссылок, порядка разделов и данных: `python tools/validate_course.py`.

## Привязка к главам

| Глава | Руководство | Исполняемый notebook | Ответы |
|---|---|---|---|
| 1. Постановка и DoE | [ЛР 1](guides/lab01.md) | [lab01](notebooks/lab01.ipynb) | [ключ](solutions/lab01.md) |
| 2. Среда | [ЛР 2](guides/lab02.md) | [lab02](notebooks/lab02.ipynb) | [ключ](solutions/lab02.md) |
| 3. Представления | [ЛР 3](guides/lab03.md) | [lab03](notebooks/lab03.ipynb) | [ключ](solutions/lab03.md) |
| 4. Дескрипторы | [ЛР 4](guides/lab04.md) | [lab04](notebooks/lab04.ipynb) | [ключ](solutions/lab04.md) |
| 5. Сходство | [ЛР 5](guides/lab05.md) | [lab05](notebooks/lab05.ipynb) | [ключ](solutions/lab05.md) |
| 6. Конформеры | [ЛР 6](guides/lab06.md) | [lab06](notebooks/lab06.ipynb) | [ключ](solutions/lab06.md) |
| 7. Базы/измерения | [ЛР 7](guides/lab07.md) | [lab07](notebooks/lab07.ipynb) | [ключ](solutions/lab07.md) |
| 8. Скрининг | [ЛР 8](guides/lab08.md) | [lab08](notebooks/lab08.ipynb) | [ключ](solutions/lab08.md) |
| 9. Визуализация | [ЛР 9](guides/lab09.md) | [lab09](notebooks/lab09.ipynb) | [ключ](solutions/lab09.md) |
| 10. Докинг | [ЛР 10](guides/lab10.md) | [lab10](notebooks/lab10.ipynb) | [ключ](solutions/lab10.md) |
| 11. QSPR | [ЛР 11](guides/lab11.md) | [lab11](notebooks/lab11.ipynb) | [ключ](solutions/lab11.md) |
| 12. Квантовая химия | [ЛР 12](guides/lab12.md) | [lab12](notebooks/lab12.ipynb) | [ключ](solutions/lab12.md) |
| 13. Ретросинтез | [ЛР 13](guides/lab13.md) | [lab13](notebooks/lab13.ipynb) | [ключ](solutions/lab13.md) |
| 14. Передача | [ЛР 14](guides/lab14.md) | [lab14](notebooks/lab14.ipynb) | [ключ](solutions/lab14.md) |

## Дополнительный инструмент для докинга

Для собственного запуска ЛР 10 скачайте AutoDock Vina с [официальной страницы релизов](https://github.com/forlilab/AutoDock-Vina/releases). Проверенный вариант: v1.2.7, Windows x64, `vina_1.2.7_win.exe` в `tools/bin/`; на другой платформе команда `vina` должна быть в PATH. Бинарник в Git не включён. Данные tutorial уже находятся в datasets, сеть во время самого расчёта не нужна. Без Vina notebook разбирает официальный выход и явно указывает ограниченный режим.

## Итоговое приложение

`python -m streamlit run Labs/app.py` открывает локальный интерфейс загрузки CSV. CLI: `python Labs/pipeline.py Labs/datasets/molecules.csv --out Labs/results/final`. Оба используют одну политику. Лимит приложения: 1 МБ / 500 строк. Полный отчёт включает ошибки, причины и паспорт. `eligible` означает только отсутствие перечисленных предупреждений.

## Дидактический маршрут

Сначала закрыть ответы и сделать прогноз. Затем выполнить разобранный пример, проверить отрицательный контроль и объяснить результат. После этого изменить вход самостоятельно и записать ограничение. На следующей неделе повторить первую тренировочную задачу без подсказки. Рубрика каждой работы оценивает исполнение и понимание отдельно.
