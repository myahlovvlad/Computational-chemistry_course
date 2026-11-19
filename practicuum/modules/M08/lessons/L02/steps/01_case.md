# Разбор A. Прибор и специфичность

Даже идеальная электронная модель не устраняет шум, фон и перекрытие сигналов. Может ли UV отличить кислоту B от лактона? Без соответствующих спектров ответ неизвестен. На A проверим закон прохождения света на условных концентрациях, а ИК обсудим как дополнительный независимый канал идентификации. Гипотеза: рост stray light искажает линейность при большом поглощении.

Смоделируйте ε=10000 L mol^-1 cm^-1, l=1 cm, c=0…4e-4 mol/L; сравните s=0/.001. Покажите линейную и насыщенную кривые. На контрольных T=.1 и .01 рассчитайте A. NIST-ИК кофеина доступен отдельной загрузкой с проверкой hash; сырой файл с ограниченными правами не включается в публикацию. Параметрический тренажёр повторяет эту модель.

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
OUT=workspace('M08-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import numpy as np
c=np.linspace(0,4e-4,101);ideal=10000*c
stray=.001;observed=-np.log10((10**(-ideal)+stray)/(1+stray))
assert np.allclose(-np.log10(10**(-ideal)),ideal)
print({'A_T_0.1':-math.log10(.1),'A_T_0.01':-math.log10(.01)})
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
fig,ax=plt.subplots();ax.plot(c,ideal,label='ideal');ax.plot(c,observed,label='stray=0.001')
ax.set(xlabel='Simulated concentration / mol L^-1',ylabel='Absorbance');ax.legend();publish_plot(fig,'instrument.png')
```

## Независимый спектральный канал: ИК

В гармоническом приближении связь напоминает пружину. Приведённая масса μ=m₁m₂/(m₁+m₂), силовая константа k в N/m, частота ν=(2π)⁻¹√(k/μ) в Hz. Деление на скорость света в cm/s даёт волновое число cm⁻¹. Это контроль размерностей для изолированной условной C=O-связи, а не рассчитанная нормальная мода истрадефиллина. У реальной молекулы колебания коллективны; нужны Hessian, геометрическая стационарность и переходный диполь.

```python
amu=1.66053906660e-27
mu=(12*16/(12+16))*amu
force_constant=1200.0  # N/m, условный параметр
wavenumber=math.sqrt(force_constant/mu)/(2*math.pi*2.99792458e10)
print('Simulated diatomic wavenumber / cm^-1:',wavenumber)
assert 1500 < wavenumber < 2000
```

Для независимого наблюдения есть паспорт газофазного ИК кофеина NIST. Сам JCAMP не распространяется в репозитории из-за ограничений прав. В локальной машине он может быть в cache; отсутствие файла означает NOT_RUN этого дополнительного анализа, а не отсутствие полос. Контроль сетки и единиц не подтверждает химическую идентичность неизвестной пробы. Для B нужен отдельный спектр выбранной формы.

```python
import hashlib
from spectra import read_nist_ir
passport=json.loads((DATA/'nist_ir_source.json').read_text(encoding='utf-8'))
cache=DATA/'cache/caffeine_ir.jdx'
ir_status='NOT_RUN: retrieve individually from NIST under its terms'
if cache.is_file():
    assert hashlib.sha256(cache.read_bytes()).hexdigest()==passport['sha256']
    spectrum=read_nist_ir(cache)
    assert len(spectrum['absorbance'])==passport['expected_points']==880
    fig,ax=plt.subplots();ax.plot(spectrum['wavenumber_cm1'],spectrum['absorbance'])
    ax.invert_xaxis();ax.set(xlabel='Wavenumber / cm^-1',ylabel='Database absorbance (gas-phase caffeine)')
    # График остаётся личным локальным результатом; не встраиваем его в распространяемые outputs.
    fig.savefig(OUT/'nist_ir_local_only.png',dpi=120,bbox_inches='tight');plt.close(fig)
    ir_status='PASS: local NIST caffeine record, not atorvastatin IR'
print(ir_status)
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'simulation','epsilon_L_mol_cm':10000,'path_cm':1,'stray_fraction':stray,
        'max_deviation_A':float(max(ideal-observed)),'chemical_specificity':'NOT_RUN',
        'diatomic_simulated_wavenumber_cm1':wavenumber,'local_IR_analysis':ir_status}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M08-L02','A',result,ROOT,inputs=[])
print('Versioned evidence:',receipt)
```

Калибровка не устанавливает селективность в смеси. Для B нужны подходящие стандарты форм и ортогональная HPLC/LC-MS проверка. Этот вопрос непосредственно ведёт к анализу реакций и превращений формы во времени.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
