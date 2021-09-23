.. currentmodule:: cm4twc
.. default-role:: obj

Development
===========

This section details the steps required to develop a component contribution
that is compliant with the framework.

You can follow the steps below to develop your component(s):

.. contents::
   :backlinks: none
   :local:

Create your component by subclassing a generic framework component
------------------------------------------------------------------

In the modelling framework, the terrestrial water cycle is divided into
three components, i.e. `SurfaceLayerComponent`, `SubSurfaceComponent`,
and `OpenWaterComponent` (see :ref:`Fig. 1<fig_diagram>`). These are the
three framework components to create subclasses from.

Each component features a fixed interface (i.e. a pre-defined set of
transfers of information with the other components of the framework):
inward information (variables that are given to the component), and
outward information (variables that are computed by the component),
see :ref:`Fig. 2<fig_transfers>`.

.. _fig_transfers:
.. figure:: ../../_doc_img/framework_detailed_transfers.png
   :scale: 60 %
   :align: center
   :alt: component transfers

   Fig. 2: Transfers of Information between Components.

For component contributions to be `cm4twc`-compliant, they need to comply
with this fixed interface. If your component contribution is overlapping
several components, it requires to be refactored into the relevant number
of components.

Contributions must be implemented as Python classes, and more specifically
as subclasses of one of the three framework components. This way, the
interface for the component contribution is already set, and the
component directly inherits all the functionalities intrinsic to the
framework so that, as a contributor, you can focus solely on specifying
the data and science elements of your component(s).

Creating your contribution as a Python class can simply be done by
subclassing from the relevant framework component, e.g. a surface layer
component would be created as follows:

.. code-block:: python
   :caption: Subclassing from `SurfaceLayerComponent` class.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       pass


.. note::

   :py:`pass` is only added here temporarily for this Python example
   script to remain valid, it will be replaced in the subsequent steps.

.. note::

   By convention, it is asked that you use the same class name as the
   one you subclassed from, e.g. *SurfaceLayerComponent* here.

Document your component using its class docstring
-------------------------------------------------

A brief description of the component (with reference(s) if applicable)
alongside a field list containing e.g. name(s) of contributor(s),
affiliation(s) of contributor(s), licence, copyright, etc. must be provided.
To do so, use your class docstring and follow a `reStructuredText syntax
<https://docutils.sourceforge.io/docs/user/rst/quickref.html>`_ as
in the example below.

.. code-block:: python
   :caption: Using the component class docstring for description and acknowledgment.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       """
       Brief description of the component.

       Details published in `Doe et al. (2020) <https://doi.org/##.####/XXX>`_.

       :Contributors: Jane Doe [1]
       :Affiliations: [1] University
       :Licence: GPL-3.0
       :Copyright: 2021, Jane Doe
       """



Define your component using its class attributes
------------------------------------------------

The component definition is used by `cm4twc` to make sure that all the
information required by the component to run is provided by the user.
The definition of a component is made of the information about its
inputs, outputs, states, parameters, and constants.

The inputs/outputs exclude those variables already included in the fixed
interface, i.e. inward and outward transfers (see :ref:`Fig. 2<fig_transfers>`).

The inputs must be one of the three following kinds:

- dynamic: data required for each spatial element and for each time step,
- static: data required for each spatial element and constant over time,
- climatologic: data required for each spatial element and for a given
  frequency within a climatology year.

The parameters are those subject to tuning, while the constants are those
not subject to tuning. Note, parameter tuning/calibration is not a
functionality offered by the framework.

The definition for the component is specified by assigning dictionaries
to the class attributes `_inputs_info`, `_outputs_info`, `_states_info`,
`_parameters_info`, and `_constants_info`. For example, in the `_inputs_info`
dictionary, each item corresponds to a different input, and for this item
the key is the name of the input, and the value is a dictionary containing
the metadata for the input, featuring at least two items, one for its *kind*
and one for its *units* (and one for its *frequency* if *kind* is
*climatologic*). All other items in the component definition must feature
at least a *units* metadata item, and an optional *description* metadata
item is strongly encouraged. An additional item *default_value* is
mandatory for each constant in `_constants_info`.

An optional *divisions* item exists for the `_states_info` dictionary,
where its expected value is an integer, a string, or a sequence of integers
and/or strings:

- by default its value is 1, indicating the state is a scalar;
- if its value is an integer greater than 1, it indicates that the state
  is a vector, and its value is the length of the vector;
- if its value is a string, the string must correspond to the name of a
  component constant, whose value will be used in place of the string
  as divisions;
- if its value is a sequence, it indicates that the state is an array,
  and its values are the length of the dimensions of the array (in the
  order in the sequence).

The *divisions* item may be useful when considering e.g. different
vertical layers in a component. Note that scalar/vector/array refer to
the dimension of the state for a given element in the SpaceDomain, so
a scalar state does not mean that there is only one state value for the
whole spatial domain, it only means that there is only one state value for
each spatial element in the space domain.

In addition, the component definition features two special optional
attributes `_requires_land_sea_mask` and `_requires_flow_direction`.
They must be assigned a boolean value (True if required by your
component, False if not) -- their default value is False. If you need
land sea mask information for your computations, set `_requires_land_sea_mask`
to True and access it in your class methods using
`self.spacedomain.land_sea_mask`. If you need flow direction information
or want to use the flow routing functionality of the component (accessible
through `self.spacedomain.route(...)`), set `_requires_flow_direction` to True,
and access it in your class methods using `self.spacedomain.flow_direction`.

See a detailed example of a mock component definition below.

.. code-block:: python
   :caption: Completing the component class definition in the class attributes.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       """component description here"""

       _inputs_info = {
           'input_1': {
               'kind': 'dynamic',
               'units': 'kg m-2 s-1'
           },
           'input_2': {
               'kind': 'climatologic',
               'frequency': 'monthly',
               'units': 'kg m-2 s-1''
           },
           'input_3': {
               'kind': 'static',
               'units': 'm'
           }
       }
       _outputs_info = {
           'output_1': {
               'units': 'kg m-2 s-1'
           },
           'output_2': {
               'units': 'kg m-3 s-1'
           }
       }
       _states_info = {
           'state_1': {
               'units': 'kg m-2'
           },
           'state_2': {
               'divisions': 4,
               'units': 'kg m-2'
           }
       }
       _parameters_info = {
           'parameter_1': {
               'description': 'brief parameter description here',
               'units': '1'
           }
       }
       _constants_info = {
           'constant_1': {
               'description': 'brief constant description here',
               'units': '1',
               'default_value': 0.5
           }
       }
       _requires_land_sea_mask = False
       _requires_flow_direction = True


Implement the initialise-run-finalise component class methods
-------------------------------------------------------------

The computations in your component contribution must be broken down into
the three phases initialise, run, and finalise. This means that your
Python class must feature three methods named `initialise`, `run`, and
`finalise`. Note, `initialize` and `finalize` spellings are not supported.

The `initialise` method defines the initial conditions for the component
states and features any other action required to enable the component to
start its integration. It is called at the beginning of a model simulation.
The available arguments for this method are the component states, parameters,
and constants. This method is not expected to return anything (i.e.
Python default's `return None`).

The `run` method contains the computations required to integrate from
one time step to the next. It is called iteratively to move through the
model simulation period. The available arguments for this method are the
component inwards, inputs, states, parameters, and constants. This method
is expected to return a tuple of two dictionaries: the first dictionary
must contain the component outward transfers (keys are the outwards names,
values are the outwards arrays), the second dictionary must contain the
component outputs (keys are the outputs names, values are the outputs
arrays). Note, the second dictionary may be empty if the component does
not feature any custom outputs.

The `finalise` method contains any action required to guarantee that the
simulation can be restarted after the last simulation time step. It is
called once at the end of a model simulation. The available arguments
for this method are the component states, parameters, and constants.
This method is not expected to return anything (i.e. Python default's
`return None`).

Since, the arguments of the three methods `initialise`, `run`, and
`finalise` are going to be passed as keyword arguments, the names of the
arguments in these methods' signatures must necessarily be the ones found
in the component class attributes (if renaming is required, this must be
done internally to the methods). Moreover, they must all feature a final
special argument `**kwargs` to collect all the remaining available
arguments that are not used.

.. code-block:: python
   :caption: Implementing the three mandatory methods initialise, run, and finalise.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       """component description here"""

       # component definition here

       def initialise(self, state_1, state_2, **kwargs):
           # set here initial condition values for component states
           state_1[-1][...] = 0
           state_2[-1][...] = 0

       def run(self, inwards_1, inwards_2, inwards_3, input_1, input_2, input_3,
               state_1, state_2, parameter_1, constant_1, **kwargs):

           # compute science using available inwards/inputs/parameters/constants
           routed, outed = self.spacedomain.route(inwards_1 + inwards_2 + inwards_3)

           outwards_1 = (routed + input_1 + state_1[-1]
                         / self.timedelta_in_seconds) * parameter_1

           m = self.current_datetime.month

           output_1 = input_2[m - 1, ...] * constant_1

           output_2 = input_2[m - 1, ...] * (1 - constant_1)
           for i in range(4):
               output_2 += (0.05 * state_2[-1][..., i]
                            / self.timedelta_in_seconds)
           output_2 /= input_3

           # update component state
           state_1[0][:] = state_1[-1] * (1 - self.timedelta_in_seconds * parameter_1)
           state_2[0][...] =  0.95 * state_2[-1][...]

           # return outwards and outputs
           return (
               {'outwards_1': outwards_1},
               {'output_1': output_1,
                'output_2': output_2}
           )

       def finalise(self, state_1, state_2, **kwargs):
           # cleanly wrap up simulation here
           # to be able to restart from where simulation stopped
           pass

This concludes the preparation of your component contribution, the next
step is to :doc:`package <packaging>` your component(s).
