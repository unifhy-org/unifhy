import numpy as np
from copy import deepcopy
import unittest
import doctest
import cf

import unifhy


def get_dummy_spacedomain(resolution):
    if resolution == "1deg":
        return unifhy.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
        )
    elif resolution == "pt5deg":
        return unifhy.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=0.5,
            longitude_extent=(-2, 1),
            longitude_resolution=0.5,
        )
    elif resolution == "pt25deg":
        return unifhy.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=0.25,
            longitude_extent=(-2, 1),
            longitude_resolution=0.25,
        )


def get_dummy_land_sea_mask_field(resolution):
    return cf.read(
        "data/dummy_global_land_sea_mask_{}.nc".format(resolution)
    ).select_field("land_sea_mask")


def get_dummy_flow_direction_field(resolution):
    return cf.read(
        "data/dummy_global_flow_direction_{}.nc".format(resolution)
    ).select_field("flow_direction")


class TestLatLonGridAPI(unittest.TestCase):
    def test_init_variants(self):
        # create a spacedomain using default instantiation
        sd1 = unifhy.LatLonGrid(
            latitude=[51.5, 52.5, 53.5, 54.5],
            longitude=np.array([-1.5, -0.5, 0.5]),
            latitude_bounds=np.array([[51, 52], [52, 53], [53, 54], [54, 55]]),
            longitude_bounds=[[-2, -1], [-1, 0], [0, 1]],
            # altitude=[2],
            # altitude_bounds=[0, 4]
        )

        # create a spacedomain using constructor method based on parameters
        sd2 = unifhy.LatLonGrid.from_extent_and_resolution(
            latitude_extent=(51, 55),
            latitude_resolution=1,
            longitude_extent=(-2, 1),
            longitude_resolution=1,
            # altitude_extent=(0, 4),
            # altitude_resolution=4
        )

        self.assertEqual(sd1, sd2)

        # # create a spacedomain using constructor method based on field
        # dataset = get_dummy_dataset('surfacelayer', 'daily', '1deg')
        # field = dataset[list(dataset.keys())[0]].field
        # sd3 = unifhy.LatLonGrid.from_field(field)
        #
        # # check that they are not equal
        # # (because field from dummy data has no Z coordinate)
        # self.assertNotEqual(sd1, sd3)
        # # check that they are equal if Z axis is ignored
        # self.assertTrue(sd1.is_space_equal_to(sd3.to_field(), ignore_z=True))


class TestGridComparison(unittest.TestCase):
    grids = [unifhy.LatLonGrid, unifhy.RotatedLatLonGrid, unifhy.BritishNationalGrid]

    axis_name = {
        "LatLonGrid": {"X": "longitude", "Y": "latitude", "Z": "altitude"},
        "RotatedLatLonGrid": {
            "X": "grid_longitude",
            "Y": "grid_latitude",
            "Z": "altitude",
        },
        "BritishNationalGrid": {
            "X": "projection_x_coordinate",
            "Y": "projection_y_coordinate",
            "Z": "altitude",
        },
    }

    extent_resolution = {
        "LatLonGrid": {
            "extent": {"X": [51, 55], "Y": [-2, 1], "Z": [0, 4]},
            "resolution": {"X": 1, "Y": 1, "Z": 4},
        },
        "RotatedLatLonGrid": {
            "extent": {"X": [-20, 50], "Y": [-10, 30], "Z": [0, 4]},
            "resolution": {"X": 5, "Y": 5, "Z": 4},
        },
        "BritishNationalGrid": {
            "extent": {"X": [1000, 2000], "Y": [3000, 4000], "Z": [0, 4]},
            "resolution": {"X": 100, "Y": 100, "Z": 4},
        },
    }

    extras = {
        "RotatedLatLonGrid": {
            "grid_north_pole_latitude": 0.0,
            "grid_north_pole_longitude": 0.0,
        }
    }

    def test_different_resolutions(self):
        for spacedomain in self.grids:
            cls_name = spacedomain.__name__
            with self.subTest(spacedomain=cls_name):
                # create a simple spacedomain
                params = {
                    "_".join(
                        [self.axis_name[cls_name][axis], prop]
                    ): self.extent_resolution[cls_name][prop][axis]
                    for prop in ["extent", "resolution"]
                    # for axis in ['X', 'Y', 'Z']
                    for axis in ["X", "Y"]
                }

                extras = self.extras.get(cls_name, {})

                sd1 = spacedomain.from_extent_and_resolution(**params, **extras)

                # create another spacedomain with same extents but halved X/Y resolutions
                params["{}_resolution".format(self.axis_name[cls_name]["X"])] /= 2
                params["{}_resolution".format(self.axis_name[cls_name]["Y"])] /= 2
                sd2 = spacedomain.from_extent_and_resolution(**params, **extras)

                # check that they are not equal
                # (because of different resolutions)
                self.assertNotEqual(sd1, sd2)
                self.assertTrue(sd1.spans_same_region_as(sd2))

    def test_different_regions(self):
        for spacedomain in self.grids:
            cls_name = spacedomain.__name__
            with self.subTest(spacedomain=cls_name):
                # create a simple spacedomain
                params = {
                    "_".join(
                        [self.axis_name[cls_name][axis], prop]
                    ): self.extent_resolution[cls_name][prop][axis]
                    for prop in ["extent", "resolution"]
                    # for axis in ['X', 'Y', 'Z']
                    for axis in ["X", "Y"]
                }

                extras = self.extras.get(cls_name, {})

                sd1 = spacedomain.from_extent_and_resolution(**params, **extras)

                # create another spacedomain with one more coordinate on X axis
                params2 = deepcopy(params)
                params2["{}_extent".format(self.axis_name[cls_name]["X"])][
                    0
                ] -= params2["{}_resolution".format(self.axis_name[cls_name]["X"])]
                sd2 = spacedomain.from_extent_and_resolution(**params2, **extras)

                # check that these are not equal
                self.assertNotEqual(sd1, sd2)

                # # create another spacedomain with a smaller Z axis extent
                # params3 = deepcopy(params)
                # params3["{}_resolution".format(self.axis_name[cls_name]['Z'])] = (
                #     params3["{}_resolution".format(self.axis_name[cls_name]['Z'])] / 2
                # )
                # params3["{}_extent".format(self.axis_name[cls_name]['Z'])][1] -= (
                #     params3["{}_resolution".format(self.axis_name[cls_name]['Z'])]
                # )
                # sd3 = spacedomain.from_extent_and_resolution(**params3, **extras)
                #
                # # check that they are not equal
                # # (because of different on Z axis)
                # self.assertNotEqual(sd1, sd3)
                # # check that they are equal if Z axis is ignored
                # self.assertTrue(sd1.is_space_equal_to(sd3.to_field(), ignore_z=True))


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestLatLonGridAPI))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestGridComparison))

    test_suite.addTests(doctest.DocTestSuite(unifhy.space))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
