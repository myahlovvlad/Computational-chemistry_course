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
OUT=workspace('M12-L01','lab')
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

Сначала нужно решить, к какой задаче относятся наблюдения и какой объём независимой информации в них есть. Число строк исходной выгрузки не равно числу пригодных структур: ограничения endpoint, повторы и курация меняют набор. Ваша работа должна позволить коллеге восстановить этот переход и понять, на каком основании обучение допускается или откладывается.

## Задание 1

Проверьте HMGCR CHEMBL402, organism, endpoint IC50, единицы и точное отношение в сохранённой карточке. Сопоставьте 318 исходных записей, 91 допустимое измерение и 57 уникальных структур. По SMILES пересчитайте число каркасов тем же правилом, что в A. Медиана повторов не устраняет assay bias; pIC50 нельзя объявить pKi.
```python
task_1=None  # Ваш вычислительный и научный аргумент.
```

## Задание 2

Оцените применимость заранее заданного протокола: минимум 80 соединений и 20 каркасов для nested 5×3 + calibration + test. Объясните, почему 57 структур и 28 каркасов дают BLOCKED по числу соединений. Не понижайте порог и не заменяйте его случайным split ради метрики. Укажите, какие выводы допустимы без обучения.
```python
task_2=None  # Ваш вычислительный и научный аргумент.
```

## Задание 3

Предложите расширение однородного набора HMGCR: независимые документы/даты и внешние assay, курация форм, censoring, duplicate flags и диапазон активности. Сравните сбор новых данных с заранее обоснованной low-data моделью как отдельным протоколом. Укажите требования к power/learning curve и критерий отказа.
```python
task_3=None  # Ваш вычислительный и научный аргумент.
```

Численный контракт ограничен полями: `curated_HMGCR_n`, `HMGCR_scaffolds`, `training_eligible`. Научный аргумент оценивается отдельно. Сохраните `answer.json`, исходные строки, графики и условия решения в новой версии досье.

```python
from research_checks import check
answer=None
print(check('M12-L01',answer))
```
