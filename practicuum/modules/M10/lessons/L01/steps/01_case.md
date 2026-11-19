# Разбор A. Реальная UHPLC–MS ксантинов: разделение и устойчивость

Работаем с опубликованными данными [DOI 10.1155/2019/2926580](https://doi.org/10.1155/2019/2926580), Tables 2/4, Creative Commons Attribution (версия лицензии в XML не указана). Объекты A — теобромин, теофиллин и кофеин, не истрадефиллин. Матрица — чай; перенос на фармацевтическую композицию не подтверждён.

Условия Table 2: Nucleodur C18 polar Tec, 50×2 mm, 1.8 μm; ACN/water 10:90 с 1% муравьиной кислоты, 0.5 mL/min, 70 °C, инъекция 5 μL, ESI+ SIM. Опубликованные t_R трёх соединений — 14, 19, 28 s. Это не сырые хроматограммы; Gaussian-пики не дорисовываем как измерения.

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
OUT=workspace('M10-L01','case')
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

```python
with (DATA/'xanthine_uhplc_ruggedness.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
t=np.array([float(r['retention_s']) for r in rows])
rsd=np.array([float(r['RSD_percent']) for r in rows])
n=np.array([int(r['n']) for r in rows])
```

Table 4 подписана «t_R ± %RSD (n=3)». Число после ± — относительная величина, не абсолютное SD. Переведём SD=t_R·%RSD/100, затем условный Student t-интервал среднего. Независимость и нормальность трёх повторов не подтверждены raw data; средние округлены до целых секунд, поэтому интервалы не восстанавливают исходную точность.

```python
sd=t*rsd/100
half=stats.t.ppf(.975,n-1)*sd/np.sqrt(n)
change=100*(t-t[0])/t[0]
display([{'condition':r['condition'],'tR_s':float(mean),'derived_SD_s':float(s),
          'conditional_mean_CI95_s':[float(mean-h),float(mean+h)],'change_percent':float(c)}
         for r,mean,s,h,c in zip(rows,t,sd,half,change)])
fig,ax=plt.subplots(figsize=(9,4))
ax.errorbar(np.arange(len(t)),t,yerr=half,fmt='o');ax.axhline(t[0],color='gray')
ax.set_xticks(np.arange(len(t)),[r['condition'] for r in rows],rotation=35,ha='right')
ax.set(ylabel='Caffeine retention time / s',title='Published means; conditional intervals from rounded summary data')
publish_plot(fig,'ruggedness.png')
```

Проверим простую альтернативу: при неизменных k′ и объёмах t_R∝1/F. Это диагностическая физическая аппроксимация, не новый fit с доказанной применимостью.

```python
for i in [1,2]:
    flow=float(rows[i]['flow_mL_min']);ideal=t[0]*.5/flow
    print({'flow_mL_min':flow,'published_tR_s':float(t[i]),'inverse_flow_approximation_s':float(ideal),'difference_s':float(t[i]-ideal)})
retention=np.array([14.,19.,28.])
print('Published adjacent retention gaps / s:',np.diff(retention))
result={'kind':'calculated','scope':'published UHPLC summary reanalysis','conditional_SD_s':sd.tolist(),
        'relative_change_percent':change.tolist(),'measured_Rs':'NOT_CALCULABLE: numerical baseline widths unavailable',
        'new_injections':'NOT_RUN','scientific_review':'NOT_RUN'}
```

Небольшой %RSD внутри условия не означает отсутствия сдвига между условиями: изменение t_R достигает 25%. Без площади, ширин, асимметрии, матричных/blank-контролей и независимых приготовлений нельзя подтвердить полную устойчивость количественного метода. Разность t_R не равна Rs. Сформулируйте, какие измерения нужны, прежде чем принимать авторский общий вывод об устойчивости.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M10-L01','A',result,ROOT,inputs=['practicuum/shared/data/xanthine_uhplc_ruggedness.csv', 'practicuum/shared/data/xanthine_uhplc_provenance.json', 'practicuum/shared/data/source-responses/xanthine_uhplc.xml', 'practicuum/shared/data/atorvastatin_hplc_table1.csv', 'practicuum/shared/data/hplc_provenance.json']))
```
