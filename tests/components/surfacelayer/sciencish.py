import numpy as np

from cm4twc.components import SurfaceLayerComponent
from cm4twc.settings import DTYPE_F


class Sciencish(SurfaceLayerComponent):

    driving_data_info = {
        'rainfall': 'kg m-2 s-1',
        'snowfall': 'kg m-2 s-1',
        'air_temperature': 'K',
    }
    ancillary_data_info = {
        'vegetation_fraction': '1'
    }
    # parameters_info = {}
    constants_info = {
        'evaporation_rate': 'kg m-2 s-1',
        'melting_temperature': 'K',
        'interception_fraction': '1'
    }
    states_info = {
        'canopy': 'kg m-2',
        'snowpack': 'kg m-2'
    }
    solver_history = 1

    def initialise(self, **kwargs):
        # component has a history of 1, so needs states for t-1 and t
        return {
            # component states
            'canopy': (  # in chronological order
                np.ones(self.spaceshape, DTYPE_F()) * 5,  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
            ),
            'snowpack': (  # in chronological order
                np.ones(self.spaceshape, DTYPE_F()) * 2,  # for t-1
                np.zeros(self.spaceshape, DTYPE_F())  # for t
            )
        }

    def run(self,
            # interface fluxes in
            soil_water_stress,
            # component driving data
            rainfall, snowfall, air_temperature,
            # component ancillary data
            vegetation_fraction,
            # component parameters
            # component states
            canopy, snowpack,
            # component constants,
            average_evaporation_rate=4.6e-5,
            melting_temperature=273,
            interception_fraction=0.25,
            **kwargs):

        direct_rainfall = (1 - vegetation_fraction) * rainfall
        canopy_rainfall = rainfall - direct_rainfall

        canopy_evaporation = canopy[-1] / self.timestepinseconds * 0.1
        interception = interception_fraction * canopy_rainfall
        throughfall = canopy_rainfall - interception
        canopy[0][:] = canopy[-1] + ((interception - canopy_evaporation)
                                     * self.timestepinseconds)

        transpiration = (vegetation_fraction * soil_water_stress *
                         average_evaporation_rate)
        soil_evaporation = ((1 - vegetation_fraction) * soil_water_stress
                            * average_evaporation_rate)

        snowmelt = np.where(
            air_temperature > melting_temperature,
            snowpack[-1] * 0.10 / self.timestepinseconds,
            0
        )
        snowpack[0][:] = snowpack[-1] + ((snowfall - snowmelt)
                                         * self.timestepinseconds)

        openwater_evaporation = np.zeros(self.spaceshape, DTYPE_F())

        return {
            # interface fluxes out
            'throughfall': throughfall + direct_rainfall,
            'snowmelt': snowmelt,
            'transpiration': transpiration,
            'evaporation_soil_surface': canopy_evaporation,
            'evaporation_ponded_water': soil_evaporation,
            'evaporation_openwater': openwater_evaporation
        }

    def finalise(self, canopy, snowpack,
                 **kwargs):

        pass
