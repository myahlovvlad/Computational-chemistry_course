# Независимое исследование B. Конформации кислоты, аниона и лактона

Данные — собственные вычисления целых форм аторвастатина, GFN2-xTB 6.8.0 / ALPB water gsolv, три seed × 100 initial structures для каждой формы. Calcium counterion исключён явно при выборе одного из двух одинаковых органических анионов; это не модель целого кальциевого комплекса. Новый full run и анализ frozen dataset различаются.

```python
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy import stats
from rdkit import Chem
from rdkit.Chem import rdMolAlign
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M06-L01','lab');C_DATA=DATA/'conformer_research'
manifest=json.loads((C_DATA/'bundle-manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():assert hashlib.sha256((C_DATA/name).read_bytes()).hexdigest()==digest,name
def read(state,name):return json.loads((C_DATA/state/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Проверьте отдельные whole-molecule наборы кислоты, органического карбоксилат-аниона и лактона. Назовите charge, formula, источник и изменение состава. Для каждой формы вычислите descriptive Spearman correlation MMFF94s vs GFN2/ALPB singlepoint energies на одинаковых принятых строках. Не смешивайте абсолютные энергетические нули разных методов/составов.
```python
task_1=None  # Ваш вычислительный, диагностический и исследовательский аргумент.
```

## Задание 2

Проверьте embedding/MMFF/SCC coverage, три seed, cap 24 и RMSD diversity после оптимизации. Сравните лучший singlepoint каждого seed и изменение энергии при переоптимизации. Почему seed plateau, малый RMSD или положительные Hessian трёх структур не доказывают полноту всех low-energy состояний? Разберите возможную потерю basins при предварительном energy window.
```python
task_2=None  # Ваш вычислительный, диагностический и исследовательский аргумент.
```

## Задание 3

Заранее выберите альтернативный sampling design для одной формы B и повторите ресурсный CLI-маршрут в новой директории; при отсутствии ресурсов честно выполните frozen-result audit. Обоснуйте seeds, coverage/diversity и критерий остановки; сохраните полный source/protocol. Новые данные не выдавайте за продолжение другого протокола.
```python
task_3=None  # Ваш вычислительный, диагностический и исследовательский аргумент.
```

Численный контракт относится к закреплённым данным и проверяет лишь `atorvastatin_descriptive_rank_correlation`, `atorvastatin_anion_descriptive_rank_correlation`, `atorvastatin_lactone_descriptive_rank_correlation`. Новый авторский протокол оценивается по его собственным входам/доказательствам; расхождение с frozen result не исправляется подгонкой. Открытый научный аргумент оценивается отдельно. Сохраните новую версию досье.

```python
from research_checks import check
answer=None
print(check('M06-L01',answer))
```
