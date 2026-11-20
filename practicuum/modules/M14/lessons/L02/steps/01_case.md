# Разбор A. Защита и лабораторная проверка

Защита завершает вычислительное исследование вопросом: какое независимое наблюдение заставит изменить решение? Для A docking, свойства и спектральная симуляция не складываются автоматически в доказанную CNS-эффективность. B должен связать форму, аналитику, мишень и экспозицию с конкретными пределами выводов.

Создайте матрицу claims A: identity, spectral model, target structure, tissue exposure. Отметьте тип evidence и следующий опыт для каждого. Проверьте планирование n=16 для условного σ/δ. Сформируйте JSON запроса лаборатории и письменную защиту: что известно, что зависит от модели, что может опровергнуть вывод.

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
OUT=workspace('M14-L02','case')
```

Расчёт числа повторов ниже условный: sigma, допустимая полуширина и коэффициент нормального приближения заданы заранее. До запуска предскажите, во сколько раз изменится n при удвоении допустимой полуширины. Такой расчёт не является анализом мощности для произвольного эксперимента.

```python
sigma=.1;delta=.05;z=1.96
n=math.ceil((z*sigma/delta)**2);assert n==16
claims=[{'claim':'graph identity','kind':'calculated','next_test':'physical sample identity with standard'},
        {'claim':'UV envelope','kind':'simulation','next_test':'matched solvent UV-Vis'},
        {'claim':'A2A structural compatibility','kind':'literature','next_test':'target-specific biochemical assay'},
        {'claim':'CNS exposure','kind':'hypothesis','next_test':'independent exposure data'}]
display(claims)
```

Сравните найденное n со сценарием более широкой допустимой полуширины интервала. Затем прочитайте таблицу утверждений: структурная запись, симуляция спектра и гипотеза об экспозиции требуют разных проверок. Одно успешно воспроизведённое вычисление не закрывает их все.

```python
print({'conditional_n':n,'twice_tolerance_n':math.ceil((z*sigma/(2*delta))**2)})
assert math.ceil((z*sigma/(2*delta))**2)==4
```

В итоговую передачу включаем условия условного расчёта и отдельный план каждого реального эксперимента. Для B нужно обосновать вариабельность, дизайн, независимость повторов и выбранный критерий решения до сбора данных.

```python
result={'kind':'simulation','planning_n':n,'assumptions':'known sigma, independent samples, normal approximation',
        'claims':claims,'laboratory_measurements':'NOT_RUN','scientific_review':'NOT_RUN','student_pilot':'NOT_RUN'}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M14-L02','A',result,ROOT,inputs=[])
print('Versioned evidence:',receipt)
```

Автоматический отчёт подтверждает наличие полей, а научную достаточность оценивает преподаватель. Пилот, независимая рецензия и реальные измерения остаются NOT_RUN до выполнения. Выпуск курса требует раздельно технического, научного, педагогического и платформенного допуска.

Какое утверждение вашего досье сейчас наиболее уязвимо? Выберите одну проверку, которая может изменить решение, и заранее назовите критерий пересмотра.
