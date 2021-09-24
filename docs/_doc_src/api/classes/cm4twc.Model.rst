.. currentmodule:: cm4twc
.. default-role:: obj

Model
=====

.. autoclass:: Model


Methods
-------

Construction
~~~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~cm4twc.Model.from_yaml
   ~cm4twc.Model.to_yaml

Initialisation
~~~~~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~cm4twc.Model.initialise_transfers_from_dump

Simulation
~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~cm4twc.Model.spin_up
   ~cm4twc.Model.simulate
   ~cm4twc.Model.resume


Attributes
----------

.. autosummary::
   :nosignatures:
   :toctree: ../attributes/
   :template: attribute.rst

   ~cm4twc.Model.identifier
   ~cm4twc.Model.config_directory
   ~cm4twc.Model.saving_directory
   ~cm4twc.Model.surfacelayer
   ~cm4twc.Model.subsurface
   ~cm4twc.Model.openwater
