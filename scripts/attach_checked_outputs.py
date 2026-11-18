"""Перенести фактические outputs разбора после сравнения ячеек с сохранённым запуском."""
import argparse,json
from pathlib import Path
import nbformat

ROOT=Path(__file__).resolve().parents[1]
def cells(book):return [(cell.cell_type,cell.source) for cell in book.cells]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args();folder=args.evidence.resolve()
    folder.relative_to(ROOT)
    course=json.loads((ROOT/'programm/course.json').read_text(encoding='utf-8'))
    lessons={lesson['id']:lesson for module in course['modules'] for lesson in module['lessons']}
    summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    count=0
    for run in summary['runs']:
      if run['role']!='case':continue
      if run['status']!='PASS':raise ValueError('Разбор не прошёл: '+run['lesson_id'])
      lesson=lessons[run['lesson_id']];target=ROOT/lesson['case_notebook']
      current=nbformat.read(target,as_version=4)
      executed=nbformat.read(folder/run['lesson_id']/'case/executed.ipynb',as_version=4)
      executed.cells=[cell for cell in executed.cells if 'audit-only' not in cell.metadata.get('tags',[])]
      if cells(current)!=cells(executed):raise ValueError('Ячейки изменились после запуска: '+run['lesson_id'])
      # Метаданные источников сохраняем из канонического Notebook; меняются только наблюдаемые outputs.
      for before,after in zip(current.cells,executed.cells):
        if before.cell_type=='code':before.outputs=after.outputs;before.execution_count=after.execution_count
      current.metadata.course['output_evidence']=(folder/run['lesson_id']/'case/run.json').relative_to(ROOT).as_posix()
      nbformat.validate(current);nbformat.write(current,target);count+=1
    print('Attached actual outputs:',count,'guided notebooks; learner answers unchanged')

if __name__=='__main__':main()
