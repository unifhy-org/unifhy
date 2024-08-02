import unittest
import unifhy
from tests.test_model import AdvancedTestModel


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

        class TestModelDiffTimeDiffSpace(AdvancedTestModel, unittest.TestCase):
            # flag to specify that components are to run at same temporal resolutions
            t = "diff_t"
            # flag to specify that components are to run at same spatial resolution
            s = "diff_s"
            #
            doe = doe             
            
        test_loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()
    
        test_suite.addTests(test_loader.loadTestsFromTestCase(TestModelDiffTimeDiffSpace))
    
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        print(result)
        results.append(result)
    
    for result in results:
        if not result.wasSuccessful():
                exit(1)
