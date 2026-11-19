# Разбор A. Оптимизация и валидация HPLC

Как выбрать рабочие условия, если таблица содержит несколько факторов и повторы в центре плана? На A учимся оценивать модель отклика, сохраняя B как отдельную опубликованную систему. Гипотеза: качество аппроксимации на обучении завышает пригодность для нового режима. Нужно проверять остатки и ошибки вне обучающей строки.

Постройте матрицу 20×10 по опубликованной таблице, оцените удерживание лактона. Проверьте ранг, RMSE на обучении и LOOCV. Затем исключайте целый уникальный режим факторов и сравните ошибку. Не используйте прогнозы для выдуманного «оптимума», если нет критериев всех аналитических ограничений.

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
OUT=workspace('M10-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import numpy as np,csv
with (DATA/'atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
factors=np.array([[float(r[k]) for k in ['acetonitrile_percent','column_temperature_C','flow_mL_min']] for r in rows])
x=(factors-[65,35,1])/[5,5,.2]
X=np.column_stack([np.ones(len(x)),x,x*x,x[:,0]*x[:,1],x[:,0]*x[:,2],x[:,1]*x[:,2]])
y=np.array([float(r['retention_ATO_lactone_min']) for r in rows]);assert X.shape==(20,10)
beta,_,rank,_=np.linalg.lstsq(X,y,rcond=None);assert rank==10
pred=X@beta;train=float(np.sqrt(np.mean((pred-y)**2)));print('Train RMSE / min',train)
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
loo=np.zeros(len(y));group=np.zeros(len(y))
for i in range(len(y)):
    keep=np.arange(len(y))!=i;loo[i]=X[i]@np.linalg.lstsq(X[keep],y[keep],rcond=None)[0]
for condition in np.unique(factors,axis=0):
    test=np.all(factors==condition,axis=1);group[test]=X[test]@np.linalg.lstsq(X[~test],y[~test],rcond=None)[0]
print('LOOCV, grouped RMSE / min',np.sqrt(np.mean((loo-y)**2)),np.sqrt(np.mean((group-y)**2)))
fig,ax=plt.subplots();ax.scatter(y,group-y);ax.axhline(0,color='gray');ax.set(xlabel='Measured retention / min',ylabel='Held-condition residual / min');publish_plot(fig,'hplc_cv.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'calculated','rank':int(rank),'rows':len(y),'train_RMSE_min':train,
        'LOOCV_RMSE_min':float(np.sqrt(np.mean((loo-y)**2))),'condition_RMSE_min':float(np.sqrt(np.mean((group-y)**2)))}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M10-L02','A',result,ROOT,inputs=['practicuum/shared/data/atorvastatin_hplc_table1.csv'])
print('Versioned evidence:',receipt)
```

Оптимизация требует селективности, runtime, pressure, устойчивости и проверки выбранного режима. Низкое RMSE одной колонки не завершает валидацию аналитического метода. После аналитики вернёмся к биологической мишени и уровням доказательств.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
