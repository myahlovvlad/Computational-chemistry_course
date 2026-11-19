# Разбор A. UV–Vis и ИК

Архив TDDFT содержит дискретные переходы, тогда как прибор показывает полосы. Гипотеза: выбранное уширение меняет максимум условной кривой без изменения самих электронных переходов. На A используем истрадефиллин, на B — отдельный архив аторвастатина. Ни одна кривая здесь не является измеренным молярным коэффициентом поглощения.

Считайте шесть переходов, проверьте преобразование энергии и длины волны. Суммируйте нормированные гауссианы для σ=0.05 и 0.15 eV на достаточно широкой сетке. Сравните численный интеграл с Σf. Найдите максимум каждой кривой, отдельно подпишите transition energy и envelope maximum.

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
OUT=workspace('M08-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import numpy as np
q=json.loads((DATA/'quantum/istradefylline/result.json').read_text(encoding='utf-8'))
t=q['transitions'];grid=np.linspace(.1,max(r['energy_eV'] for r in t)+2,3000)
def envelope(transitions,sigma):
    return sum(r['oscillator_strength']*np.exp(-.5*((grid-r['energy_eV'])/sigma)**2)/(sigma*np.sqrt(2*np.pi)) for r in transitions)
strength=sum(r['oscillator_strength'] for r in t)
print('Sum oscillator strengths',strength)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
fig,ax=plt.subplots();areas={}
for sigma in [.05,.15]:
    signal=envelope(t,sigma);area=float(np.trapezoid(signal,grid));areas[str(sigma)]=area
    assert math.isclose(area,strength,rel_tol=1e-4)
    ax.plot(grid,signal,label=f'sigma={sigma} eV');print(sigma,'max at',grid[np.argmax(signal)],'eV')
ax.set(xlabel='Energy / eV',ylabel='Simulated oscillator density / eV^-1');ax.legend();publish_plot(fig,'uv.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'sum_f':strength,'integrals':areas,'kind':'simulation','absolute_absorbance':'NOT_RUN','compound':'istradefylline'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M08-L01','A',result,ROOT,inputs=['practicuum/shared/data/quantum/istradefylline/result.json', 'practicuum/shared/data/quantum/atorvastatin/result.json'])
print('Versioned evidence:',receipt)
```

Площадь и положение максимума служат контролями кода, но не подтверждают спектр в растворе. ИК-переходы требуют колебательной модели; из этих TDDFT-данных ИК не получается. Дальше рассмотрим прибор и специфичность.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
