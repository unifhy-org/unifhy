.. currentmodule:: cm4twc
.. default-role:: obj

Getting Started
===============

This section showcases the basic usage of modelling framework `cm4twc`
(Community Model for the Terrestrial Water Cycle).

.. code-block:: python
   :caption: Importing the package and checking its version.

   >>> import cm4twc
   >>> print(cm4twc.__version__)
   0.0.1

The central object in the framework is the `Model`, which is composed of
`Component`\s for the three compartments of the hydrological cycle (see
the list of :doc:`available components <components_available>`).

Each component needs to be spatio-temporally configured through `SpaceDomain`
and `TimeDomain` objects, to be given data contained in a `DataSet` instance,
and to be given parameter and/or constant values.

Configuring a Model
-------------------

Time
~~~~

`TimeDomain` characterises the time dimension of a `Component`.

.. code-block:: python
   :caption: Instantiating a `TimeDomain` object by specifying its start, end, and step.

   >>> from datetime import datetime, timedelta
   >>> timedomain = cm4twc.TimeDomain.from_start_end_step(
   ...    start=datetime(2019, 1, 1, 9, 0, 0),
   ...    end=datetime(2019, 1, 13, 9, 0, 0),
   ...    step=timedelta(days=1)
   ... )
   >>> print(timedomain)
   TimeDomain(
       time (12,): [2019-01-01 09:00:00, ..., 2019-01-12 09:00:00] gregorian
       bounds (12, 2): [[2019-01-01 09:00:00, ..., 2019-01-13 09:00:00]] gregorian
       calendar: gregorian
       units: seconds since 1970-01-01 00:00:00Z
       period: 12 days, 0:00:00
       timedelta: 1 day, 0:00:00
   )


Space
~~~~~

`SpaceDomain` characterises the space dimensions of a `Component`.
It is intended as an umbrella class from which to subclass.
The current supported spatial configuration is `LatLonGrid`.

.. code-block:: python
   :caption: Instantiating a `LatLonGrid` object from its dimensions' extents and resolutions.

   >>> spacedomain = cm4twc.LatLonGrid.from_extent_and_resolution(
   ...    latitude_extent=(51, 55),
   ...    latitude_resolution=1,
   ...    longitude_extent=(-2, 1),
   ...    longitude_resolution=1,
   ...    altitude_extent=(0, 4),
   ...    altitude_resolution=4
   ... )
   >>> print(spacedomain)
   LatLonGrid(
       shape {Z, Y, X}: (1, 4, 3)
       Z, altitude (1,): [2.0] m
       Y, latitude (4,): [51.5, ..., 54.5] degrees_north
       X, longitude (3,): [-1.5, -0.5, 0.5] degrees_east
       Z_bounds (1, 2): [[0.0, 4.0]] m
       Y_bounds (4, 2): [[51.0, ..., 55.0]] degrees_north
       X_bounds (3, 2): [[-2.0, ..., 1.0]] degrees_east
   )


Data
~~~~

`DataSet` must be used to gather all of the data required to run a `Component`
of `Model` . It is a dictionary-like object that stores references to `cf.Field`
instances.

.. note::

   Only data fully compliant with the
   `CF conventions <https://cfconventions.org/>`_ can be used.

.. code-block:: python
   :caption: Instantiating `DataSet` objects from a CF-compliant netCDF file.

   >>> dataset_surfacelayer = cm4twc.DataSet(
   ...     'tests/data/dummy_surfacelayer_data_daily.nc'
   ... )
   >>> print(dataset)
   DataSet{
       ancillary_a: ancillary_a(atmosphere_hybrid_height_coordinate(1), latitude(4), longitude(3)) 1
       driving_a: driving_a(time(12), atmosphere_hybrid_height_coordinate(1), latitude(4), longitude(3)) 1
       driving_b: driving_b(time(12), atmosphere_hybrid_height_coordinate(1), latitude(4), longitude(3)) 1
       driving_c: driving_c(time(12), atmosphere_hybrid_height_coordinate(1), latitude(4), longitude(3)) 1
   }
   >>> dataset_subsurface = cm4twc.DataSet(
   ...     'tests/data/dummy_subsurface_data_daily.nc'
   ... )
   >>> dataset_openwater = cm4twc.DataSet(
   ...     'tests/data/dummy_openwater_data_daily.nc'
   ... )


Processes
~~~~~~~~~

`Component` is an umbrella class which is subclassed into three distinct classes
for surface, sub-surface, and open water parts of the water cycle:
`SurfaceLayerComponent`, `SubSurfaceComponent`, and `OpenWaterComponent` respectively.

.. code-block:: python
   :caption: Instantiating a 'dummy' `SurfaceLayerComponent`.

   >>> import tests
   >>> print(tests.surfacelayer.Dummy)
   Dummy(
       category: surfacelayer
       inwards:
           transfer_k [1]
           transfer_l [1]
       outwards:
           transfer_i [1]
           transfer_j [1]
       driving data:
           driving_a [1]
           driving_b [1]
           driving_c [1]
       ancillary data:
           ancillary_c [1]
       states:
           state_a [1]
           state_b [1]
       outputs:
           output_x [1]
       solver history: 1
   )
   >>> component = tests.surfacelayer.Dummy(
   ...     output_directory='outputs',
   ...     timedomain=timedomain,
   ...     spacedomain=spacedomain,
   ...     dataset=dataset_surfacelayer,
   ...     parameters={},
   ...     outputs={'output_x': {timedelta(days=1): ['sum']}}
   ... )
   >>> print(component)
   Dummy(
       category: surfacelayer
       timedomain: period: 12 days, 0:00:00
       spacedomain: shape: (Z: 1, Y: 4, X: 3)
       dataset: 4 variable(s)
       outputs:
           output_x: 1 day, 0:00:00 {'sum'}
   )


Framework
~~~~~~~~~

`Model` constitutes the actual modelling framework, and it needs to be
instantiated with three `Component` instances, one for each of the three
`Component`\s of the water cycle.

.. code-block:: python
   :caption: Instantiating a `Model`.

   >>> model = cm4twc.Model(
   ...     identifier='dummy',
   ...     config_directory='configurations',
   ...     output_directory='outputs',
   ...     surfacelayer=tests.surfacelayer.Dummy(
   ...         'outputs', timedomain, spacedomain, dataset_surfacelayer,
   ...         parameters={}
   ...     ),
   ...     subsurface=tests.subsurface.Dummy(
   ...         'outputs', timedomain, spacedomain, dataset_subsurface,
   ...         parameters={'parameter_a': 1}
   ...     ),
   ...     openwater=tests.openwater.Dummy(
   ...         'outputs', timedomain, spacedomain, dataset_openwater,
   ...         parameters={'parameter_c': 3},
   ...         outputs={'output_y': {timedelta(days=1): ['point'],
   ...                               timedelta(days=2): ['sum', 'min']},
   ...                  'state_a': {timedelta(days=1): ['point']},
   ...                  'transfer_l': {timedelta(days=2): ['mean']}}
   ...     )
   ... )
   >>> print(model)
   Model(
       surfacelayer: Dummy
       subsurface: Dummy
       openwater: Dummy
   )

At this stage, the `Model` as such is fully configured, and the configuration
can be saved as a YAML file in the *config_directory* and named using the
*identifier* (e.g. in this example, the file would be at
*configurations/dummy.yml*).

.. code-block:: python
   :caption: Saving `Model` set up in YAML file.

   >>> model.to_yaml()


Simulating with a Model
-----------------------

Once configured, the instance of `Model` can be used to start a spin up run
and/or a main simulation run.

.. code-block:: python
   :caption: Spinning-up and running the `Model` simulation.

   >>> model.spin_up(start=datetime(2019, 1, 1, 9, 0, 0),
   ...               end=datetime(2019, 1, 3, 9, 0, 0),
   ...               cycles=2,
   ...               dumping_frequency=timedelta(days=3))
   >>> model.simulate(dumping_frequency=timedelta(days=2))

If the model has crashed, and *dumping_frequency* was set in the
*spin-up* and/or *simulate* invocations, a series of snapshots in time
have been stored in dump files in the *output_directory* of each
`Component`. A *resume* method for `Model` allows for the given run
to be resumed to reach completion of the simulation period. The *tag*
argument must be used to select which run to resume (i.e. any spin-up
cycle, or the main run), and the *at* argument can be used to select the
given snapshot in time to restart from.

.. code-block:: python
   :caption: Resuming the `Model` main simulation run.

   >>> model.resume(tag='run', at=datetime(2019, 1, 7, 9, 0, 0))
