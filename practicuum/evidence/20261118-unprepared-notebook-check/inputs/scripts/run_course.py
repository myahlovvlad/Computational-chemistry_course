"""Исполнить выбранные Notebook в чистых ядрах и сохранить доказательства запуска."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
from contextlib import redirect_stderr,redirect_stdout
import traceback

import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import NoSuchKernel
from nbclient.exceptions import CellExecutionError,CellTimeoutError

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',nargs='*');parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--roles',nargs='+',choices=['case','lab'],default=['case','lab'])
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    environment={'argv':[sys.executable,*sys.argv],'python':sys.version,'platform':platform.platform(),
      'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions()))}
    (out/'environment.json').write_text(json.dumps(environment,indent=2),encoding='utf-8')
    course=json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'));runs=[]
    known={lesson['id'] for module in course['modules'] for lesson in module['lessons']}
    unknown=set(args.only or [])-known
    if unknown:parser.error('Неизвестные уроки: '+', '.join(sorted(unknown)))
    inputs={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'practicuum/shared').rglob('*'))
            if p.is_file() and p.suffix in {'.json','.csv','.py','.pdbqt','.sdf'}
            and not any(part in {'__pycache__','cache'} for part in p.parts)}
    (out/'input_manifest.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
    previous=os.environ.get('COURSE_WORK_DIR');os.environ['COURSE_WORK_DIR']=str(out/'workspace')
    try:
      for module in course['modules']:
       for lesson in module['lessons']:
        if args.only and lesson['id'] not in args.only:continue
        for role,key in [('case','case_notebook'),('lab','lab_notebook')]:
          if role not in args.roles:continue
          path=ROOT/lesson[key];folder=out/lesson['id']/role;folder.mkdir(parents=True)
          start=time.perf_counter();utc=datetime.now(timezone.utc).isoformat()
          record={'lesson_id':lesson['id'],'role':role,'kernel':'course-v2-'+lesson['profile'],
            'started_utc':utc,'source':str(path),'cwd':str(ROOT),
            'scope':'full guided computation' if role=='case' else 'empty lab scaffold; learner completion NOT_RUN'}
          book=None
          try:
            if not path.is_file():raise FileNotFoundError('Notebook не подготовлен: '+str(path))
            record['input_sha256']=sha(path)
            config=json.loads((ROOT/lesson['practice']/'lesson.json').read_text(encoding='utf-8'))
            record['data_sha256']={}
            for relative in config.get('inputs',[]):
              source=(ROOT/relative).resolve();source.relative_to(ROOT)
              record['data_sha256'][relative]=sha(source)
              target=folder/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True)
              target.write_bytes(source.read_bytes())
            record['step_sha256']={step:sha(ROOT/step) for step in
                nbformat.read(path,as_version=4).metadata.course.source_steps}
            (folder/'input.ipynb').write_bytes(path.read_bytes())
            book=nbformat.read(path,as_version=4)
            for cell in book.cells:
              if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
            # Только отчёт получает дополнительную ячейку паспорта реального ядра.
            audit=nbformat.v4.new_code_cell('import sys, platform, importlib.metadata, json\n'
              'print("AUDIT_KERNEL="+json.dumps({"python":sys.version,"executable":sys.executable,'
              '"platform":platform.platform(),"packages":dict(sorted((d.metadata["Name"],d.version) '
              'for d in importlib.metadata.distributions()))}))')
            audit.metadata['tags']=['audit-only'];book.cells.insert(0,audit)
            with (folder/'runner.log').open('w',encoding='utf-8') as log:
                with redirect_stderr(log),redirect_stdout(log):
                    NotebookClient(book,timeout=600,resources={'metadata':{'path':str(ROOT)}}).execute()
            record['status']='PASS'
          except (NoSuchKernel,FileNotFoundError,CellTimeoutError) as error:
            record.update(status='BLOCKED',error=type(error).__name__+': '+str(error))
          except Exception as error:
            record.update(status='FAIL',error=type(error).__name__+': '+str(error))
          finally:
            if book is not None:
              nbformat.write(book,folder/'executed.ipynb')
              lines=[]
              for cell in book.cells:
                if cell.cell_type!='code':continue
                lines.append('CELL '+str(cell.id)+' execution_count='+str(cell.execution_count))
                for output in cell.get('outputs',[]):
                  if output.output_type=='stream':lines.append(output.text)
                  elif output.output_type=='error':lines.append('\n'.join(output.traceback))
                  elif 'text/plain' in output.get('data',{}):lines.append(output.data['text/plain'])
              (folder/'cell_outputs.log').write_text('\n'.join(lines),encoding='utf-8')
          record['seconds']=time.perf_counter()-start
          (folder/'run.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
          runs.append(record);print(lesson['id'],role,record['status'],flush=True)
    finally:
      if previous is None:os.environ.pop('COURSE_WORK_DIR',None)
      else:os.environ['COURSE_WORK_DIR']=previous
    statuses={record['status'] for record in runs}
    overall='FAIL' if 'FAIL' in statuses else ('BLOCKED' if 'BLOCKED' in statuses else ('PASS' if runs else 'NOT_RUN'))
    summary={'status':overall,'runs':runs,
     'scope':'technical execution, not scientific or learner certification',
     'learner_work':'NOT_RUN','independent_scientific_review':'NOT_RUN','student_pilot':'NOT_RUN'}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    if summary['status']!='PASS':raise SystemExit(2 if summary['status']=='BLOCKED' else 1)

if __name__=='__main__':main()
