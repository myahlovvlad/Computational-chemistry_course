# Разбор A. Область прогноза и идентифицируемость кинетической модели

Продолжаем анализ реальных оценок кофеина из [Table 4](https://doi.org/10.1186/s40064-015-0809-x). Перед расчётом сформулируйте критерий: прогноз проверяется на исключённой концентрации, а решение о переносе за 0.02–0.10 M требует нового эксперимента. Table 5 статьи содержит авторскую экстраполяцию на 30 °C; её нельзя добавлять как независимые измерения для обучения или проверки.

```python
from pathlib import Path
import sys,json,math,csv
import numpy as np
from scipy import stats
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M09-L02','case')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight')
    display(fig)
    plt.close(fig)
```

```python
with (DATA/'caffeine_hydroxide_table4.csv').open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f))
x=np.array([float(r['NaOH_mol_L']) for r in rows])
y=np.array([float(r['kexp_min_inverse']) for r in rows])
# Два столбца соответствуют свободному члену и зависимости от [OH-].
X=np.column_stack([np.ones(len(x)),x])
beta=np.linalg.lstsq(X,y,rcond=None)[0]
residual=y-X@beta
df=len(y)-X.shape[1]
inverse=np.linalg.inv(X.T@X)
s2=float(residual@residual/df)
covariance=s2*inverse
critical=stats.t.ppf(.975,df)
ci=np.column_stack([beta-critical*np.sqrt(np.diag(covariance)),beta+critical*np.sqrt(np.diag(covariance))])
print('intercept / min^-1; slope / L mol^-1 min^-1:',beta)
print('Conditional OLS intervals, NOT measured replicate uncertainty:',ci)
```

Диагональ матрицы H=X(XᵀX)⁻¹Xᵀ даёт leverage. Для линейного OLS остаток при исключении строки равен eᵢ/(1−hᵢ). Проверим эту формулу независимым переобучением пяти моделей, исключая целую концентрацию.

```python
leverage=np.einsum('ij,jk,ik->i',X,inverse,X)
deleted_residual=residual/(1-leverage)
explicit=[]
for i in range(len(y)):
    keep=np.arange(len(y))!=i
    fitted=np.linalg.lstsq(X[keep],y[keep],rcond=None)[0]
    explicit.append(y[i]-X[i]@fitted)
assert np.allclose(deleted_residual,explicit,atol=1e-12)
rmse=float(np.sqrt(np.mean(deleted_residual**2)))
print('Leave-one-concentration-out RMSE / min^-1:',rmse)
query=np.array([.001,.03,.12])
Q=np.column_stack([np.ones(len(query)),query])
prediction=Q@beta
variance_mean=s2*np.einsum('ij,jk,ik->i',Q,inverse,Q)
half_width=critical*np.sqrt(s2+variance_mean)
display([{'NaOH_mol_L':float(c),'kexp':float(v),'conditional_prediction_interval':[float(v-w),float(v+w)],
          'domain':'interpolation' if min(x)<=c<=max(x) else 'extrapolation'}
         for c,v,w in zip(query,prediction,half_width)])
fig,ax=plt.subplots()
ax.errorbar(query,prediction,yerr=half_width,fmt='o',label='Conditional OLS prediction interval')
ax.scatter(x,y,label='Published estimates');ax.axhline(0,color='gray')
ax.set(xlabel='NaOH / mol L^-1',ylabel='k_exp / min^-1');ax.legend(fontsize=7)
publish_plot(fig,'prediction_domain.png')
```

Отрицательная нижняя граница показывает ограничение линейной модели и малой выборки; её нельзя молча обрезать и объявить физическим интервалом. Для позитивной модели нужен обоснованный закон ошибки и сравнение на новых данных. По этой таблице нельзя заново оценить Eₐ: она содержит одну температуру. Следующий опыт должен включать несколько температур, независимые приготовления, quench, проверку извлечения и отклика, а также случайный порядок анализа.

```python
result={'kind':'calculated','analysis_scope':'published_data_reanalysis','source_doi':'10.1186/s40064-015-0809-x','slope_L_mol_inverse_min_inverse':float(beta[1]),'raw_time_series_refit':'NOT_RUN','scientific_review':'NOT_RUN'}
result['LOOCV_RMSE_min_inverse']=rmse
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M09-L02','A',result,ROOT,inputs=['practicuum/shared/data/caffeine_hydroxide_table4.csv', 'practicuum/shared/data/caffeine_kinetics_provenance.json', 'practicuum/shared/data/source-responses/caffeine_kinetics.xml', 'practicuum/shared/data/source-responses/statin_stability_verified.xml'])
print(receipt)
```
