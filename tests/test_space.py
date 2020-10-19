"""
TODO: add tests using cm4twc.LatLonGrid
"""
import unittest
import doctest

import cm4twc


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


def get_sciencish_spacedomain():
    return cm4twc.RotatedLatLonGrid(
        grid_latitude=[2.2, 1.76, 1.32, 0.88, 0.44, 0., -0.44, -0.88, -1.32, -1.76],
        grid_longitude=[-4.7, -4.26, -3.82, -3.38, -2.94, -2.5, -2.06, -1.62, -1.18],
        grid_latitude_bounds=[[2.42, 1.98], [1.98, 1.54], [1.54, 1.1], [1.1, 0.66],
                              [0.66, 0.22], [0.22, -0.22], [-0.22, -0.66],
                              [-0.66, -1.1], [-1.1, -1.54], [-1.54, -1.98]],
        grid_longitude_bounds=[[-4.92, -4.48], [-4.48, -4.04], [-4.04, -3.6],
                               [-3.6,  -3.16], [-3.16, -2.72], [-2.72, -2.28],
                               [-2.28, -1.84], [-1.84, -1.4], [-1.4, -0.96]],
        earth_radius=6371007., grid_north_pole_latitude=38.0,
        grid_north_pole_longitude=190.0,
        altitude=1.5,
        altitude_bounds=[1.0, 2.0]
    )


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(doctest.DocTestSuite(cm4twc.space))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
