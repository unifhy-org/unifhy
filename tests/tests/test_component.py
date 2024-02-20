import unittest
import doctest
from importlib import import_module
from datetime import timedelta
import numpy
import cf

import unifhy

from .test_time import get_dummy_timedomain
from .test_space import (
    get_dummy_spacedomain,
    get_dummy_land_sea_mask_field,
    get_dummy_flow_direction_field,
)
from .test_data import (
    get_dummy_dataset,
    get_dummy_component_substitute_dataset,
)

time_resolutions = {
    "surfacelayer": {"same_t": "daily", "diff_t": "daily"},
    "subsurface": {"same_t": "daily", "diff_t": "4daily"},
    "openwater": {"same_t": "daily", "diff_t": "2daily"},
    "nutrientsurfacelayer": {"same_t": "daily", "diff_t": "2daily"},
    "nutrientsubsurface": {"same_t": "daily", "diff_t": "4daily"},
    "nutrientopenwater": {"same_t": "daily", "diff_t": "daily"},
}

space_resolutions = {
    "surfacelayer": {"same_s": "1deg", "diff_s": "1deg"},
    "subsurface": {"same_s": "1deg", "diff_s": "pt5deg"},
    "openwater": {"same_s": "1deg", "diff_s": "pt25deg"},
    "nutrientsurfacelayer": {"same_s": "1deg", "diff_s": "1deg"},
    "nutrientsubsurface": {"same_s": "1deg", "diff_s": "pt5deg"},
    "nutrientopenwater": {"same_s": "1deg", "diff_s": "pt25deg"},
}

parameters = {
    "surfacelayer": {"same_s": {}, "diff_s": {}},
    "subsurface": {
        "same_s": {
            "parameter_a": cf.read(
                "data/dummy_subsurface_parameter_a_{}"
                ".nc".format(space_resolutions["subsurface"]["same_s"])
            ).select_field("long_name=parameter_a")
        },
        "diff_s": {
            "parameter_a": cf.read(
                "data/dummy_subsurface_parameter_a_{}"
                ".nc".format(space_resolutions["subsurface"]["diff_s"])
            ).select_field("long_name=parameter_a")
        },
    },
    "openwater": {
        "same_s": {"parameter_c": [3, "1"]},
        "diff_s": {"parameter_c": [3, "1"]},
    },
    "nutrientsurfacelayer": {"same_s": {}, "diff_s": {}},
    "nutrientsubsurface": {
        "same_s": {
            "parameter_d": cf.read(
                "data/dummy_nutrientsubsurface_parameter_d_{}"
                ".nc".format(space_resolutions["nutrientsubsurface"]["same_s"])
            ).select_field("long_name=parameter_d")
        },
        "diff_s": {
            "parameter_d": cf.read(
                "data/dummy_nutrientsubsurface_parameter_d_{}"
                ".nc".format(space_resolutions["nutrientsubsurface"]["diff_s"])
            ).select_field("long_name=parameter_d")
        },
    },
    "nutrientopenwater": {
        "same_s": {"parameter_e": [3, "1"]},
        "diff_s": {"parameter_e": [3, "1"]},
    },
}

constants = {
    "surfacelayer": {"same_s": {}, "diff_s": {}},
    "subsurface": {"same_s": {}, "diff_s": {}},
    "openwater": {
        "same_s": {"constant_c": cf.Data(3, "1")},
        "diff_s": {"constant_c": cf.Data(3, "1")},
    },
    "nutrientsurfacelayer": {"same_s": {}, "diff_s": {}},
    "nutrientsubsurface": {"same_s": {}, "diff_s": {}},
    "nutrientopenwater": {
        "same_s": {"constant_d": cf.Data(3, "1")},
        "diff_s": {"constant_d": cf.Data(3, "1")},
    },
}

records = {
    "surfacelayer": {
        "same_t": {
            "output_x": {
                timedelta(days=1): ["instantaneous"],
                timedelta(days=8): ["cumulative", "average", "min", "max"],
            },
            # using aliases for methods in 'output_x'
            "transfer_i": {timedelta(days=1): ["point"]},
            "transfer_j": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
            "state_b": {timedelta(days=1): ["point"]},
        },
        "diff_t": {
            "output_x": {
                timedelta(days=1): ["point"],
                timedelta(days=8): ["sum", "mean", "minimum", "maximum"],
            },
            # using defaults for methods in 'output_x'
            "transfer_i": {timedelta(days=1): ["point"]},
            "transfer_j": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
            "state_b": {timedelta(days=1): ["point"]},
        },
    },
    "subsurface": {
        "same_t": {
            "output_x": {
                timedelta(days=1): ["instantaneous"],
                timedelta(days=8): ["cumulative", "average", "min", "max"],
            },
            # using aliases for methods in 'output_x'
            "transfer_k": {timedelta(days=1): ["point"]},
            "transfer_m": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
            "state_b": {timedelta(days=1): ["point"]},
        },
        "diff_t": {
            "output_x": {
                timedelta(days=4): ["point"],
                timedelta(days=8): ["sum", "mean", "minimum", "maximum"],
            },
            # using defaults for methods in 'output_x'
            "transfer_k": {timedelta(days=4): ["point"]},
            "transfer_m": {timedelta(days=4): ["point"]},
            "state_a": {timedelta(days=4): ["point"]},
            "state_b": {timedelta(days=4): ["point"]},
        },
    },
    "openwater": {
        "same_t": {
            "output_x": {
                timedelta(days=1): ["instantaneous"],
                timedelta(days=8): ["cumulative", "average", "min", "max"],
            },
            # using aliases for methods in 'output_x'
            "output_y": {timedelta(days=1): ["point"]},
            "transfer_l": {timedelta(days=1): ["point"]},
            "transfer_n": {timedelta(days=1): ["point"]},
            "transfer_o": {timedelta(days=1): ["point"]},
            "transfer_p": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
        },
        "diff_t": {
            "output_x": {
                timedelta(days=2): ["point"],
                timedelta(days=8): ["sum", "mean", "minimum", "maximum"],
            },
            # using defaults for methods in 'output_x'
            "output_y": {timedelta(days=2): ["point"]},
            "transfer_l": {timedelta(days=2): ["point"]},
            "transfer_n": {timedelta(days=2): ["point"]},
            "transfer_o": {timedelta(days=2): ["point"]},
            "transfer_p": {timedelta(days=2): ["point"]},
            "state_a": {timedelta(days=2): ["point"]},
        },
    },
    "nutrientsurfacelayer": {
        "same_t": {
            "output_x": {
                timedelta(days=1): ["instantaneous"],
                timedelta(days=8): ["cumulative", "average", "min", "max"],
            },
            # using aliases for methods in 'output_x'
            "transfer_a": {timedelta(days=1): ["point"]},
            "transfer_b": {timedelta(days=1): ["point"]},
            "transfer_h": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
            "state_b": {timedelta(days=1): ["point"]},
        },
        "diff_t": {
            "output_x": {
                timedelta(days=1): ["point"],
                timedelta(days=8): ["sum", "mean", "minimum", "maximum"],
            },
            # using defaults for methods in 'output_x'
            "transfer_a": {timedelta(days=1): ["point"]},
            "transfer_b": {timedelta(days=1): ["point"]},
            "transfer_h": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
            "state_b": {timedelta(days=1): ["point"]},
        },
    },
    "nutrientsubsurface": {
        "same_t": {
            "output_x": {
                timedelta(days=1): ["instantaneous"],
                timedelta(days=8): ["cumulative", "average", "min", "max"],
            },
            # using aliases for methods in 'output_x'
            "transfer_c": {timedelta(days=1): ["point"]},
            "transfer_e": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
            "state_b": {timedelta(days=1): ["point"]},
        },
        "diff_t": {
            "output_x": {
                timedelta(days=4): ["point"],
                timedelta(days=8): ["sum", "mean", "minimum", "maximum"],
            },
            # using defaults for methods in 'output_x'
            "transfer_c": {timedelta(days=4): ["point"]},
            "transfer_e": {timedelta(days=4): ["point"]},
            "state_a": {timedelta(days=4): ["point"]},
            "state_b": {timedelta(days=4): ["point"]},
        },
    },
    "nutrientopenwater": {
        "same_t": {
            "output_x": {
                timedelta(days=1): ["instantaneous"],
                timedelta(days=8): ["cumulative", "average", "min", "max"],
            },
            # using aliases for methods in 'output_x'
            "output_y": {timedelta(days=1): ["point"]},
            "transfer_d": {timedelta(days=1): ["point"]},
            "transfer_f": {timedelta(days=1): ["point"]},
            "transfer_g": {timedelta(days=1): ["point"]},
            "state_a": {timedelta(days=1): ["point"]},
        },
        "diff_t": {
            "output_x": {
                timedelta(days=2): ["point"],
                timedelta(days=8): ["sum", "mean", "minimum", "maximum"],
            },
            # using defaults for methods in 'output_x'
            "output_y": {timedelta(days=2): ["point"]},
            "transfer_d": {timedelta(days=2): ["point"]},
            "transfer_f": {timedelta(days=2): ["point"]},
            "transfer_g": {timedelta(days=2): ["point"]},
            "state_a": {timedelta(days=2): ["point"]},
        },
    },
}


def get_dummy_component(category, kind, time_, space_, source):
    # get component class
    component_class = getattr(
        import_module("tests.components.{}".format(category)),
        "Dummy{}".format("" if source == "Python" else source),
    )
    # get timedomain, spacedomain, dataset
    time_resolution = time_resolutions[category][time_]
    timedomain = get_dummy_timedomain(time_resolution)

    space_resolution = space_resolutions[category][space_]
    spacedomain = get_dummy_spacedomain(space_resolution)
    if category in ["surfacelayer", "nutrientsurfacelayer"]:
        spacedomain.land_sea_mask = get_dummy_land_sea_mask_field(space_resolution)
        spacedomain.flow_direction = get_dummy_flow_direction_field(space_resolution)

    dataset = get_dummy_dataset(category, time_resolution, space_resolution)

    if kind == "c":
        return component_class(
            saving_directory="outputs",
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters=parameters[category][space_],
            constants=constants[category],
            records=records[category][time_],
            io_slice=10,
        )
    elif kind == "d":
        return unifhy.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset(
                "{}_{}".format(category, time_),
                time_resolution,
                space_resolution,
            ),
            substituting_class=component_class,
            io_slice=10,
        )
    else:  # kind == 'n'
        return unifhy.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=component_class,
        )


class TestSubstituteComponent(unittest.TestCase):
    td = get_dummy_timedomain("daily")
    sd = get_dummy_spacedomain("1deg")

    def test_instantiation_datacomponent(self):
        td = self.td
        sd = self.sd

        for substituting_class in [
            unifhy.component.SurfaceLayerComponent,
            unifhy.component.SubSurfaceComponent,
            unifhy.component.OpenWaterComponent,
            unifhy.component.NutrientSurfaceLayerComponent,
            unifhy.component.NutrientSubSurfaceComponent,
            unifhy.component.NutrientOpenWaterComponent,
        ]:
            with self.subTest(subtituting_class=substituting_class.category):
                # prepare dummy dataset for substituting component
                ds = unifhy.data.DataSet()

                for outward, info in substituting_class.outwards_info.items():
                    # create dummy field from dummy timedomain and spacedomain
                    fld = sd.to_field()
                    fld.set_construct(td.to_field().domain_axis("T"))
                    fld.set_construct(td.to_field().dimension_coordinate("T"))

                    # populate with zero data
                    fld.set_data(
                        numpy.zeros((td.time.size, sd.Y.size, sd.X.size)),
                        axes=("T", "Y", "X"),
                    )

                    # define some basic metadata
                    fld.standard_name = outward
                    fld.units = info["units"]

                    # turn field into unifhy Variable
                    var = unifhy.data.Variable(fld, ())

                    # append Variable to DataSet
                    ds[outward] = var

                # test instantiation of DataComponent
                dc = unifhy.DataComponent(td, sd, ds, substituting_class)
                self.assertEqual(dc.outwards_info, substituting_class._outwards_info)

    def test_instantiation_nullcomponent(self):
        td = self.td
        sd = self.sd

        for substituting_class in [
            unifhy.component.SurfaceLayerComponent,
            unifhy.component.SubSurfaceComponent,
            unifhy.component.OpenWaterComponent,
            unifhy.component.NutrientSurfaceLayerComponent,
            unifhy.component.NutrientSubSurfaceComponent,
            unifhy.component.NutrientOpenWaterComponent,
        ]:
            with self.subTest(subtituting_class=substituting_class.category):
                # test instantiation of NullComponent
                nc = unifhy.NullComponent(td, sd, substituting_class)
                self.assertEqual(nc.outwards_info, substituting_class._outwards_info)


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(test_loader.loadTestsFromTestCase(TestSubstituteComponent))

    test_suite.addTests(doctest.DocTestSuite(unifhy.component))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
