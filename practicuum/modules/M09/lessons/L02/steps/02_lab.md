# Независимое исследование B. Опубликованная кинетика аторвастатина

Источник: [Abo Horan, Loftsson, Sigurdsson (2025), Table 1](https://doi.org/10.3390/pharmaceutics17070808), CC BY 4.0. Локальная проверенная копия `practicuum/shared/data/source-responses/statin_stability_verified.xml`. Числа характеризуют условия статьи; перенос на печёночную фармакокинетику не обоснован.

```python
from pathlib import Path
import sys,json,math,csv
import numpy as np
from scipy import stats
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M09-L02','lab')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight')
    display(fig)
    plt.close(fig)
```

## Задание 1. Применение

Используйте оба опубликованных apparent rate при pH 4.5 как альтернативные масштабы времени, не как пару microscopic rates. Для каждого постройте t=(0,0.25,0.5,1,2,4)·ln(2)/k в часах. Сравните крайние времена, необходимую стабильность проб и пределы длительности эксперимента. Не генерируйте наблюдения вместо отсутствующих исходных данных.

```python
task_1=None  # Ваш расчёт и аргумент; отсутствие решения не считается PASS.
```

## Задание 2. Критическая диагностика

Покажите структурную неидентифицируемость: одно λ даёт семейство (k_open,k_close)=(fλ,(1−f)λ), 0<f<1. Для безразмерных параметров u=k_open/λ₀, v=k_close/λ₀ рассчитайте ранг якобиана наблюдения z₁=u+v; затем добавьте равновесную долю z₂=u/(u+v) и сравните ранг. Это алгебраическая диагностика, не fit измерений. Объясните, почему полные совместные временные ряды могут нести больше информации, чем один опубликованный λ.

```python
task_2=None  # Ваш расчёт и аргумент; отсутствие решения не считается PASS.
```

## Задание 3. Исследовательское решение

Спроектируйте совместный fit концентраций обеих форм: моделируемые отклики с индивидуальными калибровками, plateau/baseline, пропуски, структура повторов и модель ошибок. Укажите профильное правдоподобие или bootstrap по независимым приготовлениям, проверку остатков и сравнение с моделью побочного разложения. Выберите новые точки и критерий прекращения экстраполяции. Без raw observations новый fit остаётся NOT_RUN.

```python
task_3=None  # Ваш расчёт и аргумент; отсутствие решения не считается PASS.
```

## Расчётный контракт

Контракт проверяет лишь отдельные численные поля. Научное решение, диагностику и план проверяет преподаватель. Пустая работа имеет NOT_RUN. Поля: `one_observable_rank`, `with_equilibrium_rank`, `slow_schedule_max_h`, `fast_schedule_max_h`. Сохраните таблицы, единицы, рисунки и журнал решений; добавьте новую версию в досье, сохранив предыдущую.

```python
from research_checks import check
answer=None
print(check('M09-L02',answer))
```
