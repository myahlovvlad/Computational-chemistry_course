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
OUT=workspace('M11-L01','lab');D=DATA/'target_docking'
manifest=json.loads((D/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():
    assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest,name
def read_json(name):return json.loads((D/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Проверьте структуру 1HWK и кристаллический reference SDF B: полный граф/стереохимию, число тяжёлых атомов, заряд −1 карбоксилата, отличие от нейтральной кислоты и лактона. По исходным protein coordinates найдите тяжёлые атомы/остатки в 6 Å и число участвующих цепей. Нельзя вырезать единственную цепь, если карман расположен на интерфейсе.
```python
task_1=None  # Ваш расчёт, решение и независимая проверка.
```

## Задание 2

Проверьте HMGCR gap/repair audit: где возник OXT, какие исходные атомы кармана сдвинулись, что означает искусственная терминальная группа у отсутствующего продолжения цепи? Отличайте внутренние backbone gaps от неразрешённых концов. Укажите необходимые sequence/structure и cofactor-проверки; ADP нельзя молча удалить или назначить произвольный заряд.
```python
task_2=None  # Ваш расчёт, решение и независимая проверка.
```

## Задание 3

Составьте обоснованный план рецептора: экспериментальная конструкция, assembly/цепи, отсутствующие фрагменты, termini/caps, cofactors, воды, protonation ensemble и чувствительность кармана. Предложите независимый кристаллический контроль и критерий допуска. Наличие автоматического PDB2PQR output не снимает BLOCKED.
```python
task_3=None  # Ваш расчёт, решение и независимая проверка.
```

Расчётный контракт ограничен полями: `ligand_heavy_atoms`, `ligand_formal_charge`, `pocket_chain_count`, `original_pocket_heavy_atoms`. Качество структурного решения оценивает преподаватель. Сохраните анализ, координатные соответствия и план в новой версии досье.

```python
from research_checks import check
answer=None
print(check('M11-L01',answer))
```
