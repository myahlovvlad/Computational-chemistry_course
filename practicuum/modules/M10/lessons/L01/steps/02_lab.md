# Независимое исследование B. Аторвастатин: разделение, моделирование и валидация

Источник: [Crevar-Sakač et al. (2013), Table 1](https://doi.org/10.3390/molecules18032469), CC BY 3.0. Полный числовой сигнал и ширины пиков отсутствуют; measured Rs не выдумывается.

```python
from pathlib import Path
import sys,json,csv,math
import numpy as np
from scipy import stats
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M10-L01','lab')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Проверьте 20 опубликованных строк B и сгруппируйте их по (ACN, temperature, flow). Посчитайте число уникальных условий и повторов центра. Для каждой строки рассчитайте разность удерживания лактона и p-ATO, найдите минимум/максимум с исходными row IDs и условиями. Различайте минуты B и секунды A.
```python
task_1=None  # Ваш расчёт, диагностика и решение.
```

## Задание 2

Объясните, почему эти разности и опубликованные symmetry factors не позволяют восстановить measured Rs без численных ширин пиков. Предложите, как проверять соответствие пиков стандартам, совместное элюирование и превращение кислота/лактон. Не приписывайте выдуманные ширины опубликованным опытам.
```python
task_2=None  # Ваш расчёт, диагностика и решение.
```

## Задание 3

Разработайте URS аналитического метода B: критические пары/примеси, pH и стабильность форм, blank/matrix/standard/spike, разрешение и количественный отклик, независимые приготовления и условия отказа. Назовите неполные данные и следующий измерительный опыт.
```python
task_3=None  # Ваш расчёт, диагностика и решение.
```

Расчётный контракт проверяет только `unique_conditions`, `minimum_retention_gap_min`, `maximum_retention_gap_min`. Открытые научные решения оцениваются отдельно. Сохраните графики, таблицы, метод, условия и новую версию досье.

```python
from research_checks import check
answer=None
print(check('M10-L01',answer))
```
