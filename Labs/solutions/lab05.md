# Ключ преподавателя: модуль 5

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M05-C1. Проверить метрику без химической библиотеки

Размер объединения уже исключает двойной счёт общих битов.


```python
case_input = {'A': [1, 2, 3], 'B': [2, 3, 4], 'C': [7, 8]}
a,b,c=[set(case_input[k]) for k in ['A','B','C']]; f=lambda x,y:len(x&y)/len(x|y) if x|y else 1.;answer={'AB':f(a,b),'AC':f(a,c)}
```


Ожидаемый численный контракт: `{"AB": 0.5, "AC": 0}`.


## M05-C2. Хиральность исчезла из поиска

Сходство относится к заданным признакам, не к любому химическому свойству.


```python
case_input = {'smiles': ['C[C@H](O)C(=O)O', 'C[C@@H](O)C(=O)O'], 'radius': 2, 'fpSize': 2048}
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
m=[Chem.MolFromSmiles(s) for s in case_input['smiles']]; fs=[]
for chiral in [False,True]:
 g=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=chiral);fs.append([g.GetFingerprint(x) for x in m])
f=DataStructs.TanimotoSimilarity; a,b=fs[1];answer={'achiral_score':f(*fs[0]),'chiral_score_below_one':f(a,b)<1,'symmetric':math.isclose(f(a,b),f(b,a)),'self_score':f(a,a)}
```


Ожидаемый численный контракт: `{"achiral_score": 1, "chiral_score_below_one": true, "symmetric": true, "self_score": 1}`.


## M05-C3. Закупить разнообразные аналоги

Оценивается воспроизводимость выбора и соответствие цели, а не единственный оптимальный список.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
