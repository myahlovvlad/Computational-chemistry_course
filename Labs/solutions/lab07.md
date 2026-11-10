# Ответы к лабораторной работе 7: Кураторство активности и происхождение данных

## Контрольный результат

Включены R01/R02 с pIC50=7; в журнале все 8 строк; остальные причины различимы.

## Ответы на задания

1. Для R03 pIC50<5; точечной регрессии в данном задании строка не подходит.
2. Разные величины требуют модели связи и условий, не только одинаковых единиц.
3. Нужны ограниченные повторы, проверка HTTP/schema и сохранение URL, параметров, даты и hash.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import curate_activity
import hashlib
with (DATA/"activities.csv").open(encoding="utf-8") as handle:
    records=[curate_activity(row) for row in csv.DictReader(handle)]
table=pd.DataFrame(records);display(table)
included=[r for r in records if r["status"]=="included"]
assert [r["record_id"] for r in included]==["R01","R02"]
assert all(math.isclose(r["pIC50"],7) for r in included)
assert len(records)==8
table.to_csv(OUT/"activity_audit.csv",index=False)
esol=pd.read_csv(DATA/"esol.csv")
print("ESOL отдельно:",len(esol),"строк; measured target присутствует")
assert "measured log solubility in mols per litre" in esol
artifact={"included":2,"excluded":6,"esol_rows":len(esol),"esol_sha256":hashlib.sha256((DATA/"esol.csv").read_bytes()).hexdigest()}

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
