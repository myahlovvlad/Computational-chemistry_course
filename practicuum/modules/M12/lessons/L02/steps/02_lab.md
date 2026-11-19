# Независимое исследование B. HMGCR: пригодность данных и область решения

Источник — полный закреплённый снимок ChEMBL/EMBL-EBI, CC BY-SA 3.0. Кураторские данные и статус отсутствующего обучения находятся в `target_qsar/hmgcr_*`. Это самостоятельная линия аторвастатина, отличная от A2A.

```python
from pathlib import Path
import sys,json,csv,hashlib,math
import numpy as np
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier,compound
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M12-L02','lab')
QDATA=DATA/'target_qsar'
manifest=json.loads((QDATA/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():
    assert hashlib.sha256((QDATA/name).read_bytes()).hexdigest()==digest,name
def read_json(name):return json.loads((QDATA/name).read_text(encoding='utf-8'))
def read_csv(name):
    with (QDATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Выделите формы аторвастатина кислота и лактон. Исключите из 57 структур HMGCR все каркасы обеих query-форм. Для оставшегося справочного набора рассчитайте ближайший Morgan Tanimoto каждой формы (radius 2, 2048, chirality). Это сходство со справочником, не с обученной моделью: HMGCR training NOT_RUN. Назовите исключённые строки и сохранившийся размер.
```python
task_1=None  # Ваш вычислительный и научный аргумент.
```

## Задание 2

Объясните, почему доверительный интервал QSAR A2A нельзя перенести на HMGCR/pIC50, а similarity не даёт интервала активности. Сравните identity, scaffold и document leakage; предложите негативный контроль утечки. Нельзя использовать строку самой query как подтверждение точности прогноза.
```python
task_2=None  # Ваш вычислительный и научный аргумент.
```

## Задание 3

Составьте решение go/no-go для эксперимента кислота/лактон: идентичность/чистота форм, превращения за время assay, контроль интерференции, стандарты и биохимические условия. Укажите, какие данные позволят обучить и внешне проверить модель и какую неопределённость current dataset не покрывает.
```python
task_3=None  # Ваш вычислительный и научный аргумент.
```

Численный контракт ограничен полями: `reference_n_after_query_scaffold_exclusion`, `acid_nearest_reference_Tanimoto`, `lactone_nearest_reference_Tanimoto`. Научный аргумент оценивается отдельно. Сохраните `answer.json`, исходные строки, графики и условия решения в новой версии досье.

```python
from research_checks import check
answer=None
print(check('M12-L02',answer))
```
