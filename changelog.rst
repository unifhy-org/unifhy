.. default-role:: obj

..
   latest
   ------

   Yet to be versioned and released. Only available from *dev* branch until then.

v0.1.1
------

Released on 2022-04-16.

.. rubric:: Bug fixes

* fix intermittent data filenames loss in YAML configuration file
  (`#80 <https://github.com/unifhy-org/unifhy/issues/80>`_)
* fix relative import bug for advanced test suite
  (`#82 <https://github.com/unifhy-org/unifhy/issues/82>`_)
* prevent unwanted installation of `tests` package alongside `unifhy`
  (`#83 <https://github.com/unifhy-org/unifhy/issues/83>`_)

.. rubric:: Documentation

* add data to run tutorial and revise tutorial accordingly
  (`#81 <https://github.com/unifhy-org/unifhy/pull/81>`_)
* revise installation instructions to recommend `conda` over `pip`
  because of `esmpy` dependency not available on PyPI
  (`#81 <https://github.com/unifhy-org/unifhy/pull/81>`_)

v0.1.0
------

Released on 2021-12-07.

.. rubric:: Functional changes

* constrain temporal and spatial resolutions of components forming a
  model to be integer multiples of one another
  (`#67 <https://github.com/unifhy-org/unifhy/pull/67>`_)
* enforce two-dimensional spatial domains for components
  (`#69 <https://github.com/unifhy-org/unifhy/pull/69>`_)
* allow components to use/produce only parts of the standardised transfers
  through the framework interfaces
  (`#76 <https://github.com/unifhy-org/unifhy/pull/76>`_)

.. rubric:: API changes

* add units requirement for component parameters and constants
  (`#21 <https://github.com/unifhy-org/unifhy/issues/21>`_)
* move `Component` and its subclasses from subpackage `components` to package root
  (`#46 <https://github.com/unifhy-org/unifhy/pull/46>`_)
* rename component class attributes `_flow_direction` and `_land_sea_mask` in
  component definition to `_requires_flow_direction` and `_requires_land_sea_mask`,
  respectively
  (`#46 <https://github.com/unifhy-org/unifhy/pull/46>`_)
* remove science components (Artemis and RFM) from framework
  (`#45 <https://github.com/unifhy-org/unifhy/issues/45>`_)
* remove vertical dimension (i.e. altitude) in `LatLonGrid`,
  `RotatedLatLonGrid`, and `BritishNationalGrid`
  (`#69 <https://github.com/unifhy-org/unifhy/pull/69>`_)
* replace `State` dunder methods `__getitem__` and `__setitem__` with
  `get_timestep` and `set_timestep` methods
  (`#71 <https://github.com/unifhy-org/unifhy/pull/71>`_)
* include component inputs as arguments given to `initialise` method
  (`#75 <https://github.com/unifhy-org/unifhy/pull/75>`_)
* revise/refine component inward and outward transfers
  (`#76 <https://github.com/unifhy-org/unifhy/pull/76>`_)

.. rubric:: Bug fixes

* fix dump file update bug due to missing 'divisions' dimension
  (`#32 <https://github.com/unifhy-org/unifhy/issues/32>`_)
* fix model identifier renaming not propagating to its components' identifiers
  (`#48 <https://github.com/unifhy-org/unifhy/issues/48>`_)
* fix impossibility to run `Model` using a `Component` on the `BritishNationalGrid`
  (`#51 <https://github.com/unifhy-org/unifhy/issues/51>`_)
* fix failed aggregation of fields with no standard name in `DataSet`
  (`#52 <https://github.com/unifhy-org/unifhy/issues/52>`_)
* apply `land_sea_mask` to underlying field of `Grid` to be used in remapping
  (`#59 <https://github.com/unifhy-org/unifhy/issues/59>`_)

.. rubric:: Enhancements

* add support for arrays for component parameters
  (`#21 <https://github.com/unifhy-org/unifhy/issues/21>`_)
* add support for multiple divisions for component states
  (`#39 <https://github.com/unifhy-org/unifhy/pull/39>`_)
* add support for customisable divisions for component states
  (`#31 <https://github.com/unifhy-org/unifhy/issues/31>`_)
* add time slice for I/O operations (user customisable)
  (`#42 <https://github.com/unifhy-org/unifhy/pull/42>`_)
* cache remapping weights at initialisation
  (`#44 <https://github.com/unifhy-org/unifhy/pull/44>`_)
* add `cell_area` property to `SpaceDomain` that can be provided by the
  user or else automatically computed for `Grid`
  (`#61 <https://github.com/unifhy-org/unifhy/issues/61>`_)
* add `initialised_states` property to `Component` to allow component
  contributors not to overwrite user-defined initial conditions
  (`#75 <https://github.com/unifhy-org/unifhy/pull/75>`_)
* add `shelf` attribute to `Component` to allow the communication of
  data between component methods
  (`#75 <https://github.com/unifhy-org/unifhy/pull/75>`_)
* add `_inwards` and `_outwards` component class attributes to allow
  contributors to declare what interface transfers their component
  use and produce, respectively
  (`#76 <https://github.com/unifhy-org/unifhy/pull/76>`_)

.. rubric:: Dependencies

* change dependency ``cf-python>=3.11.0``
* drop support for Python 3.6

.. rubric:: Documentation

* document 'divisions' for component states in preparation page
  (`#35 <https://github.com/unifhy-org/unifhy/issues/35>`_)
* move API reference page to doc tree root
* move science library page to doc tree root
* add support page
* add change log page
* add logo for package

v0.1.0-beta
-----------

Released on 2021-02-10.

* first release
