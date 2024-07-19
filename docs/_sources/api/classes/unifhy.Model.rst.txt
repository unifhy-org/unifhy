.. currentmodule:: unifhy
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

   ~unifhy.Model.from_yaml
   ~unifhy.Model.to_yaml

Initialisation
~~~~~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.Model.initialise_transfers_from_dump

Simulation
~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.Model.spin_up
   ~unifhy.Model.simulate
   ~unifhy.Model.resume


Attributes
----------

.. autosummary::
   :nosignatures:
   :toctree: ../attributes/
   :template: attribute.rst

   ~unifhy.Model.identifier
   ~unifhy.Model.config_directory
   ~unifhy.Model.saving_directory
   ~unifhy.Model.surfacelayer
   ~unifhy.Model.subsurface
   ~unifhy.Model.openwater
   ~unifhy.Model.nutrientsurfacelayer
   ~unifhy.Model.nutrientsubsurface
   ~unifhy.Model.nutrientopenwater
