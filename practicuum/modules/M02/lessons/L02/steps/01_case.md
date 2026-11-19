# Разбор A. Python как инструмент исследования

Паспорт входа есть, но таблица после обработки стала короче. Были ли потеряны неправильные строки или научно важные наблюдения? Исследуем таблицу ксантинов, затем перенесём проверку на формы B. Гипотеза: явная схема и журнал отклонений делают преобразование проверяемым, в отличие от молчаливого dropna. Базовые конструкции Python здесь служат научной прослеживаемости.

Создайте записи расчёта для 1.0 mg вещества в 10.0 mL; массы берём из структурных карточек. Это моделируемая подготовка, не протокол реального раствора. Напишите функцию с проверками конечности и положительности. Добавьте контроль на нулевой объём, сохраните valid и rejected отдельно и проверьте повторное чтение JSON.

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
OUT=workspace('M02-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
def concentration(mass_mg,molar_mass,volume_ml):
    values=[mass_mg,molar_mass,volume_ml]
    if not all(math.isfinite(v) and v>0 for v in values):raise ValueError('Positive finite inputs required')
    return (mass_mg/1000)/molar_mass/(volume_ml/1000)
rows=[{'name':n,'c_mol_L':concentration(1,compound(n)['molecular_weight_g_mol'],10)} for n in ['caffeine','istradefylline']]
display(rows)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
try:concentration(1,194.19,0)
except ValueError as error:print('Rejected control:',str(error))
else:raise AssertionError('Zero volume was accepted')
fig,ax=plt.subplots();ax.bar([r['name'] for r in rows],[r['c_mol_L'] for r in rows]);ax.set_ylabel('Simulated c / mol L^-1')
publish_plot(fig,'concentrations.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
write_json(OUT/'table.json',rows)
assert json.loads((OUT/'table.json').read_text(encoding='utf-8'))==rows
result={'rows':rows,'kind':'simulation'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M02-L02','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Количество знаков после запятой в выводе не создаёт точность весов. Для B масса безводной кислоты и соли на этикетке имеет разный смысл. Следующий модуль отвечает, какая структура стоит за строкой и формулой.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
