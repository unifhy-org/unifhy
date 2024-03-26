import unittest
import doctest

import unifhy


def get_dummy_dataset(component_category, time_res, space_res):
    return unifhy.DataSet(
        "data/dummy_{}_data_{}_{}.nc".format(component_category, time_res, space_res)
    )


def get_dummy_component_substitute_dataset(component_category, time_res, space_res):
    return unifhy.DataSet(
        "data/dummy_{}_substitute_data_{}_{}.nc".format(
            component_category, time_res, space_res
        )
    )


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(unifhy.data))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
