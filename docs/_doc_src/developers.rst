.. currentmodule:: unifhy
.. default-role:: obj

Developer Guide
===============

This guide is for people interested in extending the technical
capabilities of the framework.

.. warning::

   Work in progress...

The transfers that make up the framework (shown in `Table 1 <https://unifhy-org.github.io/unifhy/contributors/development.html#id2>`_ and :ref:`Fig. 1<fig_transfers>`) are defined in the unifhy/component.py file.

.. _fig_transfers:
.. figure:: ../../_doc_img/framework_detailed_transfers.svg
   :align: center
   :alt: component transfers

To add new transfers to the framework it is simply a case of adding the name and details of the transfer to the `_outwards_info` section of the component the transfer is coming from and the `_inwards_info` section of the component the transfer is going to. 

.. rubric:: Example

For example to add transfer_x from the `SurfaceLayer` to `NutrientSurfaceLayer` components:

.. code-block:: python
   :caption: Add the transfer information to the `_outwards_info` of the `SurfaceLayerComponent` class

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
   :caption: Add the transfer information to the '_inwards_info' of the `NutrientSurfaceLayerComponent` class

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

Each transfer defined within a component's `_inwards_info` and `_outwards_info` attributes consists of a dictionary key-value pair where the key is the transfer name and the value a further dictionary with 3 key-value pairs, `units`, `from` or `to` and `method`. If the transfer goes 'to' more than 1 component then `to` can be a list of component names, otherwise a string. The component names are given by the `_category` attributes of the Components. 

.. note::

   Remember adding a transfer between Components in the *framework* means that any Components developed for the framework now have the option to receive and make use of the transfer variable if they are sub-classing the 'to' Component, or have the option to produce the transfer variable if they are sub-classing the 'from' Component. In the example above, any Components developed for the NutrientSurfaceLayer could make use of `transfer_x` and any Components developed for the SurfaceLayer could produce `transfer_x`. Both Components would have to be developed to build a Model that actually made use of the new transfer. 

Adding new Components to the framework
======================================

.. note::
   By adding a new Component to the *framework* you are creating the space for others to put in the science that represents a new part of the Earth-System that UnifHy has heretofore not accounted for and has had to be input to components via in*puts* i.e. data files instead of dynamically modelled variables. 
   

Adding new Components to the framework is a more complicated business. 
The broad strokes are:
- Decide which area of the Earth-System the Component will represent and what transfers it will need from other Components and provide to other Components
- Add the Component to unifhy/component.py, subclassing the Component class and following the structure and syntax of the existing Components, and the inwards and outwards transfers to _inwards_info and _outwards_info respectively
- Add the new transfers provided by the new Component, described by the new Component's _outwards_info, to the relevant other Components' _inward_info
- Adapt unifhy.Model to accept the extra Component(s)
- Update the unit tests to handle the extra Component(s). This involves creating dummy Component version(s) of the new dummy Component(s) and calculating the values of all the transfers and records for various configurations of the model when all the Components are run together. There is a tool for this here. 
