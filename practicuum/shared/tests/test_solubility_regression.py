from pathlib import Path
import sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_istradefylline_solubility import vanthoff


class SolubilityRegressionTests(unittest.TestCase):
    def test_kelvin_scaling_recovers_known_slope(self):
        T=np.array([293.15,303.15,313.15,323.15,333.15])
        x=np.exp(-4-50000/8.31446261815324*(1/T-1/313.15))
        result=vanthoff(T,x)
        self.assertAlmostEqual(result['apparent_slope_enthalpy_kJ_mol'],50.,places=10)

    def test_constant_concentration_unit_factor_does_not_change_slope(self):
        T=np.array([293.15,303.15,313.15,323.15,333.15]);x=np.array([.01,.02,.035,.06,.1])
        a=vanthoff(T,x);b=vanthoff(T,x*.001)
        self.assertAlmostEqual(a['apparent_slope_enthalpy_kJ_mol'],b['apparent_slope_enthalpy_kJ_mol'],places=10)
        np.testing.assert_allclose(a['residuals_ln_x'],b['residuals_ln_x'],atol=1e-12)

    def test_no_temperature_variation_cannot_identify_enthalpy(self):
        with self.assertRaises(ValueError):vanthoff([298.15]*5,[.01,.02,.03,.04,.05])

    def test_missing_solubility_is_not_zero(self):
        with self.assertRaises(ValueError):vanthoff([293,303,313,323,333],[.01,.02,float('nan'),.04,.05])
