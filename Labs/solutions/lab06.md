# Ключ преподавателя: модуль 6

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M06-C1. Другой seed — другая гипотеза поиска

Сходящийся найденный минимум не является доказательством глобального минимума.


```python
case_input = {'smiles': 'CCCC', 'seed': 7}
from chemistry import optimize_conformer
r=optimize_conformer(case_input['smiles'],seed=case_input['seed']);answer={'has_converged':r['converged'],'finite_energy':math.isfinite(r['energy_kcal_mol']),'energy_unit':'kcal/mol'}
```


Ожидаемый численный контракт: `{"has_converged": true, "finite_energy": true, "energy_unit": "kcal/mol"}`.


## M06-C2. Торсион или поворот камеры?

Изменение внутреннего угла и жёсткий поворот всего объекта — разные преобразования.


```python
case_input = {'smiles': 'CCCC', 'atoms': [0, 1, 2, 3], 'target_degrees': 60}
from rdkit import Chem
from rdkit.Chem import AllChem,rdMolTransforms
m=Chem.AddHs(Chem.MolFromSmiles('CCCC'));p=AllChem.ETKDGv3();p.randomSeed=7;assert AllChem.EmbedMolecule(m,p)==0;c=m.GetConformer();d=rdMolTransforms.GetBondLength(c,1,2);rdMolTransforms.SetDihedralDeg(c,0,1,2,3,case_input['target_degrees']);answer={'angle_degrees':rdMolTransforms.GetDihedralDeg(c,0,1,2,3),'bond_length_preserved':math.isclose(d,rdMolTransforms.GetBondLength(c,1,2))}
```


Ожидаемый численный контракт: `{"angle_degrees": 60, "bond_length_preserved": true}`.


## M06-C3. Несошедшуюся геометрию назвали лучшей

Нужны единый состав/метод, сходимость и покрытие пространства стартов; низкого числа недостаточно.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
