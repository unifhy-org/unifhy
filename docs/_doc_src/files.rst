.. currentmodule:: cm4twc
.. default-role:: obj

Files
=====

Configuration files
-------------------

.. code-block:: yaml
   :caption: *Content of a `cm4twc` configuration YAML file.*

   identifier: dummy
   config_directory: configurations
   surfacelayer:
     module: tests.components.surfacelayer.dummy
     class: Dummy
     output_directory: outputs
     timedomain:
       start: 2019-01-01 09:00:00
       end: 2019-01-07 09:00:00
       step:
         seconds: 86400.0
       units: days since 2019-01-01 09:00:00Z
       calendar: gregorian
     spacedomain:
       class: LatLonGrid
       latitude_extent: [51, 55]
       latitude_resolution: 1
       longitude_extent: [-2, 1]
       longitude_resolution: 1
       latitude_longitude_location: centre
       altitude_extent: [0, 4]
       altitude_resolution: 4
       altitude_location: centre
     dataset:
       driving_a:
         files: [data/dummy_surfacelayer_data_daily.nc]
         select: driving_a
       driving_b:
         files: [data/dummy_surfacelayer_data_daily.nc]
         select: driving_b
       driving_c:
         files: [data/dummy_surfacelayer_data_daily.nc]
         select: driving_c
       ancillary_a:
         files: [data/dummy_surfacelayer_data_daily.nc]
         select: ancillary_a
     parameters: null
     constants: null
   subsurface:
     module: tests.components.subsurface.dummy
     class: Dummy
     output_directory: outputs
     timedomain:
       start: 2019-01-01 09:00:00
       end: 2019-01-07 09:00:00
       step:
         seconds: 86400.0
       units: days since 2019-01-01 09:00:00Z
       calendar: gregorian
     spacedomain:
       class: LatLonGrid
       latitude_extent: [51, 55]
       latitude_resolution: 1
       longitude_extent: [-2, 1]
       longitude_resolution: 1
       latitude_longitude_location: centre
       altitude_extent: [0, 4]
       altitude_resolution: 4
       altitude_location: centre
     dataset:
       driving_a:
         files: [data/dummy_subsurface_data_daily.nc]
         select: driving_a
     parameters:
       parameter_a: 2
     constants: null
   openwater:
     module: tests.components.openwater.dummy
     class: Dummy
     output_directory: outputs
     timedomain:
       start: 2019-01-01 09:00:00
       end: 2019-01-07 09:00:00
       step:
         seconds: 86400.0
       units: days since 2019-01-01 09:00:00Z
       calendar: gregorian
     spacedomain:
       class: LatLonGrid
       latitude_extent: [51, 55]
       latitude_resolution: 1
       longitude_extent: [-2, 1]
       longitude_resolution: 1
       latitude_longitude_location: centre
       altitude_extent: [0, 4]
       altitude_resolution: 4
       altitude_location: centre
     dataset:
       ancillary_a:
         files: [data/dummy_openwater_data_daily.nc]
         select: ancillary_a
     parameters:
       parameter_a: 3
     constants: null
