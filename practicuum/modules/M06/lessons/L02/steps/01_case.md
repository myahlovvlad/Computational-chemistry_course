# Разбор A. Энергии и ограничения

Теперь есть несколько минимумов одной молекулы. Можно ли считать самый низкий единственной формой? Начнём с контролируемого двухуровневого примера, а затем проверим ансамбль A. Гипотеза: близкие по энергии состояния вносят вклад при конечной температуре. Для B небольшая ошибка разности энергий может поменять ранжирование.

На условных уровнях 0,1,2 kcal/mol вычислите нормированные веса при 298.15 и 350 K. Сравните аналитическое отношение p1/p0 с exp(−1/RT). Затем возьмите три стартовых конформера A, покажите чувствительность к ±0.5 kcal/mol у одного уровня. Не выдавайте веса поисковых геометрий за измеренные популяции.

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
OUT=workspace('M06-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import numpy as np
R=.001987204258
levels=np.array([0.,1.,2.])
def weights(energies,T):
    if T<=0:raise ValueError('Kelvin temperature must be positive')
    raw=np.exp(-(energies-min(energies))/(R*T));return raw/raw.sum()
rows={str(T):weights(levels,T).tolist() for T in [298.15,350.]}
assert math.isclose(sum(rows['298.15']),1) and math.isclose(rows['298.15'][1]/rows['298.15'][0],math.exp(-1/(R*298.15)))
display(rows)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
from rdkit import Chem
from rdkit.Chem import AllChem
m=Chem.AddHs(Chem.MolFromSmiles(compound('istradefylline')['smiles']))
p=AllChem.ETKDGv3();p.randomSeed=17;p.numThreads=1
AllChem.EmbedMultipleConfs(m,numConfs=3,params=p)
values=AllChem.MMFFOptimizeMoleculeConfs(m,numThreads=1,maxIters=1000)
good=np.array([e for s,e in values if s==0]);assert len(good)>0
print('Search-conformer weights, unclustered approximation:',weights(good,298.15))
fig,ax=plt.subplots();ax.bar(['0','1','2'],rows['298.15']);ax.set(xlabel='Simulated level / kcal mol^-1',ylabel='Normalized model weight');publish_plot(fig,'weights.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'simulated_weights':rows,'MMFF_converged_energies':good.tolist(),'kind':'simulation','free_energy_calculation':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M06-L02','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Больцмановское взвешивание превращает энергию в гипотезу о распределении только при перечисленных допущениях. Для спектра понадобится электронная, а не механическая модель.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
