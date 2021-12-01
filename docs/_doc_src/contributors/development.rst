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

Create your science component by subclassing a generic framework component
--------------------------------------------------------------------------

In the modelling framework, the terrestrial water cycle is divided into
three components, i.e. `SurfaceLayerComponent`, `SubSurfaceComponent`,
and `OpenWaterComponent` (see :ref:`Fig. 1<fig_diagram>`). These are the
three framework components to create subclasses from to start your
science component.

Each component features a fixed interface (i.e. a pre-defined set of
transfers of information with the other components of the framework):
inward information (variables that are given to the component, i.e.
"inwards"), and outward information (variables that are computed by the
component, i.e. "outwards"), see :ref:`Fig. 2<fig_transfers>`, and
:ref:`Tab. 1<tab_transfers>`.

.. _fig_transfers:
.. figure:: ../../_doc_img/framework_detailed_transfers.svg
   :align: center
   :alt: component transfers

   Fig. 2: Transfers of Information between Components (see
   :ref:`Tab. 1<tab_transfers>` for the numbers meanings).

.. _tab_transfers:
.. table:: Tab. 1: Transfers of Information between Components (see
           :ref:`Fig. 2<fig_transfers>` for the numbers context)

   ==  ==============================================  ========================
   #   Name                                            Unit
   ==  ==============================================  ========================
   1   canopy_throughfall_flux                         |kg m-2 s-1|
   2   snow_melt_flux                                  |kg m-2 s-1|
   3   transpiration_flux_from_root_uptake             |kg m-2 s-1|
   4   soil_water_stress_for_transpiration             1
   5   direct_water_evaporation_flux_from_soil         |kg m-2 s-1|
   6   soil_water_stress_for_direct_soil_evaporation   1
   7   water_evaporation_flux_from_standing_water      |kg m-2 s-1|
   8   standing_water_area_fraction                    1
   9   total_water_area_fraction                       1
   10  water_evaporation_flux_from_open_water          |kg m-2 s-1|
   11  direct_throughfall_flux                         |kg m-2 s-1|
   12  surface_runoff_flux_delivered_to_rivers         |kg m-2 s-1|
   13  net_groundwater_flux_to_rivers                  |kg m-2 s-1|
   14  open_water_area_fraction                        1
   15  open_water_surface_height                       m
   ==  ==============================================  ========================

.. |kg m-2 s-1| replace:: kg m\ :sup:`-2` s\ :sup:`-1`

For component contributions to be fully `cm4twc`-compliant, they need to
comply with this fixed interface. If your science component contribution
is overlapping several components, it requires to be refactored into the
relevant number of components.

Contributions must be implemented as Python classes, and more specifically
as subclasses of one of the three framework components. This way, the
interface for the science component contribution is already set, and the
component directly inherits all the functionalities intrinsic to the
framework so that, as a contributor, you can focus solely on specifying
the data and science elements of your component(s).

Creating your contribution as a Python class can simply be done by
subclassing from the relevant framework component.

.. rubric:: Example

See an example of a mock surface layer component creation below.

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

Document your science component using its class docstring
---------------------------------------------------------

A description of the component (with reference(s) if applicable) alongside
a field list containing e.g. name(s) of contributor(s), affiliation(s) of
contributor(s), licence, copyright, etc. must be provided. To do so, use
your class docstring and follow a `reStructuredText syntax
<https://docutils.sourceforge.io/docs/user/rst/quickref.html>`_.

For the structure of the docstring itself, please start with a short summary line
followed by a blank line before providing a more elaborate description as per
`PEP 257 <https://www.python.org/dev/peps/pep-0257/#multi-line-docstrings>`_.
The field list should be placed last and preceded by a blank line.

.. rubric:: Example

See an example of a mock component description below.

.. code-block:: python
   :caption: Using the component class docstring for description and acknowledgment.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       """Summary line describing the component.

       More elaborate description for the component.

       References:
       `Doe et al. (2020) <https://doi.org/##.####/XXX>`_.

       :Contributors: Jane Doe [1]
       :Affiliations: [1] University
       :Licence: GPL-3.0
       :Copyright: 2021, Jane Doe
       """



Define your science component using its class attributes
--------------------------------------------------------

The component interface definition is used by the framework to make sure
that your component can be coupled with other components to form a model.
Indeed, while a standard interface exists for the framework component
(see :ref:`Fig. 2<fig_transfers>`), the science component may fall short
to use or produce some of them. So long as the other components it is
coupled with are not needing the ones not produced, the framework does
not enforce a full compliance with its standard interface. However,
transfers not present in the standard interface cannot be used.

The definition of the component interface is specified by assigning
sets to the class attributes `_inwards` and `_outwards`. In such a set,
the items must be part or all of the transfers in the fixed interface
for this component (see :ref:`Fig. 2<fig_transfers>`).

The component definition is used by the framework to make sure that all
the information required by the component to run is provided by the
user. The definition of a component is made of the information about its
inputs, outputs, states, parameters, and constants.

The definition for the component is specified by assigning dictionaries
to the class attributes `_inputs_info`, `_outputs_info`, `_states_info`,
`_parameters_info`, and `_constants_info`. In such a dictionary, the
keys correspond to the variable names, and the corresponding value
is another dictionary containing the metadata for the variable. The
metadata must at least feature the variable *units* in the
`SI system <https://en.wikipedia.org/wiki/International_System_of_Units>`_
and a brief *description* of the variable in plain english is encouraged.

See an example below:

.. code-block:: python

   {
       'variable_name': {
           'units': 'SI unit',
           'description': 'plain english'
       }
   }

Details on what each type of variable is, and their potential additional
metadata are provided in the sub-sections below.

.. rubric:: Inputs

The inputs correspond to the driving data required by the component.
They exclude those variables already included in the fixed interface,
i.e. inwards (see :ref:`Fig. 2<fig_transfers>`).

In addition to its *units* and *description*, input variables must be
given a *kind*. The inputs can be one of the three following kinds:

- `'dynamic'`: data required for each spatial element and for each time step,
- `'static'`: data required for each spatial element and constant over time,
- `'climatologic'`: data required for each spatial element and for a given
  frequency within a climatology year.

If no kind is specified, a dynamic kind is assumed.

If the input is of climatologic kind, *frequency* must also be given and it
can take one of the supported values described in :ref:`Tab. 1<tab_frequencies>`
below.

.. _tab_frequencies:
.. table:: Tab. 2: Supported frequencies for climatologic inputs

   ======================  ====================================================
   climatologic frequency  length of time dimension in data
   ======================  ====================================================
   ``'seasonal'``          Length of 4, corresponding to the meteorological
                           seasons (i.e. Winter [DJF], Spring [MAM],
                           Summer [JJA], Autumn [SON], in this order).

   ``'monthly'``           Length of 12, corresponding to the months in the
                           calendar year (i.e. from January to December).

   ``'day_of_year'``       Length of 366, corresponding to the days in the
                           calendar year (i.e. from January 1st to December
                           31st, including value for February 29th).

   `int`                   Length according to the integer value (e.g. a
                           value of 6 means 6 climatologic values for the
                           calendar year).
   ======================  ====================================================

The framework gives the inputs as keyword arguments to the component
`run` method. They are given as arrays of the same shape as the component
space domain.

.. rubric:: Outputs

The outputs correspond to the variables computed by the component that
you want the component users to be able to record. The outputs exclude
those variables already included in the fixed interface, i.e. outwards
(see :ref:`Fig. 2<fig_transfers>`). The component users will always be
able to record the component outwards and the component states they would
like, component outputs offer you the possibility to add more variables
to their list of recordable variables.

Any output returned must be a `numpy.ndarray` of the same shape as the
component space domain. The output name used in the returned dictionary
can differ from the Python variable pointing to the array.

.. rubric:: States

The states correspond to the component variables that need to be given
initial values to start the component time integration, and whose values
need to be sustained from one time step to the next.

In addition to its *units* and *description*, an optional *divisions*
metadata exists, where its expected value is an integer, a string, or
a sequence of integers and/or strings:

- by default its value is 1, indicating the state is a scalar;
- if its value is an integer greater than 1, it indicates that the state
  is a vector, and its value is the length of the vector;
- if its value is a string, the string must correspond to the name of a
  component constant, whose value will be used in place of the string
  as divisions;
- if its value is a sequence, it indicates that the state is an array,
  and its values are the lengths of the dimensions of the array (in the
  order in the sequence).

The *divisions* metadata can be used when considering e.g. different
vertical layers in a component. Note that scalar/vector/array refers to
the dimension of the state for a given element in the space domain, so
a scalar state does not mean that there is only one state value for the
whole spatial domain, it only means that there is only one state value
for each spatial element in the space domain.

The framework gives the states as keyword arguments to the component
`initialise`, `run`, and `finalise` methods. They are given as framework
`State` objects.

.. important::

   Each `State` object stores the different timesteps of a component
   state. To retrieve or assign values for a given timestep, the methods
   `get_timestep` and `set_timestep` must be used.

   .. list-table::

      * - .. automethod:: cm4twc._utils.state.State.get_timestep
      * - .. automethod:: cm4twc._utils.state.State.set_timestep

The retrieved state arrays are of the same size as the component space
domain plus (an) additional trailing axis (axes) if the given component
state features *divisions* (i.e. a scalar state will feature no additional
axis, a vector state will feature one additional axis of size equal to the
vector length, and an array state will feature as many additional axes
as the array dimension of sizes equal to the array dimension lengths and
in the same order).

.. rubric:: Parameters

The parameters are those variables subject to tuning. Note, parameter
tuning/calibration is not a functionality offered by the framework.

In addition to its *units* and *description*, a *valid_range* metadata
is recommended to be given and take a sequence of two numbers as
value to define the extent of the valid range of parameter values.
Providing such a range helps the users of your component to determine
its parameters values for their specific modelling context.

The framework gives the parameters as keyword arguments to the component
`initialise`, `run`, `finalise` methods. They are given as arrays of the
same shape as the component space domain.

.. rubric:: Constants

The constants are those variable not subject to tuning. Nevertheless,
they can be adjusted by the users, e.g. to adjust its precision, or to
adapt it to their modelling context.

In addition to its *units* and *description*, a *default_value* metadata
is mandatory for each constant. This is to provide a value for the user
if they are not interested in providing/adjusting it.

The framework gives the constants as keyword arguments to the component
`initialise`, `run`, and `finalise` methods. They are given as scalars.

.. rubric:: Extra spatial attributes

In addition, the component definition features three optional spatial
attributes `_requires_land_sea_mask`, `_requires_flow_direction` and
`_requires_cell_area`. They must be assigned a boolean value (True if
required by your component, False if not) -- their default value is
False. If they are required, the framework will ensure that the user
provides the information so that the component can run successfully.

If you need land sea mask information for your computations, set
`_requires_land_sea_mask` to True and access it in your class methods
using `self.spacedomain.land_sea_mask`. This will return an array of the
same size as the space domain (see e.g. `LatLonGrid.land_sea_mask` for
details).

If you need flow direction information or want to use the flow routing
functionality of the component (accessible through `self.spacedomain.route(...)`),
set `_requires_flow_direction` to True, and access it in your class methods
using `self.spacedomain.flow_direction`. This will return an array of the
same size as the space domain plus an additional trailing axis of size 2
for gridded space domains (see e.g. `LatLonGrid.flow_direction` for
details).

If you need the horizontal cell area of the space domain elements, set
`_requires_cell_area` to True and access it in your class methods using
`self.spacedomain.cell_area`. This will return an array of the same size
as the space domain (see e.g. `LatLonGrid.cell_area` for details).

.. rubric:: Example

See a detailed example of a mock component definition below.

.. code-block:: python
   :caption: Completing the component class definition in the class attributes.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       """component description here"""
       _inwards = {
           'inwards_1',
           'inwards_2',
           'inwards_3'
       }
       _outwards = {
           'outwards_1'
       }
       _inputs_info = {
           'input_1': {
               'kind': 'dynamic',
               'units': 'kg m-2 s-1',
               'description': 'brief input description here'
           },
           'input_2': {
               'kind': 'climatologic',
               'frequency': 'monthly',
               'units': 'kg m-2 s-1',
               'description': 'brief input description here'
           },
           'input_3': {
               'kind': 'static',
               'units': 'm',
               'description': 'brief input description here'
           }
       }
       _outputs_info = {
           'output_1': {
               'units': 'kg m-2 s-1',
               'description': 'brief output description here'
           },
           'output_2': {
               'units': 'kg m-3 s-1',
               'description': 'brief output description here'
           }
       }
       _states_info = {
           'state_1': {
               'units': 'kg m-2',
               'description': 'brief state description here'
           },
           'state_2': {
               'divisions': 4,
               'units': 'kg m-2',
               'description': 'brief state description here'
           }
       }
       _parameters_info = {
           'parameter_1': {
               'units': '1',
               'valid_range': [0, 1],
               'description': 'brief parameter description here'
           }
       }
       _constants_info = {
           'constant_1': {
               'units': '1',
               'default_value': 0.5,
               'description': 'brief constant description here'
           }
       }
       _requires_land_sea_mask = False
       _requires_flow_direction = True
       _requires_cell_area = False


Implement the initialise-run-finalise component class methods
-------------------------------------------------------------

The numerical calculations in your component contribution must be broken
down into the three phases initialise, run, and finalise. This means that
your Python class must feature three methods named `initialise`, `run`,
and `finalise`. Note, `initialize` and `finalize` spellings are not
supported.

Since the parameters of the three methods `initialise`, `run`, and
`finalise` are going to be passed as keyword arguments, the names of the
parameters in the signatures of these methods must necessarily be the ones
found in the component definition attributes (if renaming is required,
this can be done internally to the methods). In turn, this means that the
order of the method parameters in the method signatures does not matter.
Moreover, your method signatures must all feature a final special
method parameter `**kwargs` to collect all the remaining available
arguments given by the framework that the component is not using.

.. rubric:: Initialise

The `initialise` method must define the initial conditions for the
component states so that its integration can be started. However, the
component user may have already set initial component state values that
should not be overwritten. This is why state initial conditions must be
set only if the component property `initialised_states` evaluates as `False`.

This method can also feature any other action that is required to be
done only once before the start of the integration, i.e. pre-processing.
In such a situation, a special component attribute `shelf` exists. It is
a dictionary that can be used e.g. to store anything that needs computing
once in `initialise` and to be used repeatedly in `run`.

It is called at the beginning of a model simulation period.

The possible method parameters in the method signature are the component
inputs, states, parameters, and constants.

This method is not expected to return anything.

.. rubric:: Run

The `run` method contains the computations required to integrate from
one time step to the next.

It is called iteratively to move through the model simulation period.
Between each call, the component states are automatically incremented in
time by the framework.

The possible method parameters in the method signature are the component
inwards, inputs, states, parameters, and constants.

This method is expected to return a tuple of two dictionaries:

  - the first dictionary must contain the component outward transfers
    (keys are the outwards names, values are the outwards arrays),
  - the second dictionary must contain the component outputs
    (keys are the outputs names, values are the outputs arrays).

Note, the second dictionary may be empty if the component does not
feature any outputs in its definition.

.. rubric:: Finalise

The `finalise` method should contain any action required to guarantee
that the simulation completes "elegantly" and can be restarted after
the last simulation time step. It can also feature any other action
that is required to be done only once after the end of the integration
over the whole simulation period.

It is called once at the end of a model simulation period.

The possible method parameters in the method signature are the component
states, parameters, and constants.

This method is not expected to return anything.

.. rubric:: Example

See a detailed example of a mock component implementation below.

.. code-block:: python
   :caption: Implementing the three mandatory methods initialise, run, and finalise.

   import cm4twc


   class SurfaceLayerComponent(cm4twc.component.SurfaceLayerComponent):
       """component description here"""

       # component definition here

       def initialise(self, state_1, state_2, parameter_1, constant_1, **kwargs):
           if not self.initialised_states:
               # set here initial condition values for component states
               state_1.set_timestep(-1, 0.)
               state_2.set_timestep(-1, 0.)

       def run(self, inwards_1, inwards_2, inwards_3, input_1, input_2, input_3,
               state_1, state_2, parameter_1, constant_1, **kwargs):

           # compute science using available inwards/inputs/parameters/constants
           routed, outed = self.spacedomain.route(inwards_1 + inwards_2 + inwards_3)

           outwards_1 = (routed + input_1 + state_1.get_timestep(-1)
                         / self.timedelta_in_seconds) * parameter_1

           m = self.current_datetime.month

           output_1 = input_2[m - 1, ...] * constant_1

           output_2 = input_2[m - 1, ...] * (1 - constant_1)
           for i in range(4):
               output_2 += (0.05 * state_2.get_timestep(-1)[..., i]
                            / self.timedelta_in_seconds)
           output_2 /= input_3

           # update component state
           state_1.set_timestep(
               0,
               state_1.get_timestep(-1)
               * (1 - self.timedelta_in_seconds * parameter_1)
           )
           state_2.set_timestep(
               0,
               0.95 * state_2.get_timestep(-1)
           )

           # return outwards and outputs
           return (
               {'outwards_1': outwards_1},
               {'output_1': output_1,
                'output_2': output_2}
           )

       def finalise(self, state_1, state_2, parameter_1, constant_1, **kwargs):
           # cleanly wrap up simulation here
           # to be able to restart from where simulation stopped
           pass

Real component implementations are available in the
:doc:`science library <../science_library>` section.

This concludes the preparation of your component contribution, the next
step is to :doc:`package <packaging>` your component(s).
