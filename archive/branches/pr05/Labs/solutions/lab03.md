# Ключ преподавателя: модуль 3

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M03-C1. Соль поменяла порядок компонентов

Компоненты соли и ковалентные атомы требуют разных решений.


```python
case_input = {'smiles': ['CC(=O)[O-].[Na+]', '[Na+].CC(=O)[O-]', 'Brc1ccccc1']}
from chemistry import standardize,parse
p=[standardize(s).parent_smiles for s in case_input['smiles']]; answer={'same_parent':p[0]==p[1],'covalent_br_retained':any(a.GetSymbol()=='Br' for a in parse(p[2]).GetAtoms()),'rows':len(p)}
```


Ожидаемый численный контракт: `{"same_parent": true, "covalent_br_retained": true, "rows": 3}`.


## M03-C2. Не схлопнуть стереопару

Равенство представлений зависит от политики; стереоинформация здесь сохраняется.


```python
case_input = {'stereo': ['C[C@H](O)C(=O)O', 'C[C@@H](O)C(=O)O'], 'tautomers': ['O=c1cccc[nH]1', 'Oc1ccccn1']}
from chemistry import standardize
f=lambda s,t=False:standardize(s,t).parent_smiles; a,b=case_input['stereo']; x,y=case_input['tautomers']; answer={'stereo_distinct':f(a)!=f(b),'default_tautomers_distinct':f(x)!=f(y),'explicit_tautomers_equal':f(x,True)==f(y,True)}
```


Ожидаемый численный контракт: `{"stereo_distinct": true, "default_tautomers_distinct": true, "explicit_tautomers_equal": true}`.


## M03-C3. Можно ли усреднить растворимость соли и кислоты?

До проверки формы, pH, температуры и метода одинаковый parent не оправдывает усреднение.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
