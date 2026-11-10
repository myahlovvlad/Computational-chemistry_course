# Ответы к лабораторной работе 14: Передаваемый лабораторный конвейер

## Контрольный результат

CLI и прямой вызов сохраняют 12 строк и hash; отсутствующий столбец/повторный ID отклоняются; Streamlit — тот же pipeline.

## Ответы на задания

1. ID должен быть уникальным: иначе теряется связь строки и результата.
2. Нужны зависимости, относительные пути, исходные данные и ядро выбранной среды.
3. Параметр должен присутствовать в контракте и паспорте; результаты старого ввода/политики не смешивают с новыми.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from pipeline import process_csv
import subprocess
data=(DATA/"molecules.csv").read_bytes()
rows,passport=process_csv(data)
assert len(rows)==12
assert sum(row["status"]=="invalid" for row in rows)==2
for bad in [b"id,wrong\nX,CCO\n",b"id,smiles\nX,CCO\nX,CCN\n"]:
    try: process_csv(bad)
    except ValueError: continue
    raise AssertionError("Неверный контракт принят")
process=subprocess.run([sys.executable,str(ROOT/"Labs/pipeline.py"),str(DATA/"molecules.csv"),"--out",str(OUT/"cli")],capture_output=True,text=True,check=True)
loaded=json.loads((OUT/"cli/report.json").read_text(encoding="utf-8"))
assert loaded["passport"]["input_sha256"]==passport["input_sha256"]
assert len(loaded["rows"])==12
display(pd.DataFrame(rows))
print("Интерфейс: python -m streamlit run Labs/app.py")
artifact=passport

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
