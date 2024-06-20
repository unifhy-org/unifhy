.. currentmodule:: unifhy
.. default-role:: obj

Developer Guide
===============

This guide is for people interested in extending the technical
capabilities of the framework.

.. warning::

   Work in progress...

.. toctree::
   :maxdepth: 4

   developers/transfers
   developers/components

Development Guidance
--------------------
The UnifHy repository is at https://github.com/unifhy-org/unifhy. The recommended approach if you wish to make your changes available to all users of UnifHy is to create a branch/fork of the repository, make the changes and create a Pull Request (PR) once done. Creating the Pull Request triggers the unit tests to run, but these can also be triggered manually by changing the status of the PR to draft and back again. 

To run/test UnifHy from your local copy in which you have made changes, you can install it into your active python environment by pointing pip at the repository containing the code: `pip install /path/to/unifhy/repo`. If further changes are made to the code in /path/to/unifhy/repo then you may need to uninstall (`pip uninstall unifhy`) and reinstall for them to be picked up in your envrionment. 

Adding new Components 
---------------------

.. note::
   By adding a new Component to the *framework* you are creating the space for others to put in the science that represents a new part of the Earth-System that UnifHy has heretofore not accounted for and has had to be input to components via in*puts* i.e. data files instead of dynamically modelled variables. 
   

Adding new Components to the framework is a more complicated business. 
The broad strokes are:

1. Decide which area of the Earth-System the Component will represent and what transfers it will need from other Components and provide to other Components
2. Add the Component to unifhy/component.py, subclassing the Component class and following the structure and syntax of the existing Components, and the inwards and outwards transfers to _inwards_info and _outwards_info respectively
3. Add the new transfers provided by the new Component, described by the new Component's `_outwards_info`, to the relevant other Components' `_inward_info`s
4. Adapt unifhy.Model to accept the extra Component(s)
5. Update the unit tests to handle the extra Component(s). This involves creating dummy Component version(s) of the new dummy Component(s) and calculating the values of all the transfers and records for various configurations of the model when all the dummy Components are run together. There is a tool for calculating the values here. 

More detail for the steps:

2. Adding Components to component.py
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :caption: Components have the following structure, and should be added before the `DataComponent` class

   class ComponentNameHere(Component, metaclass=abc.ABCMeta):
       """ Component description here
       """
   
       _category = "componentnamehere"
       _inwards_info = { # transfers accepted by this component
           "transfer_a": {
               "units": "1", # units of transfer
               "from": "_category of component the transfer is coming from",
               "method": "mean",
           },
           "transfer_b": {
               "units": "1",
               "from": "_category of component the transfer is coming from",
               "method": "mean",
            },
            ...
       }
       _outwards_info = { # transfers produced by this component
           "transfer_c": {
               "units": "kg m-2 s-1",
               "to": ["_category of component the transfer can be going to",
                      "_category of another component the transfer can be going to"],
               "method": "mean",
           },
           "transfer_d": {
               "units": "kg m-2 s-1",
               "to": ["_category of component the transfer can be going to"],
               "method": "mean",
           },
           ...
       }
   
       # if not specified, assume all inwards are required
       _inwards = tuple(_inwards_info)
       # if not specified, assume all outwards are produced
       _outwards = tuple(_outwards_info)

The main things to specify are:

- The name of the class
- The informal name of the class defined by the `_category` variable and used to determine where to send transfers and where they have come from
- A description of what the Component is intended to simulate in the class docstring
- The `_inwards_info` and `_outwards_info` dictionaries that describe the transfers that this Component can receive and produce respectively. 

Anything else does not need to be touched.

3. Adding the transfers
^^^^^^^^^^^^^^^^^^^^^^^
The transfers into and out of the component are specified in the `_inwards_info` and `_outwards_info` dictionaries. The structure of these is explained in the previous section <LINK>

4. Adapting unifhy.Model
^^^^^^^^^^^^^^^^^^^^^^^^
This step is more involved. Whilst the changes that need to be made are simple, there are a lot of them. The majority of the changes to be made are in the unifhy/model.py file, and they are `listed here <https://github.com/unifhy-org/unifhy/issues/14#issuecomment-2163572649>`_

5. Adapting the unit tests
^^^^^^^^^^^^^^^^^^^^^^^^^^
The changes made in Step 4 mean that the unit tests that check UnifHy works correctly themselves no longer work correctly and will fail. In order for any further minor changes that are made to UnifHy to be tested correctly, these tests also need to be updated to account for the new Component(s). A comprehensive list of the changes that need to be made `is here <https://github.com/unifhy-org/unifhy/issues/93#issuecomment-2167823946>`_
The tests for a large part rely on 'dummy' Components that mimick actual science Components developed for UnifHy, containing dummy calculations with dummy input data and dummy transfers. The transfers loosely mimick those of the official UnifHy interface (:ref:`Fig. 1<fig_transfers>`). The biggest bit of work in this step is thus to create the dummy component, dummy input data, and calculate the values of the transfers for the tests to be validated against. Some tools have been developed to help with this process:

- `Transfers and outputs calculator <https://github.com/unifhy-org/unifhy/blob/nutrients/tests/tests/test_utils/dummy_output_calculator.py>`_ that calculates the transfers and outputs of the dummy components for the various configurations that are tested by the unit tests, for validation of these tests. Instructions are in the 'dummy_output_calculator.py' linked above. The starting point is to replicate the new dummy component in `dummy_nutrient_components_for_testing.py <https://github.com/unifhy-org/unifhy/blob/nutrients/tests/tests/test_utils/dummy_components_for_testing.py>`_.
- `Data generators <https://github.com/hydro-jules/data-generators>`_ to produce the netcdf files needed as inputs, substitute data and ancillaries

.. note::
   It is likely going forward that this level of testing will become unwieldy and unnecessary as UnifHy grows in complexity. Therefore it might instead be more worthwhile spending time adapting the tests so that not every Component and transfer and configuration of possible Models needs to be tested. After all, it is the core functionality of UnifHy that is being tested and this doesn't change regardless of how many components are added. 

