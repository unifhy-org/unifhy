.. currentmodule:: unifhy
.. default-role:: obj

Tutorial
========

This section showcases the basic usage of the modelling framework `unifhy`
(Unified Framework for Hydrology).

.. important::

   To run this tutorial, you need to install the framework and the relevant
   science components to be used (here Artemis, RFM and LTLS). To install the framework, 
   follow the instructions in the :doc:`installation <installation>` section, then run the 
   command:
   
      
      $ pip install unifhycontrib-artemis unifhycontrib-rfm unifhycontrib-ltls


   This tutorial is based on v1.0.0 of the framework, you can check the version
   you have just installed by starting a Python console and executing the following
   commands:

   .. code-block:: python
      :caption: Importing the framework and checking its version.

      >>> import unifhy
      >>> print(unifhy.__version__)
      1.0.0


   The input data required to run this tutorial can be found in the ``data``
   folder of the repository.


Configuring a Model
-------------------

The central object in the framework is the `Model`, which combines six
science components for the three compartments of the terrestrial water cycle and nutrients cycle.
The science components currently available to choose from are listed in
the :doc:`science library <../science_library>` section.

Each science component needs to be spatio-temporally discretised through
`SpaceDomain` and `TimeDomain` instances, to be given data contained in
a `DataSet` instance, and to be given parameter and/or constant values.

See :ref:`Fig. 3<fig_uml>` for more details on how all these concepts are
articulated together.

Time
~~~~

`TimeDomain` characterises the time dimension of a `Component`, i.e.
the period and the temporal resolution.

.. code-block:: python
   :caption: Instantiating a `TimeDomain` by specifying its start, end, and step.

   >>> from datetime import datetime, timedelta
   >>> timedomain = unifhy.TimeDomain.from_start_end_step(
   ...    start=datetime(2017, 1, 1, 0, 0, 0),
   ...    end=datetime(2017, 2, 1, 0, 0, 0),
   ...    step=timedelta(hours=1),
   ...    calendar='gregorian'
   ... )
   >>> print(timedomain)
   TimeDomain(
       time (744,): [2017-01-01 00:00:00, ..., 2017-01-31 23:00:00] gregorian
       bounds (744, 2): [[2017-01-01 00:00:00, ..., 2017-02-01 00:00:00]] gregorian
       calendar: gregorian
       units: seconds since 1970-01-01 00:00:00Z
       period: 31 days, 0:00:00
       timedelta: 1:00:00
   )


Space
~~~~~

All spatial configurations supported by the framework are subclasses of
`SpaceDomain`: they characterise the spatial dimensions of a `Component`,
i.e. the region and the spatial resolution. The spatial configurations
currently supported can be found in the :doc:`API Reference<../api_reference>`'s
Space section. `LatLonGrid` is one example.

.. code-block:: python
   :caption: Instantiating a `LatLonGrid` from its dimensions' extents and resolutions.

   >>> spacedomain = unifhy.LatLonGrid.from_extent_and_resolution(
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
*flow_direction*, and *cell_area*:

   - *land_sea_mask* may be used by a component to be aware of where there
     is land and where there is sea, but if set, it is also used to mask
     the component records;
   - *flow_direction* may be used by a component to determine where to move
     flow downstream, it is namely compulsory if the component is using the
     `SpaceDomain`'s *route* method;
   - *cell_area* may be used by a component to determine the surface area of
     each spatial element in the component spacedomain. For some spacedomains
     (e.g. `LatLonGrid`, `RotatedLatLonGrid`, `BritishNationalGrid`), the
     cell area is calculated automatically by the framework if not already set.

.. code-block:: python
   :caption: Setting land sea mask and flow direction for `LatLonGrid`.

   >>> import cf
   >>> spacedomain.land_sea_mask = (
   ...     cf.read('data/land_sea_mask.nc').select_field('land_binary_mask')
   ... )
   >>> print(spacedomain.land_sea_mask)
   [[ True  True  True  True  True  True]
    [ True  True  True  True  True  True]
    [ True  True  True  True  True  True]
    [ True  True  True  True  True  True]
    [ True  True  True  True  True False]
    [ True  True  True  True  True False]
    [ True  True  True  True False False]
    [ True  True  True False False False]]
   >>> spacedomain.flow_direction = (
   ...     cf.read('data/flow_direction.nc').select_field("long_name=flow direction")
   ... )


.. note::

   To check whether a component needs any of these spatial properties,
   each `Component` can be queried via its methods `requires_land_sea_mask()`,
   `requires_flow_direction()`, and `requires_cell_area()`.

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

   >>> dataset_surfacelayer = unifhy.DataSet(
   ...     files=['data/surface_downwelling_longwave_flux_in_air.nc',
   ...            'data/surface_downwelling_shortwave_flux_in_air.nc',
   ...            'data/specific_humidity.nc',
   ...            'data/air_temperature.nc',
   ...            'data/wind_speed.nc',
   ...            'data/precipitation_flux.nc',
   ...            'data/leaf_area_index.nc',
   ...            'data/canopy_height.nc',
   ...            'data/soil_albedo.nc'],
   ...     name_mapping={'leaf-area index': 'leaf_area_index',
   ...                   'canopy height': 'vegetation_height',
   ...                   'soil albedo': 'surface_albedo'}
   ... )
   >>> print(dataset_surfacelayer)
   DataSet{
       air_temperature(time(744), latitude(20), longitude(28)) K
       leaf_area_index(time(12), latitude(360), longitude(720)) 1
       precipitation_flux(time(744), latitude(20), longitude(28)) kg m-2 s-1
       specific_humidity(time(744), latitude(20), longitude(28)) kg kg-1
       surface_albedo(latitude(360), longitude(720)) 1
       surface_downwelling_longwave_flux_in_air(time(744), latitude(20), longitude(28)) W m-2
       surface_downwelling_shortwave_flux_in_air(time(744), latitude(20), longitude(28)) W m-2
       vegetation_height(latitude(360), longitude(720)) m
       wind_speed(time(744), latitude(20), longitude(28)) m s-1
   }
   >>> dataset_subsurface = unifhy.DataSet(
   ...     files=['data/saturated_hydraulic_conductivity.nc',
   ...            'data/available_water_storage_capacity.nc',
   ...            'data/topographic_index.nc'],
   ...     name_mapping={
   ...         'saturated hydraulic conductivity': 'saturated_hydraulic_conductivity',
   ...         'available water storage capacity': 'topmodel_saturation_capacity',
   ...         'topographic index': 'topographic_index'
   ...      }
   ... )
   >>> dataset_openwater = unifhy.DataSet(
   ...     files='data/flow_accumulation.nc',
   ...     name_mapping={
   ...         'RFM drainage area in cell counts (WFDEI)': 'flow_accumulation'
   ...     }
   ... )
   >>> dataset_nutrientsubsurface = unifhy.DataSet(
   ...     files=['data/nutrients_runoffs/DOC_ro.nc',      
   ...            'data/nutrients_runoffs/DIC_ro.nc',      
   ...            'data/nutrients_runoffs/DON_ro.nc',      
   ...            'data/nutrients_runoffs/Ammonium_ro.nc', 
   ...            'data/nutrients_runoffs/Nitrate_ro.nc',
   ...            'data/nutrients_runoffs/TDP_ro.nc',
   ...            'data/nutrients_runoffs/Calcium_ro.nc',  
   ...            'data/nutrients_runoffs/Sulphate_ro.nc', 
   ...            'data/nutrients_runoffs/Silicon_ro.nc',  
   ...            'data/nutrients_runoffs/DOC_gw.nc',
   ...            'data/nutrients_runoffs/DIC_gw.nc',      
   ...            'data/nutrients_runoffs/DON_gw.nc',
   ...            'data/nutrients_runoffs/Ammonium_gw.nc',
   ...            'data/nutrients_runoffs/Nitrate_gw.nc',
   ...            'data/nutrients_runoffs/TDP_gw.nc',
   ...            'data/nutrients_runoffs/Calcium_gw.nc',  
   ...            'data/nutrients_runoffs/Sulphate_gw.nc', 
   ...            'data/nutrients_runoffs/Silicon_gw.nc',  
   ...            'data/nutrients_runoffs/CO2.nc']
   ... ) 
   >>> dataset_nutrientopenwater = unifhy.DataSet(
   ...     files='data/flow_accumulation.nc',
   ...     name_mapping={
   ...         'RFM drainage area in cell counts (WFDEI)': 'flow_accumulation'
   ...     }
   ... )

Science
~~~~~~~

Each science component is either of a `SurfaceLayerComponent`,
`SubSurfaceComponent`, `OpenWaterComponent`, `NutrientSurfaceLayerComponent`,
`NutrientSubSurfaceComponent` or `NutrientOpenWaterComponent` type, and it embeds the
biophysical processes for the surface, sub-surface, or open water parts
of the water and nutrients cycle, respectively. All six types share the framework
`Component` class as their base class, which makes them readily compatible
with `unifhy`. They have the same API, only their interfaces and data
needs differ (i.e their signatures). Not all the components must be used to create 
a Model, any of the components can be substituted with a `DataComponent` or
`NullComponent`.

.. code-block:: python
   :caption: Exploring the signature of 'Artemis' `SubSurfaceComponent`.

   >>> import unifhycontrib.artemis
   >>> print(unifhycontrib.artemis.SubSurfaceComponent)
   SubSurfaceComponent(
       category: subsurface
       inwards metadata:
           canopy_liquid_throughfall_and_snow_melt_flux [kg m-2 s-1]
           transpiration_flux_from_root_uptake [kg m-2 s-1]
       inputs metadata:
           topmodel_saturation_capacity [mm m-1]
           saturated_hydraulic_conductivity [m s-1]
           topographic_index [1]
       requires land sea mask: False
       requires flow direction: False
       requires cell area: False
       constants metadata:
           m [1]
           rho_lw [kg m-3]
           S_top [m]
       states metadata:
           subsurface_store [m]
       outwards metadata:
           soil_water_stress_for_transpiration [1]
           surface_runoff_flux_delivered_to_rivers [kg m-2 s-1]
           net_groundwater_flux_to_rivers [kg m-2 s-1]
   )

.. note::

   This information is also available on the online documentation, e.g.
   see :doc:`Artemis <../science/subsurface/unifhycontrib.artemis.SubSurfaceComponent>`
   subsurface component page.

To get a science component instance, one needs to provide a `TimeDomain`
instance, a `SpaceDomain` instance, a `DataSet` instance, and parameter
and/or constant values as per indicated in its signature.

.. code-block:: python
   :caption: Getting an instance of `SubSurfaceComponent` 'Artemis'.

   >>> component = unifhycontrib.artemis.SubSurfaceComponent(
   ...     saving_directory='outputs',
   ...     timedomain=timedomain,
   ...     spacedomain=spacedomain,
   ...     dataset=dataset_subsurface,
   ...     parameters={},
   ...     records={
   ...         'surface_runoff_flux_delivered_to_rivers': {timedelta(days=1): ['mean']}
   ...     }
   ... )
   >>> print(component)
   SubSurfaceComponent(
       category: subsurface
       saving directory: outputs
       timedomain: period: 31 days, 0:00:00
       spacedomain: shape: (Y: 8, X: 6)
       records:
           surface_runoff_flux_delivered_to_rivers: 1 day, 0:00:00 {'mean'}
   )

.. note::

   The variables that can be recorded using the *records* optional
   parameter are the component's outwards, outputs, and states. By default,
   none are recorded.

Framework
~~~~~~~~~

`Model` constitutes the core object of the modelling framework. It needs
to be instantiated with six science `Component` instances, one for each
of the three parts of the terrestrial water cycle and one for each of the
three parts of the terrestrial nutrients cycle. It combines these six
science components to make a fully functional model for the terrestrial
water and nutrients cycles.

.. code-block:: python
   :caption: Instantiating a `Model`.

   >>> import unifhycontrib.rfm
   >>> import unifhycontrib.ltls
   >>> model = unifhy.Model(
   ...     identifier='tutorial',
   ...     config_directory='configurations',
   ...     saving_directory='outputs',
   ...     surfacelayer=unifhycontrib.artemis.SurfaceLayerComponent(
   ...         'outputs', timedomain, spacedomain, dataset_surfacelayer,
   ...         parameters={}
   ...     ),
   ...     subsurface=unifhycontrib.artemis.SubSurfaceComponent(
   ...         'outputs', timedomain, spacedomain, dataset_subsurface,
   ...         parameters={}
   ...     ),
   ...     openwater=unifhycontrib.rfm.OpenWaterComponent(
   ...         'outputs', timedomain, spacedomain, dataset_openwater,
   ...         parameters={'c_land': (0.20, 'm s-1'),
   ...                     'cb_land': (0.10, 'm s-1'),
   ...                     'c_river': (0.62, 'm s-1'),
   ...                     'cb_river': (0.15, 'm s-1'),
   ...                     'ret_l': (0.0, '1'),
   ...                     'ret_r': (0.005, '1'),
   ...                     'routing_length': (50000, 'm')},
   ...         records={
   ...             'outgoing_water_volume_transport_along_river_channel': {
   ...                 timedelta(days=1): ['mean']
   ...             }
   ...         }
   ...     ),
   ...     nutrientsurfacecomponent = unifhy.NullComponent(
   ...          timedomain, spacedomain, unifhy.component.NutrientSurfaceLayerComponent
   ...     ),
   ...     nutrientsubsurface=unifhy.DataComponent(
   ...          timedomain, spacedomain, dataset_nutrientsubsurface, 
   ...          unifhy.component.NutrientSubSurfaceComponent
   ...     ),
   ...     nutrientopenwater=unifhycontrib.ltls.NutrientOpenWaterComponent(
   ...         'outputs', timedomain, spacedomain, dataset_nutrientopenwater,
   ...         parameters={}
   ...     )
   ... )
   >>> print(model)
   Model(
       identifier: tutorial
       config directory: configurations
       saving directory: outputs
       surfacelayer: unifhycontrib.artemis.surfacelayer
       subsurface: unifhycontrib.artemis.subsurface
       openwater: unifhycontrib.rfm.openwater
       nutrientsurfacelayer: unifhy.component
       nutrientsubsurface: unifhy.component
       nutrientopenwater: unifhycontrib.ltls.nutrientopenwater
   )

.. warning::

   While the resolutions of the three components of the `Model` can be
   different, there are limitations.

   In space, the `SpaceDomain`\s of the three components must:

   - be in the same coordinate system (e.g. all using `LatLonGrid`);
   - span the same geographical region (i.e. the edges of their domains
     must overlap);
   - feature resolutions that are integer multiples of one another (i.e.
     grid cells of a domain must fully include or fully be included
     in grid cells of the other domains).

   In time, the `TimeDomain`\s of the three components must:

   - be in the same calendar (e.g. all in 'gregorian');
   - span the same period (i.e. the start and end of their domains
     must coincide);
   - feature resolutions that are integer multiples of one another (i.e.
     time steps of a domain must fully include or fully be included in
     time steps of the other domains)


.. note::

   `DataComponent` and `NullComponent` represent a convenient utility to
   substitute science components. Any of the six components can be
   replaced by these alternatives.

   `DataComponent` is provided to act the part of a component of the water or nutrient
   cycles by sourcing the component's outwards transfers from a `DataSet`,
   e.g. containing outputs of a previous simulation.

   `NullComponent` is provided to ignore a component of the water or nutrient cycles
   by not processing the component's inwards transfers received, and by
   returning null values for the component's outwards transfers.

At this stage, the `Model` as such is fully configured, and the configuration
is automatically saved as a YAML file in the *config_directory* and named using the
*identifier* (e.g. in this tutorial, the file would be at
*configurations/tutorial.yml*). This file can be reused later to directly obtain
a configured model.

.. code-block:: python
   :caption: Configuring a `Model` from a YAML configuration file.

   >>> another_model = unifhy.Model.from_yaml('configurations/tutorial.yml')
   >>> print(another_model)
   Model(
       identifier: tutorial
       config directory: configurations
       saving directory: outputs
       surfacelayer: unifhycontrib.artemis.surfacelayer
       subsurface: unifhycontrib.artemis.subsurface
       openwater: unifhycontrib.rfm.openwater
       nutrientsurfacelayer: unifhy.component,
       nutrientsubsurface: unifhy.component,
       nutrientopenwater: unifhycontrib.ltls.nutrientopenwater
   )


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

   >>> model.spin_up(start=datetime(2017, 1, 1, 0, 0, 0),
   ...               end=datetime(2017, 1, 3, 0, 0, 0),
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
period. The *tag* parameter must be used to select which run to resume
(i.e. any spin-up cycle, or the main run), and the *at* parameter can be
used to select the given snapshot in time to restart from.

.. code-block:: python
   :caption: Resuming the `Model` main simulation run.

   >>> model.resume(tag='run', at=datetime(2017, 1, 7, 0, 0, 0))


.. note::

   Further training resources are available at `<https://github.com/unifhy-org/unifhy-training>`_.
