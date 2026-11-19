# Разбор A. Поиск и проверка мишени

Структурная модель A2A с истрадефиллином подтверждает совместимость лиганда с наблюдаемой структурой, но не концентрацию в мозге. Аналогично комплекс HMGCR с B не устанавливает печёночную экспозицию. Гипотеза: разделение структуры, assay и organism предотвращает ложное объединение несовместимых доказательств.

Из локальных RCSB-паспортов выберите 8RW0 и 1HWK. В ChEMBL-копии A разделите записи по target, organism, type, relation и assay. Рассчитывайте pKi только для численных положительных Ki с relation = и известными единицами. Покажите, сколько записей исключено каждым правилом; записи A1 не превращайте в A2A.

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
OUT=workspace('M11-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
structures=json.loads((DATA/'structures.json').read_text(encoding='utf-8'))
display([{k:r[k] for k in ['pdb_id','compound','resolution_A','doi']} for r in structures])
records=json.loads((DATA/'istradefylline_activities.json').read_text(encoding='utf-8'))['records']
print('Targets:',sorted({r['target_pref_name'] for r in records if r['target_pref_name']}))
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
selected=[];excluded={}
for r in records:
    reason=None
    if r['standard_type']!='Ki':reason='endpoint'
    elif r['standard_relation']!='=':reason='relation'
    elif r['standard_units']!='nM':reason='unit'
    else:
        try:v=float(r['standard_value']);assert math.isfinite(v) and v>0
        except (ValueError,TypeError,AssertionError):reason='value'
    if reason:excluded[reason]=excluded.get(reason,0)+1
    else:selected.append({'assay':r['assay_chembl_id'],'target':r['target_pref_name'],'organism':r['target_organism'],'pKi':-math.log10(v*1e-9)})
display(selected[:8]);print('Excluded',excluded)
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'kind':'calculated','total':len(records),'selected_Ki':len(selected),'excluded':excluded,
        'records':selected,'clinical_efficacy':'NOT_INFERRED'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M11-L01','A',result,ROOT,inputs=['practicuum/shared/data/structures.json', 'practicuum/shared/data/istradefylline_activities.json', 'practicuum/shared/data/atorvastatin_activities.json'])
print('Versioned evidence:',receipt)
```

Реестр делает пробелы видимыми: структурный комплекс и значение биохимического assay не доказывают доставку. Следующий шаг — проверить, способен ли выбранный докинг воспроизвести известную позу при фиксированном протоколе.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
