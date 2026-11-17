# Ключ преподавателя: модуль 2

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M02-C1. Две единицы в одной поставке

Одинаковая концентрация должна дать одинаковый результат; invalid остаётся отдельным состоянием.


```python
case_input = {'values': [2.5, 2500, 0, 1], 'units': ['uM', 'nM', 'M', 'unknown']}
scale={'M':1,'mM':1e-3,'uM':1e-6,'nM':1e-9}; p=[]; statuses=[]
for v,u in zip(case_input['values'],case_input['units']):
    valid=u in scale and math.isfinite(v) and v>0
    p.append(-math.log10(v*scale[u]) if valid else None); statuses.append('ok' if valid else 'invalid')
answer={'p_values':p,'statuses':statuses}
```


Ожидаемый численный контракт: `{"p_values": [5.6020599913279625, 5.6020599913279625, null, null], "statuses": ["ok", "ok", "invalid", "invalid"]}`.


## M02-C2. Совпадает имя, различаются байты

Различие hash подтверждает различие snapshot; химическое качество требуется оценить отдельно.


```python
case_input = {'text': 'id,smiles\nA,CCO\n', 'suffix': '\n'}
import hashlib
b=case_input['text'].encode(); original=hashlib.sha256(b).hexdigest(); copy=bytes(b); changed=b+case_input['suffix'].encode(); answer={'same_copy':hashlib.sha256(copy).hexdigest()==original,'changed_copy':hashlib.sha256(changed).hexdigest()!=original,'source_preserved':b==case_input['text'].encode()}
```


Ожидаемый численный контракт: `{"same_copy": true, "changed_copy": true, "source_preserved": true}`.


## M02-C3. Импорт работает в терминале, но не в ядре

Нужно доказать выбор одного окружения; само отсутствие сообщения об ошибке без пути интерпретатора недостаточно.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
