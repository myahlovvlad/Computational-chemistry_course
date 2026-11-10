# Ответы к лабораторной работе 3: Идентичность, соли и таутомеры

## Контрольный результат

12 строк на выходе; M08/M09 invalid; M01=M02 и M03=M04 по parent; M10≠M11.

## Ответы на задания

1. Ковалентный Br должен сохраниться при parent-политике.
2. Порядок компонентов не определяет parent; split по точке некорректен.
3. Измерения относятся к физическим формам и условиям, которые parent-представление теряет.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import screen, standardize, parse
raw = pd.read_csv(DATA/"molecules.csv", keep_default_na=False)
records = [{"id": row.id, **screen(row.smiles)} for row in raw.itertuples()]
report = pd.DataFrame(records); display(report)
report.to_csv(OUT/"curated.csv", index=False)
by_id = {row["id"]:row for row in records}
assert len(records)==12 and sum(row["status"]=="invalid" for row in records)==2
assert by_id["M01"]["parent_smiles"]==by_id["M02"]["parent_smiles"]
assert by_id["M03"]["parent_smiles"]==by_id["M04"]["parent_smiles"]
assert "Cl" in by_id["M05"]["parent_smiles"]
assert by_id["M10"]["parent_smiles"]!=by_id["M11"]["parent_smiles"]
pair=["O=c1cccc[nH]1","Oc1ccccn1"]
assert standardize(pair[0]).parent_smiles != standardize(pair[1]).parent_smiles
assert standardize(pair[0],True).parent_smiles == standardize(pair[1],True).parent_smiles
artifact={"rows":len(records),"invalid":2,"policy":by_id["M01"]["policy"]}

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
