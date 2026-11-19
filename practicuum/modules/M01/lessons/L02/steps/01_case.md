# Разбор A. Исследовательский вопрос

В предыдущем уроке мы отделили объект от его описания. Теперь лаборатория спрашивает, можно ли выбирать растворитель по прогнозу растворимости. У истрадефиллина нет в этом наборе сопоставимого измерения: обещать точность для него нельзя. Вспомогательная ESOL позволяет сформулировать опровержимую гипотезу о методе. До вычисления предположите, будет ли ошибка одинаковой у хорошо и плохо растворимых соединений. Для B вернитесь к аторвастатину: определите форму, pH, температуру, равновесную или кинетическую растворимость, а не переносите числа ESOL на лекарство.

Прочитайте закреплённый CSV и сохраните row_id. Не сортируйте прогнозы отдельно от наблюдений. Рассчитайте остатки, сравните средние ошибки для y < −3 и y ≥ −3. Постройте наблюдение–прогноз и диагональ. Затем выпишите до следующего опыта endpoint, критерий ошибки и правила исключения.

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
OUT=workspace('M01-L02','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
rows=esol()
errors=[r['predicted']-r['measured'] for r in rows]
mae=sum(abs(e) for e in errors)/len(errors)
rmse=math.sqrt(sum(e*e for e in errors)/len(errors))
print({'n':len(rows),'MAE_logS':mae,'RMSE_logS':rmse})
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
for label,group in [('low',[r for r in rows if r['measured'] < -3]),('high',[r for r in rows if r['measured'] >= -3])]:
    print(label,len(group),sum(abs(r['predicted']-r['measured']) for r in group)/len(group))
fig,ax=plt.subplots()
ax.scatter([r['measured'] for r in rows],[r['predicted'] for r in rows],s=7,alpha=.4)
ax.plot([-12,3],[-12,3],color='black');ax.set(xlabel='Observed logS',ylabel='Predicted logS')
publish_plot(fig,'esol.png')
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'n':len(rows),'mae_logS':mae,'rmse_logS':rmse,'kind':'calculated','target_drug_prediction':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M01-L02','A',result,ROOT,inputs=['practicuum/shared/data/esol.csv'])
print('Versioned evidence:',receipt)
```

Расположение относительно диагонали показывает направление ошибки, но не причину. Корреляция не гарантирует калибровку. Для решения об истрадефиллине нужен новый релевантный набор измерений. Вопрос для перехода: каким образом другой исследователь воспроизведёт выбор строк и версии расчёта?

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
