# Разбор A. Проверяем запись истрадефиллина

Перед запуском прочитайте [постановку](../../../../../../theory/modules/M03/lessons/L01/01_problem.md), [модель](../../../../../../theory/modules/M03/lessons/L01/02_model.md) и [процедуру](../../../../../../theory/modules/M03/lessons/L01/03_workflow.md). Здесь повторим решение в исполняемых шагах. Отчёт строим из наблюдаемых данных, а не из имени молекулы.

```python
from pathlib import Path
import sys, json, math
import matplotlib.pyplot as plt
from IPython.display import display, Image

# Path.cwd() — текущая папка; parents позволяет найти корень при запуске из папки Notebook.
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import compound, workspace, write_json
from rdkit import Chem,rdBase
from rdkit.Chem import Descriptors,rdMolDescriptors
OUT=workspace('M03-L01','case')
record=compound('istradefylline')
display(record)
```

Словарь `record` хранит поля одной записи. Обращение по ключу `record['smiles']` выбирает конкретное представление. Передадим его химическому парсеру. Успешный синтаксический разбор не подтверждает, что реальный образец имеет этот состав.

```python
raw_smiles=record['smiles']
mol=Chem.MolFromSmiles(raw_smiles)
if mol is None:
    raise ValueError('Источник не удалось прочитать как молекулярный граф')

# isomericSmiles=True сохраняет доступную информацию о конфигурации.
isomeric=Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True)
connectivity=Chem.MolToSmiles(mol,canonical=True,isomericSmiles=False)
display({'raw':raw_smiles,'canonical_isomeric':isomeric,'connectivity_only':connectivity})
```

До следующей ячейки назовите, какой символ в строке может относиться к геометрии двойной связи. Затем проверим признаки самого графа. `for` перебирает связи; список сохраняет наблюдения, которые позднее можно проверить.

```python
bond_stereo=[]
for bond in mol.GetBonds():
    if bond.GetStereo()!=Chem.BondStereo.STEREONONE:
        bond_stereo.append({'atom_indices':[bond.GetBeginAtomIdx(),bond.GetEndAtomIdx()],
                            'stereo':str(bond.GetStereo())})

# Индекс атома — адрес в этом графе, не номер атома по химической номенклатуре.
summary={'cid':record['cid'],'formula':rdMolDescriptors.CalcMolFormula(mol),
         'molecular_weight_g_mol':Descriptors.MolWt(mol),
         'heavy_atoms':mol.GetNumHeavyAtoms(),'atoms_with_explicit_H':Chem.AddHs(mol).GetNumAtoms(),
         'double_bond_stereo':bond_stereo,'rdkit':rdBase.rdkitVersion}
display(summary)
```

Теперь проверим ловушку: упрощённая запись может утратить конфигурацию, сохранив массу и формулу. Поэтому совпадение двух чисел не заменяет выбранную политику идентичности.

```python
simplified=Chem.MolFromSmiles(connectivity)
assert simplified is not None
assert rdMolDescriptors.CalcMolFormula(simplified)==summary['formula']
assert math.isclose(Descriptors.MolWt(simplified),summary['molecular_weight_g_mol'],abs_tol=1e-9)
assert Chem.MolToSmiles(simplified,isomericSmiles=True)!=isomeric
write_json(OUT/'identity_passport.json',{'source':record,'computed':summary,
          'canonical_isomeric':isomeric,'connectivity_only':connectivity,
          'conclusion':'Масса и формула не доказывают сохранение всей стереохимии',
          'next_check':'Уточнить соответствие экспериментального образца выбранной конфигурации'})
print(OUT/'identity_passport.json')
```

Мы обнаружили потерю информации при определённом преобразовании. Не установили активность, чистоту или свойства неизвестного образца. В досье переносится паспорт и ограничение. На следующем уроке проверим, что меняется при работе с солевой и лактонной формами.
