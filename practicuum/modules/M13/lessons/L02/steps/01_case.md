# Разбор A. Технологическое решение

Маршрут с лучшим общим выходом может быть хуже по стоимости, отходам или контролю стереохимии. На A разбираем явно вымышленную таблицу routes.csv; её числа не относятся к промышленному синтезу истрадефиллина. B применяет баланс к условным маршрутам и формулирует требования к реальным данным процесса.

Рассчитайте Y и C_eff двух учебных маршрутов. Проверьте сценарий ±.05 абсолютного выхода каждой стадии и изменение рейтинга. Явно отделите неизвестные объёмы растворителей, стоимость очистки и риск стереоизомеров. Для B сформулируйте материальный баланс без выдуманных промышленных чисел.

```python
from pathlib import Path
import sys,json,math
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,compound,esol,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=120,bbox_inches='tight')
    display(fig)
    plt.close(fig)
OUT=workspace('M13-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import csv
with (DATA/'routes.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
values=[]
for r in rows:
    a,b,c=map(float,[r['yield1'],r['yield2'],r['assumed_cost']]);total=a*b
    values.append({'route':r['route'],'overall_yield':total,'cost_per_equivalent':c/total,
                   'lower_yield_scenario':(a-.05)*(b-.05)})
display(values)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
fig,ax=plt.subplots();ax.bar([r['route'] for r in values],[r['cost_per_equivalent'] for r in values])
ax.set(xlabel='Fictional route',ylabel='Simulated cost / product equivalent');publish_plot(fig,'routes.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'simulation','routes':values,'PMI':'NOT_CALCULABLE: missing masses','real_drug_manufacturing':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M13-L02','A',result,ROOT,inputs=['practicuum/shared/data/routes.csv'])
print('Versioned evidence:',receipt)
```

Ни yield, ни cost surrogate не оценивают безопасность процесса. Научное решение включает область допустимых условий и запрос недостающих измерений. В финальном модуле соберём цепочку доказательств и укажем, что ещё не подтверждено.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
