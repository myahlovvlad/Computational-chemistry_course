# Разбор A. Сборка исследовательского досье

За курс возникли таблицы, графики и противоположные гипотезы. Итоговое досье должно позволить восстановить путь от входа к решению, сохраняя ранние версии. Гипотеза: связанный граф происхождения быстрее обнаруживает необоснованный переход, чем перечень красивых результатов. Для A структурное evidence A2A и вычисленный спектр остаются разными узлами. В B самостоятельное решение не может заменяться копированием A.

Создайте новое versioned evidence в общем досье, связав паспорт структуры A с условным claim. Проверьте digest входа, отсутствие висячих рёбер и ацикличность вычислительной части. Добавьте намеренно повреждённое ребро и покажите отказ. Редактор dossier позволяет просмотреть JSON и сохранить новую версию, не оценивая текст по ключевым словам.

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
OUT=workspace('M14-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import hashlib,networkx as nx
dossier=init_dossier();digest=hashlib.sha256((DATA/'compounds.json').read_bytes()).hexdigest()
nodes=[{'id':'input','kind':'literature','sha256':digest,'file':'compounds.json'},
       {'id':'structure_check','kind':'calculated','method':'graph identity, RDKit'},
       {'id':'claim','kind':'hypothesis','text':'Structure supports a testable A2A study, not clinical efficacy'}]
edges=[('input','structure_check'),('structure_check','claim')]
graph=nx.DiGraph();graph.add_nodes_from(n['id'] for n in nodes);graph.add_edges_from(edges)
assert nx.is_directed_acyclic_graph(graph)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
bad=edges+[('missing','claim')]
known={n['id'] for n in nodes};dangling=[e for e in bad if any(n not in known for n in e)]
assert dangling==[('missing','claim')]
graph.add_edge('claim','input');assert not nx.is_directed_acyclic_graph(graph)
print('Detected dangling edge and calculation cycle')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'nodes':nodes,'edges':edges,'kind':'calculated','scientific_argument_review':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M14-L01','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Формальная целостность не доказывает истинность вывода. Разделите открытые гипотезы и выводы с достаточной опорой. Последний урок готовит независимые опровержимые проверки и защиту.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
