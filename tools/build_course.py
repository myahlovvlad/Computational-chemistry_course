"""Assemble canonical theory, laboratory guides, answer keys and notebooks."""
from __future__ import annotations
import json
from pathlib import Path
import re
from urllib.parse import quote

import nbformat as nbf

from lab_materials import LABS
from theory_notes import NOTES

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"Stepik_course/modules"
BOOKS={
 "B01":"Kulkarni et al. (eds.). Artificial Intelligence for Chemical Sciences. 2025.",
 "B02":"Bajorath (ed.). Chemoinformatics: Concepts, Methods, and Tools for Drug Discovery. Methods in Molecular Biology 275.",
 "B03":"Mollick. Co-Intelligence. 2024.",
 "B04":"Young. Computational Chemistry: A Practical Guide for Applying Techniques to Real-World Problems. 2001.",
 "B05":"Cramer. Essentials of Computational Chemistry. 2nd ed. 2004.",
 "B06":"Leardi. Experimental design in chemistry: A tutorial. Analytica Chimica Acta 652 (2009), 161–172.",
 "B07":"Ильяхов, Сарычева. Пиши, сокращай 2025. Выходные данные файла: 2024.",
}
FILES={
1:"Module 1_SDLC.md",2:"Module 2_Setup Workharness.md",
3:"Module 3_compound and reaction-representation.md",4:"Module 4_Descriptor.md",
5:"Module 5_Fingerprinter_Farmacophore.md",6:"Module 6_Moleculr mechanics.md",
7:"Module 7_Database.md",8:"Module 8_Screening.md",9:"Module 9_Visualization.md",
10:"Module 10_docking.md",11:"Module 11_QSAR.md",12:"Module 12_quatium chemistry.md",
13:"Module 13_retrosynthesis.md",14:"Module 14_SDLS-workflow development_web app.md"}

def bootstrap(number: int) -> str:
 return f'''from pathlib import Path
import sys, json, math, csv, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

# WHY: relative discovery makes the notebook portable across machines.
ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "Labs" / "chemistry.py").exists()), None)
if ROOT is None:
    raise FileNotFoundError("Запустите notebook внутри репозитория курса")
sys.path.insert(0, str(ROOT / "Labs"))
DATA = ROOT / "Labs" / "datasets"
OUT = ROOT / "Labs" / "results" / "lab{number:02d}"
OUT.mkdir(parents=True, exist_ok=True)
started = time.perf_counter()
'''


def main() -> None:
 manifest=[]
 for number,lab in LABS.items():
    original=next(SOURCE.glob(f"{number:02d}_*.md"))
    content=original.read_text(encoding="utf-8")
    body,_,references=content.rpartition("\nИсточники:")
    if not body:body=content
    # Stage-one drafts become a deeper canonical text in Module_theory itself.
    body=body.replace("Самого приложения Streamlit в текущем пакете нет: его реализация — итоговое задание студента.",
                      "Рабочий пример Streamlit находится в Labs/app.py; студент расширяет и защищает собственную версию.")
    body=body.replace("В комплекте нет предрассчитанного 1IEP и установщика Vina.",
                      "Подготовленные файлы и официальный выход 1IEP входят в Labs/datasets/docking; бинарник устанавливается отдельно.")
    body=body.replace("В текущей проверке пакета PySCF не запускался.",
                      "PySCF здесь остаётся дополнительным запуском; обязательный notebook выполняет собственный RHF/STO-3G для H2 и не выдаёт его за DFT.")
    # Normalize contextual relative references without pretending all old file paths are current.
    body=body.replace("В пакете `practice/`", "В пакете `Labs/`")
    body=body.replace("Stepik_course/practice/requirements.txt", "Labs/requirements.txt")
    body=body.replace("Stepik_course/practice/chemistry.py", "Labs/chemistry.py")
    body=body.replace("`practice/train_esol.py`", "`Labs/train_esol.py`")
    body=body.replace("`practice/requirements-ml.txt`", "`Labs/requirements.txt`")
    body=body.replace("`practice/esol_results/`", "`Labs/results/lab11/`")
    body=body.replace("`practice/`", "`Labs/`")
    body=body.replace("из `practice`", "из `Labs`")
    body=body.replace("В практикуме используется `practice/", "В практикуме используется `Labs/")
    notes=NOTES[number].replace("по сохранённым именам", "по сохранённым serial-идентификаторам")
    # Explanatory depth precedes the worked practice/summary, not vice versa.
    fourth=re.search(rf"^## {number}\.4\..*",body,re.M)
    practice_section=""
    if fourth:
        practice_section=body[fourth.start():].replace(f"## {number}.4.",f"## {number}.7.",1)
        body=body[:fourth.start()]
    for old,new in [(5,4),(6,5),(7,6)]:
        notes=notes.replace(f"## {number}.{old}.",f"## {number}.{new}.")
    ids=sorted(set(re.findall(r"B\d{2}",notes)))
    bibliography="\n".join(f"- **[{key}]** {BOOKS[key]}" for key in ids)
    lab_link=f"../Labs/guides/lab{number:02d}.md"
    notebook_link=f"../Labs/notebooks/lab{number:02d}.ipynb"
    bridge=f'''\n## {number}.8. Переходим к лабораторному столу

Теперь у нас есть объяснение метода и способ проверить его границы. В [лабораторной работе {number}]({lab_link}) вы выполните полный workflow: {lab['workflow'].lower()} Сначала запишите прогноз, затем откройте [рабочий Jupyter notebook]({notebook_link}). Все локальные пути практикума считаются относительно корня репозитория; для кода главы используется `Labs/`, а ранний `Stepik_course/practice/` сохранён как предыдущая редакция.

**Измеримый результат:** {lab['benchmark']} Ответы открывайте после самостоятельной попытки. Повторите одну задачу на новом вводе через неделю: воспроизведение знакомого числа не заменяет переноса навыка.

## Литература и происхождение дополнений

{bibliography}

Номера PDF-страниц в тексте относятся к локальным файлам, а не обязательно к печатной пагинации. Связь изданий, разделов, Markdown и визуальных оригиналов дана в [карте чтения](../Literature/READING_MAP.md). Текст написан заново; страницы книг не вставлены в публичный курс.

Техническая документация:{references}
'''
    target=ROOT/"Module_theory"/FILES[number]
    target.write_text(body+"\n\n"+notes+"\n\n"+practice_section+bridge,encoding="utf-8")
    steps="\n".join(f"{i}. {step}" for i,step in enumerate(lab['steps'],1))
    tasks="\n".join(f"{i}. {task}" for i,task in enumerate(lab['tasks'],1))
    answers="\n".join(f"{i}. {answer}" for i,answer in enumerate(lab['answers'],1))
    guide=f'''# Лабораторная работа {number}. {lab['title']}

**Привязка:** [глава {number}](../../Module_theory/{quote(FILES[number])}). **Режим:** локальный CPU; сначала выполненный пример, затем новая задача. **Автор и аффилиация:** владелец курса заполняет при публикации. **Ориентир времени:** 60–120 минут для большинства работ; для QSPR и докинга дополнительно учитывайте запуск и разбор.

## Сущность и назначение

{lab['purpose']} Работа проверяет не только исполнение кода, но и допустимость вывода. До запуска сформулируйте ожидаемый результат и один случай, в котором алгоритму нельзя доверять.

## Данные и постановка кейса

{lab['data']} Полное происхождение, единицы, тип данных и ограничения находятся в [паспорте datasets](../datasets/README.md). Искусственные значения не смешиваются с реальными измерениями. Каждый вход сохраняется с идентификатором и hash; генерируемые результаты записываются в `Labs/results/lab{number:02d}/`.

## Workflow

**{lab['workflow']}**

Разделите три этапа: проверка входа, применение метода и оценка результата. Успешный запуск не отменяет проверки химической формы, единиц, состояния модели и независимости сравнения.

## Guideline: пошаговый разбор

{steps}

Откройте [notebook](../notebooks/lab{number:02d}.ipynb) и выполните ячейки сверху вниз с чистым ядром. Первая ячейка находит корень репозитория, затем задаются DATA/OUT. Следующая содержит полный код данного кейса с проверками. Последняя сохраняет `benchmark.json`: параметры, артефакты и время расчётной части. Ошибка assert означает, что результат нужно исследовать; удалять проверку ради прохождения нельзя.

Вставки `# WHY` и объяснения в теории связывают вызовы с научным смыслом. Если основной алгоритм вынесен в общий модуль, прочитайте его исходник по ссылке из notebook: общий код нужен, чтобы CLI, ноутбук и приложение использовали одну политику.

## Benchmark и критерии приёмки

{lab['benchmark']}

Время измеряется на конкретном компьютере и не служит обещанием ускорения. Эталонные показатели проверенного запуска находятся в [сводном benchmark](../benchmarks/REPORT.md). Числа с плавающей точкой сравниваются с допуском, стохастические результаты — по явно указанным инвариантам. Наличие правильного ответа в книге не заменяет фактический запуск вашего кода.

## Тренировка и закрепление

{tasks}

**Сдача:** notebook после Restart & Run All, таблица/рисунок из OUT, три предложения «наблюдение — ограничение — следующее действие». Не сдавайте только скриншот зелёной ячейки. Через 7 дней выполните первое упражнение на новом вводе без копирования ответа.

## Оценка

10 баллов: 2 за вход и происхождение, 3 за корректный запуск и проверки, 3 за интерпретацию, 2 за самостоятельный перенос. Обязательны сохранение ошибочных записей там, где это предусмотрено, отсутствие выдачи прогнозов за измерения и явный режим фактического исполнения тяжёлого инструмента.

Ответы и ход рассуждения: [ключ к работе {number}](../solutions/lab{number:02d}.md). Для первой самостоятельной попытки сначала закройте ключ.
'''
    (ROOT/f"Labs/guides/lab{number:02d}.md").write_text(guide,encoding="utf-8")
    solution=f'''# Ответы к лабораторной работе {number}: {lab['title']}

## Контрольный результат

{lab['benchmark']}

## Ответы на задания

{answers}

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
{lab['code']}
```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
'''
    (ROOT/f"Labs/solutions/lab{number:02d}.md").write_text(solution,encoding="utf-8")
    notebook=nbf.v4.new_notebook()
    notebook.metadata={"kernelspec":{"name":"python3","display_name":"Python 3","language":"python"},
                       "language_info":{"name":"python"}}
    notebook.cells=[
      nbf.v4.new_markdown_cell(f"# ЛР {number}. {lab['title']}\n\n**Сущность:** {lab['purpose']}\n\n**Данные:** {lab['data']}\n\n**Workflow:** {lab['workflow']}\n\nПеред запуском прочитайте [guideline](../guides/lab{number:02d}.md) и [теорию](../../Module_theory/{quote(FILES[number])})."),
      nbf.v4.new_markdown_cell("## 1. Прогноз\n\nЗапишите ожидаемое поведение и отрицательный контроль. Какое изменение входа должно изменить результат, а какое — сохранить?"),
      nbf.v4.new_code_cell(bootstrap(number)),
      nbf.v4.new_markdown_cell("## 2. Разбор и исполнение\n\n"+steps+"\n\nОжидаемое: "+lab['benchmark']),
      nbf.v4.new_code_cell(lab['code']),
      nbf.v4.new_markdown_cell("## 3. Проверяемая запись запуска\n\nBenchmark фиксирует этот запуск. Время включает расчёт и создание артефактов, но не установку среды; это не сравнительный рейтинг оборудования."),
      nbf.v4.new_code_cell('''elapsed = time.perf_counter()-started
run_record = {"lab": '''+str(number)+''', "calculation_wall_seconds": elapsed, "result": artifact}
(OUT/"benchmark.json").write_text(json.dumps(run_record,ensure_ascii=False,indent=2),encoding="utf-8")
print("Запуск сохранён:",OUT/"benchmark.json")
'''),
      nbf.v4.new_markdown_cell("## 4. Самостоятельная тренировка\n\n"+tasks+f"\n\n[Ответы после попытки](../solutions/lab{number:02d}.md). Вернитесь к первому заданию через неделю."),
      nbf.v4.new_markdown_cell("## 5. Ваш научный вывод\n\n1. Какой результат получен?\n2. Какой вывод из него пока не следует?\n3. Какой следующий эксперимент или контроль нужен?\n\nСохраните свой вариант notebook отдельно; исходный пример должен остаться воспроизводимым.")]
    notebook_path=ROOT/f"Labs/notebooks/lab{number:02d}.ipynb"
    if notebook_path.exists():
        prior=nbf.read(notebook_path,as_version=4)
        for cell,old in zip(notebook.cells,prior.cells):
            if cell.cell_type==old.cell_type=="code" and cell.source==old.source:
                cell.outputs=old.outputs
                cell.execution_count=old.execution_count
    nbf.write(notebook,notebook_path)
    manifest.append({"module":number,"theory":str(target.relative_to(ROOT)).replace('\\','/'),
                     "lab":f"Labs/guides/lab{number:02d}.md","notebook":f"Labs/notebooks/lab{number:02d}.ipynb",
                     "solutions":f"Labs/solutions/lab{number:02d}.md","title":lab['title']})
 (ROOT/"course-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
 from build_paired_labs import build as build_pairs
 build_pairs()
 print("Built",len(manifest),"theory chapters and paired laboratory notebooks")


if __name__=="__main__":main()
