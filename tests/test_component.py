from importlib import import_module
from datetime import timedelta
import cf

import unifhy

from tests.test_time import get_dummy_timedomain
from tests.test_space import (get_dummy_spacedomain,
                              get_dummy_land_sea_mask_field,
                              get_dummy_flow_direction_field)
from tests.test_data import (get_dummy_dataset,
                             get_dummy_component_substitute_dataset)

time_resolutions = {
    'surfacelayer': {
        'same_t': 'daily',
        'diff_t': 'daily'
    },
    'subsurface': {
        'same_t': 'daily',
        'diff_t': '4daily'
    },
    'openwater': {
        'same_t': 'daily',
        'diff_t': '2daily'
    },
}

space_resolutions = {
    'surfacelayer': {
        'same_s': '1deg',
        'diff_s': '1deg'
    },
    'subsurface': {
        'same_s': '1deg',
        'diff_s': 'pt5deg'
    },
    'openwater': {
        'same_s': '1deg',
        'diff_s': 'pt25deg'
    },
}

parameters = {
    'surfacelayer': {
        'same_s': {},
        'diff_s': {}
    },
    'subsurface': {
        'same_s': {
            'parameter_a':
                cf.read(
                    'data/dummy_subsurface_parameter_a_{}'
                    '.nc'.format(space_resolutions['subsurface']['same_s'])
                ).select_field('long_name=parameter_a')
        },
        'diff_s': {
            'parameter_a':
                cf.read(
                    'data/dummy_subsurface_parameter_a_{}'
                    '.nc'.format(space_resolutions['subsurface']['diff_s'])
                ).select_field('long_name=parameter_a')
        }
    },
    'openwater': {
        'same_s': {
            'parameter_c': [3, '1']
        },
        'diff_s': {
            'parameter_c': [3, '1']
        }
    },
}

constants = {
    'surfacelayer': {
        'same_s': {},
        'diff_s': {}
    },
    'subsurface': {
        'same_s': {},
        'diff_s': {}
    },
    'openwater': {
        'same_s': {
            'constant_c': cf.Data(3, '1')
        },
        'diff_s': {
            'constant_c': cf.Data(3, '1')
        }
    },
}

records = {
    'surfacelayer': {
        'same_t': {'output_x': {timedelta(days=1): ['instantaneous'],
                                timedelta(days=8): ['cumulative', 'average',
                                                    'min', 'max']},
                   # using aliases for methods in 'output_x'
                   'transfer_i': {timedelta(days=1): ['point']},
                   'transfer_j': {timedelta(days=1): ['point']},
                   'state_a': {timedelta(days=1): ['point']},
                   'state_b': {timedelta(days=1): ['point']}},
        'diff_t': {'output_x': {timedelta(days=1): ['point'],
                                timedelta(days=8): ['sum', 'mean',
                                                    'minimum', 'maximum']},
                   # using defaults for methods in 'output_x'
                   'transfer_i': {timedelta(days=1): ['point']},
                   'transfer_j': {timedelta(days=1): ['point']},
                   'state_a': {timedelta(days=1): ['point']},
                   'state_b': {timedelta(days=1): ['point']}}
    },
    'subsurface': {
        'same_t': {'output_x': {timedelta(days=1): ['instantaneous'],
                                timedelta(days=8): ['cumulative', 'average',
                                                    'min', 'max']},
                   # using aliases for methods in 'output_x'
                   'transfer_k': {timedelta(days=1): ['point']},
                   'transfer_m': {timedelta(days=1): ['point']},
                   'state_a': {timedelta(days=1): ['point']},
                   'state_b': {timedelta(days=1): ['point']}},
        'diff_t': {'output_x': {timedelta(days=4): ['point'],
                                timedelta(days=8): ['sum', 'mean',
                                                    'minimum', 'maximum']},
                   # using defaults for methods in 'output_x'
                   'transfer_k': {timedelta(days=4): ['point']},
                   'transfer_m': {timedelta(days=4): ['point']},
                   'state_a': {timedelta(days=4): ['point']},
                   'state_b': {timedelta(days=4): ['point']}},
    },
    'openwater': {
        'same_t': {'output_x': {timedelta(days=1): ['instantaneous'],
                                timedelta(days=8): ['cumulative', 'average',
                                                    'min', 'max']},
                   # using aliases for methods in 'output_x'
                   'output_y': {timedelta(days=1): ['point']},
                   'transfer_l': {timedelta(days=1): ['point']},
                   'transfer_n': {timedelta(days=1): ['point']},
                   'transfer_o': {timedelta(days=1): ['point']},
                   'state_a': {timedelta(days=1): ['point']}},
        'diff_t': {'output_x': {timedelta(days=2): ['point'],
                                timedelta(days=8): ['sum', 'mean',
                                                    'minimum', 'maximum']},
                   # using defaults for methods in 'output_x'
                   'output_y': {timedelta(days=2): ['point']},
                   'transfer_l': {timedelta(days=2): ['point']},
                   'transfer_n': {timedelta(days=2): ['point']},
                   'transfer_o': {timedelta(days=2): ['point']},
                   'state_a': {timedelta(days=2): ['point']}}
    }
}


def get_dummy_component(category, kind, time_, space_, source):
    # get component class
    component_class = getattr(
        import_module('tests.components.{}'.format(category)),
        'Dummy{}'.format('' if source == 'Python' else source)
    )
    # get timedomain, spacedomain, dataset
    time_resolution = time_resolutions[category][time_]
    timedomain = get_dummy_timedomain(time_resolution)

    space_resolution = space_resolutions[category][space_]
    spacedomain = get_dummy_spacedomain(space_resolution)
    if category == 'surfacelayer':
        spacedomain.land_sea_mask = get_dummy_land_sea_mask_field(
            space_resolution
        )
        spacedomain.flow_direction = get_dummy_flow_direction_field(
            space_resolution
        )

    dataset = get_dummy_dataset(category, time_resolution, space_resolution)

    if kind == 'c':
        return component_class(
            saving_directory='outputs',
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters=parameters[category][space_],
            constants=constants[category],
            records=records[category][time_],
            io_slice=10
        )
    elif kind == 'd':
        return unifhy.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset(
                '{}_{}'.format(category, time_),
                time_resolution, space_resolution
            ),
            substituting_class=component_class,
            io_slice=10
        )
    else:  # kind == 'n'
        return unifhy.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=component_class
        )
