import numpy as np
import warnings

from ..component import OpenWaterComponent


class RFM(OpenWaterComponent):
    """
    River flow model (RFM) is a runoff routing model based on a discrete
    approximation of the one-directional kinematic wave with lateral
    inflow (`Bell et al., 2007 <https://doi.org/10.5194/hess-11-532-2007>`_,
    `Dadson et al., 2011 <https://doi.org/10.1016/j.jhydrol.2011.10.002>`_).

    The wave equation is parametrised differently for surface and
    sub-surface pathways, themselves split into a land domain, and a
    river domain. Return flow is also possible between surface and
    sub-surface pathways in each domain.

    This Python implementation of RFM is based on the work by Huw Lewis.

    :contributors: Huw Lewis [1]
    :affiliations:
        1. UK Met Office
    :licence: UK Open Government
    :copyright: 2020, UK Met Office
    """

    _inputs_info = {
        'i_area': {
            'units': '1',
            'kind': 'static',
            'description': 'drainage area (specified in number of '
                           'cells) draining to a grid box'
        }
    }
    _parameters_info = {
        'c_land': {
            'units': 'm s-1',
            'description': 'kinematic wave speed for surface flow in '
                           'a land grid box on the river routing grid'
        },
        'cb_land': {
            'units': 'm s-1',
            'description': 'kinematic wave speed for subsurface flow in '
                           'a land grid box on the river routing grid'
        },
        'c_river': {
            'units': 'm s-1',
            'description': 'kinematic wave speed for surface flow in '
                           'a river grid box on the river routing grid'
        },
        'cb_river': {
            'units': 'm s-1',
            'description': 'kinematic wave speed for subsurface flow in '
                           'a river grid box on the river routing grid'
        },
        'ret_l': {
            'units': '1',
            'description': 'land return flow fraction '
                           '(resolution dependent)'
        },
        'ret_r': {
            'units': '1',
            'description': 'river return flow fraction '
                           '(resolution dependent)'
        },
        'river_length': {
            'units': 'm',
            'description': 'length of river reach'
        }
    }
    _states_info = {
        'flow_in': {
            'units': 'm',
            'description': 'surface flow from neighbouring cells'
        },
        'b_flow_in': {
            'units': 'm',
            'description': 'sub-surface flow from neighbouring cells'
        },
        'surf_store': {
            'units': 'm',
            'description': 'surface water store'
        },
        'sub_store': {
            'units': 'm',
            'description': 'sub-surface water store'
        }
    }
    _constants_info = {
        'a_thresh': {
            'units': '1',
            'description': 'threshold drainage area (specified in number of '
                           'cells) draining to a grid box, above which the '
                           'grid cell is considered to be a river point - '
                           'remaining points are treated as land (drainage '
                           'area = 0) or sea (drainage area < 0)'
        },
        'rho_lw': {
            'description': 'specific mass of liquid water',
            'units': 'kg m-3'
        }
    }
    _outputs_info = {
        'outgoing_water_volume_transport_along_river_channel': {
            'units': 'm3 s-1',
            'description': 'streamflow at outlet of grid element'
        }
    }
    _flow_direction = True

    def initialise(self,
                   # component states
                   flow_in, b_flow_in, surf_store, sub_store,
                   **kwargs):

        # set initialise conditions for component states
        flow_in[-1][:] = 0
        b_flow_in[-1][:] = 0
        surf_store[-1][:] = 0
        sub_store[-1][:] = 0

    def run(self,
            # from exchanger
            surface_runoff, subsurface_runoff,
            # component inputs
            i_area,
            # component parameters
            c_land, cb_land, c_river, cb_river, ret_l, ret_r, river_length,
            # component states
            flow_in, b_flow_in, surf_store, sub_store,
            # component constants
            a_thresh=13, rho_lw=1e3,
            **kwargs):

        # /!\__RENAMING_CM4TWC__________________________________________
        dt = self.timedelta_in_seconds
        shape = self.spaceshape

        dx = river_length
        area = dx * dx
        surf_in = surface_runoff
        sub_in = subsurface_runoff
        # ______________________________________________________________

        # Set theta values
        r_theta = c_river * dt / dx
        if np.any(r_theta < 0) or np.any(r_theta > 1):
            warnings.warn("theta river surface not within [0, 1]",
                          RuntimeWarning)
        sub_r_theta = cb_river * dt / dx
        if np.any(sub_r_theta < 0) or np.any(sub_r_theta > 1):
            warnings.warn("theta river subsurface not within [0, 1]",
                          RuntimeWarning)
        l_theta = c_land * dt / dx
        if np.any(sub_r_theta < 0) or np.any(sub_r_theta > 1):
            warnings.warn("theta land surface not within [0, 1]",
                          RuntimeWarning)
        sub_l_theta = cb_land * dt / dx
        if np.any(sub_r_theta < 0) or np.any(sub_r_theta > 1):
            warnings.warn("theta land subsurface not within [0, 1]",
                          RuntimeWarning)

        # define sea/land/river points
        sea = np.where(i_area < 0)
        land = np.where((i_area < a_thresh) & (i_area >= 0))
        riv = np.where(i_area >= a_thresh)

        # initialise mapped variables
        theta = np.zeros(shape)
        s_theta = np.zeros(shape)
        ret_flow = np.zeros(shape)
        theta[land] = l_theta
        theta[riv] = r_theta
        s_theta[land] = sub_l_theta
        s_theta[riv] = sub_r_theta
        ret_flow[land] = ret_l
        ret_flow[riv] = ret_r
        mask = np.ones(shape)
        mask[sea] = 0

        # convert units for input runoffs
        surf_runoff = mask * surf_in * dt * area / rho_lw
        sub_surf_runoff = mask * sub_in * dt * area / rho_lw

        # compute stores
        surf_store_n = (1.0 - theta) * surf_store[-1] + flow_in[-1] + surf_runoff
        sub_store_n = (1.0 - s_theta) * sub_store[-1] + b_flow_in[-1] + sub_surf_runoff

        # return flow between surface and subsurface
        return_flow = np.maximum(sub_store_n * ret_flow, 0.0)
        surf_store[0][:] = surf_store_n + return_flow
        sub_store[0][:] = sub_store_n - return_flow

        # move water between adjacent grid points
        flow_in[0][:], outed = self.spacedomain.route(theta * surf_store[-1])
        b_flow_in[0][:], b_outed = self.spacedomain.route(s_theta * sub_store[-1])

        # compute river flow output
        riv_flow = theta / dt * surf_store[-1]

        return (
            # to exchanger
            {
                'water_level': surf_store[0] * rho_lw
            },
            # component outputs
            {
                'outgoing_water_volume_transport_along_river_channel': riv_flow
            }
        )

    def finalise(self,
                 # component states
                 flow_in, b_flow_in, surf_store, sub_store,
                 **kwargs):
        pass
