.. currentmodule:: cm4twc
.. default-role:: obj

Tutorial
========

This section showcases the basic usage of modelling framework `cm4twc`
(Community Model for the Terrestrial Water Cycle).

.. code-block:: python
   :caption: Importing the package and checking its version.

   >>> import cm4twc
   >>> print(cm4twc.__version__)
   0.1.0-beta

The central object in the framework is the `Model`, which requires three
`Component`\s for the three compartments of the terrestrial water cycle.
The components currently available to choose from are listed in the
:doc:`science library <../science_library>` section.

Each component needs to be spatio-temporally configured through `SpaceDomain`
and `TimeDomain` objects, to be given data contained in a `DataSet` instance,
and to be given parameter and/or constant values.

Configuring a Model
-------------------

Time
~~~~

`TimeDomain` characterises the time dimension of a `Component`.

.. code-block:: python
   :caption: Instantiating a `TimeDomain` by specifying its start, end, and step.

   >>> from datetime import datetime, timedelta
   >>> timedomain = cm4twc.TimeDomain.from_start_end_step(
   ...    start=datetime(2017, 1, 1, 0, 0, 0),
   ...    end=datetime(2018, 1, 1, 0, 0, 0),
   ...    step=timedelta(hours=1),
   ...    calendar='gregorian'
   ... )
   >>> print(timedomain)
   TimeDomain(
       time (8760,): [2017-01-01 00:00:00, ..., 2017-12-31 23:00:00] gregorian
       bounds (8760, 2): [[2017-01-01 00:00:00, ..., 2018-01-01 00:00:00]] gregorian
       calendar: gregorian
       units: seconds since 1970-01-01 00:00:00Z
       period: 365 days, 0:00:00
       timedelta: 1:00:00
   )


Space
~~~~~

All spatial configurations supported by the framework are subclasses of
`SpaceDomain`, they characterise the spatial dimensions of a `Component`.
The current supported spatial configurations can be found in the
:doc:`API Reference<../api_reference>`'s Space section. `LatLonGrid` is one example.

.. code-block:: python
   :caption: Instantiating a `LatLonGrid` from its dimensions' extents and resolutions.

   >>> spacedomain = cm4twc.LatLonGrid.from_extent_and_resolution(
   ...    latitude_extent=(51, 55),
   ...    latitude_resolution=0.5,
   ...    longitude_extent=(-2, 1),
   ...    longitude_resolution=0.5
   ... )
   >>> print(spacedomain)
   LatLonGrid(
       shape {Y, X}: (8, 6)
       Y, latitude (8,): [51.25, ..., 54.75] degrees_north
       X, longitude (6,): [-1.75, ..., 0.75] degrees_east
       Y_bounds (8, 2): [[51.0, ..., 55.0]] degrees_north
       X_bounds (6, 2): [[-2.0, ..., 1.0]] degrees_east
   )

Three additional properties of `SpaceDomain` may require to be set
depending on the component's requirements: *land_sea_mask*,
*flow_direction*, and *cell_area*. *land_sea_mask* may be used by a
component to be aware of where there is land and where there is sea,
but if set, it is also used to mask the component records. *flow_direction*
may be used by a component to determine where to move flow downstream,
it is namely compulsory if the component is using the `SpaceDomain`'s
*route* method. *cell_area* may be used by a component to determine the
surface area of each spatial element in the component spacedomain. For
some spacedomains (e.g. `LatLonGrid`, `RotatedLatLonGrid`,
`BritishNationalGrid`), the cell_area is calculated automatically by the
framework if not already set.

.. code-block:: python
   :caption: Setting land sea mask and flow direction for `LatLonGrid`.

   >>> import cf
   >>> spacedomain.land_sea_mask = cf.read('in/ancillary/land_sea_mask.nc').select_field('land_binary_mask')
   >>> print(spacedomain.land_sea_mask)
   [[ True  True  True  True  True  True]
    [ True  True  True  True  True  True]
    [ True  True  True  True  True  True]
    [ True  True  True  True  True  True]
    [ True  True  True  True  True False]
    [ True  True  True  True  True False]
    [ True  True  True  True False False]
    [ True  True  True False False False]]
   >>> spacedomain.flow_direction = cf.read('in/ancillary/flow_direction.nc').select_field("long_name=flow direction")


Data
~~~~

`DataSet` must be used to gather all of the data required to run a `Component`
of `Model` . It is a dictionary-like object that stores references to `cf.Field`
instances.

.. warning::

   Only data fully compliant with the
   `CF conventions <https://cfconventions.org/>`_ (v1.8 or later) can be used.

.. code-block:: python
   :caption: Instantiating `DataSet` from a CF-compliant netCDF file.

   >>> dataset_surfacelayer = cm4twc.DataSet(
   ...     files=['in/driving/LWdown_WFDE5_CRU_2017*_v1.0.nc',
   ...            'in/driving/SWdown_WFDE5_CRU_2017*_v1.0.nc',
   ...            'in/driving/Qair_WFDE5_CRU_2017*_v1.0.nc',
   ...            'in/driving/Tair_WFDE5_CRU_2017*_v1.0.nc',
   ...            'in/driving/Wind_WFDE5_CRU_2017*_v1.0.nc',
   ...            'in/driving/Precip_WFDE5_CRU_2017*_v1.0.nc',
   ...            'in/ancillary/leaf_area_index.nc',
   ...            'in/ancillary/canopy_height.nc',
   ...            'in/ancillary/soil_albedo.nc'],
   ...     name_mapping={'leaf-area index': 'leaf_area_index',
   ...                   'canopy height': 'vegetation_height',
   ...                   'soil albedo': 'surface_albedo'}
   ... )
   >>> print(dataset)
   DataSet{
       air_temperature(time(8760), latitude(20), longitude(28)) K
       leaf_area_index(time(12), latitude(360), longitude(720)) 1
       precipitation_flux(time(8760), latitude(20), longitude(28)) kg m-2 s-1
       specific_humidity(time(8760), latitude(20), longitude(28)) kg kg-1
       surface_albedo(latitude(360), longitude(720)) 1
       surface_downwelling_longwave_flux_in_air(time(8760), latitude(20), longitude(28)) W m-2
       surface_downwelling_shortwave_flux_in_air(time(8760), latitude(20), longitude(28)) W m-2
       vegetation_height(latitude(360), longitude(720)) m
       wind_speed(time(8760), latitude(20), longitude(28)) m s-1
   }
   >>> dataset_subsurface = cm4twc.DataSet(
   ...     files=['in/ancillary/saturated_hydraulic_conductivity.nc',
   ...            'in/ancillary/topmodel_saturation_capacity.nc',
   ...            'in/ancillary/topographic_index.nc'],
   ...     name_mapping={'saturated hydraulic conductivity': 'saturated_hydraulic_conductivity',
   ...                   'topmodel saturation capacity': 'topmodel_saturation_capacity',
   ...                   'topographic index': 'topographic_index'}
   ... )
   >>> dataset_openwater = cm4twc.DataSet(
   ...     files='in/ancillary/rfm_iarea.nc',
   ...     name_mapping={'RFM drainage area in cell counts (WFDEI)': 'i_area'}
   ... )


Science
~~~~~~~

`Component` is the core object subclassed into three distinct classes
for surface, sub-surface, and open water parts of the water cycle:
`SurfaceLayerComponent`, `SubSurfaceComponent`, and `OpenWaterComponent`
respectively. Each kind of component has the same API, only their interfaces
and data needs differ.

.. code-block:: python
   :caption: Exploring the signature of 'Artemis' `SubSurfaceComponent`.

   >>> import cm4twccontrib.artemis
   >>> print(cm4twccontrib.artemis.SubSurfaceComponent)
   SubSurfaceComponent(
       category: subsurface
       inwards info:
           evaporation_soil_surface [kg m-2 s-1]
           evaporation_ponded_water [kg m-2 s-1]
           transpiration [kg m-2 s-1]
           throughfall [kg m-2 s-1]
           snowmelt [kg m-2 s-1]
           water_level [kg m-2]
       inputs info:
           topmodel_saturation_capacity [mm m-1]
           saturated_hydraulic_conductivity [m s-1]
           topographic_index [1]
       requires land sea mask: False
       requires flow direction: False
       requires cell area: False
       constants info:
           m [1]
           rho_lw [kg m-3]
           S_top [m]
       states info:
           subsurface_store [m]
       outwards info:
           surface_runoff [kg m-2 s-1]
           subsurface_runoff [kg m-2 s-1]
           soil_water_stress [1]
   )

.. note::

   This information is also available on the online documentation, e.g.
   see :doc:`Artemis <../science/subsurface/cm4twccontrib.artemis.SubSurfaceComponent>`
   subsurface component page.


.. code-block:: python
   :caption: Getting an instance of `SubSurfaceComponent` 'Artemis'.

   >>> component = cm4twccontrib.artemis.SubSurfaceComponent(
   ...     saving_directory='outputs',
   ...     timedomain=timedomain,
   ...     spacedomain=spacedomain,
   ...     dataset=dataset_subsurface,
   ...     parameters={},
   ...     records={'surface_runoff': {timedelta(days=1): ['mean']}}
   ... )
   >>> print(component)
   SubSurfaceComponent(
       category: subsurface
       saving directory: outputs
       timedomain: period: 365 days, 0:00:00
       spacedomain: shape: (Y: 8, X: 6)
       records:
           surface_runoff: 1 day, 0:00:00 {'mean'}
   )

.. note::

   The variables that can be recorded using the *records* optional
   argument are the component's outwards, outputs, and states. By default,
   none are recorded.

Framework
~~~~~~~~~

`Model` constitutes the core object of the modelling framework. It needs
to be instantiated with three `Component` instances, one for each of the
three parts of the terrestrial water cycle.

.. code-block:: python
   :caption: Instantiating a `Model`.

   >>> import cm4twccontrib.rfm
   >>> model = cm4twc.Model(
   ...     identifier='tutorial',
   ...     config_directory='configurations',
   ...     saving_directory='outputs',
   ...     surfacelayer=cm4twc.surfacelayer.Artemis(
   ...         'outputs', timedomain, spacedomain, dataset_surfacelayer,
   ...         parameters={}
   ...     ),
   ...     subsurface=cm4twccontrib.artemis.SubSurfaceComponent(
   ...         'outputs', timedomain, spacedomain, dataset_subsurface,
   ...         parameters={}
   ...     ),
   ...     openwater=cm4twccontrib.rfm.OpenWaterComponent(
   ...         'outputs', timedomain, spacedomain, dataset_openwater,
   ...         parameters={'c_land': (0.20, 'm s-1'),
   ...                     'cb_land': (0.10, 'm s-1'),
   ...                     'c_river': (0.62, 'm s-1'),
   ...                     'cb_river': (0.15, 'm s-1'),
   ...                     'ret_l': (0.0, 'm s-1'),
   ...                     'ret_r': (0.005, 'm s-1'),
   ...                     'river_length': (50000, 'm')},
   ...         records={
   ...             'outgoing_water_volume_transport_along_river_channel': {
   ...                 timedelta(days=1): ['mean']
   ...             }
   ...         }
   ...     )
   ... )
   >>> print(model)
   Model(
       surfacelayer: Artemis
       subsurface: Artemis
       openwater: RFM
   )

.. warning::

   While the resolutions of the three components of the `Model` can be
   different, there are limitations.

   In space, the `SpaceDomain`\s of the three components must be in the
   same coordinate system (e.g. all using `LatLonGrid`) and their
   respective domains must span the same geographical region (i.e. the
   edges of their domains must overlap).

   In time, the `TimeDomain`\s of the three components must be in the
   same calendar (e.g. 'gregorian') and their respective resolutions
   must be a multiple integer of the fastest `Component`'s resolution.


.. note::

   `DataComponent` and `NullComponent` represent convenient utility to
   substitute science components. Any of the three components can be
   replaced by these alternatives.

   `DataComponent` is provided to act the part of a component of the water
   cycle by sourcing the component's outwards transfers from a `DataSet`,
   e.g. containing outputs of a previous simulation.

   `NullComponent` is provided to ignore a component of the water cycle
   by not processing the component's inwards transfers received, and by
   returning null values for the component's outwards transfers.

At this stage, the `Model` as such is fully configured, and the configuration
can be saved as a YAML file in the *config_directory* and named using the
*identifier* (e.g. in this example, the file would be at
*configurations/tutorial.yml*).

.. code-block:: python
   :caption: Saving `Model` set up in YAML file.

   >>> model.to_yaml()


See the :doc:`files <files>` section for an example of such model
configuration YAML file.

Simulating with a Model
-----------------------

Spin-Up and Simulate
~~~~~~~~~~~~~~~~~~~~

Once configured, the instance of `Model` can be used to start a spin up run
and/or a main simulation run.

.. code-block:: python
   :caption: Spinning-up and running the `Model` simulation.

   >>> model.spin_up(start=datetime(2019, 1, 1, 9, 0, 0),
   ...               end=datetime(2019, 1, 3, 9, 0, 0),
   ...               cycles=2,
   ...               dumping_frequency=timedelta(days=3))
   >>> model.simulate(dumping_frequency=timedelta(days=2))


Resume
~~~~~~

If the model has terminated prematurely, and *dumping_frequency* was
set in the *spin-up* and/or *simulate* invocations, a series of snapshots
in time have been stored in dump files in the *saving_directory* of each
`Component` and of the `Model`. A *resume* method for `Model` allows
for the given run to be resumed to reach completion of the simulation
period. The *tag* argument must be used to select which run to resume
(i.e. any spin-up cycle, or the main run), and the *at* argument can be
used to select the given snapshot in time to restart from.

.. code-block:: python
   :caption: Resuming the `Model` main simulation run.

   >>> model.resume(tag='run', at=datetime(2019, 1, 7, 9, 0, 0))
