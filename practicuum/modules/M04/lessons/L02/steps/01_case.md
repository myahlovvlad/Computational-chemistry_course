# Разбор A. Среда и растворитель

Предложение выбрать растворитель только по logP оставляет неизвестными pH и форму. Для нейтральной кислоты B растворимость и доля нейтральной формы могут меняться в противоположных направлениях. На линии A оставляем нейтральный базовый контроль, а численную pH-модель изучаем на условной одноосновной кислоте. Её pKa не является измерением аторвастатина.

Используйте явно условные pKa=4.5 и S0=10^-5 mol/L. Постройте долю нейтральной формы и общую растворимость в диапазоне pH 2–8. Проверьте pH=pKa аналитически и измените pKa на ±0.5. Эта чувствительность показывает неопределённость параметра, а не доверительный интервал измерения.

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
OUT=workspace('M04-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import numpy as np
pH=np.linspace(2,8,121);pka=4.5;s0=1e-5
neutral=1/(1+10**(pH-pka));solubility=s0*(1+10**(pH-pka))
print({'at_pKa':{'neutral_fraction':.5,'solubility_mol_L':2*s0},'parameters':'simulation'})
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
fig,axes=plt.subplots(1,2,figsize=(9,3))
for delta in [-.5,0,.5]:
    axes[0].plot(pH,1/(1+10**(pH-(pka+delta))),label=f'pKa={pka+delta}')
    axes[1].semilogy(pH,s0*(1+10**(pH-(pka+delta))))
axes[0].set(xlabel='pH',ylabel='Neutral fraction');axes[0].legend()
axes[1].set(xlabel='pH',ylabel='Simulated total S / mol L^-1');publish_plot(fig,'ph.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'pKa_simulated':pka,'S0_simulated_mol_L':s0,'kind':'simulation','atorvastatin_parameter_measurement':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M04-L02','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Увеличение модельной растворимости не доказывает увеличение мембранного переноса. В B дополнительно нужны стабильность кислоты/лактона и состав среды. Дальше сравним структуры, чтобы выбирать информативные аналоги.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
