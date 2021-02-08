import unittest
import doctest

from tests.test_model import BasicTestModel
import cm4twc


class TestModelSameTimeSameSpace(BasicTestModel, unittest.TestCase):
    # flag to specify that components are to run at same temporal resolutions
    t = 'sync'
    # flag to specify that components are to run at same spatial resolution
    s = 'match'


class TestModelDiffTimeDiffSpace(BasicTestModel, unittest.TestCase):
    # flag to specify that components are to run at different temporal resolutions
    t = 'async'
    # flag to specify that components are to run at different spatial resolutions
    s = 'remap'


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelSameTimeSameSpace))
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))

    test_suite.addTests(doctest.DocTestSuite(cm4twc.data))
    test_suite.addTests(doctest.DocTestSuite(cm4twc.time))
    test_suite.addTests(doctest.DocTestSuite(cm4twc.space))
    test_suite.addTests(doctest.DocTestSuite(cm4twc.model))
    test_suite.addTests(doctest.DocTestSuite(cm4twc._utils.exchanger))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
