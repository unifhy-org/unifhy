.. currentmodule:: unifhy
.. default-role:: obj

TimeDomain
==========

.. autoclass:: TimeDomain


Methods
-------

Construction
~~~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.TimeDomain.from_datetime_sequence
   ~unifhy.TimeDomain.from_start_end_step
   ~unifhy.TimeDomain.from_field

Comparison
~~~~~~~~~~

.. autosummary::
   :nosignatures:
   :toctree: ../methods/
   :template: method.rst

   ~unifhy.TimeDomain.is_time_equal_to
   ~unifhy.TimeDomain.spans_same_period_as


Attributes
----------

.. autosummary::
   :nosignatures:
   :toctree: ../attributes/
   :template: attribute.rst

   ~unifhy.TimeDomain.time
   ~unifhy.TimeDomain.bounds
   ~unifhy.TimeDomain.units
   ~unifhy.TimeDomain.calendar
   ~unifhy.TimeDomain.period
   ~unifhy.TimeDomain.timedelta
