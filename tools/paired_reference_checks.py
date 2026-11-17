"""Author-only solution execution. Student notebooks never call this module."""
from datetime import datetime, timezone
import contextlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def run(output,only=None):
    for path in [ROOT/'Stepik_course/practice',ROOT/'Labs']:
        if str(path) not in sys.path:sys.path.insert(0,str(path))
    from paired_lab_materials import CASES
    from practice_checks import check_case
    results=[]
    for module,cases in CASES.items():
        if only and module!=only:continue
        for number,case in enumerate(cases,1):
            identifier=f'M{module:02d}-C{number}'
            if case['mode']!='auto':
                results.append({'id':identifier,'status':'NOT_RUN','scope':'requires independent research/IDE artifact and human rubric'})
                continue
            folder=output/identifier;folder.mkdir()
            code=case['solution'];(folder/'reference.py').write_text(code,encoding='utf-8')
            case_input=case['input']
            (folder/'input.json').write_text(json.dumps(case_input,ensure_ascii=False,indent=2),encoding='utf-8')
            namespace={'np':np,'pd':pd,'math':math,'ROOT':ROOT,'DATA':ROOT/'Labs/datasets','case_input':case_input}
            started=time.perf_counter();utc=datetime.now(timezone.utc).isoformat()
            with (folder/'stdout.txt').open('w',encoding='utf-8') as stdout,(folder/'stderr.txt').open('w',encoding='utf-8') as stderr:
                try:
                    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):exec(compile(code,str(folder/'reference.py'),'exec'),namespace)
                    observation=check_case(identifier,namespace['answer'])
                except Exception as exc:
                    observation={'id':identifier,'status':'FAIL','reason':repr(exc)};stderr.write(repr(exc))
            record={**observation,'scope':'author numeric reference only, not learner completion','started_utc':utc,
                    'wall_seconds':time.perf_counter()-started,'actual':namespace.get('answer'),'reference':'reference.py','inputs':'input.json',
                    'command':'uv run --frozen python tools/run_labs.py --output <new-directory> (author-reference stage)'}
            (folder/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
            results.append(record);print(identifier,record['status'],flush=True)
    return results
