from pathlib import Path
import hashlib,json,os,shutil
import nbformat
from nbclient import NotebookClient
R=Path(__file__).resolve().parents[1];package=R/'parser/dist/main-method-articles-20261119'
out=R/'practicuum/evidence/20261119-main-portable-article-review';out.mkdir(exist_ok=False)
source=package/'practicuum/modules/M12/lessons/L02/Notebooks_cases/01_case.ipynb'
shutil.copyfile(__file__,out/'runner-source.py');shutil.copyfile(source,out/'input.ipynb')
nb=nbformat.read(source,as_version=4)
for cell in nb.cells:
 if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
record={'scope':'Actual M12 guided QSAR/primary-article recomputation from portable package, not new training',
 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'Stepik_platform':'NOT_RUN','student_review':'NOT_RUN'}
try:
 env=dict(os.environ,COURSE_WORK_DIR=str(R/'tmp/main-portable-article-work'),PYTHONUTF8='1')
 NotebookClient(nb,kernel_name='course-v2-chem',timeout=600,resources={'metadata':{'path':str(package)}}).execute(env=env)
 record['status']='PASS'
except Exception as e:record.update(status='FAIL',error=str(e))
nbformat.write(nb,out/'executed.ipynb');(out/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
print(record['status'],record['scope'])
if record['status']!='PASS':raise SystemExit(1)
