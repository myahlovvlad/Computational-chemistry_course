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
OUT=workspace('M10-L02','lab')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

## Задание 1

По Table 1 B постройте полную квадратичную модель удерживания лактона, кодируя (ACN−65)/5, (T−35)/5, (F−1)/.2. Проверьте 20 строк, 10 столбцов и полный ранг. Рассчитайте коэффициенты, остатки, SE и интервалы; явно назовите модель ошибок.
```python
task_1=None  # Ваш расчёт, диагностика и решение.
```

## Задание 2

Разложите SSE на pure error и lack of fit по одинаковым условиям. Вычислите степени свободы и LOF F/p. При leave-one-condition-out исключайте все повторы режима сразу. Сравните train RMSE и held-condition RMSE, leverage/Cook и Q–Q; не трактуйте p>.05 как валидацию. Повторные инъекции не заменяют независимые приготовления.
```python
task_2=None  # Ваш расчёт, диагностика и решение.
```

## Задание 3

Для условий внутри области плана рассчитайте условные mean CI и new-observation PI. Предложите подтверждающий режим с учётом семи откликов и необходимости измерить критические Rs/специфичность/количественный отклик. Не объявляйте оптимум по одному t_R готовым методом. Обоснуйте экспериментальную проверку и критерии пересмотра.
```python
task_3=None  # Ваш расчёт, диагностика и решение.
```

Расчётный контракт проверяет только `rows`, `columns`, `rank`, `pure_error_df`, `lack_of_fit_df`, `held_condition_RMSE_min`. Открытые научные решения оцениваются отдельно. Сохраните графики, таблицы, метод, условия и новую версию досье.

```python
from research_checks import check
answer=None
print(check('M10-L02',answer))
```
