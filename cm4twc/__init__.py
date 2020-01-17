# -*- coding: utf-8 -*-
from os import path
from configparser import ConfigParser
from importlib import import_module

from .model import Model
from .time_ import TimeFrame
from .space_ import Grid, Network
from .data_ import DataBase, Variable
from .components import surface, subsurface, openwater, \
    SurfaceComponent, SubSurfaceComponent, OpenWaterComponent

# import the modelling components defined in the configuration file
cfg = ConfigParser()
cfg.read(path.join(path.abspath(path.dirname(__file__)),
         'components', 'components.ini'))

for model_type in ['surface', 'subsurface', 'openwater']:
    if model_type in cfg:
        for name in cfg[model_type]:
            try:
                import_module(cfg[model_type][name], package='cm4twc')
            except ImportError:
                raise ImportError("The {} model '{}' could not "
                                  "be imported.".format(model_type, name))
