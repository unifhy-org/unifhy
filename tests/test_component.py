import cm4twc

from tests.components.surfacelayer import Dummy as SurfaceLayerDummy
from tests.components.subsurface import Dummy as SubSurfaceDummy
from tests.components.openwater import Dummy as OpenWaterDummy
from tests.test_time import get_dummy_timedomain
from tests.test_space import get_dummy_spacedomain
from tests.test_data import (get_dummy_dataset,
                             get_dummy_component_substitute_dataset)


def get_dummy_surfacelayer_component(kind, time_resolution, sync=True):
    timedomain = get_dummy_timedomain(time_resolution)
    spacedomain = get_dummy_spacedomain()
    dataset = get_dummy_dataset('surfacelayer', time_resolution)

    if kind == 'c':
        surfacelayer = SurfaceLayerDummy(
            output_directory='outputs',
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={},
            constants={}
        )
    elif kind == 'd':
        surfacelayer = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset(
                'surfacelayer' if sync else 'surfacelayer_async',
                time_resolution
            ),
            substituting_class=SurfaceLayerDummy
        )
    else:  # i.e. 'n'
        surfacelayer = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=SurfaceLayerDummy
        )
    return surfacelayer


def get_dummy_subsurface_component(kind, time_resolution, sync=True):
    timedomain = get_dummy_timedomain(time_resolution)
    spacedomain = get_dummy_spacedomain()
    dataset = get_dummy_dataset('subsurface', time_resolution)

    if kind == 'c':
        subsurface = SubSurfaceDummy(
            output_directory='outputs',
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={'parameter_a': 1},
            constants={}
        )
    elif kind == 'd':
        subsurface = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset(
                'subsurface' if sync else 'subsurface_async',
                time_resolution
            ),
            substituting_class=SubSurfaceDummy
        )
    else:  # i.e. 'n'
        subsurface = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=SubSurfaceDummy
        )
    return subsurface


def get_dummy_openwater_component(kind, time_resolution, sync=True):
    timedomain = get_dummy_timedomain(time_resolution)
    spacedomain = get_dummy_spacedomain()
    dataset = get_dummy_dataset('openwater', time_resolution)

    if kind == 'c':
        openwater = OpenWaterDummy(
            output_directory='outputs',
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={'parameter_c': 3},
            constants={}
        )
    elif kind == 'd':
        openwater = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset(
                'openwater' if sync else 'openwater_async',
                time_resolution
            ),
            substituting_class=OpenWaterDummy
        )
    else:  # i.e. 'n'
        openwater = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=OpenWaterDummy
        )
    return openwater
