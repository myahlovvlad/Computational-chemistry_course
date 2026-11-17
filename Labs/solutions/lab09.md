# Ключ преподавателя: модуль 9

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M09-C1. Две строки исчезли из отчёта

Проверка чисел не проверяет визуальную читаемость HTML; её оценивают по отдельной рубрике.


```python
case_input = {'dataset': 'molecules.csv'}
from chemistry import screen
r=pd.read_csv(DATA/'molecules.csv',keep_default_na=False); t=[{'id':x.id,**screen(x.smiles)} for x in r.itertuples()];answer={'rows':len(t),'valid_structures':sum(x['status']!='invalid' for x in t),'invalid_ids':[x['id'] for x in t if x['status']=='invalid']}
```


Ожидаемый численный контракт: `{"rows": 12, "valid_structures": 10, "invalid_ids": ["M08", "M09"]}`.


## M09-C2. ID оказался HTML-кодом

Экранирование для HTML и санитарная проверка молекулы — разные контракты.


```python
case_input = {'id': '<script>alert(1)</script>'}
import html
answer={'escaped_label':html.escape(case_input['id'])}
```


Ожидаемый численный контракт: `{"escaped_label": "&lt;script&gt;alert(1)&lt;/script&gt;"}`.


## M09-C3. Исправить подпись drug-ready

Оценивается честность интерпретации и читаемость; screenshot сам по себе не подтверждает результат.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
