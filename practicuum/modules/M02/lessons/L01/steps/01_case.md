# Разбор A. Воспроизводимая среда

Получив результат, коллега запускает Notebook на другой машине и видит другое число. Сначала проверим не формулу, а исходные байты и интерпретатор. Паспорт эксперимента с ксантинами должен переживать перенос на другую ОС. Гипотеза: одинаковые байты входа и документированная программа позволят локализовать источник расхождения. Это необходимое, но недостаточное условие численного совпадения: существуют различия библиотек и аппаратной арифметики.

Проверьте profile base, получите sys.version и версии пакетов через importlib.metadata. Прочитайте compounds.json как байты, вычислите digest, затем отдельно декодируйте UTF-8 и проверьте структуру. Создайте копию в новой рабочей папке; добавьте пробел только к копии и сравните хеши. Исходник сохраняется.

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
OUT=workspace('M02-L01','case')
```

Сначала проверяем входы и единицы. Словари сохраняют названия полей вместе со значениями; список сохраняет соответствие записей. Выведите промежуточный результат перед дальнейшим анализом.

```python
import platform,importlib.metadata,hashlib
path=DATA/'compounds.json'
raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
print({'bytes':len(raw),'sha256':digest,'python':sys.version,'platform':platform.platform()})
```

Теперь сравним модель с контрольным случаем. `assert` останавливает расчёт при нарушении контракта; это защита от ошибочного продолжения, а не оценка научного понимания.

```python
copy=OUT/'compound_copy.json';copy.write_bytes(raw+b' ')
same_object=json.loads(raw)==json.loads(copy.read_bytes())
same_bytes=raw==copy.read_bytes()
assert same_object and not same_bytes
print({'same_object':same_object,'same_bytes':same_bytes})
```

Сохраним именно полученный результат. Не переносите этот вывод на другую химическую форму, мишень или экспериментальные условия без отдельной проверки.

```python
result={'input_sha256':digest,'kind':'calculated','semantic_identity':same_object,
        'packages':{n:importlib.metadata.version(n) for n in ['nbformat','matplotlib']}}
```

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
receipt=append_record(init_dossier(),'M02-L01','A',result,ROOT,inputs=['practicuum/shared/data/compounds.json'])
print('Versioned evidence:',receipt)
```

Различие digest у семантически одинакового JSON объясняет, почему паспорт должен различать байтовую и структурную идентичность. Проверка формы аторвастатина всё ещё химическая задача. Далее понадобится прочитать таблицу без утраты единиц и ошибок.

Перед переходом ответьте: какие результаты получены вычислением, какие заданы условно, и какая независимая проверка ещё отсутствует?
