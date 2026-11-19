# Разбор A. Отбор следующего кандидата

Высокое сходство с кофеином выбирает знакомый объект, но не обязательно информативный опыт. На линии A рассмотрим конфликт между близостью и полярностью; линия B перенесёт логику на формы аторвастатина без выдуманной биоактивности. Гипотеза: Парето-множество честнее единственного скрытого взвешенного score, если цели ещё обсуждаются.

Рассчитайте сходство к кофеину и TPSA для кандидатов A. Явно задайте направления критериев. Сравните каждую пару и покажите недоминируемые объекты на плоскости. Затем измените предпочтение TPSA и объясните, почему отбор изменился. Не называйте выбранный объект лекарством с лучшей эффективностью.

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
OUT=workspace('M05-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
from chemistry import similarity,descriptors
names=['theophylline','theobromine','istradefylline']
points={n:(similarity(compound('caffeine')['smiles'],compound(n)['smiles']),-descriptors(compound(n)['smiles'])['TPSA']) for n in names}
def frontier(points):
    return [n for n,p in points.items() if not any(all(a>=b for a,b in zip(q,p)) and any(a>b for a,b in zip(q,p)) for other,q in points.items() if other!=n)]
selected=frontier(points);print(points,selected)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
fig,ax=plt.subplots()
for n,(s,t) in points.items():ax.scatter(s,-t);ax.annotate(n,(s,-t))
ax.set(xlabel='Tanimoto to caffeine',ylabel='TPSA / Angstrom^2');publish_plot(fig,'pareto.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'criteria':'maximize similarity, minimize TPSA; teaching preference only','points':points,'frontier':selected,'kind':'calculated'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M05-L02','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Парето-анализ делает ценностный выбор явным, но не оценивает неизвестную активность. Для исследования B полезен также выбор наиболее различающихся форм, даже если они проигрывают эвристике. Далее проверим 3D-геометрию, которой нет в этих признаках.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
