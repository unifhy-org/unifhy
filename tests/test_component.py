import cm4twc

from importlib import import_module
from tests.test_time import get_dummy_timedomain
from tests.test_space import get_dummy_spacedomain
from tests.test_data import (get_dummy_dataset,
                             get_dummy_component_substitute_dataset)

time_resolutions = {
    'surfacelayer': {
        'sync': 'daily',
        'async': 'daily'
    },
    'subsurface': {
        'sync': 'daily',
        'async': '3daily'
    },
    'openwater': {
        'sync': 'daily',
        'async': '2daily'
    },
}

space_resolutions = {
    'surfacelayer': {
        'match': '1deg',
        'remap': '1deg'
    },
    'subsurface': {
        'match': '1deg',
        'remap': 'pt5deg'
    },
    'openwater': {
        'match': '1deg',
        'remap': 'pt2deg'
    },
}

parameters = {
    'surfacelayer': {},
    'subsurface': {
        'parameter_a': 1
    },
    'openwater': {
        'parameter_c': 3
    },
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

    dataset = get_dummy_dataset(category, time_resolution, space_resolution)

    if kind == 'c':
        return component_class(
            output_directory='outputs',
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters=parameters[category],
            constants={}
        )
    elif kind == 'd':
        return cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset(
                '{}_{}'.format(category, time_),
                time_resolution, space_resolution
            ),
            substituting_class=component_class
        )
    else:  # i.e. 'n'
        return cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=component_class
        )
