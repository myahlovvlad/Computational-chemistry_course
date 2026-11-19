from pathlib import Path
import csv
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_hplc_research import fit_response


class HplcAdequacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'practicuum/shared/data/atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as stream:
            rows=list(csv.DictReader(stream))
        cls.factors=np.array([[float(r[k]) for k in ['acetonitrile_percent','column_temperature_C','flow_mL_min']] for r in rows])

    def data(self,interaction=False):
        x=(self.factors-[65,35,1])/[5,5,.2]
        y=7+.2*x[:,0]-.4*x[:,1]+.5*x[:,2]
        centers=np.flatnonzero(np.all(x==0,axis=1));noise=np.linspace(-.01,.01,len(centers));y[centers]+=noise-noise.mean()
        if interaction:y+=2*x[:,0]*x[:,1]*x[:,2]
        return y

    def test_known_correct_mean_has_only_pure_error(self):
        result=fit_response(self.factors,self.data())
        self.assertAlmostEqual(result['SSE'],result['pure_error_SS'],places=11)
        self.assertGreater(result['lack_of_fit_p'],.99)

    def test_omitted_three_factor_effect_is_detected(self):
        result=fit_response(self.factors,self.data(interaction=True))
        self.assertTrue(result['lack_of_fit_detected'])
        self.assertLess(result['lack_of_fit_p'],.001)

    def test_validation_excludes_all_replicates_of_condition(self):
        result=fit_response(self.factors,self.data())
        for fold in result['folds']:
            train={tuple(self.factors[i]) for i in fold['train_row_ids']}
            test={tuple(self.factors[i]) for i in fold['test_row_ids']}
            self.assertFalse(train & test)
