.. currentmodule:: cm4twc
.. default-role:: obj

Preparation
===========

This section details the steps required to prepare a component contribution
for inclusion in the science repository of the framework.

You can then follow the steps below to prepare your component contribution:

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
inwards information (variables that are given to the component), and
outwards information (variables that are computed by the component),
see :ref:`Fig. 2<fig_transfers>`.

.. _fig_transfers:
.. figure:: ../../_doc_img/framework_detailed_transfers.png
   :scale: 60 %
   :align: center
   :alt: component transfers

   Fig. 2: Transfers of Information between Components.

Contributions to the science repository of `cm4twc` need to comply with
this fixed interface. If your contribution to `cm4twc` is overlapping
several components, it requires to be refactored into the relevant number
of components.

Contributions must be implemented as a Python class, and more specifically
as a subclass of one of the three framework components. This way, the
interface for the component contribution is already set, and the
component directly inherits all the functionalities intrinsic to the
framework so that, as a contributor, you can focus solely on specifying
the data and science elements of the component.

Creating your contribution as a Python class can simply be done by
subclassing from the relevant framework component, e.g. a surface layer
component named `MyContribution` would be created as follows:

.. code-block:: python
   :caption: Subclassing from `SurfaceLayerComponent` class.

   from cm4twc import SurfaceLayerComponent


   class MyContribution(SurfaceLayerComponent):
       pass


Note, :py:`pass` is only added here temporarily for this Python example
script to remain valid, it will be replaced in the subsequent steps.

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

   from cm4twc import SurfaceLayerComponent


   class MyContribution(SurfaceLayerComponent):
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
interface, i.e. inwards and outwards transfers (see :ref:`Fig. 2<fig_transfers>`).

The inputs must be one of three following kinds:

- dynamic: data required for each spatial element and for each time step,
- static: data required for each spatial location and constant over time,
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
item is strongly encouraged. An optional *divisions* item exists for the
`_states_info` dictionary, where its expected value is an integer: by
default its value is 1, indicating the state is a scalar, if its value
is greater than 1, it indicates the state is a vector, and its value is
the length of the vector. The *divisions* item may be useful when
considering e.g. different soil layers.

In addition, special attributes in the definition `_land_sea_mask` and
`_flow_direction` and must be assigned a boolean value (True if required,
False if not required). If you need land sea mask information for your
computation, set `_land_sea_mask` to True and access it in your class
methods using `self.spacedomain.land_sea_mask`. If you need flow
direction information or want to use the flow routing functionality of
the component (accessible through `self.spacedomain.route()`), set
`_flow_direction` as True, and access it in your class methods using
`self.spacedomain.flow_direction`.

See a detailed example of component definition below.

.. code-block:: python
   :caption: Completing the component class definition in the class attributes.

   from cm4twc import SurfaceLayerComponent


   class MyContribution(SurfaceLayerComponent):
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
               'units': '1'
           }
       }
       _land_sea_mask = False
       _flow_direction = True


Implement the initialise-run-finalise component class methods
-------------------------------------------------------------

The computations of your component contribution must be broken down into
the three phases initialise, run, and finalise. This means that your
Python class must feature three methods named `initialise`, `run`, and
`finalise`.

The `initialise` method defines the initial conditions for the component
states and features any other action required to enable the component to
start its integration. It is called at the beginning of a model simulation.
The arguments of this method are the component states. This method is not
expected to return anything.

The `run` method contains the computations required to integration from
one time step to the next. It is called multiple times to move through
the model simulation period. The arguments of this method are the component
inwards, inputs, states, parameters, and constants (constants must be
given a default value directly in the method signature). This method is
expected to return a tuple of two dictionaries: the first dictionary
must contain the component outward transfers (keys are the outward names,
values are the outward arrays), the second dictionary must contain the
component outputs (keys are the output names, values are the output arrays).
Note, the second dictionary may be empty if the component does not
feature any custom outputs.

The `finalise` method contains any action required to guarantee that the
simulation can be restarted after the last simulation time step. It is
called at the end of a model simulation. This method is not expected to
return anything.

Since, the arguments of the three methods `initialise`, `run`, and
`finalise` are going to be passed as keyword arguments, the names of the
arguments in their signatures must necessarily be the ones found in the
component class attribute (if renaming is required, this must be done
internally to the method). Moreover, they must all feature a final
special argument `**kwargs`.

.. code-block:: python
   :caption: Implementing the three mandatory methods initialise, run, and finalise.

   from cm4twc import SurfaceLayerComponent


   class MyContribution(SurfaceLayerComponent):
       """component description here"""

       # component definition here

       def initialise(self, state_1, state_2, **kwargs):
           # set here initial condition values for component states
           state_1[-1][...] = 0
           state_2[-1][...] = 0

       def run(self, inwards_1, inwards_2, inwards_3, input_1, input_2, input_3,
               state_1, state_2, parameter_1, constant_1=0.5, **kwargs)

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
           output_2 /= input_1

           # update component state
           state_1[0][:] = state_1[-1] * (1 - self.timedelta_in_seconds * parameter_1)
           state_2[0][...] =  0.95 * state_2[-1][...]

           # return outwards and outputs
           return (
               {'outwards_1': outwards_1},
               {'output_1': output_1,
                'output_2': output_2}
           )

       def finalise(self, state_1, state_2, **kwargs)
           # cleanly wrap up simulation here
           # to be able to restart from where simulation stopped
           pass

This concludes the preparation of your component contribution, the next
step is to share your work by submitting it for inclusion in the framework
(see section :doc:`submission`).
