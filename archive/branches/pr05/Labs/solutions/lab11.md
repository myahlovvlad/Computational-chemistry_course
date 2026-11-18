# Ключ преподавателя: модуль 11

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M11-C1. Выбрать ошибку, а не красивое R²

Ошибка имеет единицы target; R² и MAE описывают разные аспекты.


```python
case_input = {'y': [-3, -2, -1], 'A': [-2.5, -2.5, -1], 'B': [-2, -2, -2]}
y=np.array(case_input['y']);answer={'MAE_A':float(np.abs(y-case_input['A']).mean()),'MAE_B':float(np.abs(y-case_input['B']).mean()),'units':'logS'}
```


Ожидаемый численный контракт: `{"MAE_A": 0.3333333333333333, "MAE_B": 0.6666666666666666, "units": "logS"}`.


## M11-C2. Сериализации протекли через split

Identity-группировка устраняет этот вид утечки; каркасная и временная зависимость остаются отдельными вопросами.


```python
case_input = {'smiles': ['CCO', 'OCC', 'CCN', 'NCC'], 'train': [0, 2], 'test': [1, 3]}
from rdkit import Chem
from sklearn.model_selection import GroupShuffleSplit
g=[Chem.MolToSmiles(Chem.MolFromSmiles(s),isomericSmiles=True) for s in case_input['smiles']]; overlap=sorted({g[i] for i in case_input['train']}&{g[i] for i in case_input['test']});tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.5,random_state=42).split(np.zeros((4,1)),groups=g));answer={'leaked_identities':overlap,'group_split_has_overlap':bool({g[i] for i in tr}&{g[i] for i in te})}
```


Ожидаемый численный контракт: `{"leaked_identities": ["CCN", "CCO"], "group_split_has_overlap": false}`.


## M11-C3. Пять крупнейших ошибок ESOL

Рубрика требует сохранённые predictions, baseline и ограничения применимости; хорошее число не является оценкой переноса.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
