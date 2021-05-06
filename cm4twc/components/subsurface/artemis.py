import numpy as np

from ..component import SubSurfaceComponent


class Artemis(SubSurfaceComponent):
    """
    Artemis provides a simple runoff production model designed to be
    comparable with the runoff-production models typically embedded
    within climate models. It is driven with precipitation, radiation,
    temperature, humidity and wind speed on a daily time step and
    calculates canopy interception, evaporation, snowmelt, infiltration,
    and runoff. It uses a Rutter–Gash canopy formulation (`Gash, 1979`_)
    to represent interception, together with Penman–Monteith evaporation
    calculated using available radiation data (`Monteith, 1965`_). Soil
    moisture is accounted for using a two-layer model with
    saturation-excess runoff computed using a generalized TOPMODEL
    (`Clark and Gedney, 2008`_). The snowpack is represented using a
    temperature-based model of accumulation and melt (`Moore et al.,
    1999`_, `Hock, 2003`_, `Beven, 2011`_). Snow accumulates when
    precipitation falls while temperature is below a threshold
    temperature. When temperature is above a threshold for melt, melting
    occurs at a rate proportional to the difference between the current
    temperature and the melting temperature. This conceptual model is
    widely used (`Hock, 2003`_, `Zhang et al., 2006`_, `Rango and
    Martinec, 1995`_, `Beven, 2011`_) and gives performance comparable
    with that of more parameter rich energy balance models, despite
    their greater complexity (`Parajka et al., 2010`_).

    The sub-surface component of Artemis comprises infiltration and
    runoff.

    .. _`Gash, 1979`: https://doi.org/10.1002/qj.49710544304
    .. _`Monteith, 1965`: https://repository.rothamsted.ac.uk/item/8v5v7
    .. _`Clark and Gedney, 2008`: https://doi.org/10.1029/2007JD008940
    .. _`Moore et al., 1999`: https://doi.org/10.5194/hess-3-233-1999
    .. _`Hock, 2003`: https://doi.org/10.1016/S0022-1694(03)00257-9
    .. _`Beven, 2011`: http://doi.org/10.1002/9781119951001
    .. _`Rango and Martinec, 1995`: https://doi.org/10.1111/j.1752-1688.1995.tb03392.x
    .. _`Zhang et al., 2006`: https://doi.org/10.3189/172756406781811952
    .. _`Parajka et al., 2010`: https://doi.org/10.1029/2010JD014086

    :contributors: Simon Dadson [1,2]
    :affiliations:
        1. UK Centre for Ecology and Hydrology
        2. School of Geography and the Environment, University of Oxford
    :licence: BSD-3
    :copyright: 2020, University of Oxford
    """

    _inputs_info = {
        'topmodel_saturation_capacity': {
            'units': 'mm m-1',
            'kind': 'static'
        },
        'saturated_hydraulic_conductivity': {
            'units': 'm s-1',
            'kind': 'static'
        },
        'topographic_index': {
            'units': '1',
            'kind': 'static'
        }
    }
    _parameters_info = {}
    _states_info = {
        'subsurface_store': {
            'units': 'm'
        }
    }
    _constants_info = {
        'm': {
            'description': 'K_sat decay constant - Marthews et al',
            'units': '1',
            'default_value': 0.02
        },
        'rho_lw': {
            'description': 'specific mass of liquid water',
            'units': 'kg m-3',
            'default_value': 1e3
        },
        'S_top': {
            'description': 'soil depth over which to apply topmodel',
            'units': 'm',
            'default_value': 3.
        }
    }

    def initialise(self,
                   # component states
                   subsurface_store,
                   **kwargs):

        subsurface_store[-1][:] = 0

    def run(self,
            # from exchanger
            throughfall, snowmelt, transpiration, evaporation_soil_surface,
            evaporation_ponded_water,
            # component inputs
            topmodel_saturation_capacity,
            saturated_hydraulic_conductivity,
            topographic_index,
            # component parameters
            # component states
            subsurface_store,
            # component constants
            m, rho_lw, S_top,
            **kwargs):

        # /!\__RENAMING_CM4TWC__________________________________________
        dt = self.timedelta_in_seconds

        q_m = snowmelt / rho_lw
        q_t = throughfall / rho_lw
        e_surf = (transpiration + evaporation_soil_surface
                  + evaporation_ponded_water) / rho_lw

        K_s = saturated_hydraulic_conductivity
        S_max = topmodel_saturation_capacity
        Lambda = topographic_index

        subsurface_prev = subsurface_store[-1]
        # ______________________________________________________________

        # SURFACE

        # surface store
        surface = (q_t + q_m) * dt  # add new rain, snowmelt and throughfall

        surface = surface - e_surf * dt  # update
        surface = np.ma.where(surface < 1.e-11, 0., surface)  # avoid small roundoff values

        # Infiltration
        q_i = K_s  # use JULES formulation rather than full Green-Ampt
        q_i = np.minimum(surface / dt, q_i)  # limit q_i to available water
        surface = surface - q_i * dt  # update
        surface = np.ma.where(surface < 1.e-11, 0., surface)  # avoid small roundoff values

        # Surface runoff
        q_s = surface / dt  # everything left over runs off

        # SUB-SURFACE

        # Baseflow
        S_max = np.ma.where(S_max > 0., S_max * S_top / 1000., 0.6)
        subsurface = subsurface_prev + q_i * dt  # add new infiltrated water
        q_s = np.ma.where(subsurface > S_max,
                          q_s + (subsurface - S_max) / dt,
                          q_s)  # if soil saturates route excess to surface runoff

        subsurface = np.ma.where(subsurface > S_max, S_max, subsurface)
        S_b_prime = S_max - subsurface
        with np.errstate(over='ignore'):
            q_b = (K_s / m) * np.exp(-Lambda) * np.exp(-S_b_prime / m)

        # Update sub-surface store
        q_b = np.minimum(subsurface / dt, q_b)  # limit q_b to available water
        subsurface = subsurface - q_b * dt  # remove water that has run off

        subsurface = np.ma.where(subsurface < 1.e-11, 0., subsurface)  # avoid small roundoff values

        # /!\__ADDITION_CM4TWC__________________________________________
        soil_water_stress = subsurface / S_max
        # ______________________________________________________________

        # /!\__UPDATE_STATES_CM4TWC_____________________________________
        subsurface_store[0][:] = subsurface
        # ______________________________________________________________

        return (
            # to exchanger
            {
                'surface_runoff': q_s * rho_lw,
                'subsurface_runoff': q_b * rho_lw,
                'soil_water_stress': soil_water_stress
            },
            # component outputs
            {}
        )

    def finalise(self, **kwargs):

        pass
