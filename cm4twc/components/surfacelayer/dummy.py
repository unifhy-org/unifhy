import numpy as np

from ..components import SurfaceLayerComponent


class Dummy(SurfaceLayerComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={
                'rainfall': 'kg m-2 s-1',
                'snowfall': 'kg m-2 s-1',
                'air_temperature': 'K',
            },
            ancil_data_info={
                'vegetation_fraction': '1'
            },
            parameters_info={},
            states_info={
                'canopy': 'kg m-2',
                'snowpack': 'kg m-2'
            },
            constants_info={},
            solver_history=1
        )

    def initialise(self, spaceshape, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            # component states for t-1
            'canopy_': np.zeros(spaceshape, np.float32),
            'snowpack_': np.zeros(spaceshape, np.float32),
            # component states for t
            'canopy': np.zeros(spaceshape, np.float32),
            'snowpack': np.zeros(spaceshape, np.float32)
        }

    def run(self,
            # interface fluxes in
            # component features
            spaceshape,
            # component driving data
            rainfall, snowfall, air_temperature,
            # component ancillary data
            vegetation_fraction,
            # component parameters
            # component states
            canopy_, snowpack_, canopy, snowpack,
            # component constants
            **kwargs):

        dummy_array = np.ones(spaceshape, np.float32)

        canopy[:] = canopy_ + 1
        snowpack[:] = snowpack_ + 1

        return {
            # interface fluxes out
            'throughfall': dummy_array,
            'snowmelt': dummy_array,
            'transpiration': dummy_array,
            'evaporation_soil_surface': dummy_array,
            'evaporation_ponded_water': dummy_array,
            'evaporation_openwater': dummy_array,
        }

    def finalise(self, canopy_, snowpack_,
                 **kwargs):

        pass
