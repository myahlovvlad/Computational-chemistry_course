# Ответы к лабораторной работе 8: Скрининг с журналом и контролями

## Контрольный результат

Катехол review, пустой ввод invalid; Z′=2/3; EF@50=5; журнал 12 строк.

## Ответы на задания

1. Z′=−1/3; контрольные распределения плохо разделены в данной оценке.
2. Прогнозы модели не являются истинной разметкой активности.
3. Нужны вероятность помехи, чувствительность контроля и цена потерянного полезного кандидата; одних цен закупки недостаточно.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import screen
from metrics import z_prime,enrichment
raw=pd.read_csv(DATA/"molecules.csv",keep_default_na=False)
records=[{"id":r.id,**screen(r.smiles)} for r in raw.itertuples()]
table=pd.DataFrame(records);display(table[["id","status","reason"]])
assert screen("Oc1ccccc1O")["status"]=="review"
assert screen("")["status"]=="invalid"
assert math.isclose(z_prime(100,10,5,5),2/3)
assert enrichment(1000,20,50,5)==5
table.to_csv(OUT/"decisions.csv",index=False)
artifact={"Z_prime":z_prime(100,10,5,5),"EF_at_50":enrichment(1000,20,50,5),"statuses":table.status.value_counts().to_dict()}

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
