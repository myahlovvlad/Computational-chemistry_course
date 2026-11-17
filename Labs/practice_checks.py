"""Bounded numeric contract checks. Never award learner/research completion."""
import json
import math
from numbers import Real
from pathlib import Path

CONTRACTS={r['id']:r for r in json.loads(Path(__file__).with_name('practice_contracts.json').read_text(encoding='utf-8'))}

def compare(actual,expected,tolerance,path='answer'):
    if isinstance(expected,dict):
        if not isinstance(actual,dict):return f'{path}: требуется словарь'
        if set(actual)!=set(expected):return f'{path}: ожидаемые поля {sorted(expected)}, получены {sorted(actual)}'
        for key,value in expected.items():
            error=compare(actual[key],value,tolerance,f'{path}.{key}')
            if error:return error
    elif isinstance(expected,list):
        if not isinstance(actual,(list,tuple)) or len(actual)!=len(expected):return f'{path}: неверная длина/тип списка'
        for i,(a,b) in enumerate(zip(actual,expected)):
            error=compare(a,b,tolerance,f'{path}[{i}]')
            if error:return error
    elif isinstance(expected,bool):
        if not isinstance(actual,bool) or actual!=expected:return f'{path}: неверное логическое значение'
    elif isinstance(expected,Real):
        if isinstance(actual,bool) or not isinstance(actual,Real) or not math.isfinite(actual) or not math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance):return f'{path}: численное расхождение; absolute tolerance={tolerance}'
    elif actual!=expected:return f'{path}: значение не соответствует контракту'
    return ''

def check_case(identifier,answer):
    case=CONTRACTS[identifier]
    result={'id':identifier,'scope':'returned numeric contract only; artifacts and scientific interpretation require review'}
    if answer is None:return {**result,'status':'NOT_RUN','reason':'Собственное решение не представлено'}
    if case['mode']!='auto':return {**result,'status':'NOT_RUN','reason':'Требуется фактическое оценивание артефактов/интерпретации/IDE; наличие текста не равно PASS'}
    error=compare(answer,case['expected'],case['tolerance'])
    return {**result,'status':'FAIL' if error else 'PASS','reason':error or 'Совпадает только указанный численный контракт'}
