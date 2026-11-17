# Ключ преподавателя: модуль 7

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M07-C1. Граница не является точным измерением

Убывающий логарифм меняет знак; цензурированное наблюдение не становится точным.


```python
case_input = {'value': 10, 'unit': 'uM', 'relation': '>'}
from chemistry import p_activity
answer={'p_bound':p_activity(case_input['value'],case_input['unit']),'p_relation':{'<':'>','>':'<','=':'='}[case_input['relation']],'exact_regression_eligible':case_input['relation']=='='}
```


Ожидаемый численный контракт: `{"p_bound": 5, "p_relation": "<", "exact_regression_eligible": false}`.


## M07-C2. Новая партия активности

Одинаковая единица не делает endpoint и assay сопоставимыми.


```python
case_input = {'records': [{'record_id': 'S1', 'target_id': 'T1', 'assay_id': 'A1', 'endpoint': 'IC50', 'value': '50', 'unit': 'nM', 'relation': '='}, {'record_id': 'S2', 'target_id': 'T1', 'assay_id': 'A1', 'endpoint': 'Ki', 'value': '50', 'unit': 'nM', 'relation': '='}, {'record_id': 'S3', 'target_id': 'T2', 'assay_id': 'A1', 'endpoint': 'IC50', 'value': '50', 'unit': 'nM', 'relation': '='}, {'record_id': 'S4', 'target_id': 'T1', 'assay_id': 'A1', 'endpoint': 'IC50', 'value': '-2', 'unit': 'nM', 'relation': '='}]}
from chemistry import curate_activity
r=[curate_activity(x) for x in case_input['records']];answer={'included_ids':[x['record_id'] for x in r if x['status']=='included'],'p_values':[x['pIC50'] for x in r if x['status']=='included'],'excluded_reasons':[x['reason'] for x in r if x['status']=='excluded'],'total_rows':len(r)}
```


Ожидаемый численный контракт: `{"included_ids": ["S1"], "p_values": [7.301029995663981], "excluded_reasons": ["endpoint", "target_id", "value_or_unit"], "total_rows": 4}`.


## M07-C3. API оборвался на второй странице

Неполная выгрузка не должна получать статус полной; работоспособность реального API здесь не доказана.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
