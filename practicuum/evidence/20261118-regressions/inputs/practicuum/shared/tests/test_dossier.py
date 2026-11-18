"""Проверка накопительного досье: переход урока не должен стирать работу."""
from pathlib import Path
import os,sys,tempfile,unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from course_support import init_dossier,workspace,DOSSIER_SECTIONS,submission_feedback

class DossierContract(unittest.TestCase):
    def test_one_dossier_survives_lesson_transition(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'COURSE_WORK_DIR':tmp}):
            first=init_dossier()
            question=first/(DOSSIER_SECTIONS[0]+'.md')
            original='Мой вопрос с неизвестными условиями'
            question.write_text(original,encoding='utf-8')
            workspace('M03-L01','lab')
            self.assertEqual(first,init_dossier())
            self.assertEqual(question.read_text(encoding='utf-8'),original)
            self.assertEqual(len(list(first.glob('*.md'))),9)

    def test_empty_answer_is_not_success(self):
        self.assertEqual(submission_feedback(None)['status'],'NOT_RUN')
        self.assertEqual(submission_feedback({'answer':'текст'})['status'],'REVIEW_REQUIRED')

if __name__=='__main__':unittest.main()
