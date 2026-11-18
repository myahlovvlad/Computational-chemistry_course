"""Служебные операции курса: входы, рабочая папка и досье, без скрытой химической модели."""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=Path(__file__).with_name('data')
ESOL_SHA='8c06a76f0c6487d29ab0f903e6a7a7139f189ab3c1178f159c8be8964602f189'
OBSERVED='measured log solubility in mols per litre'
PREDICTED='ESOL predicted log solubility in mols per litre'

def sha256(path):
    """Сумма относится к байтам файла, а не к истинности химического утверждения."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_json(name):
    return json.loads((DATA/name).read_text(encoding='utf-8'))

def compounds():
    return read_json('compounds.json')

def compound(name):
    return next(record for record in compounds() if record['name']==name)

def esol():
    path=DATA/'esol.csv'
    if sha256(path)!=ESOL_SHA:raise ValueError('Изменилась версия ESOL: проверьте источник, не заменяйте hash ради теста')
    with path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    if len(rows)!=1128:raise ValueError('Неожиданное число записей ESOL')
    return [dict(row_id=i,name=r['Compound ID'],smiles=r['smiles'],measured=float(r[OBSERVED]),
                 predicted=float(r[PREDICTED])) for i,r in enumerate(rows)]

def workspace(lesson_id,role):
    # Автопрогон задаёт отдельный COURSE_WORK_DIR; личные результаты остаются в workspace урока.
    base=Path(os.environ.get('COURSE_WORK_DIR',str(ROOT/'practicuum/workspace')))
    path=base/lesson_id/role;path.mkdir(parents=True,exist_ok=True);return path

def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def submission_feedback(answer):
    if answer is None:return {'status':'NOT_RUN','scope':'student work','message':'Сначала выполните собственный кейс и объясните результат.'}
    return {'status':'REVIEW_REQUIRED','scope':'scientific reasoning not graded automatically',
            'message':'Сопоставьте код, наблюдения, ограничения и следующий эксперимент с рубрикой.'}

DOSSIER_SECTIONS=['01_question_and_sources','02_forms_and_descriptors','03_solvent',
 '04_reactions_and_kinetics','05_spectroscopy_and_instrument','06_chromatography',
 '07_targets_and_exposure','08_retrosynthesis_and_process','09_laboratory_verification']

def init_dossier(path=None):
    """Не перезаписывает уже созданные студентом записи."""
    if path is None:
        # Одно досье на весь курс; папки отдельных уроков содержат его доказательства.
        base=Path(os.environ.get('COURSE_WORK_DIR',str(ROOT/'practicuum/workspace')))
        path=base/'my_research'
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    for section in DOSSIER_SECTIONS:
        file=path/(section+'.md')
        if not file.exists():file.write_text('# '+section+'\n\nВопрос:\nИсточник и условия:\nМетод:\nНаблюдение/расчёт:\nИнтерпретация:\nНеопределённость:\nСледующий эксперимент:\n',encoding='utf-8')
    concept=path/'concept_map.json'
    if not concept.exists():write_json(concept,{'nodes':[],'edges':[],'instruction':'Для ребра нужны объяснение, источник, ограничение и следующая проверка.'})
    return path
