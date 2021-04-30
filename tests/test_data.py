import unittest
import doctest

import cm4twc


def get_dummy_dataset(component_category, time_res, space_res):
    return cm4twc.DataSet(
        'data/dummy_{}_data_{}_{}.nc'.format(component_category, time_res,
                                             space_res)
    )


def get_dummy_component_substitute_dataset(component_category, time_res,
                                           space_res):
    return cm4twc.DataSet(
        'data/dummy_{}_substitute_data_{}_{}.nc'.format(component_category,
                                                        time_res, space_res)
    )


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(cm4twc.data))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
