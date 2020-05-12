import cm4twc

from tests.dummy_components.surfacelayer import Dummy as SurfaceLayerDummy
from tests.dummy_components.subsurface import Dummy as SubSurfaceDummy
from tests.dummy_components.openwater import Dummy as OpenWaterDummy


def get_surfacelayer_component(kind, timedomain, spacedomain, dataset):
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
            dataset=cm4twc.DataSet.from_file(
                'dummy_data/dummy_surfacelayer_substitute_data.nc'),
            substituting_class=cm4twc.SurfaceLayerComponent
        )
    else:  # i.e. 'n'
        surfacelayer = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=cm4twc.SurfaceLayerComponent
        )
    return surfacelayer


def get_subsurface_component(kind, timedomain, spacedomain, dataset):
    if kind == 'c':
        subsurface = SubSurfaceDummy(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={'saturated_hydraulic_conductivity': 2},
            constants={}
        )
    elif kind == 'd':
        subsurface = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=cm4twc.DataSet.from_file(
                'dummy_data/dummy_subsurface_substitute_data.nc'),
            substituting_class=cm4twc.SubSurfaceComponent
        )
    else:  # i.e. 'n'
        subsurface = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=cm4twc.SubSurfaceComponent
        )
    return subsurface


def get_openwater_component(kind, timedomain, spacedomain, dataset):
    if kind == 'c':
        openwater = OpenWaterDummy(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=dataset,
            parameters={'residence_time': 1},
            constants={}
        )
    elif kind == 'd':
        openwater = cm4twc.DataComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            dataset=cm4twc.DataSet.from_file(
                'dummy_data/dummy_openwater_substitute_data.nc'),
            substituting_class=cm4twc.OpenWaterComponent
        )
    else:  # i.e. 'n'
        openwater = cm4twc.NullComponent(
            timedomain=timedomain,
            spacedomain=spacedomain,
            substituting_class=cm4twc.OpenWaterComponent
        )
    return openwater
