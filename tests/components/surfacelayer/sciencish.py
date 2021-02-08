import numpy as np

from cm4twc.components import SurfaceLayerComponent


class Sciencish(SurfaceLayerComponent):

    _inputs_info = {
        'rainfall': {
            'units': 'kg m-2 s-1',
            'kind': 'dynamic'
        },
        'snowfall': {
            'units': 'kg m-2 s-1',
            'kind': 'dynamic'
        },
        'air_temperature': {
            'units': 'K',
            'kind': 'dynamic'
        },
        'vegetation_fraction': {
            'units': '1',
            'kind': 'static'
        }
    }
    # _parameters_info = {}
    _constants_info = {
        'evaporation_rate': {
            'units': 'kg m-2 s-1'
        },
        'melting_temperature': {
            'units': 'K'
        },
        'interception_fraction': {
            'units': '1'
        }
    }
    _states_info = {
        'canopy': {
            'units': 'kg m-2',
            'divisions': 1
        },
        'snowpack': {
            'units': 'kg m-2',
            'divisions': 1
        }
    }
    _solver_history = 1

    def initialise(self,
                   # component states
                   canopy, snowpack,
                   **kwargs):
        canopy[-1][:] = 5
        snowpack[-1][:] = 2

    def run(self,
            # from exchanger
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

        canopy_evaporation = canopy[-1] / self.timedelta_in_seconds * 0.1
        interception = interception_fraction * canopy_rainfall
        throughfall = canopy_rainfall - interception
        canopy[0][:] = canopy[-1] + ((interception - canopy_evaporation)
                                     * self.timedelta_in_seconds)

        transpiration = (vegetation_fraction * soil_water_stress *
                         average_evaporation_rate)
        soil_evaporation = ((1 - vegetation_fraction) * soil_water_stress
                            * average_evaporation_rate)

        snowmelt = np.where(
            air_temperature > melting_temperature,
            snowpack[-1] * 0.10 / self.timedelta_in_seconds,
            0
        )
        snowpack[0][:] = snowpack[-1] + ((snowfall - snowmelt)
                                         * self.timedelta_in_seconds)

        openwater_evaporation = soil_evaporation * 0

        return (
            # to exchanger
            {
                'throughfall': throughfall + direct_rainfall,
                'snowmelt': snowmelt,
                'transpiration': transpiration,
                'evaporation_soil_surface': canopy_evaporation,
                'evaporation_ponded_water': soil_evaporation,
                'evaporation_openwater': openwater_evaporation
            },
            # component outputs
            {}
        )

    def finalise(self,
                 # to exchanger
                 canopy, snowpack,
                 **kwargs):
        pass
