import unittest
import doctest

import unifhy


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(unifhy._utils.exchanger))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
