import numpy as np

from ..component import SurfaceLayerComponent
from ...settings import dtype_float


class Artemis(SurfaceLayerComponent):
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

    The surface layer component of Artemis comprises canopy
    interception, evaporation, and snowmelt.

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
        'precipitation_flux': {
            'units': 'kg m-2 s-1',
            'kind': 'dynamic'
        },
        'specific_humidity': {
            'units': '1',
            'kind': 'dynamic'
        },
        'surface_downwelling_shortwave_flux_in_air': {
            'units': 'W m-2',
            'kind': 'dynamic'
        },
        'surface_downwelling_longwave_flux_in_air': {
            'units': 'W m-2',
            'kind': 'dynamic'
        },
        'air_temperature': {
            'units': 'K',
            'kind': 'dynamic'
        },
        'surface_albedo': {
            'units': '1',
            'kind': 'static'
        },
        'wind_speed': {
            'units': 'm s-1',
            'kind': 'dynamic'
        },
        'vegetation_height': {
            'units': 'm',
            'kind': 'static'
        },
        'leaf_area_index': {
            'units': '1',
            'kind': 'climatologic',
            'frequency': 'monthly'
        }
    }
    _parameters_info = {}
    _states_info = {
        'canopy_store': {
            'units': 'm'
        },
        'snowpack_store': {
            'units': 'm'
        }
    }
    _constants_info = {
        'sigma_sb': {
            'description': 'Stefan-Boltzman constant',
            'units': 'W m-2 K-4'
        },
        'kappa': {
            'description': 'von Karman constant',
            'units': '1'
        },
        'lambda_lh': {
            'description': 'latent heat of vaporisation '
                           '(water vapour @ 288K) - M&U90 p.268',
            'units': 'J kg-1'
        },
        'rho_a': {
            'description': 'specific mass of (dry) air @ 288K - M&U90 p.268',
            'units': 'kg m-3'
        },
        'rho_lw': {
            'description': 'specific mass of liquid water',
            'units': 'kg m-3'
        },
        'c_p': {
            'description': 'specific heat of air - M&U90 p.267',
            'units': 'J kg-1 K-1'
        },
        'R_v': {
            'description': 'gas constant for water vapour - P&P77 p.23',
            'units': 'J kg-1 K-1'
        },
        't_freeze': {
            'description': 'freezing point of water',
            'units': 'K'
        },
        'gamma': {
            'description': 'psychrometric constant [kPa/K] M&U90 p.181',
            'units': 'kPa K-1'
        },
        'D_s': {
            'description': 'drainage rate when canopy is full - '
                           'Shuttleworth, 2007. p. 218; orig Rutter',
            'units': 'm s-1'
        },
        'b': {
            'description': 'canopy drainage decay term - '
                           'Shuttleworth, 2007. p. 218',
            'units': 's-1'
        },
        'F': {
            'description': 'degree-day melting factor - '
                           'Beven 2000; 0.004 m/K/day',
            'units': 'm K-1 s-1'
        },
        'z': {
            'description': 'height measurement for wind speed',
            'units': 'm'
        }
    }
    _outputs_info = {
        'evaporation_canopy': {
            'description': 'evaporation of the water on the leaf surface',
            'units': 'kg m-2 s-1'
        }
    }

    def initialise(self,
                   # component states
                   canopy_store, snowpack_store,
                   **kwargs):

        canopy_store[-1][:] = 0
        snowpack_store[-1][:] = 0

    def run(self,
            # from exchanger
            # component inputs
            precipitation_flux, air_temperature, wind_speed, specific_humidity,
            surface_downwelling_shortwave_flux_in_air,
            surface_downwelling_longwave_flux_in_air, surface_albedo,
            leaf_area_index, vegetation_height,
            # component parameters
            # component states
            canopy_store, snowpack_store,
            # component constants
            sigma_sb=5.67e-8, kappa=0.41, lambda_lh=2.48e6, rho_a=1.22,
            rho_lw=1e3, c_p=1.01e3, t_freeze=273., R_v=461.5,
            gamma=0.066, D_s=6e-9, b=0.062, F=4.6e-8, z=10,
            **kwargs):

        # /!\__RENAMING_CM4TWC__________________________________________
        dt = self.timedelta_in_seconds
        datetime = self.current_datetime

        pr = precipitation_flux
        huss = specific_humidity
        tas = air_temperature
        rsds = surface_downwelling_shortwave_flux_in_air
        rlds = surface_downwelling_longwave_flux_in_air

        h = vegetation_height
        ancil_L = leaf_area_index

        canopy_prev = canopy_store[-1]
        snowpack_prev = snowpack_store[-1]
        # ______________________________________________________________

        # Compute derived parameters
        z0 = np.ma.where(h == 0, 3e-4, 0.1 * h)  # vegetation roughness length [m] (3e-4 is for bare soil)
        d = 0.75 * h  # zero-plane displacement [m]
        t_snow = t_freeze  # temperature for snowfall [K]
        T_F = t_freeze  # snowmelt threshold [K]

        with np.errstate(over='ignore'):
            # Update LAI and derived terms
            month = datetime.month
            L = ancil_L[month-1, ...]
            C_t = 0.002 * L  # Canopy storage capacity [m] (Hough and Jones, MORECS)
            phi_t = np.ma.where(L == 0, 1, 1 - 0.5 ** L)  # throughfall coefficient [-]
            r_c = 40.  # Canopy resistance (calc from LAI) [s/m] (Beven 2000 p. 76)

            # Compute derived meteorological variables
            T_degC = tas - 273.
            wind_speed = wind_speed * 4.87 / (np.log(67.8 * z - 5.42))  # Scale to 2m wind speed

            e_sat = 0.6108 * np.exp(T_degC * 17.27 / (237.3 + T_degC))  # Hendrik; kPa
            e_abs = huss * rho_a * R_v * tas / 1000  # kg/kg to kPa; Parish and Putnam 1977)
            Delta_e = 4098. * e_sat / (237.3 + T_degC) ** 2  # slope of SVP curve kPa / degC
            with np.errstate(invalid='ignore'):
                r_a = np.log((z - d) / z0) ** 2 / (kappa ** 2 * wind_speed)  # aerodynamic resistance to evaporation
            r_a = np.ma.where(r_a <= 0., 1, r_a)  # Prevent negative r_a

            # /!\__ADJUSTMENT_CM4TWC____________________________________
            # calculate upwelling shortwave "rsus" with albedo
            rsus = surface_albedo * rsds

            # calculate upwelling longwave "rlus" with air temperature
            # (assuming surface temperature is air temperature)
            # (ignoring emissivity)
            rlus = air_temperature ** 4 * sigma_sb

            # total net radiation in W m-2
            R_n = rsds + rlds - rsus - rlus
            # __________________________________________________________

        # Partition precipitation between canopy, snow, and soil
        pr = pr / rho_lw  # convert to m/s
        p_snow = np.ma.where(tas <= t_snow, pr, 0.)
        p_soil = np.ma.where(tas > t_snow, phi_t * pr, 0.)
        p_can = np.ma.where(tas > t_snow, pr - p_soil, 0.)

        # CANOPY

        # Add canopy rainfall to store from previous timestep
        canopy = canopy_prev + p_can * dt

        # Calculate canopy evaporation, e_can
        D = e_sat - e_abs  # vapour pressure gradient (kPa)
        D = np.ma.where(D >= 0, D, 0.)
        e_can = (Delta_e * R_n + (rho_a * c_p * D) / r_a) / (Delta_e + gamma)
        # Penman-Monteith (rc = 0; Rutter/Gash)
        e_can = e_can / lambda_lh / 1000.  # convert to m/s
        e_can = e_can * (canopy / C_t)  # scale canopy evaporation by canopy wetted fraction
        e_can = np.minimum(canopy / dt, e_can)  # limit e_can to available canopy water
        canopy = canopy - e_can * dt  # update
        canopy = np.ma.where(canopy < 1.e-11, 0., canopy)  # avoid small roundoff values

        # Calculate canopy throughfall, q_t
        q_t = np.ma.where(canopy < C_t, 0., D_s * np.exp(b * (canopy - C_t)))

        q_t = np.minimum(canopy / dt, q_t)  # limit throughfall if it would deplete more than available
        canopy = canopy - q_t * dt  # update
        canopy = np.ma.where(canopy < 1.e-11, 0., canopy)  # avoid small roundoff values

        # Ensure canopy storage doesnt exceed capacity
        q_t = np.ma.where(canopy > C_t, q_t + (canopy - C_t) / dt, q_t)
        canopy = np.ma.where(canopy > C_t, C_t, canopy)

        # SNOW PACK

        # Calculate snowmelt, q_m
        q_m = F * np.maximum(0., tas - T_F)  # Degree-day melting model

        # Update snowpack
        snowpack = snowpack_prev + p_snow * dt  # add new snow to store from previous timestep
        q_m = np.minimum(snowpack / dt, q_m)  # limit snowmelt to available snowpack
        snowpack = snowpack - q_m * dt  # update
        snowpack = np.ma.where(snowpack < 1.e-11, 0., snowpack)  # avoid small roundoff values

        # SURFACE

        # surface store
        surface = (p_soil + q_m + q_t) * dt  # add new rain, snowmelt and throughfall

        # Surface evaporation
        e_surf = ((Delta_e * R_n + (rho_a * c_p * D) / r_a)
                  / (Delta_e + gamma * (1 + r_c / r_a)))  # Penman-Monteith

        e_surf = e_surf / lambda_lh / 1000.  # convert to m/s
        e_surf = np.maximum(e_surf - e_can, 0.)  # subtract canopy evaporation if possible, to conserve energy

        e_surf = np.minimum(surface / dt, e_surf)  # limit e_surf to available water

        # /!\__UPDATE_STATES_CM4TWC_____________________________________
        canopy_store[0][:] = canopy
        snowpack_store[0][:] = snowpack
        # ______________________________________________________________

        return (
            # to exchanger
            {
                'throughfall': (q_t + p_soil) * rho_lw,
                'snowmelt': q_m * rho_lw,
                'transpiration': np.zeros(self.spaceshape, dtype_float()),
                'evaporation_soil_surface': e_surf * rho_lw,
                'evaporation_ponded_water': np.zeros(self.spaceshape, dtype_float()),
                'evaporation_openwater': np.zeros(self.spaceshape, dtype_float())
            },
            # component outputs
            {
                'evaporation_canopy': e_can * rho_lw
            }
        )

    def finalise(self, **kwargs):

        pass
