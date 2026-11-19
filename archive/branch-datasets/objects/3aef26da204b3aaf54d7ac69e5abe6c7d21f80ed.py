"""Проверить локальные хеши/шаги пакета; не вызывает Stepik API."""
import argparse,hashlib,json,math
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('package',type=Path)
    args=parser.parse_args();root=args.package.resolve()
    manifest=json.loads((root/'package.json').read_text(encoding='utf-8'))
    for relative,digest in manifest['files_sha256'].items():
        path=(root/relative).resolve();path.relative_to(root)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Changed file: '+relative)
    count=0;ids=[]
    for record in manifest['lessons']:
        lesson=json.loads((root/record['file']).read_text(encoding='utf-8'))
        if len(lesson['steps'])!=record['steps']:raise ValueError('Step count mismatch')
        for position,step in enumerate(lesson['steps'],1):
            if step['position']!=position or step['block']['name']!='text':raise ValueError('Invalid text step')
            source=root/'sources'/step['source']
            if hashlib.sha256(source.read_bytes()).hexdigest()!=step['source_sha256']:raise ValueError('Source changed')
            ids.append(step['local_id']);count+=1
        for path in lesson['notebooks']:
            if not (root/path).is_file():raise ValueError('Missing notebook: '+path)
        assessment=lesson.get('assessment',{})
        if 'checker' in assessment:
            checker=(root/assessment['checker']).resolve();checker.relative_to(root)
            namespace={};exec(compile(checker.read_text(encoding='utf-8'),str(checker),'exec'),namespace)
            contract=assessment['contract'];check=namespace['check']
            if not check(json.dumps(contract)):raise ValueError('Checker rejects numerical anchor')
            if check('{}') or check('null') or check('{bad json'):raise ValueError('Checker accepts empty or invalid answer')
            for field,expected in contract.items():
                wrong=dict(contract);wrong[field]=False if type(expected) is not bool else not expected
                if check(json.dumps(wrong)):raise ValueError('Checker accepts wrong field '+field)
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate step ID')
    forbidden={'instructor','cache','workspace'}
    for path in root.rglob('*'):
        if path.is_file() and forbidden.intersection(path.relative_to(root).parts):raise ValueError('Private or restricted resource leaked '+str(path))
    for path in ['programm/course.json','practicuum/shared/course_support.py','practicuum/shared/data/esol.csv',
                 'scripts/environment/uv.lock','THIRD_PARTY_NOTICES.md','scripts/train_target_qsar.py',
                 'practicuum/shared/data/target_qsar/manifest.json',
                 'practicuum/evidence/20261119-research-A2A-dataset/curated.csv']:
        if not (root/path).is_file():raise ValueError('Missing portable resource '+path)
    data=root/'practicuum/shared/data/target_qsar'
    for name,digest in json.loads((data/'manifest.json').read_text(encoding='utf-8'))['files_sha256'].items():
        if hashlib.sha256((data/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed target QSAR resource '+name)
    print(json.dumps({'status':'PASS','scope':'local review package integrity only','lessons':len(manifest['lessons']),
      'steps':count,'partial':manifest['partial'],'stepik_integration':'NOT_RUN','stepik_grader':'NOT_RUN'},indent=2))

if __name__=='__main__':main()
