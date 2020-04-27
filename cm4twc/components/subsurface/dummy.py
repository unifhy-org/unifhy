import numpy as np

from ..components import SubSurfaceComponent


class Dummy(SubSurfaceComponent):

    def __init__(self):
        super().__init__(
            driving_data_info={
                'soil_temperature': 'K',
            },
            ancil_data_info={},
            parameters_info={
                'saturated_hydraulic_conductivity': 'kg m-2 s-1',
            },
            states_info={
                'soil_moisture': 'kg m-2',
                'aquifer': 'kg m-2'
            },
            constants_info={},
            solver_history=1
        )

    def initialise(self, spaceshape, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            'soil_moisture': (
                np.zeros(spaceshape, np.float32),  # for t-1
                np.zeros(spaceshape, np.float32)  # for t
            ),
            'aquifer': (
                np.zeros(spaceshape, np.float32),  # for t-1
                np.zeros(spaceshape, np.float32)  # for t
            )
        }

    def run(self,
            # interface fluxes in
            evaporation_soil_surface, evaporation_ponded_water,
            transpiration, throughfall, snowmelt,
            # component features
            spaceshape,
            # component driving data
            soil_temperature,
            # component ancillary data
            # component parameters
            saturated_hydraulic_conductivity,
            # component states
            soil_moisture, aquifer,
            # component constants
            **kwargs):

        dummy_array = np.ones(spaceshape, np.float32)

        soil_moisture[0][:] = soil_moisture[-1] + 1
        aquifer[0][:] = soil_moisture[-1] + 1

        return {
            # interface fluxes out
            'runoff': dummy_array
        }

    def finalise(self, soil_moisture, aquifer,
                 **kwargs):

        pass
