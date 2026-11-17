"""Back up the existing learner files, then copy the new paired curriculum."""
from datetime import datetime
from pathlib import Path
import shutil
import json
source=Path('/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course/tmp/paired-case-notebooks-20261117')
target=Path('/home/miakhlov/course-notebooks')
backup=Path('/home/miakhlov')/('course-notebooks-before-pairs-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(exist_ok=False)
for name in ['Labs/notebooks','Labs/guides','Labs/solutions','tools','Stepik_course']:
    if (target/name).exists():shutil.copytree(target/name,backup/name,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['README.md','course-manifest.json','NOTEBOOK_ENVIRONMENT.md']:
    if (target/name).is_file():shutil.copy2(target/name,backup/name)
for name in ['Labs','tools','Module_theory','Literature','Stepik_course']:
    shutil.copytree(source/name,target/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','results','executed','converted'))
for name in ['README.md','course-manifest.json','NOTEBOOK_ENVIRONMENT.md']:
    shutil.copy2(source/name,target/name)
print(json.dumps({'source':str(source),'target':str(target),'backup':str(backup),'active_notebooks':len(list((target/'Labs/notebooks').glob('lab*.ipynb')))},indent=2))
