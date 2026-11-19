from pathlib import Path
import sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_xanthine_chromatography import extract,diagnostics


class ChromatographySummaryTests(unittest.TestCase):
    def test_percent_RSD_is_not_absolute_SD(self):
        _,rows=extract(ROOT/'practicuum/shared/data/source-responses/xanthine_uhplc.xml')
        result=diagnostics(rows)
        self.assertAlmostEqual(result['derived_SD_s'][0],.1736)
        self.assertNotAlmostEqual(result['derived_SD_s'][0],.62)

    def test_interaction_is_invisible_in_OFAT(self):
        _,rows=extract(ROOT/'practicuum/shared/data/source-responses/xanthine_uhplc.xml')
        factors=np.array([[r[k] for k in ['ACN_percent','temperature_C','flow_mL_min']] for r in rows])
        x=(factors-[10,70,.5])/[5,5,.05]
        baseline=np.full(len(x),28.)
        alternative=baseline+100*x[:,0]*x[:,1]
        np.testing.assert_array_equal(baseline,alternative)
        self.assertNotEqual(28.,28.+100*1.*1.)
        result=diagnostics(rows)
        self.assertEqual(result['full_quadratic_rank'],7)
        self.assertEqual(result['additive_model_condition_mean_residual_df'],0)
