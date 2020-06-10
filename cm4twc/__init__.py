import sys
from os import path
from configparser import ConfigParser
from importlib import import_module

from .version import __version__
from .model import Model
from .time_ import TimeDomain
from .space_ import LatLonGrid, RotatedLatLonGrid
from .data_ import DataSet
from .components import (surfacelayer, subsurface, openwater,
                         SurfaceLayerComponent, SubSurfaceComponent,
                         OpenWaterComponent, DataComponent, NullComponent)
from .settings import ATOL, RTOL, DECR

# import the modelling components defined in the configuration file
_cfg = ConfigParser()
_cfg.read(path.join(path.abspath(path.dirname(__file__)),
          'components', 'components.ini'))

for _component_type in ['surfacelayer', 'subsurface', 'openwater']:
    if _component_type in _cfg:
        for path_ in _cfg[_component_type]:
            cls_name = _cfg[_component_type][path_]
            # import the module defined as a key in the configuration file
            try:
                mod_ = import_module(path_, package=__name__)
            except ImportError:
                raise ImportError("The {} component '{}' could not be "
                                  "imported.".format(_component_type, cls_name))
            # get the class defined as a value in the configuration file
            try:
                cls_ = getattr(mod_, cls_name)
            except AttributeError:
                raise AttributeError("The class '{}' could not be found in "
                                     "the module '{}'.".format(cls_name,
                                                               mod_.__name__))
            # assign the class to the relevant component module
            setattr(sys.modules['.'.join([__name__, 'components',
                                          _component_type])],
                    cls_name, cls_)
