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
OUT=workspace('M06-L02','lab');C_DATA=DATA/'conformer_research'
manifest=json.loads((C_DATA/'bundle-manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():assert hashlib.sha256((C_DATA/name).read_bytes()).hexdigest()==digest,name
def read(state,name):return json.loads((C_DATA/state/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Для трёх Hessian-проверенных конформеров кислоты вычислите минимальную внутреннюю частоту, число внутренних modes и restricted weights при 298.15 K. Сопоставьте electronic/ALPB и native thermochemistry варианты. Проверьте spin/valence-electron consistency, сохраняя отдельную модель каждого химического состояния.
```python
task_1=None  # Ваш вычислительный, диагностический и исследовательский аргумент.
```

## Задание 2

Покажите, какие пропущенные entropy/degeneracy/states сведения запрещают полный population claim. Почему нельзя непосредственно сравнить total energies кислоты, аниона и лактона для вывода об их долях? Запишите сбалансированные процессы, необходимые chemical potentials и standard states; не подменяйте их сортировкой трёх абсолютных чисел.
```python
task_2=None  # Ваш вычислительный, диагностический и исследовательский аргумент.
```

## Задание 3

Выберите дополнительный conformer/Hessian/numerical/DFT контроль и независимое наблюдение B. Обоснуйте treatment low modes, cutoff/solvent sensitivity и критерий отказа. При негативной mode/identity проверке сохраните FAIL; не удаляйте неудобную структуру и не ослабляйте критерий после результата.
```python
task_3=None  # Ваш вычислительный, диагностический и исследовательский аргумент.
```

Численный контракт относится к закреплённым данным и проверяет лишь `acid_minimum_internal_frequency_cm1`, `acid_internal_mode_count`, `restricted_conformer_count`, `complete_population_claim_allowed`. Новый авторский протокол оценивается по его собственным входам/доказательствам; расхождение с frozen result не исправляется подгонкой. Открытый научный аргумент оценивается отдельно. Сохраните новую версию досье.

```python
from research_checks import check
answer=None
print(check('M06-L02',answer))
```
