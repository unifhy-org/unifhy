import numpy as np
import unittest
import doctest
import cf

import cm4twc
from tests.test_data import get_dummy_dataset


def get_dummy_spacedomain(resolution):
    if resolution == '1deg':
        return cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )
    elif resolution == 'pt5deg':
        return cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=0.5,
            longitude_extent=(-2, 1),
            longitude_resolution=0.5,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )
    elif resolution == 'pt2deg':
        return cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=0.2,
            longitude_extent=(-2, 1),
            longitude_resolution=0.2,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )


def get_dummy_land_sea_mask_field(resolution):
    return cf.read(
        'data/dummy_global_land_sea_mask_{}.nc'.format(resolution)
    ).select_field('land_sea_mask')


def get_dummy_flow_direction_field(resolution):
    return cf.read(
        'data/dummy_global_flow_direction_{}.nc'.format(resolution)
    ).select_field('flow_direction')


class TestLatLonGridAPI(unittest.TestCase):

    def test_init_variants(self):
        sd1 = cm4twc.LatLonGrid(
            latitude=[51.5, 52.5, 53.5, 54.5],
            longitude=np.array([-1.5, -0.5, 0.5]),
            latitude_bounds=np.array([[51, 52], [52, 53], [53, 54], [54, 55]]),
            longitude_bounds=[[-2, -1], [-1, 0], [0, 1]],
            altitude=[2],
            altitude_bounds=[0, 4]
        )

        sd2 = cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )

        self.assertEqual(sd1, sd2)

        dataset = get_dummy_dataset('surfacelayer', 'daily', '1deg')
        field = dataset[list(dataset.keys())[0]]
        sd3 = cm4twc.LatLonGrid.from_field(field)

        # field from dummy data has no Z coordinate
        self.assertNotEqual(sd1, sd3)
        self.assertTrue(sd1.is_space_equal_to(sd3.to_field(), ignore_z=True))


class TestLatLonGridComparison(unittest.TestCase):

    def test_latlongrid_resolutions(self):
        sd1 = cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )

        sd2 = cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=0.5,
            longitude_extent=(-2, 1),
            longitude_resolution=0.5,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )

        self.assertNotEqual(sd1, sd2)
        self.assertTrue(sd1.spans_same_region_as(sd2))

    def test_latlongrid_regions(self):
        sd1 = cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )

        sd2 = cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(50, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            altitude_extent=(0, 4),
            altitude_resolution=4
        )

        self.assertNotEqual(sd1, sd2)

        sd3 = cm4twc.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            altitude_extent=(0, 2),
            altitude_resolution=2
        )

        self.assertNotEqual(sd1, sd3)
        self.assertTrue(sd1.is_space_equal_to(sd3.to_field(), ignore_z=True))


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestLatLonGridAPI)
    )
    test_suite.addTests(
        test_loader.loadTestsFromTestCase(TestLatLonGridComparison)
    )

    test_suite.addTests(doctest.DocTestSuite(cm4twc.space))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
