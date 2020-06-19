import cm4twc

from tests.components.surfacelayer import Dummy as SurfaceLayerDummy
from tests.components.subsurface import Dummy as SubSurfaceDummy
from tests.components.openwater import Dummy as OpenWaterDummy
from tests.test_time import get_dummy_timedomain
from tests.test_space import get_dummy_spacedomain
from tests.test_data import (get_dummy_dataset,
                             get_dummy_component_substitute_dataset)


def get_dummy_surfacelayer_component(kind, timedomain=None, spacedomain=None,
                                     dataset=None):
    if timedomain is None:
        timedomain = get_dummy_timedomain()
    if spacedomain is None:
        spacedomain = get_dummy_spacedomain()
    if dataset is None:
        dataset = get_dummy_dataset('surfacelayer')

    if kind == 'c':
        surfacelayer = SurfaceLayerDummy(
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
            dataset=get_dummy_component_substitute_dataset('surfacelayer'),
            substituting_class=cm4twc.SurfaceLayerComponent
        )
    else:  # i.e. 'n'
        surfacelayer = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=cm4twc.SurfaceLayerComponent
        )
    return surfacelayer


def get_dummy_subsurface_component(kind, timedomain=None, spacedomain=None,
                                   dataset=None):
    if timedomain is None:
        timedomain = get_dummy_timedomain()
    if spacedomain is None:
        spacedomain = get_dummy_spacedomain()
    if dataset is None:
        dataset = get_dummy_dataset('surfacelayer')

    if kind == 'c':
        subsurface = SubSurfaceDummy(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={'parameter_a': 2},
            constants={}
        )
    elif kind == 'd':
        subsurface = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset('subsurface'),
            substituting_class=cm4twc.SubSurfaceComponent
        )
    else:  # i.e. 'n'
        subsurface = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=cm4twc.SubSurfaceComponent
        )
    return subsurface


def get_dummy_openwater_component(kind, timedomain=None, spacedomain=None,
                                  dataset=None):
    if timedomain is None:
        timedomain = get_dummy_timedomain()
    if spacedomain is None:
        spacedomain = get_dummy_spacedomain()
    if dataset is None:
        dataset = get_dummy_dataset('surfacelayer')

    if kind == 'c':
        openwater = OpenWaterDummy(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={'parameter_a': 3},
            constants={}
        )
    elif kind == 'd':
        openwater = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=get_dummy_component_substitute_dataset('openwater'),
            substituting_class=cm4twc.OpenWaterComponent
        )
    else:  # i.e. 'n'
        openwater = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=cm4twc.OpenWaterComponent
        )
    return openwater
