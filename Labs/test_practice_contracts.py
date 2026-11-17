"""Regressions against false completion, sign mistakes and ignored controls."""
import unittest
from practice_checks import CONTRACTS,check_case

class PracticeContractTests(unittest.TestCase):
    def test_blank_and_written_essays_do_not_pass(self):
        self.assertEqual(len(CONTRACTS),42)
        for identifier,case in CONTRACTS.items():
            self.assertEqual(check_case(identifier,None)['status'],'NOT_RUN')
            if case['mode']!='auto':
                self.assertEqual(check_case(identifier,{'claim':'all done'})['status'],'NOT_RUN')

    def test_energy_sign_and_censored_relation(self):
        self.assertEqual(check_case('M12-C1',{'delta_kJ_mol':26.255})['status'],'FAIL')
        self.assertEqual(check_case('M07-C1',{'p_bound':5,'p_relation':'>','exact_regression_eligible':True})['status'],'FAIL')

    def test_false_boolean_and_nonfinite_cannot_pass(self):
        self.assertEqual(check_case('M06-C1',{'has_converged':False,'finite_energy':True,'energy_unit':'kcal/mol'})['status'],'FAIL')
        self.assertEqual(check_case('M12-C1',{'delta_kJ_mol':float('nan')})['status'],'FAIL')

if __name__=='__main__':unittest.main()
