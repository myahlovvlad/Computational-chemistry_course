# Разбор A. Реальные температурные данные, растворитель и твёрдая фаза

Table S1 [Wang et al.](https://doi.org/10.3390/cryst12070917) содержит 60 строк: 12 растворителей/смесей × 5 температур 293.15–333.15 K. Методы: 12 h перемешивание и ещё 12 h выдержка; среднее трёх опытов, без raw repeats/SD в таблице. Reported equilibrium forms различны: I, гидрат II, сольват III. Смешивать их как одну твёрдую фазу нельзя. **100δ — отклонение авторской модели, не ошибка измерения.**

Фитируем ln x=a+b·(1000/T−mean(1000/T)). Apparent slope quantity ΔH_app=−R·b в kJ/mol, если R выражена в J mol⁻¹ K⁻¹. Это условный параметр выбранной концентрационной основы; thermodynamic enthalpy требует activities, стабильности фаз и согласованных исходных данных.

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
OUT=workspace('M04-L02','case');S_DATA=DATA/'istradefylline_solubility'
def read_csv(name):
    with (S_DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

```python
rows=read_csv('istradefylline_solubility_table_S1.csv')
solvents=list(dict.fromkeys(r['solvent'] for r in rows));fits=[]
for solvent in solvents:
    group=[r for r in rows if r['solvent']==solvent]
    T=np.array([float(r['temperature_K']) for r in group]);x=np.array([float(r['x_as_reported']) for r in group])
    z=1000/T;X=np.column_stack([np.ones(len(T)),z-z.mean()]);y=np.log(x)
    beta=np.linalg.lstsq(X,y,rcond=None)[0];residual=y-X@beta;df=len(y)-2
    inverse=np.linalg.inv(X.T@X);mse=float(residual@residual/df)
    se=np.sqrt(np.diag(mse*inverse));critical=stats.t.ppf(.975,df)
    h=np.einsum('ij,jk,ik->i',X,inverse,X)
    fits.append({'solvent':solvent,'form':group[0]['equilibrium_form_as_reported'],
                 'apparent_slope_kJ_mol':float(-8.31446261815324*beta[1]),
                 'conditional_half_CI95_kJ_mol':float(8.31446261815324*critical*se[1]),
                 'leave_one_temperature_out_RMSE_ln_x':float(np.sqrt(np.mean((residual/(1-h))**2)))})
display(fits)
```

Проверка source consistency важнее выбора «лучшего» растворителя. Отдельно пересчитаем 100|x_calc−x|/x; значительные расхождения с 100δ требуют review. Не используем δ как вес. Если столбец mg/mL означает API equivalents и x — обычную мольную долю, они задают implied solvent molarity c_solvent=(S_mass/MW)(1−x)/x. Сравним изменение этой величины, не подставляя выдуманную плотность.

```python
group=[r for r in rows if r['solvent']=='methanol']
T=np.array([float(r['temperature_K']) for r in group]);x=np.array([float(r['x_as_reported']) for r in group])
xcalc=np.array([float(r['x_calculated_by_authors']) for r in group]);mass=np.array([float(r['solubility_mg_mL_as_reported']) for r in group])
derived_deviation=100*abs(xcalc-x)/x
implied_solvent_molarity=(mass/384.43)*(1-x)/x  # mg/mL numerically equals g/L.
display({'recomputed_relative_deviation_percent':derived_deviation.tolist(),
         'implied_solvent_molarity_mol_L':implied_solvent_molarity.tolist(),
         'relative_to_293K':(implied_solvent_molarity/implied_solvent_molarity[0]).tolist()})
z=1000/T;X=np.column_stack([np.ones(len(T)),z-z.mean()])
b_x=np.linalg.lstsq(X,np.log(x),rcond=None)[0]
b_mass=np.linalg.lstsq(X,np.log(mass),rcond=None)[0]
print('Apparent slopes, mole fraction and mass basis / kJ mol^-1:',-8.31446261815324*b_x[1],-8.31446261815324*b_mass[1])
fig,ax=plt.subplots();ax.plot(T,implied_solvent_molarity/implied_solvent_molarity[0],'o-')
ax.set(xlabel='T / K',ylabel='Implied solvent molarity relative to 293 K',title='Source-basis diagnostic, not measured solvent density')
publish_plot(fig,'solubility_basis_audit.png')
result={'kind':'calculated','scope':'primary solubility table reanalysis and source-consistency audit',
        'n_observations':len(rows),'conditional_fits':fits,'source_data_acceptance':'REVIEW_REQUIRED',
        'thermodynamic_enthalpy_accepted':False,'new_experiments':'NOT_RUN'}
```

Метанольные столбцы дают ≈66.23 и ≈35.22 kJ/mol; implied solvent molarity к 333 K составляет лишь ≈0.220 от начальной. Требуется сверить dilution, единицы, состав раствора и определение x с raw data/авторами. Мы не исправляем таблицу по удобной гипотезе и не выбираем один столбец как «истину». Для солватов и смешанных растворителей отдельно проверяется термодинамическая основа. Численный OLS выполнен, физический параметр не принят.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M04-L02','A',result,ROOT,inputs=['practicuum/shared/data/istradefylline_solubility/istradefylline_solubility_table_S1.csv', 'practicuum/shared/data/istradefylline_solubility/istradefylline_aqueous_pH_table2.csv', 'practicuum/shared/data/istradefylline_solubility/supporting-information.pdf', 'practicuum/shared/data/istradefylline_solubility/primary-article.pdf', 'practicuum/shared/data/istradefylline_solubility/result.json', 'practicuum/shared/data/source-responses/statin_stability_verified.xml']))
```
