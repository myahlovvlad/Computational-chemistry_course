# Разбор A. Закон скорости по опубликованным данным кофеина

Научный вопрос: согласуется ли зависимость опубликованных k_exp от концентрации NaOH с псевдопервым порядком k_exp=k₂[OH⁻]? Работаем с Table 4 [Edwards, Kulikov, Garner-O’Neale (2015)](https://doi.org/10.1186/s40064-015-0809-x), CC BY 4.0. Условия: 100 °C, исходно 25 mg/L кофеина, GC–MS/MS–MRM, NaOH 0.02–0.10 mol/L. Кофеин относится к линии ксантинов A; эти константы нельзя приписывать истрадефиллину.

Различайте наблюдаемый k_exp в min⁻¹ и бимолекулярный k₂ в L mol⁻¹ min⁻¹. Единица k₂ в тексте первоисточника размерностно противоречит его уравнению скорости: сохраняем исходный XML и объясняем выбор единицы. Табличные k_exp уже оценены авторами из временных рядов. Сырые временные концентрации здесь отсутствуют; новый fit временного ряда не выполняется.

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
OUT=workspace('M09-L01','case')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight')
    display(fig)
    plt.close(fig)
```

Оценим y=b₀+b₁x обычным МНК и проверим остатки. Интервал Student t использует лишь три остаточные степени свободы. Он условен на независимость и одинаковую дисперсию табличных оценок, которые невозможно проверить по пяти строкам без ошибок повторов.

У нас опубликованы оценки k_exp при разных концентрациях NaOH. Я сначала спрашиваю, какой признак поддержал бы связь k_exp=k2[OH−]: пропорциональность в выбранном диапазоне и согласованность с нулевым свободным членом при допущениях модели. Поэтому сначала оцениваю прямую со свободным членом, а затем сравниваю её с ограничением проходить через начало координат.

Столбец единиц в X соответствует свободному члену, второй — концентрации. Наклон имеет размерность L mol⁻¹ min⁻¹, свободный член — min⁻¹. Уже по размерностям видно, что это разные параметры. Остатки используются для условной оценки дисперсии, потому что исходные повторные временные ряды здесь отсутствуют. Я не назначаю им выдуманные измеренные ошибки.

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

Сравним модель с физически мотивированным нулевым свободным членом. Отсутствие значимости b₀ не доказывает отсутствие иных путей. Взвешенный fit без опубликованных дисперсий означал бы выдуманные веса, поэтому его не применяем.

```python
k2_origin=float(x@y/(x@x))
sse0=float(np.sum((y-k2_origin*x)**2))
F=max(0.,(sse0-float(residual@residual))/s2)
p=float(stats.f.sf(F,1,df))
print('Origin-constrained k2:',k2_origin,'intercept F-test p:',p)
reported_half=np.array([float(r['reported_half_life_min']) for r in rows])
print('ln(2)/k_exp minus published rounded half-life / min:',np.log(2)/y-reported_half)
fig,axes=plt.subplots(1,2,figsize=(9,3.5))
axes[0].plot(x,y,'o',label='Published rate estimates')
axes[0].plot(x,X@beta,label='OLS with intercept')
axes[0].plot(x,k2_origin*x,'--',label='Through origin')
axes[0].set(xlabel='NaOH / mol L^-1',ylabel='k_exp / min^-1');axes[0].legend(fontsize=7)
axes[1].axhline(0,color='gray');axes[1].plot(x,residual,'o-')
axes[1].set(xlabel='NaOH / mol L^-1',ylabel='Residual / min^-1')
publish_plot(fig,'rate_law.png')
```

Наклон с нулевым свободным членом около 0.713 L mol⁻¹ min⁻¹ сопоставим с опубликованным 0.71; это повторный анализ того же материала. Для проверки lack of fit нужны повторные условия, отделяющие pure error. Температурный перенос на 30 °C и физиологическую среду этим fit не подтверждён.

```python
result={'kind':'calculated','analysis_scope':'published_data_reanalysis','source_doi':'10.1186/s40064-015-0809-x','slope_L_mol_inverse_min_inverse':float(beta[1]),'raw_time_series_refit':'NOT_RUN','scientific_review':'NOT_RUN'}
```

Сравнение моделей задаёт вопрос, какой ценой ограничение на свободный член описывает эти пять оценок. Большой p-value не доказал бы точность закона во всех условиях; маленький потребовал бы разбирать допустимость ограничения и модели ошибки. Проверка ln(2)/k_exp с опубликованным периодом полупревращения проверяет согласованность представления при принятом первом порядке. Для выбора механизма и нового температурного режима понадобятся другие наблюдения.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M09-L01','A',result,ROOT,inputs=['practicuum/shared/data/caffeine_hydroxide_table4.csv', 'practicuum/shared/data/caffeine_kinetics_provenance.json', 'practicuum/shared/data/source-responses/caffeine_kinetics.xml', 'practicuum/shared/data/source-responses/statin_stability_verified.xml'])
print(receipt)
```
