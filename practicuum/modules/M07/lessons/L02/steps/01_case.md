# Разбор A. От энергии к физическому выводу

У нас уже есть сохранённые PySCF-вычисления трёх молекул. Прочитать число из файла проще, чем проверить, относится ли оно к нужной геометрии. Гипотеза: явная связь geometry_sha256, метода и сходимости позволяет обнаружить подмену входа. На линии A проверяем истрадефиллин; B независимо проверяет аторвастатин. Этот урок анализирует фактический архив, а не заявляет повторный запуск PySCF на Windows.

Прочитайте result.json и исходную geometry.json, пересчитайте SHA-256. Проверьте SCF, charge, spin, метод и число переходов. Сопоставьте файл с логом и версиями. Полный Linux-маршрут: установите quantum и выполните scripts/calculate_quantum_reference.py --help; запускайте его в новом каталоге, не заменяя reference.

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
OUT=workspace('M07-L02','case')
```

Открываем сохранённый расчёт целого истрадефиллина и сначала сверяем отпечаток геометрии, метод и электронное состояние. Это аудит конкретного исторического набора, а не новый CAM-B3LYP/def2-TZVP расчёт. Прежде чем читать энергию, найдите в паспорте, какая геометрия и какой уровень модели её определяют.

```python
import hashlib
qfolder=DATA/'quantum'/'istradefylline'
q=json.loads((qfolder/'result.json').read_text(encoding='utf-8'))
actual=hashlib.sha256((qfolder/'geometry.json').read_bytes()).hexdigest()
assert actual==q['geometry_sha256'] and q['scf_converged']
print({k:q[k] for k in ['compound','method','charge','spin','energy_hartree','geometry_method']})
```

Теперь проверим связь энергии перехода и длины волны. Совпадение по Eλ — контроль единиц и сериализации; оно не показывает физическую точность рассчитанного спектра. Шесть переходов относятся к этому сохранённому набору и не заменяют ожидаемый профессиональный расчёт 30 состояний.

```python
assert len(q['transitions'])==6 and q['charge']==0 and q['spin']==0
for t in q['transitions']:
    assert math.isclose(t['wavelength_nm']*t['energy_eV'],1239.8419843320026,rel_tol=1e-6)
display(q['transitions']);display(q['limitations'])
```

В досье фиксируем, что проверен паспорт и внутренняя согласованность сохранённого результата. Вывод о минимуме, устойчивости или экспериментальном спектре требует своих свидетельств и не выводится из одного флага SCF convergence.

```python
result={'compound':q['compound'],'geometry_sha256':actual,'archive_scf_converged':q['scf_converged'],
        'kind':'calculated','PySCF_rerun_this_lesson':'NOT_RUN','method':q['method']}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M07-L02','A',result,ROOT,inputs=['practicuum/shared/data/quantum/istradefylline/result.json', 'practicuum/shared/data/quantum/istradefylline/geometry.json', 'practicuum/shared/data/quantum/atorvastatin/result.json', 'practicuum/shared/data/quantum/atorvastatin/geometry.json'])
print('Versioned evidence:',receipt)
```

Хеш связывает байты геометрии с результатом; он не доказывает правильный выбор конформера. Открытый вопрос — насколько спектральный отклик изменится при растворителе и базисе. M08 превращает переходы в явно условный спектр.

Какую проверку вы потребуете перед сравнением двух энергий разных форм B? Назовите условие, при котором сами численные значения сравнивать некорректно.
