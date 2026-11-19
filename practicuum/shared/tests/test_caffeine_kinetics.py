from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_caffeine_kinetics import rate_law


class RateLawTests(unittest.TestCase):
    def setUp(self):
        self.x=np.array([.02,.04,.06,.08,.10])
        self.y=np.array([.014,.024,.052,.059,.066])

    def test_PRESS_matches_independent_refitting(self):
        result=rate_law(self.x,self.y)
        errors=[]
        for i in range(len(self.x)):
            keep=np.arange(len(self.x))!=i
            X=np.column_stack([np.ones(keep.sum()),self.x[keep]])
            b=np.linalg.lstsq(X,self.y[keep],rcond=None)[0]
            errors.append(self.y[i]-np.array([1,self.x[i]])@b)
        self.assertAlmostEqual(result['leave_one_concentration_out_RMSE_min_inverse'],np.sqrt(np.mean(np.square(errors))),places=13)

    def test_time_unit_conversion_scales_rates_and_intervals(self):
        minute=rate_law(self.x,self.y)
        second=rate_law(self.x,self.y/60)
        self.assertAlmostEqual(minute['k2_L_mol_inverse_min_inverse']/60,second['k2_L_mol_inverse_min_inverse'])
        np.testing.assert_allclose(np.array(minute['conditional_OLS_CI95'])/60,second['conditional_OLS_CI95'])
        self.assertAlmostEqual(minute['intercept_F_test']['p'],second['intercept_F_test']['p'])

    def test_constant_concentration_is_not_identifiable(self):
        with self.assertRaises(ValueError):rate_law(np.ones(5),self.y)

    def test_invalid_rates_rejected(self):
        with self.assertRaises(ValueError):rate_law(self.x,[.014,.024,float('nan'),.059,.066])
