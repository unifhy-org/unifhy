.. currentmodule:: unifhy
.. default-role:: obj

Adding new transfers
--------------------

The transfers that make up the UniFHy framework (shown in `Table 1 <https://unifhy-org.github.io/unifhy/contributors/development.html#id2>`_ and :ref:`Fig. 1<fig_transfers>`) are defined in the unifhy/component.py file.

.. _fig_transfers:
.. figure:: ../../_doc_img/framework_detailed_transfers.svg
   :align: center
   :alt: component transfers

Each core Component of UniFHy is defined by a python class which subclasses the `Component` class. The `Component` class contains all the functionality that underpins all UniFHy Components. The only significant difference between the Components is defined by the `_inwards_info` and `_outwards_info` attributes which define the transfers each Component is set up to receive and produce.

To add new transfers to the UniFHy framework it is therefore a case of adding the name and details of the transfer to the `_outwards_info` attribute of the Component the transfer is coming from and the `_inwards_info` attribute of the Component the transfer is going to.

.. rubric:: Example

For example to add transfer_x from the `SurfaceLayer` to `NutrientSurfaceLayer` Components:

.. code-block:: python
   :caption: Add the transfer information to the `_outwards_info` attribute of the `SurfaceLayerComponent` class

   class SurfaceLayerComponent(Component,  metaclass=abc.ABCMeta):
          _category = "surfacelayer"
         ...
          _outwards_info = {
               ...,
              "transfer_x": {
              "units": "kg m-2 s-1",
              "to": ["nutrientsurfacelayer"],
              "method": "mean",
            },
         ...
         }

.. code-block:: python
   :caption: Add the transfer information to the `_inwards_info` attribute of the `NutrientSurfaceLayerComponent` class

   class NutrientSurfaceLayerComponent(Component,  metaclass=abc.ABCMeta):
          _category = "nutrientsurfacelayer"
         ...
          _inwards_info = {
               ...,
              "transfer_x": {
              "units": "kg m-2 s-1",
              "from": "surfacelayer",
              "method": "mean",
           },
        ...
        }

Each transfer defined within a component's `_inwards_info` and `_outwards_info` attributes consists of a dictionary key-value pair where the key is the transfer name and the value a further dictionary with 3 key-value pairs, 'units', 'from' or 'to' and 'method'. 'units', 'from' and 'method' are strings whereas 'to' is a list of one or more Component names as strings. The Component names are given by the `_category` attributes of the Components. The 'method' key sets the method used by the Exchanger (the core of UniFHy, which handles the transfers between components) to process transfers between Components running on different timesteps. "mean" is usually the most appropriate but the other options available are "sum", "min" and "max".

.. rubric::example

E.g. for a transfer from Component A running with a 15-min timestep and Component B running on an hourly timestep, the Exchanger will take either a (weighted) mean, (weighted) sum, the min or the max of the 4 timestep values of Component A's transfer to provide to Component B, depending on the value of 'method'.

.. note::

   Adding transfers between Components in the *framework* means that any models developed to fit one or more of the affected Components of the framework can receive and make use of the transfer variable if they are sub-classing (based on) the 'to' Component, or produce the transfer variable if they are sub-classing the 'from' Component. In the example above, any models developed for the NutrientSurfaceLayer Component can now make use of `transfer_x` and any models developed for the SurfaceLayer Component can now produce `transfer_x`.

It is important to stress that defining the interface by determining which variables to transfer to/from which Components is no trivial task, and great care should be taken. To a certain degree it locks in what contributors can do when developing their models for the framework, and frequent ad-hoc or on-demand changes to the interface should be avoided to prevent obselescence of contributors' models.
