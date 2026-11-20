# Разбор A. Структурное сходство

Ксантины имеют общий мотив, но список «похожих» зависит от определения сходства. Проверим, насколько рейтинг к кофеину устойчив к радиусу Morgan. Гипотеза: локальная похожесть не совпадает с равенством молекул. Для B кислота и лактон могут иметь высокий коэффициент, оставаясь разными аналитическими объектами.

Получите fingerprints для четырёх ксантинов при radius=2, chirality=True. Вычислите полную матрицу, проверьте симметрию и единицы на диагонали. Измените радиус на 3 и сравните рейтинг. Отдельный ручной пример двух множеств проверяет формулу вне RDKit.

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
OUT=workspace('M05-L01','case')
```

Мы хотим сравнить графы четырёх ксантинов. Сначала построим Morgan fingerprints с одинаковыми параметрами для всех молекул. До запуска предскажите диагональ и симметрию матрицы Танимото: это проверки реализации, которые не требуют заранее знать сходство разных веществ.

```python
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
import numpy as np
names=['caffeine','theophylline','theobromine','istradefylline']
def matrix(radius):
    g=rdFingerprintGenerator.GetMorganGenerator(radius=radius,fpSize=2048,includeChirality=True)
    fps=[g.GetFingerprint(Chem.MolFromSmiles(compound(n)['smiles'])) for n in names]
    return np.array([[DataStructs.TanimotoSimilarity(a,b) for b in fps] for a in fps])
values=matrix(2);assert np.allclose(values,values.T) and np.allclose(np.diag(values),1)
display(values)
```

Теперь прочитайте тепловую карту: найдите пару вне диагонали с высоким сходством и назовите, какие особенности представления могли на него повлиять. Изменение radius — проверка чувствительности дескриптора; изменение коэффициента не означает изменение самой молекулы.

```python
fig,ax=plt.subplots();im=ax.imshow(values,vmin=0,vmax=1);fig.colorbar(im,ax=ax,label='Tanimoto')
ax.set_xticks(range(4),names,rotation=25);ax.set_yticks(range(4),names);publish_plot(fig,'similarity.png')
print('radius=3 caffeine similarities',matrix(3)[0].tolist())
```

В досье попадут матрица и параметры fingerprint. Для решения о следующем эксперименте этого недостаточно: близость представлений не устанавливает одинаковую активность, растворимость или экспозицию.

```python
a={1,2,3};b={2,3,4,5};assert len(a&b)/len(a|b)==.4
result={'names':names,'matrix':values.tolist(),'kind':'calculated','radius':2,'fpSize':2048,'includeChirality':True}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M05-L01','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Изменение рейтинга является свойством представления. Чтобы выбрать следующий опыт, нужно учитывать не только сходство, но и неизвестность. Следующий урок добавит несколько критериев отбора.

Если порядок сходства изменился при другом radius, какой вывод остаётся устойчивым и какую проверку вы запросите для B?
