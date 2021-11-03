import unittest
import doctest

import cm4twc._utils


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(cm4twc._utils.compass))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
