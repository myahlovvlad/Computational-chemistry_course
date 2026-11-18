"""Data integrity and format-only feedback. No RDKit or learner-answer solver."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import urllib.request

MODULE=Path(__file__).resolve().parent
META=json.loads((MODULE/'data/provenance.json').read_text(encoding='utf-8'))
MEASURED=META['measured_column']
PREDICTED=META['predicted_column']

def checksum(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(path):
    path=Path(path)
    if checksum(path)!=META['sha256']:raise ValueError('Snapshot SHA256 mismatch; do not silently replace source/version')
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    if len(rows)!=1128 or not {'Compound ID','smiles',MEASURED,PREDICTED}<=set(fields or []):raise ValueError('Unexpected ESOL schema/row count')
    for row in rows:
        if not all(math.isfinite(float(row[k])) for k in [MEASURED,PREDICTED]):raise ValueError('Nonfinite observed/predicted value')
    return path

def locate_snapshot():
    candidates=[]
    if os.getenv('M01_DATA_FILE'):candidates.append(Path(os.environ['M01_DATA_FILE']))
    candidates += [MODULE/'local_data/esol.csv',MODULE.parents[2]/'Labs/datasets/esol.csv']
    for path in candidates:
        if path.is_file():return verify(path)
    raise FileNotFoundError('Run fetch_data.py before the lesson (internet needed once), or set M01_DATA_FILE to the checked snapshot')

def acquire(source=None):
    target=MODULE/'local_data/esol.csv'
    if target.exists():return verify(target)
    target.parent.mkdir(exist_ok=True)
    temporary=target.with_suffix('.download')
    if source is not None:shutil.copyfile(verify(source),temporary)
    else:
        with urllib.request.urlopen(META['url'],timeout=60) as stream:temporary.write_bytes(stream.read())
    verify(temporary)
    temporary.replace(target)
    return target

def read_rows(path=None):
    path=verify(path) if path is not None else locate_snapshot()
    with path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    return [dict(row_id=i,name=r['Compound ID'],smiles=r['smiles'],measured=float(r[MEASURED]),predicted=float(r[PREDICTED])) for i,r in enumerate(rows)]

def prepare_import_case(rows):
    """Explicitly synthetic pipeline fault; immutable original measurements."""
    return {'metadata':{'kind':'synthetic import fault, not an error attributed to publication',
                        'column_header':'reported_logS','producer_quantity':'S_predicted','producer_unit':'mol/L',
                        'measurement_unit':META['units'],'source_sha256':META['sha256']},
            'rows':[{'row_id':r['row_id'],'name':r['name'],'measured':r['measured'],
                     'reported_logS':10**r['predicted']} for r in rows]}

def format_feedback(answer,required):
    if answer is None:return {'status':'NOT_RUN','scope':'submission-format only','reason':'Сначала выполните собственное исследование'}
    if not isinstance(answer,dict) or not set(required)<=set(answer):
        return {'status':'FAIL','scope':'submission-format only','reason':'Проверьте поля: '+', '.join(required)}
    return {'status':'PASS','scope':'submission-format only','scientific_review':'NOT_RUN',
            'reason':'Формат принят; правильность чисел, метода и решения проверяется отдельно'}

def metric_invariants(errors,mae,rmse):
    if errors is None:return {'status':'NOT_RUN','scope':'arithmetic invariants only'}
    try:
        valid=len(errors)>0 and all(math.isfinite(x) for x in errors)
        valid=valid and math.isfinite(mae) and math.isfinite(rmse) and 0<=mae<=rmse+1e-12
        valid=valid and math.isclose(mae,statistics.mean(abs(x) for x in errors),abs_tol=1e-9)
        valid=valid and math.isclose(rmse,math.sqrt(statistics.mean(x*x for x in errors)),abs_tol=1e-9)
    except (TypeError,ValueError):valid=False
    return {'status':'PASS' if valid else 'FAIL','scope':'internal arithmetic only, not agreement with measurements or model validation'}

def create_dossier(destination):
    """Create only learner-owned files; never overwrite an existing dossier."""
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    contents={
      'research_question.md':'# Мой научный вопрос\n\nОбъект/форма: TODO\nУсловия: TODO\nГипотеза: TODO\nЧто опровергнет её: TODO\nПочему ESOL не отвечает на этот вопрос целиком: TODO\n',
      'decisions.md':'# Мои решения\n\nВыбранный вариант: TODO\nАльтернатива: TODO\nОснование: TODO\nОграничение: TODO\nСледующий эксперимент: TODO\n',
      'source_register.csv':'id,url,type,conditions,rights,status\nSRC-001,https://doi.org/10.1021/ci034243x,paper,see_source_card,not_reproduced,READING_REQUIRED\n',
      'evidence_register.csv':'claim,type,source,limitation,status\nTODO,TODO,TODO,TODO,UNTESTED\n',
      'concept_map.json':json.dumps({'nodes':[],'edges':[],'instruction':'Add a directed relation with scientific explanation, source, limitation and next check'},ensure_ascii=False,indent=2)
    }
    for name,text in contents.items():
        path=destination/name
        if not path.exists():path.write_text(text,encoding='utf-8')
    starter=Path(__file__).resolve().parents[2]/'RESEARCH_DOSSIER_STARTER.md'
    if starter.is_file() and not (destination/'README.md').exists():
        shutil.copy2(starter,destination/'README.md')
    return destination
