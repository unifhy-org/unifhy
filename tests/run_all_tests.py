import unittest
import doctest

import unifhy
from tests.test_model import AdvancedTestModel

from tests.test_space import TestLatLonGridAPI, TestGridComparison
from tests.test_time import TestTimeDomainAPI, TestTimeDomainComparison
from tests.test_utils.test_clock import TestClock
from tests.test_component import TestSubstituteComponent


if __name__ == "__main__":
    
    does = (
        (sl, ss, ow, nsl, nss, now)
        for sl in ("c",)
        for ss in ("c",)
        for ow in ("c",)
        for nsl in ("c", "d", "n")
        for nss in ("c", "d", "n")
        for now in ("c", "d", "n")
    )
    
    results = []
    for doe in does:
        print(doe)
        class TestModelSameTimeSameSpace(AdvancedTestModel, unittest.TestCase):
            # flag to specify that components are to run at same temporal resolutions
            t = "same_t"
            # flag to specify that components are to run at same spatial resolution
            s = "same_s"
            #
            doe = doe 

        class TestModelSameTimeDiffSpace(AdvancedTestModel, unittest.TestCase):
            # flag to specify that components are to run at same temporal resolutions
            t = "same_t"
            # flag to specify that components are to run at same spatial resolution
            s = "diff_s"
            #
            doe = doe 

        class TestModelDiffTimeSameSpace(AdvancedTestModel, unittest.TestCase):
            # flag to specify that components are to run at same temporal resolutions
            t = "diff_t"
            # flag to specify that components are to run at same spatial resolution
            s = "same_s"
            #
            doe = doe 

        class TestModelDiffTimeDiffSpace(AdvancedTestModel, unittest.TestCase):
            # flag to specify that components are to run at same temporal resolutions
            t = "diff_t"
            # flag to specify that components are to run at same spatial resolution
            s = "diff_s"
            #
            doe = doe             
            
        test_loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()
    
        test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace))
        test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelSameTimeDiffSpace))
        test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelDiffTimeSameSpace))
        test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))
    
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        print(result)
        results.append(result)
    
    print('Other tests')
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestLatLonGridAPI))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestGridComparison))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestTimeDomainAPI))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestTimeDomainComparison))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestClock))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestSubstituteComponent))

    test_suite.addTests(doctest.DocTestSuite(unifhy.data))
    test_suite.addTests(doctest.DocTestSuite(unifhy.time))
    test_suite.addTests(doctest.DocTestSuite(unifhy.space))
    test_suite.addTests(doctest.DocTestSuite(unifhy.component))
    test_suite.addTests(doctest.DocTestSuite(unifhy.model))
    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.clock))
    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.exchanger))
    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.compass))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    print(result)
    results.append(result)

    for result in results:
        if not result.wasSuccessful():
                exit(1)
