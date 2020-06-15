.. currentmodule:: cm4twc
.. default-role:: obj

Tutorial
========

This draft of the modelling framework has a code-name: `cm4twc` for Community
Model for the Terrestrial Water Cycle.

The central object in the framework is the `Model`, which is composed of
`Component`\s for the various compartments of the hydrological cycle,
themselves spatio-temporally configured through `SpaceDomain` and `TimeDomain`
objects, and driven by data contained
in a `DataSet` instance.

.. code-block:: python
   :caption: *Importing the package and checking its version.*

   >>> import cm4twc
   >>> print(cm4twc.__version__)
   0.0.1

Core concepts structuring the framework
---------------------------------------

.. rubric:: `TimeDomain` object

This class characterises the time dimension of a `Component`.

.. code-block:: python
   :caption: *Instantiating a TimeDomain object from tuple of datetime objects.*

   >>> from datetime import datetime
   >>> timedomain = cm4twc.TimeDomain.from_datetime_sequence(
   ...    datetimes=(datetime(2019, 1, 1, 9, 0, 0),
   ...               datetime(2019, 1, 2, 9, 0, 0),
   ...               datetime(2019, 1, 3, 9, 0, 0))
   ... )
   >>> print(timedomain)
   TimeDomain(
       time (3,): [2019-01-01 09:00:00, 2019-01-02 09:00:00, 2019-01-03 09:00:00] gregorian
       bounds (3, 2): [[2019-01-01 09:00:00, ..., 2019-01-04 09:00:00]] gregorian
       calendar: gregorian
       units: seconds since 1970-01-01 00:00:00Z
       timedelta: 1 day, 0:00:00
   )

.. code-block:: python
   :caption: *Instantiating a TimeDomain object from tuple of datetime objects.*

   >>> from datetime import datetime, timedelta
   >>> timedomain2 = cm4twc.TimeDomain.from_start_end_step(
   ...    start=datetime(2019, 1, 1, 9, 0, 0),
   ...    end=datetime(2020, 1, 1, 9, 0, 0),
   ...    step=timedelta(days=1)
   ... )
   >>> print(timedomain2)
   TimeDomain(
       time (367,): [2020-01-01 09:00:00, ..., 2021-01-01 09:00:00] gregorian
       bounds (367, 2): [[2020-01-01 09:00:00, ..., 2021-01-02 09:00:00]] gregorian
       calendar: gregorian
       units: seconds since 1970-01-01 00:00:00Z
       timedelta: 1 day, 0:00:00
   )

.. rubric:: `SpaceDomain` object

This class characterises the space dimensions of a `Component`.
It is intended as an umbrella class from which to subclass.
A first subclass available is the `Grid`, itself discretised into `LatLonGrid` and `RotatedLatLonGrid`.

.. code-block:: python
   :caption: *Instantiating a RotatedLatLonGrid object from lists of data.*

   >>> spacedomain = cm4twc.RotatedLatLonGrid(
   ...     grid_latitude=[2.2, 1.76, 1.32, 0.88, 0.44, 0., -0.44, -0.88, -1.32, -1.76],
   ...     grid_longitude=[-4.7, -4.26, -3.82, -3.38, -2.94, -2.5, -2.06, -1.62, -1.18],
   ...     grid_latitude_bounds=[[2.42, 1.98], [1.98, 1.54], [1.54, 1.1], [1.1,  0.66],
   ...                           [0.66, 0.22], [0.22, -0.22], [-0.22, -0.66],
   ...                           [-0.66, -1.1], [-1.1, -1.54], [-1.54, -1.98]],
   ...     grid_longitude_bounds=[[-4.92, -4.48], [-4.48, -4.04], [-4.04, -3.6],
   ...                            [-3.6,  -3.16], [-3.16, -2.72], [-2.72, -2.28],
   ...                            [-2.28, -1.84], [-1.84, -1.4], [-1.4, -0.96]],
   ...     altitude=1.5, altitude_bounds=[1.0, 2.0],
   ...     earth_radius=6371007.,  grid_north_pole_latitude=38.0,
   ...     grid_north_pole_longitude=190.0
   ... )
   >>> print(spacedomain)
   RotatedLatLonGrid(
       shape {Z, Y, X}: (1, 10, 9)
       Z, altitude (1,): [1.5] m
       Y, grid_latitude (10,): [2.2, ..., -1.76] degrees
       X, grid_longitude (9,): [-4.7, ..., -1.18] degrees
       Z_bounds (1, 2): [[1.0, 2.0]] m
       Y_bounds (10, 2): [[2.42, ..., -1.98]] degrees
       X_bounds (9, 2): [[-4.92, ..., -0.96]] degrees
   )

.. code-block:: python
   :caption: *Instantiating a LatLonGrid object from its dimensions' extents and resolutions.*

   >>> spacedomain2 = cm4twc.LatLonGrid.from_extent_and_resolution(
   ...    latitude_extent=(30, 70),
   ...    latitude_resolution=5,
   ...    longitude_extent=(0, 90),
   ...    longitude_resolution=10,
   ...    altitude_extent=(0, 10),
   ...    altitude_resolution=10
   ... )
   >>> print(spacedomain2)
   LatLonGrid(
      shape {Y, X}: (8, 9)
      Z, altitude (1,): [5.0] m
      Y, latitude (8,): [32.5, ..., 67.5] degrees_north
      X, longitude (9,): [5.0, ..., 85.0] degrees_east
      Z_bounds (1, 2): [[0.0, 10.0]] m
      Y_bounds (8, 2): [[30.0, ..., 70.0]] degrees_north
      X_bounds (9, 2): [[0.0, ..., 90.0]] degrees_east
   )

.. rubric:: `DataSet` object

This class exists to host all of the data required to run a `Component` of `Model` .
It is a dictionary-like object that stores references to `cf.Field` instances.

.. code-block:: python
   :caption: *Instantiating a Dataset object from a netCDF file.*

   >>> dataset = cm4twc.DataSet(
   ...     files=['in/dummy_driving_data_1day.nc', 'in/dummy_ancillary_data.nc'],
   ...     name_mapping={
   ...         'rainfall_flux': 'rainfall',
   ...         'snowfall_flux': 'snowfall',
   ...         'air_temperature': 'air_temperature',
   ...         'soil_temperature': 'soil_temperature'
   ...     }
   ... )
   >>> print(dataset)
   DataSet{
       air_temperature: <CF Field: air_temperature(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
       rainfall: <CF Field: rainfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
       snowfall: <CF Field: snowfall_flux(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) kg m-2 s-1>
       soil_temperature: <CF Field: soil_temperature(time(6), atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
       vegetation_fraction: <CF Field: vegetation_fraction(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) 1>
   }

.. rubric:: `Component` object

This class is an umbrella class which is subclassed into three distinct classes
for surface, sub-surface, and open water parts of the water cycle:
`SurfaceLayerComponent`, `SubSurfaceComponent`, and `OpenWaterComponent` respectively.

.. code-block:: python
   :caption: *Instantiating a 'dummy' SurfaceLayerComponent.*

   import tests
   >>> component = tests.dummy_components.surfacelayer.Dummy(
   ...     timedomain=timedomain,
   ...     spacedomain=spacedomain,
   ...     dataset=dataset,
   ...     parameters={}
   ... )
   >>> print(component)
   Dummy(
       category: surfacelayer
       inwards:
           soil_water_stress [1]
       outwards:
           throughfall [kg m-2 s-1]
           snowmelt [kg m-2 s-1]
           transpiration [kg m-2 s-1]
           evaporation_soil_surface [kg m-2 s-1]
           evaporation_ponded_water [kg m-2 s-1]
           evaporation_openwater [kg m-2 s-1]
       driving data:
           rainfall [kg m-2 s-1]
           snowfall [kg m-2 s-1]
           air_temperature [K]
       ancillary data:
           vegetation_fraction [1]
       states:
           canopy [kg m-2]
           snowpack [kg m-2]
       solver history: 1
   )

.. rubric:: `Model` object

This class constitutes the actual modelling framework, and it needs to be
instantiated with three `Component` instances, one for each of the three
`Component`\s of the water cycle.

.. code-block:: python
   :caption: *Instantiating a Model.*

   >>> model = cm4twc.Model(
   ...     surfacelayer=tests.dummy_components.surfacelayer.Dummy(
   ...         timedomain=timedomain,
   ...         spacedomain=spacedomain,
   ...         dataset=dataset,
   ...         parameters={}
   ...     ),
   ...     subsurface=tests.dummy_components.subsurface.Dummy(
   ...         timedomain=timedomain,
   ...         spacedomain=spacedomain,
   ...         dataset=dataset,
   ...         parameters={'saturated_hydraulic_conductivity': 2}
   ...     ),
   ...     openwater=tests.dummy_components.openwater.Dummy(
   ...         timedomain=timedomain,
   ...         spacedomain=spacedomain,
   ...         dataset=dataset,
   ...         parameters={'residence_time': 1}
   ...     )
   ... )
   >>> print(model)
   Model(
       surfacelayer: Dummy
       subsurface: Dummy
       openwater: Dummy
   )

Using the `Model` once configured
---------------------------------

This instance of `Model` can now be used to start a spin up run and/or a simulation run.

.. code-block:: python
   :caption: *Spinning-up and running the Model simulation.*

   >>> model.spin_up(start=datetime(2019, 1, 1, 9, 0, 0),
   ...               end=datetime(2019, 1, 2, 9, 0, 0),
   ...               cycles=2)
   >>> outputs = model.simulate()
