import unittest
import doctest

import cm4twc


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    all_tests = test_loader.discover('.', pattern='test_*.py')
    test_suite.addTests(all_tests)

    test_suite.addTests(doctest.DocTestSuite(cm4twc.data))
    test_suite.addTests(doctest.DocTestSuite(cm4twc.time))
    test_suite.addTests(doctest.DocTestSuite(cm4twc.space))
    test_suite.addTests(doctest.DocTestSuite(cm4twc.model))
    test_suite.addTests(doctest.DocTestSuite(cm4twc._utils.clock))
    test_suite.addTests(doctest.DocTestSuite(cm4twc._utils.exchanger))
    test_suite.addTests(doctest.DocTestSuite(cm4twc._utils.compass))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    if not result.wasSuccessful():
        exit(1)
