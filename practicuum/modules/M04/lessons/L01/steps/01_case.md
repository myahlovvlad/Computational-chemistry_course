# Разбор A. Свойства и физический смысл

После проверки идентичности можно вычислять свойства. Почему похожий ксантиновый фрагмент не гарантирует одинакового распределения между фазами? Сравним графовые дескрипторы кофеина и истрадефиллина. Гипотеза: изменение заместителей меняет несколько признаков одновременно; один logP не определяет экспозицию CNS. В B сравнение свободной кислоты и лактона должно сохранять различие химических форм.

Для всех четырёх ксантинов рассчитайте M, TPSA, HBD, HBA и MolLogP. В таблице отдельно оставьте PubChem XLogP: это другой вычислительный метод, расхождение ожидаемо. Постройте TPSA против MolLogP. Проверяйте единицы и не усредняйте разные химические формы.

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
OUT=workspace('M04-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
from rdkit import Chem
from rdkit.Chem import Descriptors,Lipinski
rows=[]
for name in ['caffeine','theophylline','theobromine','istradefylline']:
    r=compound(name);m=Chem.MolFromSmiles(r['smiles']);assert m is not None
    rows.append({'name':name,'MW':Descriptors.MolWt(m),'TPSA':Descriptors.TPSA(m),'logP_RDKit':Descriptors.MolLogP(m),
                 'XLogP_PubChem':r['pubchem_XLogP'],'HBD':Lipinski.NumHDonors(m),'HBA':Lipinski.NumHAcceptors(m)})
display(rows)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
fig,ax=plt.subplots();ax.scatter([r['logP_RDKit'] for r in rows],[r['TPSA'] for r in rows])
for r in rows:ax.annotate(r['name'],(r['logP_RDKit'],r['TPSA']))
ax.set(xlabel='Calculated MolLogP',ylabel='Calculated TPSA / Angstrom^2');publish_plot(fig,'descriptors.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'rows':rows,'kind':'calculated','tissue_exposure':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M04-L01','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Дескрипторы характеризуют запись при выбранной модели. Они помогают формировать гипотезы, а не заменяют измерение растворимости. Следующий урок добавит pH и среду.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
