"""Создать изолированный профиль uv и зарегистрировать однозначное ядро Jupyter."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'scripts/environment'


def environment_path(project,profile,platform_name):
    """Keep an environment installed by the other OS intact in a shared checkout."""
    environment=Path(project)/('.venv-'+profile)
    if platform_name=='linux' and (environment/'Scripts/python.exe').is_file():
        return Path(project)/('.venv-linux-'+profile)
    if platform_name=='win32' and (environment/'bin/python').exists():
        return Path(project)/('.venv-windows-'+profile)
    return environment

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['base','chem','quantum-core','quantum','docking'],default='base')
    parser.add_argument('--uv',help='Путь к исполняемому uv, если его нет в PATH')
    parser.add_argument('--register-only',action='store_true')
    args=parser.parse_args()
    if args.profile in {'quantum','docking'} and sys.platform!='linux':
        raise SystemExit('Профили quantum (с dispersion/geometry) и docking устанавливаются в Linux/WSL. Для Windows доступны base/chem/quantum-core; quantum-core не включает dispersion и geometry optimizer.')
    uv=args.uv or shutil.which('uv')
    if not uv:raise SystemExit('Сначала выполните setup-windows.ps1 или setup-linux.sh для установки uv в локальный bootstrap.')
    # Разные профили используют разные каталоги: вводное ядро не получает RDKit случайно.
    environment=environment_path(PROJECT,args.profile,sys.platform)
    env=dict(os.environ,UV_PROJECT_ENVIRONMENT=str(environment),PYTHONUTF8='1',PYTHONNOUSERSITE='1')
    groups=[] if args.profile=='base' else ['--group',args.profile]
    if not args.register_only:
        command=[uv,'sync','--frozen','--project',str(PROJECT),'--python','3.12','--no-default-groups',*groups]
        subprocess.run(command,cwd=ROOT,env=env,check=True)
    python=environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():raise SystemExit('Профиль не установлен: '+str(environment))
    spec={'argv':[str(uv),'run','--frozen','--project',str(PROJECT),'--no-default-groups',*groups,
                  'python','-m','ipykernel_launcher','-f','{connection_file}'],
          'display_name':'Курс химии v2 · '+args.profile+' · uv','language':'python',
          'env':{'UV_PROJECT_ENVIRONMENT':str(environment),'PYTHONUTF8':'1','PYTHONNOUSERSITE':'1',
                 'PYTHONPATH':str(ROOT/'practicuum/shared'),'MPLBACKEND':'Agg','COURSE_ROOT':str(ROOT)}}
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary);(folder/'kernel.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        # Установка kernelspec выполняется именно Python выбранного профиля.
        subprocess.run([str(python),'-m','jupyter','kernelspec','install','--user','--name','course-v2-'+args.profile,
                        '--replace',str(folder)],env=env,check=True)
    print(json.dumps({'profile':args.profile,'environment':str(environment),'kernel':'course-v2-'+args.profile,
                      'uv':subprocess.check_output([uv,'--version'],text=True).strip()},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
