"""Проверить локальные хеши/шаги пакета; не вызывает Stepik API."""
import argparse,hashlib,json
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
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate step ID')
    print(json.dumps({'status':'PASS','scope':'local review package integrity only','lessons':len(manifest['lessons']),
      'steps':count,'partial':manifest['partial'],'stepik_integration':'NOT_RUN','stepik_grader':'NOT_RUN'},indent=2))

if __name__=='__main__':main()
