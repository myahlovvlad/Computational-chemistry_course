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
OUT=workspace('M09-L01','lab')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight')
    display(fig)
    plt.close(fig)
```

## Задание 1. Применение

Из первичного XML Abo Horan et al. извлеките все 16 записей параметров аторвастатина Table 1. Сохраните начальную форму, название параметра, pH, значение и единицу h⁻¹; пропуски оставьте None. Для начальной Ring-closed при pH 4.5 сравните параметры lactone loss и acid formation; вычислите отношение и времена ln(2)/k в часах. Условия: 0.15 M universal buffer, 0% CD, 23±1 °C. Это исследование водной офтальмологической композиции.

```python
task_1=None  # Ваш расчёт и аргумент; отсутствие решения не считается PASS.
```

## Задание 2. Критическая диагностика

Выведите аналитически для L⇌A общий показатель релаксации λ=k_open+k_close. Сравните его с двумя независимо опубликованными параметрами при pH 4.5. Объясните, почему десятикратное различие требует проверки отклика, плато, баланса и первичных данных, но без ошибок повторов не даёт статистического отвержения. Нельзя напрямую назначить опубликованные apparent rates прямой и обратной константами.

```python
task_2=None  # Ваш расчёт и аргумент; отсутствие решения не считается PASS.
```

## Задание 3. Исследовательское решение

Составьте протокол повторного измерения обеих форм: независимые приготовления, стандарты кислоты и лактона, quench с проверкой отсутствия превращения в автосэмплере, контроль pH/температуры, баланс органических эквивалентов и возможные продукты. Заранее определите условие отказа от замкнутой двухсостоянийной модели.

```python
task_3=None  # Ваш расчёт и аргумент; отсутствие решения не считается PASS.
```

## Расчётный контракт

Контракт проверяет лишь отдельные численные поля. Научное решение, диагностику и план проверяет преподаватель. Пустая работа имеет NOT_RUN. Поля: `reported_rate_ratio_pH4_5`, `lactone_loss_half_relaxation_h`, `acid_formation_half_relaxation_h`. Сохраните таблицы, единицы, рисунки и журнал решений; добавьте новую версию в досье, сохранив предыдущую.

```python
from research_checks import check
answer=None
print(check('M09-L01',answer))
```
