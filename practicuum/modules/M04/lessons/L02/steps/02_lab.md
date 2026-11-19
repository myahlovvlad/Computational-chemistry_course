# Независимое исследование B. Аторвастатин: растворимость и комплексирование

[Первичный источник, Table 11](https://doi.org/10.3390/pharmaceutics17070808), CC BY 4.0. Локальная проверенная копия `source-responses/statin_stability_verified.xml`. Условия и молярная основа сохраняются; клинические свойства из этих таблиц не выводятся.

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
OUT=workspace('M04-L02','lab');S_DATA=DATA/'istradefylline_solubility'
def read_csv(name):
    with (S_DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Для двух опубликованных K и baseline S0 рассчитайте условный наклон линейной 1:1 модели slope=K·S0/(1+K·S0). Независимо пересчитайте наклон из опубликованного CE как CE/(1+CE). Сравните значения и единицы; обе оценки производны от опубликованных параметров, не являются новым экспериментальным fit.
```python
task_1=None  # Ваш расчёт, диагностический вывод и план.
```

## Задание 2

Объясните, почему тип A_N для HPβCD ограничивает линейную 1:1 интерпретацию, а A_L сам по себе не доказывает стехиометрию. Разберите чувствительность K к выбору baseline и наличию нескольких форм. Сырые phase-solubility точки/ошибки здесь отсутствуют: новые интервалы K не выдумываются.
```python
task_2=None  # Ваш расчёт, диагностический вывод и план.
```

## Задание 3

Выберите дальнейшую formulation/solvent стратегию B с контролями растворимости, химической стабильности, комплексирования и высвобождения. Укажите raw данные для совместной модели и независимый опыт. Офтальмологическая композиция источника не является проверкой печёночной доставки или биодоступности B.
```python
task_3=None  # Ваш расчёт, диагностический вывод и план.
```

Контракт ограничен полями: `HPbetaCD_conditional_slope`, `gammaCD_conditional_slope`, `HPbetaCD_linear_model_accepted_without_review`. Преподаватель отдельно оценивает открытый аргумент. Сохраните единицы, источник, неопределённость и решение в новой версии досье.

```python
from research_checks import check
answer=None
print(check('M04-L02',answer))
```
