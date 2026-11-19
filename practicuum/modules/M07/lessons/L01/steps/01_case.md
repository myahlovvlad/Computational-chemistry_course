# Разбор A. Электронная модель

Механическое поле не описывает перераспределение электронов. Прежде чем читать квантовый результат истрадефиллина, воспроизведём ограниченный RHF-контроль H₂. Гипотеза: энергия зависит от межъядерного расстояния, а код должен одновременно контролировать плотность и энергию. H₂ проверяет метод, но не сообщает свойства A2A-лиганда или аторвастатина.

Запустите существующее прозрачное ядро h2_scf на 0.74, 1.0 и 1.5 Å. Сохраните трассы итераций, проверьте известный контроль около −1.11676 Eh на 0.74 Å. Затем попытайтесь ограничить число итераций единицей и зафиксируйте отказ. Обсудите невозможность переноса энергий H₂ на лекарственные объекты.

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
OUT=workspace('M07-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
from h2_scf import rhf_h2
rows=[rhf_h2(r) for r in [.74,1.,1.5]]
assert all(r['converged'] for r in rows)
assert abs(rows[0]['energy_hartree']-(-1.1167593))<1e-5
display([{k:r[k] for k in ['distance_angstrom','energy_hartree','cycles']} for r in rows])
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
try:rhf_h2(.74,max_cycles=1)
except RuntimeError as error:print('Expected nonconvergence:',error)
else:raise AssertionError('One cycle accepted')
fig,ax=plt.subplots();ax.plot([r['distance_angstrom'] for r in rows],[r['energy_hartree'] for r in rows],'o-')
ax.set(xlabel='H-H / Angstrom',ylabel='RHF/STO-3G energy / Eh');publish_plot(fig,'h2.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'control':'H2 only','runs':rows,'kind':'calculated','drug_QM':'not inferred from H2'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M07-L01','A',result,ROOT,inputs=[])
print('Versioned evidence:',receipt)
```

Кривая показывает зависимость энергии в выбранном базисе, не свободную энергию реакции. Для реального B нужно отдельно задать заряд, spin=2S, геометрию и метод. Следующий урок проверит именно паспорт полного расчёта.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
