import unittest

import cm4twc


def get_instance_model_from_components(surfacelayer, subsurface, openwater):

    return cm4twc.Model(
        surfacelayer=surfacelayer,
        subsurface=subsurface,
        openwater=openwater
    )


class TestModelAPI(unittest.TestCase):

    def test_model_init_with_all_possible_component_combinations(self):

        # full factorial design of experiment
        # (i.e. all possible combinations of components)
        doe = (
            # tuple(surfacelayer_component, subsurface_component, openwater_component)
            # with 'c' for _Component, 'd' for DataComponent, 'n' for NullComponent
            ('c', 'c', 'c'),
            ('d', 'c', 'c'),
            ('n', 'c', 'c'),
            ('c', 'd', 'c'),
            ('d', 'd', 'c'),
            ('n', 'd', 'c'),
            ('c', 'n', 'c'),
            ('d', 'n', 'c'),
            ('n', 'n', 'c'),
            ('c', 'c', 'd'),
            ('d', 'c', 'd'),
            ('n', 'c', 'd'),
            ('c', 'd', 'd'),
            ('d', 'd', 'd'),
            ('n', 'd', 'd'),
            ('c', 'n', 'd'),
            ('d', 'n', 'd'),
            ('n', 'n', 'd'),
            ('c', 'c', 'n'),
            ('d', 'c', 'n'),
            ('n', 'c', 'n'),
            ('c', 'd', 'n'),
            ('d', 'd', 'n'),
            ('n', 'd', 'n'),
            ('c', 'n', 'n'),
            ('d', 'n', 'n'),
            ('n', 'n', 'n')
        )

        # instantiate dummy TimeDomain and SpaceDomain
        timedomain = cm4twc.TimeDomain(
            timestamps=[0, 1, 2, 3],
            units='days since 2019-01-01 09:00:00Z',
            calendar='gregorian'
        )
        spacedomain = cm4twc.Grid(
            latitude_deg=[2.2, 1.76, 1.32, 0.88, 0.44, 0., -0.44, -0.88, -1.32, -1.76],
            longitude_deg=[-4.7, -4.26, -3.82, -3.38, -2.94, -2.5, -2.06, -1.62, -1.18],
            latitude_bounds_deg=[[2.42, 1.98], [1.98, 1.54], [1.54, 1.1], [1.1,  0.66],
                                 [0.66, 0.22], [0.22, -0.22], [-0.22, -0.66],
                                 [-0.66, -1.1], [-1.1, -1.54], [-1.54, -1.98]],
            longitude_bounds_deg=[[-4.92, -4.48], [-4.48, -4.04], [-4.04, -3.6],
                                  [-3.6,  -3.16], [-3.16, -2.72], [-2.72, -2.28],
                                  [-2.28, -1.84], [-1.84, -1.4], [-1.4, -0.96]],
            rotated=True,
            earth_radius_m=6371007., grid_north_pole_latitude_deg=38.0,
            grid_north_pole_longitude_deg=190.0
        )

        # load dummy driving and ancillary data
        dataset = cm4twc.DataSet.from_cf_nc_file(
            ['dummy_data/dummy_driving_data.nc',
             'dummy_data/dummy_ancillary_data.nc'],
            name_mapping={'rainfall_flux': 'rainfall',
                          'snowfall_flux': 'snowfall',
                          'air_temperature': 'air_temperature',
                          'soil_temperature': 'soil_temperature'})

        # load substitute data for DataComponents
        surfacelayer_substitute_dataset = cm4twc.DataSet.from_cf_nc_file(
            'dummy_data/dummy_surfacelayer_substitute_data.nc')
        subsurface_substitute_dataset = cm4twc.DataSet.from_cf_nc_file(
            'dummy_data/dummy_subsurface_substitute_data.nc')
        openwater_substitute_dataset = cm4twc.DataSet.from_cf_nc_file(
            'dummy_data/dummy_openwater_substitute_data.nc')

        # loop through all the possible combinations of components
        for combination in doe:
            # for surfacelayer component
            if combination[0] == 'c':
                surfacelayer = cm4twc.surfacelayer.Dummy(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    dataset=dataset,
                    parameters={},
                    constants={}
                )
            elif combination[0] == 'd':
                surfacelayer = cm4twc.DataComponent(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    dataset=surfacelayer_substitute_dataset,
                    substituting_class=cm4twc.SurfaceLayerComponent
                )
            else:  # i.e. 'n'
                surfacelayer = cm4twc.NullComponent(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    substituting_class=cm4twc.SurfaceLayerComponent
                )

            # for subsurface component
            if combination[1] == 'c':
                subsurface = cm4twc.subsurface.Dummy(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    dataset=dataset,
                    parameters={'saturated_hydraulic_conductivity': 2},
                    constants={}
                )
            elif combination[1] == 'd':
                subsurface = cm4twc.DataComponent(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    dataset=subsurface_substitute_dataset,
                    substituting_class=cm4twc.SubSurfaceComponent
                )
            else:  # i.e. 'n'
                subsurface = cm4twc.NullComponent(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    substituting_class=cm4twc.SubSurfaceComponent
                )

            # for openwater
            if combination[2] == 'c':
                openwater = cm4twc.openwater.Dummy(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    dataset=dataset,
                    parameters={'residence_time': 1},
                    constants={}
                )
            elif combination[2] == 'd':
                openwater = cm4twc.DataComponent(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    dataset=openwater_substitute_dataset,
                    substituting_class=cm4twc.OpenWaterComponent
                )
            else:  # i.e. 'n'
                openwater = cm4twc.NullComponent(
                    timedomain=timedomain,
                    spacedomain=spacedomain,
                    substituting_class=cm4twc.OpenWaterComponent
                )

            # try to get an instance of model with the given combination
            model = get_instance_model_from_components(surfacelayer,
                                                       subsurface,
                                                       openwater)

            model.simulate()


if __name__ == '__main__':
    unittest.main()
