# Разбор A. Разделение смеси

Одновременный UV-сигнал нескольких форм не позволяет независимо восстановить их концентрации. Разделение по времени удерживания добавляет информацию. На A мы строим условные два пика как контроль метода; для B используем экспериментальную Table 1 исследования аторвастатина. Нельзя выдавать эти экспериментальные строки за измерение ксантинов.

Сформируйте условные пики tR=3 и 4 min, σ=.15/.2 min; проверьте площадь и Rs. Затем прочитайте экспериментальный CSV B, выведите диапазоны удерживания и условия. HPLC-тренажёр доступен по web-training/trainers/hplc/index.html и явно разделяет таблицу и симуляцию. Не меняйте pH/колонку за пределами паспорта.

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
OUT=workspace('M10-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import numpy as np,csv
t=np.linspace(0,8,2000);mus=[3.,4.];sigmas=[.15,.2]
signals=[np.exp(-.5*((t-mu)/sigma)**2)/(sigma*np.sqrt(2*np.pi)) for mu,sigma in zip(mus,sigmas)]
Rs=2*(mus[1]-mus[0])/(4*sum(sigmas));print('Simulated Rs',Rs)
assert all(math.isclose(float(np.trapezoid(s,t)),1,rel_tol=1e-6) for s in signals)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
with (DATA/'atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
print('Published B rows',len(rows));display(rows[:3]);assert len(rows)==20
fig,ax=plt.subplots();ax.plot(t,sum(signals));ax.set(xlabel='Time / min',ylabel='Simulated detector response / a.u.');publish_plot(fig,'peaks.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'simulation','Rs':Rs,'B_experimental_table_rows':len(rows),'measured_B_Rs':'NOT_AVAILABLE: widths absent'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M10-L01','A',result,ROOT,inputs=['practicuum/shared/data/atorvastatin_hplc_table1.csv', 'practicuum/shared/data/hplc_provenance.json'])
print('Versioned evidence:',receipt)
```

Пики на рисунке делают пределы разрешения видимыми, но приписанная ширина не превращается в экспериментальное измерение. Для B нужны сырые хроматограммы, стандарт и проверка идентичности. Далее подберём условия и проверим ошибку прогноза.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
