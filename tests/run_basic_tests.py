import unittest
import doctest

from tests.test_model import BasicTestModel
from tests.test_space import TestLatLonGridAPI, TestGridComparison
from tests.test_time import TestTimeDomainAPI, TestTimeDomainComparison
from tests.test_utils.test_clock import TestClock
from tests.test_component import TestSubstituteComponent
import unifhy


class TestModelSameTimeSameSpace(BasicTestModel, unittest.TestCase):
    # flag to specify that components are to run at same temporal resolutions
    t = "same_t"
    # flag to specify that components are to run at same spatial resolution
    s = "same_s"


class TestModelDiffTimeDiffSpace(BasicTestModel, unittest.TestCase):
    # flag to specify that components are to run at different temporal resolutions
    t = "diff_t"
    # flag to specify that components are to run at different spatial resolutions
    s = "diff_s"


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))

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

    if not result.wasSuccessful():
        exit(1)
