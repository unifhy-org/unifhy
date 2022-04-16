import unittest
import doctest

import unifhy
from tests.test_model import (
    TestModelSameTimeSameSpace, TestModelSameTimeDiffSpace,
    TestModelDiffTimeSameSpace, TestModelDiffTimeDiffSpace
)
from tests.test_space import (
    TestLatLonGridAPI, TestGridComparison
)
from tests.test_time import (
    TestTimeDomainAPI, TestTimeDomainComparison
)
from tests.test_utils.test_clock import TestClock


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeDiffSpace)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeSameSpace)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace)
    )

    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestLatLonGridAPI)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestGridComparison)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestTimeDomainAPI)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestTimeDomainComparison)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestClock)
    )

    test_suite.addTests(doctest.DocTestSuite(unifhy.data))
    test_suite.addTests(doctest.DocTestSuite(unifhy.time))
    test_suite.addTests(doctest.DocTestSuite(unifhy.space))
    test_suite.addTests(doctest.DocTestSuite(unifhy.model))
    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.clock))
    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.exchanger))
    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.compass))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if not result.wasSuccessful():
        exit(1)
