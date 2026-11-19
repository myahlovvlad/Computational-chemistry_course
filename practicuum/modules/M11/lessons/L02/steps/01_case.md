# Разбор A. Докинг как проверяемый расчёт

Перед переносом докинга на A2A и HMGCR нужно проверить технический протокол на контрольной системе. Используем официальный tutorial 1IEP–иматиниб. Гипотеза: сравнение в системе координат рецептора обнаружит ошибочное смещение, которое исчезло бы после независимого выравнивания лиганда. Контроль 1IEP не является redocking A или B.

Прочитайте reference и официальный output, вычислите RMSD без выравнивания. Для отрицательного контроля сдвиньте все координаты на (1,0,0) Å: RMSD должен стать 1. Полный запуск при установленном Vina доступен через docking.run_docking(ROOT,new_output); при отсутствии binary статус NOT_RUN. Сохраните отдельный протокол подготовки 8RW0/1HWK и не объявляйте его исполненным.

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
OUT=workspace('M11-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
from docking import mapped_rmsd,first_pose
import numpy as np
folder=DATA/'docking';rmsd=mapped_rmsd(folder/'1iep_ligand.pdbqt',folder/'1iep_ligand_vina_out.pdbqt')
atoms,score=first_pose(folder/'1iep_ligand_vina_out.pdbqt')
print({'official_reference_RMSD_A':rmsd,'official_score':score,'heavy_atoms':len(atoms)})
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
coordinates=np.array(list(atoms.values()));shifted=coordinates+[1,0,0]
negative=float(np.sqrt(np.mean(np.sum((shifted-coordinates)**2,axis=1))))
assert math.isclose(negative,1,abs_tol=1e-12)
print('Shift control / Angstrom',negative)
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'calculated','system':'1IEP / imatinib control only','official_RMSD_A':rmsd,'shift_control_A':negative,
        'Vina_run_this_lesson':'NOT_RUN','A2A_redocking':'NOT_RUN','HMGCR_redocking':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M11-L02','A',result,ROOT,inputs=['practicuum/shared/data/docking/1iep_ligand.pdbqt', 'practicuum/shared/data/docking/1iep_ligand_vina_out.pdbqt'])
print('Versioned evidence:',receipt)
```

Хороший контрольный RMSD подтверждает ограниченную способность протокола воспроизвести известную позу. Для target-specific переноса остаются подготовка системы, redocking, альтернативные protonation и независимая биохимическая проверка. Следующий модуль рассмотрит более общие предсказательные модели.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
