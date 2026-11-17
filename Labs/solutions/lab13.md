# Ключ преподавателя: модуль 13

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M13-C1. Новый эфир вместо обучающего примера

Полученные кислота и спирт — учебные предшественники, а не валидированный препаративный протокол.


```python
case_input = {'smiles': 'CCOC(C)=O'}
from rdkit import Chem
from rdkit.Chem import rdChemReactions
r=rdChemReactions.ReactionFromSmarts('[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH:3].[OH][C:4]');p=r.RunReactants((Chem.MolFromSmiles(case_input['smiles']),));names=[]
for m in p[0]:
 Chem.SanitizeMol(m)
 for a in m.GetAtoms():a.SetAtomMapNum(0)
 names.append(Chem.MolToSmiles(m))
answer={'precursors':sorted(names)}
```


Ожидаемый численный контракт: `{"precursors": ["CC(=O)O", "CCO"]}`.


## M13-C2. Более дорогой вход — меньшая приведённая цена?

Сравнение условно: нельзя выдавать assumed_cost за актуальный прайс-лист.


```python
case_input = {'A': {'yields': [0.8, 0.7], 'cost': 600}, 'B': {'yields': [0.95, 0.9], 'cost': 750}}
ys=[math.prod(case_input[k]['yields']) for k in ['A','B']];answer={'yields':ys,'normalized_costs':[case_input[k]['cost']/y for k,y in zip(['A','B'],ys)]}
```


Ожидаемый численный контракт: `{"yields": [0.56, 0.855], "normalized_costs": [1071.4285714285713, 877.1929824561404]}`.


## M13-C3. Шаблон не сработал на амиде

Отсутствие совпадения одного правила не доказывает несинтезируемость.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
