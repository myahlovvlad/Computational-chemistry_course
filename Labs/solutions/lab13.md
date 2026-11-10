# Ответы к лабораторной работе 13: Шаблонный ретросинтез и выбор маршрута

## Контрольный результат

Продукты метилацетата: уксусная кислота и метанол; выходы A=0,56/B=0,855; приведённые затраты A≈1071,43/B≈877,19 при явно заданной модели.

## Ответы на задания

1. Кислота остаётся уксусной, спирт — этанол.
2. Совместимость групп, селективность, выделение/очистка и условия требуют источников и опыта.
3. SA Score — структурная эвристика без поставщика, даты, масштаба и проверенного синтеза.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from rdkit import Chem
from rdkit.Chem import rdChemReactions
reaction=rdChemReactions.ReactionFromSmarts("[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH:3].[OH][C:4]")
products=reaction.RunReactants((Chem.MolFromSmiles("COC(C)=O"),))
assert products
names=[]
for mol in products[0]:
    Chem.SanitizeMol(mol)
    for atom in mol.GetAtoms(): atom.SetAtomMapNum(0)
    names.append(Chem.MolToSmiles(mol))
print("Учебные предшественники:",names)
assert set(names)=={"CC(=O)O","CO"}
routes=pd.read_csv(DATA/"routes.csv")
routes["overall_yield"]=routes.yield1*routes.yield2
routes["normalized_cost"]=routes.assumed_cost/routes.overall_yield
display(routes)
assert np.allclose(routes.overall_yield,[0.56,0.855])
assert routes.loc[1,"normalized_cost"]<routes.loc[0,"normalized_cost"]
routes.to_csv(OUT/"route_comparison.csv",index=False)
artifact={"precursors":names,"routes":routes.to_dict(orient="records"),"scope":"one ester template, not general AI retrosynthesis"}

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
