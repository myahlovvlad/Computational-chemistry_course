# Ответы к лабораторной работе 4: Осмысленные дескрипторы

## Контрольный результат

MW этанола 46,069±0,01; TPSA бензола 0; контрольный полиол нарушает HBD/HBA.

## Ответы на задания

1. MW>500, MolLogP>5, HBD>5, HBA>10; TPSA отдельно.
2. Масса и число тяжёлых атомов обычно связаны; причинный вывод из корреляции не следует.
3. LogD учитывает распределение всех форм при заданном pH; MolLogP не является его прямым измерением.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import standardize, descriptors
raw=pd.read_csv(DATA/"molecules.csv",keep_default_na=False)
table=[]
for row in raw.itertuples():
    try:
        parent=standardize(row.smiles).parent_smiles
    except ValueError:
        continue
    table.append({"id":row.id,"parent":parent,**descriptors(parent)})
features=pd.DataFrame(table); display(features)
features.to_csv(OUT/"features.csv",index=False)
assert math.isclose(descriptors("CCO")["MolWt"],46.069,abs_tol=0.01)
assert descriptors("c1ccccc1")["TPSA"]==0
polyol=descriptors("OC(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)CO")
assert polyol["HBD"]>5 and polyol["HBA"]>10 and polyol["ro5_violations"]==2
artifact={"valid_rows":len(features),"ethanol":descriptors("CCO"),"polyol":polyol}

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
