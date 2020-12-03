"""
a Community Model for the Terrestrial Water Cycle
"""

# import python built-in packages, modules, classes, functions
import sys
from os import path
import yaml
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
with open(path.join(path.abspath(path.dirname(__file__)),
          'components', 'components.yml'), 'r') as f:
    _cfg = yaml.load(f, yaml.FullLoader)

for _category in ['surfacelayer', 'subsurface', 'openwater']:
    if (_category in _cfg) and (_cfg[_category] is not None):
        for _cls_name, _path in _cfg[_category].items():
            # import module using path provided in configuration file
            try:
                _module = import_module(_path, package=__name__)
            except ImportError:
                raise ImportError("{} component '{}' could not be "
                                  "imported.".format(_category, _cls_name))
            # get class using name provided in configuration file
            try:
                _class = getattr(_module, _cls_name)
            except AttributeError:
                raise AttributeError("class '{}' could not be found in "
                                     "module '{}'.".format(_cls_name,
                                                           _module.__name__))
            # assign class to relevant component module
            setattr(sys.modules['.'.join([__name__, 'components',
                                          _category])],
                    _cls_name, _class)
