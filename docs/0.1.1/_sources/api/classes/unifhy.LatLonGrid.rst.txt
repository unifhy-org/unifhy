.. currentmodule:: unifhy
.. default-role:: obj

LatLonGrid
==========

.. autoclass:: LatLonGrid
   :show-inheritance:


Methods
-------

Construction
~~~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.LatLonGrid.from_extent_and_resolution
   ~unifhy.LatLonGrid.from_field

Comparison
~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.LatLonGrid.is_space_equal_to
   ~unifhy.LatLonGrid.spans_same_region_as
   ~unifhy.LatLonGrid.is_matched_in

Utility
~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.LatLonGrid.route


Attributes
----------

.. autosummary::
   :nosignatures:
   :toctree: ../attributes/
   :template: attribute.rst

   ~unifhy.LatLonGrid.shape
   ~unifhy.LatLonGrid.axes
   ~unifhy.LatLonGrid.X
   ~unifhy.LatLonGrid.Y
   .. ~unifhy.LatLonGrid.Z
   ~unifhy.LatLonGrid.X_bounds
   ~unifhy.LatLonGrid.Y_bounds
   .. ~unifhy.LatLonGrid.Z_bounds
   ~unifhy.LatLonGrid.X_name
   ~unifhy.LatLonGrid.Y_name
   .. ~unifhy.LatLonGrid.Z_name
   ~unifhy.LatLonGrid.land_sea_mask
   ~unifhy.LatLonGrid.flow_direction
   ~unifhy.LatLonGrid.cell_area