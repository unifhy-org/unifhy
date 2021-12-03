import unittest
import doctest

import unifhy


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    all_tests = test_loader.discover('.', pattern='test_*.py')
    test_suite.addTests(all_tests)

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
