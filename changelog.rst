.. default-role:: obj

latest
------

Yet to be versioned and released. Only available from *dev* branch until then.

.. rubric:: API changes

* add units requirement for component parameters and constants
  (`#21 <https://github.com/cm4twc-org/cm4twc/issues/21>`_)
* move `Component` and its subclasses from subpackage `components` to package root
  (`#46 <https://github.com/cm4twc-org/cm4twc/pull/46>`_)
* rename component class attributes `_flow_direction` and `_land_sea_mask` in
  component definition to `_requires_flow_direction` and `_requires_land_sea_mask`,
  respectively
  (`#46 <https://github.com/cm4twc-org/cm4twc/pull/46>`_)
* remove science components (Artemis and RFM) from framework
  (`#45 <https://github.com/cm4twc-org/cm4twc/issues/45>`_)

.. rubric:: Bug fixes

* fix dump file update bug due to missing 'divisions' dimension
  (`#32 <https://github.com/cm4twc-org/cm4twc/issues/32>`_)
* fix model identifier renaming not propagating to its components' identifiers
  (`#48 <https://github.com/cm4twc-org/cm4twc/issues/48>`_)

.. rubric:: Enhancements

* add support for arrays for component parameters
  (`#21 <https://github.com/cm4twc-org/cm4twc/issues/21>`_)
* add support for multiple divisions for component states
  (`#39 <https://github.com/cm4twc-org/cm4twc/pull/39>`_)
* add support for customisable divisions for component states
  (`#31 <https://github.com/cm4twc-org/cm4twc/issues/31>`_)
* add time slice for I/O operations (user customisable)
  (`#42 <https://github.com/cm4twc-org/cm4twc/pull/42>`_)
* cache remapping weights at initialisation
  (`#44 <https://github.com/cm4twc-org/cm4twc/pull/44>`_)

.. rubric:: Documentation

* document 'divisions' for component states in preparation page
  (`#35 <https://github.com/cm4twc-org/cm4twc/issues/35>`_)
* move API reference page to doc tree root
* move science repository page to doc tree root
* add support page
* add change log page
* add logo for package

v0.1.0-beta
-----------

Released on 2021-02-10.

* first release
