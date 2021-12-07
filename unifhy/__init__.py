"""A Community Model for the Terrestrial Water Cycle."""


# import package's own modules, classes, functions
from .version import __version__
from .model import Model
from .time import TimeDomain
from .space import LatLonGrid, RotatedLatLonGrid, BritishNationalGrid
from .data import DataSet
from .component import (
    SurfaceLayerComponent, SubSurfaceComponent, OpenWaterComponent,
    DataComponent, NullComponent
)
from .settings import atol, rtol, decr, dtype_float
