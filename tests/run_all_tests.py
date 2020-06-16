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

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
