import unittest
import doctest

import cm4twc


def get_dummy_dataset():
    return cm4twc.DataSet.from_file(
        ['dummy_data/dummy_driving_data.nc',
         'dummy_data/dummy_ancillary_data.nc'],
        name_mapping={'rainfall_flux': 'rainfall',
                      'snowfall_flux': 'snowfall',
                      'air_temperature': 'air_temperature',
                      'soil_temperature': 'soil_temperature'}
    )


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(cm4twc.data_))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
