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

Сначала прочитаем опубликованные выходы двух режимов синтеза. Для каждого продукта вычислим разность в процентных пунктах: это сравнение строк источника, а не оценка универсального преимущества нагревания. До запуска перечислите условия, которые должны быть сопоставимы для содержательного вывода.

В таблице я вижу выходы двух режимов для определённых продуктов и хочу понять, какое сравнение действительно разрешено источником. Поэтому сохраняю продукт и условия в той же строке, а разность считаю в процентных пунктах. Если условные выходы 60% и 80%, разность составляет 20 пунктов, тогда как относительное увеличение к первому — около 33%. Подмена этих двух величин изменила бы смысл вывода.

После сравнения опубликованных строк переходим к другой операции — генерации продукта по шаблону графа. Я отделяю её заранее, чтобы не получить ложную цепочку «шаблон дал структуру, значит опубликованный синтез её подтверждает». Каждое ребро будущего маршрута должно иметь собственное основание.

```python
import csv
with (DATA/'xanthine_synthesis_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
display(rows)
differences=[float(r['microwave_yield_percent'])-float(r['reflux_yield_percent']) for r in rows]
print('Yield differences / percentage points:',differences)
```

Следующий блок — отдельное упражнение с формальным преобразованием графа модельного сложного эфира. Он показывает, как reaction SMARTS порождает кандидатные структуры; это не механизм и не подтверждённый маршрут получения изучаемого ксантина. Проверка графа продукта не заменяет проверку реагентов, условий и экспериментального выхода.

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

В досье нужно различить опубликованное сравнение выходов и формально сгенерированные структуры. Не объединяйте их в один якобы выполненный синтез; для B потребуется отдельный источник стадий и стереохимии.

```python
result={'kind':'calculated','published_yield_differences_percentage_points':differences,
        'toy_template_proposals':proposals,'B_route_experiment':'NOT_RUN','istradefylline_route':'not established by this table'}
```

Успешная санитизация продукта показывает приемлемость представления в правилах инструмента. Для синтетической стадии затем нужны стехиометрия, реагенты, условия, стереохимия и фактический выход. Шаблон превращения модельного сложного эфира оставляет эти вопросы открытыми, в том числе происхождение добавляемых атомов. Я передаю его как формальное предложение для проверки и не присваиваю ему выход из другой строки публикации.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M13-L01','A',result,ROOT,inputs=['practicuum/shared/data/xanthine_synthesis_table1.csv', 'practicuum/shared/data/xanthine_synthesis_source.json'])
print('Versioned evidence:',receipt)
```

Успех графового шаблона означает лишь соответствие локальному правилу. Независимое подтверждение требует источника, реагентов, условий и данных выделения. Следующий урок рассмотрит потери, стоимость и опасность сравнения маршрутов по одному выходу.

Какое свидетельство позволит превратить формальную схему в обоснованную синтетическую стадию? Укажите, что ещё неизвестно помимо графов реагента и продукта.
