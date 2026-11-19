"""Factual anchor for open research-question exercises, not a model student essay."""
from pathlib import Path
import json
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import compound,DATA


def reference():
    record=compound('atorvastatin')
    structure=next(r for r in json.loads((DATA/'structures.json').read_text(encoding='utf-8')) if r['pdb_id']=='1HWK')
    assert record['cid']==60823 and structure['compound']=='atorvastatin'
    return {'CID':record['cid'],'form':'free acid database representation',
            'target_structure':'1HWK','source':structure['source_url'],
            'allowed_inference':'experimentally derived structural complex model',
            'hepatic_exposure':'NOT_ESTABLISHED_BY_THIS_RECORD',
            'open_question_rubric':'RUBRIC.md; alternative justified research questions accepted'}


if __name__=='__main__':
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
