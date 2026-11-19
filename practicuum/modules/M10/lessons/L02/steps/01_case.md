# Разбор A. План эксперимента и неидентифицируемые взаимодействия

Семь условий Table 4 [исследования ксантинов](https://doi.org/10.1155/2019/2926580) изменяют по одному фактору. Проверим, какие члены поверхности отклика этот реальный план способен определить. Эта диагностика предшествует любой оптимизации.

```python
from pathlib import Path
import sys,json,csv,math
import numpy as np
from scipy import stats
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M10-L02','case')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

```python
with (DATA/'xanthine_uhplc_ruggedness.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
t=np.array([float(r['retention_s']) for r in rows])
rsd=np.array([float(r['RSD_percent']) for r in rows])
n=np.array([int(r['n']) for r in rows])
```

Кодируем ACN, температуру и поток как x=(factor−center)/scale. Полная квадратичная модель трёх факторов содержит 10 коэффициентов. При OFAT все x_i x_j равны нулю, поэтому взаимодействия неидентифицируемы. Даже идеальный fit семи средних семью аддитивными коэффициентами не даёт проверки lack of fit.

```python
factors=np.array([[float(r[k]) for k in ['ACN_percent','temperature_C','flow_mL_min']] for r in rows])
x=(factors-[10,70,.5])/[5,5,.05]
def design(z):
    return np.column_stack([np.ones(len(z)),z,z*z,z[:,0]*z[:,1],z[:,0]*z[:,2],z[:,1]*z[:,2]])
X=design(x);rank=int(np.linalg.matrix_rank(X));zero_columns=np.flatnonzero(np.all(X==0,axis=0))
print({'conditions':len(t),'columns':X.shape[1],'rank':rank,'unidentifiable_columns':zero_columns.tolist()})
assert rank==7 and zero_columns.tolist()==[7,8,9]
beta=np.linalg.lstsq(X[:,:7],t,rcond=None)[0]
residual=t-X[:,:7]@beta
print('Saturated additive-model coefficients / s:',beta)
print('Condition-mean lack-of-fit df:',len(t)-np.linalg.matrix_rank(X[:,:7]))
assert np.max(abs(residual))<1e-10
```

Предложим **ещё не выполненное** расширение восемью угловыми условиями 2³. Оно устраняет линейную неидентифицируемость взаимодействий, но требует физической проверки давления, температуры, состава и идентичности пиков. Новых откликов не генерируем. Повторы центра, рандомизация, блокирование по дню и независимые приготовления планируются до измерения.

```python
from itertools import product
corners=np.array(list(product([-1.,1.],repeat=3)))
proposed=np.vstack([x,corners]);planned_rank=int(np.linalg.matrix_rank(design(proposed)))
assert planned_rank==10
print('Planned full design rank:',planned_rank,'new conditions:',len(corners))
fig,ax=plt.subplots()
ax.imshow(X,aspect='auto',cmap='coolwarm');ax.set(xlabel='Quadratic model column',ylabel='Published OFAT condition')
publish_plot(fig,'design_identifiability.png')
result={'kind':'calculated','scope':'actual design-rank audit; proposed new conditions NOT_RUN',
        'published_rank':rank,'planned_rank':planned_rank,'optimization':'BLOCKED: interactions and method constraints not measured',
        'new_experiments':'NOT_RUN'}
```

В самостоятельной линии B есть другой реальный план: 20 опытов аторвастатина с 10 коэффициентами полного квадратичного уравнения. Он позволяет отдельно оценить pure error и lack of fit. Это иной метод/матрица; коэффициенты ксантинов на B не переносятся. Профессиональный анализ семи откликов выполнен в `scripts/analyze_hplc_research.py`; задания требуют воспроизвести диагностику, а не считать отсутствие значимого LOF доказательством валидации.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M10-L02','A',result,ROOT,inputs=['practicuum/shared/data/xanthine_uhplc_ruggedness.csv', 'practicuum/shared/data/xanthine_uhplc_provenance.json', 'practicuum/shared/data/source-responses/xanthine_uhplc.xml', 'practicuum/shared/data/atorvastatin_hplc_table1.csv', 'practicuum/shared/data/hplc_provenance.json']))
```
