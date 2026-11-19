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
OUT=workspace('M04-L01','lab');S_DATA=DATA/'istradefylline_solubility'
def read_csv(name):
    with (S_DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

Из Table 11 Abo Horan et al. (DOI 10.3390/pharmaceutics17070808, CC BY 4.0) извлеките S0, K1:1, CE и тип phase-solubility для двух аторвастатин/CD систем при pH 6.9. Сохраните опубликованную молярную основу. Рассчитайте K·S0 и сравните с CE; не объявляйте baseline 0.000270 M intrinsic neutral-acid solubility.
```python
task_1=None  # Ваш расчёт, диагностический вывод и план.
```

## Задание 2

Разберите разницу chemical form, equilibrium/apparent solubility, total vs free concentration и acid/lactone interconversion. Почему K/CE округление и отсутствие raw slope uncertainty не позволяют статистически отвергнуть или подтвердить согласованность? Какие условия и определения молярной основы кальциевой соли нужно проверить до перевода mg/mL?
```python
task_2=None  # Ваш расчёт, диагностический вывод и план.
```

## Задание 3

Предложите pH-solubility эксперимент кислоты/карбоксилата/лактона: твёрдая фаза, время равновесия, температура/ionic strength, независимые приготовления, отделение частиц, HPLC-калибровка и LOQ, стабильность форм. Определите, какие данные разрешат оценку intrinsic S0/pKa и какие потребуют отказа.
```python
task_3=None  # Ваш расчёт, диагностический вывод и план.
```

Контракт ограничен полями: `reported_baseline_mol_L`, `HPbetaCD_K_times_baseline`, `gammaCD_K_times_baseline`. Преподаватель отдельно оценивает открытый аргумент. Сохраните единицы, источник, неопределённость и решение в новой версии досье.

```python
from research_checks import check
answer=None
print(check('M04-L01',answer))
```
