# Разбор A. Истрадефиллин: pH, форма и измеримость растворимости

Вместо условного pKa используем Table 2 [Wang et al. (2022)](https://doi.org/10.3390/cryst12070917), CC BY 4.0: восемь значений при 293.15 K. Первичный PDF и supporting material доступны локально. Таблица содержит **µg/mL**, а не mg/mL. Репликатные ошибки для этих значений не опубликованы в таблице; весовую регрессию с вымышленными SD не проводим.

Вопрос: позволяют ли эти данные количественно оценить pKa или intrinsic S0? Сначала проверяем единицы, аналитическую область и solid-phase assumptions. Формула Henderson–Hasselbalch для равновесной растворимости слабого основания S=S0(1+10^(pKa−pH)) требует одной постоянной нейтральной твёрдой фазы, равновесия и применимого activity model.

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
OUT=workspace('M04-L01','case');S_DATA=DATA/'istradefylline_solubility'
def read_csv(name):
    with (S_DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

Моя первая развилка здесь — не «какая pKa лучше описывает график», а «какой величине соответствует опубликованная концентрация и в каком диапазоне её определяли». Прежде чем подбирать параметр, я привожу массовые единицы к общей базе. Для μg/mL численное значение совпадает с mg/L; чтобы получить g/L, множитель равен 0,001. Деление на принятую молярную массу затем даёт API-эквивалентную mol/L.

Теперь сравниваю значения с заявленным аналитическим диапазоном. Попадание ниже границы без описанного концентрирования — основание запросить процедуру, а не молча исправить таблицу. Если смысл исходной величины не установлен, красивая регрессия лишь точнее опишет неопределённый вход.

```python
rows=read_csv('istradefylline_aqueous_pH_table2.csv')
pH=np.array([float(r['pH']) for r in rows]);S=np.array([float(r['solubility_ug_mL_as_reported']) for r in rows])
# 1 ug/mL = 1 mg/L = 0.001 g/L; molarity uses API-equivalent molecular mass.
MW=384.43;mass_g_L=S*.001;molar=mass_g_L/MW
display([{'pH':float(p),'reported_ug_mL':float(s),'API_equivalent_mol_L':float(c)} for p,s,c in zip(pH,S,molar)])
calibration_min_mg_mL=.001  # Stated calibration lower bound in the primary article.
below=S*.001<calibration_min_mg_mL
print('Below stated calibration without a documented concentration step:',below.tolist())
```

Первичный текст сообщает диапазон HPLC-калибровки 0.001–0.1 mg/mL, то есть нижняя граница 1 µg/mL. Все восемь aqueous-значений ниже неё. Это запрос на проверку отдельной калибровки/LOQ или концентрирования, а не утверждение, что авторы обязательно измеряли неправильно. Соответствующие raw analytical details в нашем наборе отсутствуют.

Проверим **условное** следствие одной HH-модели: при выбранном постоянном S0 выражение pH+log10(S/S0−1) должно дать один pKa. Значение 0.10 µg/mL из самой таблицы используем только как диагностическое допущение, не как доказанный intrinsic S0. Там, где S≤S0, логарифм не определён; не заменяем это искусственным epsilon.

```python
assumed_S0=.10
valid=S>assumed_S0
implied=np.full(len(S),np.nan)
implied[valid]=pH[valid]+np.log10(S[valid]/assumed_S0-1)
display([{'pH':float(p),'conditional_implied_pKa':None if not ok else float(v)} for p,ok,v in zip(pH,valid,implied)])
fig,axes=plt.subplots(1,2,figsize=(9,3.5))
axes[0].plot(pH,S,'o-');axes[0].set(xlabel='pH',ylabel='Published solubility / ug mL^-1')
axes[1].plot(pH[valid],implied[valid],'o');axes[1].set(xlabel='pH',ylabel='Implied pKa under unverified constant S0')
publish_plot(fig,'pH_model_diagnostic.png')
result={'kind':'calculated','scope':'published pH-solubility audit','API_equivalent_molarity':molar.tolist(),
        'conditional_HH_pKa_values':[float(v) for v in implied[valid]],'pKa_accepted':False,
        'intrinsic_S0_accepted':False,'analytical_domain':'REVIEW_REQUIRED','new_measurements':'NOT_RUN'}
```

Условные implied pKa не совпадают. Одной этой диагностикой нельзя установить причину: возможны неадекватная модель, изменение фазы/состава, аналитические ограничения или неполное описание подготовки. Не выдаём диапазон значений за измеренную pKa. Для B аналогично различаем baseline при заданном pH, химическую форму и intrinsic neutral-species S0.

Диагностическая формула предполагает S=S0·[1+10^(pKa−pH)]. Отсюда pKa=pH+log10(S/S0−1), причём S должно быть больше S0. Именно поэтому код оставляет неприменимые точки неопределёнными. Я подставляю условное S0, чтобы проверить последствия предположения: одна константа должна давать согласованные оценки между точками. Расхождение требует разбора модели и источника. Его нельзя устранить усреднением полученных pKa и выдать среднее за измеренную константу.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M04-L01','A',result,ROOT,inputs=['practicuum/shared/data/istradefylline_solubility/istradefylline_solubility_table_S1.csv', 'practicuum/shared/data/istradefylline_solubility/istradefylline_aqueous_pH_table2.csv', 'practicuum/shared/data/istradefylline_solubility/supporting-information.pdf', 'practicuum/shared/data/istradefylline_solubility/primary-article.pdf', 'practicuum/shared/data/istradefylline_solubility/result.json', 'practicuum/shared/data/source-responses/statin_stability_verified.xml']))
```
