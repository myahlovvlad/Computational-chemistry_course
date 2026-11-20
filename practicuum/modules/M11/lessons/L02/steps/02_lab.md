# Независимое исследование B. Аторвастатин/HMGCR: вход, gate и валидация

Источники: [RCSB PDB 1HWK](https://www.rcsb.org/structure/1HWK), исходный кристаллический карбоксилат аторвастатина (charge −1). Координаты PDB CC0, результаты подготовки и неудача сохранены; этот карман не объявлен готовым к docking.

```python
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from rdkit import Chem
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M11-L02','lab');D=DATA/'target_docking'
manifest=json.loads((D/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():
    assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest,name
def read_json(name):return json.loads((D/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

Перед вами решение о допуске входа. Сначала установите, сохранился ли смысл исходного комплекса после подготовки; затем решайте, обоснован ли новый дорогостоящий поиск. Для каждого численного gate поясните, какую ошибку он должен обнаруживать и почему запуск следует приостановить при его нарушении. Объявленные пороги относятся к этому протоколу подготовки.

## Задание 1

Из HMGCR repair audit извлеките максимальное смещение исходных pocket-heavy atoms и ближайший новый heavy atom. Сравните со строгим заранее заданным gate 0.05 Å для смещения и 6 Å для новых атомов, требующих review. Сформируйте машиночитаемый вывод: подготовка BLOCKED, docking NOT_RUN. Не создавайте фиктивные poses/scores.
```python
task_1=None  # Ваш расчёт, решение и независимая проверка.
```

## Задание 2

На примере A2A разделите sampling и ranking, top-1 и best-by-native-RMSD, алгоритмический и научный статус. Объясните, почему выбор одного удачного seed или постфактум правильной позы создаёт смещение. Для B обоснуйте, почему этот A2A результат не заменяет target-specific redocking HMGCR.
```python
task_2=None  # Ваш расчёт, решение и независимая проверка.
```

## Задание 3

Спроектируйте новый HMGCR redocking после научно обоснованной подготовки: независимые ligand starts, заранее заданные search seeds/критерии, symmetry-aware receptor-frame RMSD, negative translation control, сравнение cofactors/protonation и внешний комплекс. Укажите какие наблюдения разрешат запуск и какие потребуют отказа. До исправления входа score и affinity остаются NOT_RUN.
```python
task_3=None  # Ваш расчёт, решение и независимая проверка.
```

Расчётный контракт ограничен полями: `max_original_pocket_displacement_A`, `nearest_new_heavy_atom_A`, `preparation_accepted`. Качество структурного решения оценивает преподаватель. Сохраните анализ, координатные соответствия и план в новой версии досье.

```python
from research_checks import check
answer=None
print(check('M11-L02',answer))
```
