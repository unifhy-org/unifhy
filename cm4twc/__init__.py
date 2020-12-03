"""
a Community Model for the Terrestrial Water Cycle
"""

# import python built-in packages, modules, classes, functions
import sys
from os import path
from configparser import ConfigParser
from importlib import import_module

# import package's own modules, classes, functions
from .version import __version__
from .model import Model
from .time import TimeDomain
from .space import LatLonGrid, RotatedLatLonGrid
from .data import DataSet
from .components import (surfacelayer, subsurface, openwater,
                         SurfaceLayerComponent, SubSurfaceComponent,
                         OpenWaterComponent, DataComponent, NullComponent)
from .settings import atol, rtol, decr, dtype_float

# import modelling component classes defined in configuration file
_cfg = ConfigParser()
_cfg.read(path.join(path.abspath(path.dirname(__file__)),
          'components', 'components.ini'))

for _component_type in ['surfacelayer', 'subsurface', 'openwater']:
    if _component_type in _cfg:
        for path_ in _cfg[_component_type]:
            cls_name = _cfg[_component_type][path_]
            # import module defined as key in configuration file
            try:
                mod_ = import_module(path_, package=__name__)
            except ImportError:
                raise ImportError("The {} component '{}' could not be "
                                  "imported.".format(_component_type, cls_name))
            # get class defined as value in configuration file
            try:
                cls_ = getattr(mod_, cls_name)
            except AttributeError:
                raise AttributeError("The class '{}' could not be found in "
                                     "the module '{}'.".format(cls_name,
                                                               mod_.__name__))
            # assign class to relevant component module
            setattr(sys.modules['.'.join([__name__, 'components',
                                          _component_type])],
                    cls_name, cls_)
