# Разбор A. Опубликованный маршрут

Прогноз свойства не отвечает, как получить вещество. Опубликованная циклизация 8-замещённых ксантинов показывает, что близкие схемы могут иметь разные выходы. Не выдаём эту работу за синтез истрадефиллина. Гипотеза: различение прямого эксперимента и обратного предложения предотвращает ложные маршруты. B должен сохранять стереохимию кислоты при разрыве на синтоны.

Прочитайте закреплённую Table 1 ксантинов и сравните reflux/microwave без подмены нулей пропусками. Затем выполните учебное SMARTS-расщепление простого метилового эфира; это контроль шаблона, не маршрут B. Для реального B составьте карту требуемых доказательств по стадиям, а не выдуманные yields.

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
OUT=workspace('M13-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import csv
with (DATA/'xanthine_synthesis_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
display(rows)
differences=[float(r['microwave_yield_percent'])-float(r['reflux_yield_percent']) for r in rows]
print('Yield differences / percentage points:',differences)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
from rdkit import Chem
from rdkit.Chem import rdChemReactions
reaction=rdChemReactions.ReactionFromSmarts('[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH].[O:3][C:4]')
products=reaction.RunReactants((Chem.MolFromSmiles('CC(=O)OC'),))
proposals=[]
for pair in products:
    for m in pair:Chem.SanitizeMol(m)
    proposals.append([Chem.MolToSmiles(m) for m in pair])
display(proposals);assert proposals
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'calculated','published_yield_differences_percentage_points':differences,
        'toy_template_proposals':proposals,'B_route_experiment':'NOT_RUN','istradefylline_route':'not established by this table'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M13-L01','A',result,ROOT,inputs=['practicuum/shared/data/xanthine_synthesis_table1.csv', 'practicuum/shared/data/xanthine_synthesis_source.json'])
print('Versioned evidence:',receipt)
```

Успех графового шаблона означает лишь соответствие локальному правилу. Независимое подтверждение требует источника, реагентов, условий и данных выделения. Следующий урок рассмотрит потери, стоимость и опасность сравнения маршрутов по одному выходу.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
