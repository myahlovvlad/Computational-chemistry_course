from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,platform,shutil,sys,time
import nbformat
from nbclient import NotebookClient
R=Path(__file__).resolve().parents[1];package=R/'parser/dist/professional-conformers-20261119'
out=R/'practicuum/evidence/20261119-portable-professional-conformers';out.mkdir(exist_ok=False)
shutil.copyfile(__file__,out/'runner-source.py');runs=[]
for id in ['M06-L01','M06-L02']:
 source=package/f'practicuum/modules/M06/lessons/{id[-3:]}/Notebooks_cases/01_case.ipynb'
 start=time.perf_counter();record={'lesson':id,'started_utc':datetime.now(timezone.utc).isoformat(),
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'actual frozen-data recomputation from portable package, not a new external xTB run'}
 shutil.copyfile(source,out/(id+'-input.ipynb'));nb=nbformat.read(source,as_version=4)
 for cell in nb.cells:
  if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
 try:
  env=dict(os.environ,COURSE_WORK_DIR=str(R/'tmp/portable-conformer-work'),PYTHONUTF8='1')
  NotebookClient(nb,kernel_name='course-v2-chem',timeout=600,resources={'metadata':{'path':str(package)}}).execute(env=env)
  record['status']='PASS'
 except Exception as error:record.update(status='FAIL',type=type(error).__name__,message=str(error))
 nbformat.write(nb,out/(id+'-executed.ipynb'));record['seconds']=time.perf_counter()-start;runs.append(record)
 print(id,record['status'],flush=True)
report={'status':'PASS' if all(r['status']=='PASS' for r in runs) else 'FAIL','runs':runs,'platform':platform.platform(),
 'python':sys.version,'data_manifest_sha256':hashlib.sha256((package/'practicuum/shared/data/conformer_research/bundle-manifest.json').read_bytes()).hexdigest(),
 'student_solutions':'NOT_RUN','scientific_review':'NOT_RUN','Stepik_platform':'NOT_RUN'}
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if report['status']!='PASS':raise SystemExit(1)
