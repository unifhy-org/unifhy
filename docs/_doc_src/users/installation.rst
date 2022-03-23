.. currentmodule:: unifhy
.. default-role:: obj

Installation
============

Installing the framework
------------------------

Official releases
~~~~~~~~~~~~~~~~~

If you wish to install the most recent **stable** version of `unifhy`, it is
available from the *conda-forge* channel, so you can use `conda` (recommended
way):

.. code-block:: bash
   :caption: Installing stable version using `conda`.

   conda install -c conda-forge unifhy

It is also available from the Python Package Index (PyPI), so you can also
use `pip`:

.. code-block:: bash
   :caption: Installing stable version using `pip`.

   pip install unifhy

.. warning::

   Some of the package dependencies cannot be installed using `pip`
   (e.g. `esmpy`). These needs to be installed prior the installation of
   this package using `pip`. Please refer to the online documentation of
   these packages to follow the recommended way of installing them. The
   full list of package dependencies can be found in the ``requirements.txt``
   file of the given release.


Latest developments
~~~~~~~~~~~~~~~~~~~

If you need the **latest**, potentially unstable, features listed in the
:doc:`change log <../changelog>`, please install from the *dev* branch on the
GitHub repository:

.. code-block:: bash
   :caption: Installing latest features using `pip`.

   pip install git+https://github.com/unifhy-org/unifhy.git@dev


Testing the framework
---------------------

To check whether the framework has been installed properly, you can run
tests. These tests are to be run from the ``tests`` directory:

.. code-block:: bash
   :caption: Running the basic test suite.

   python run_basic_tests.py


Installing framework components
-------------------------------

The framework components listed in the :doc:`science library <../science_library>`
are independent of the framework: they come as Python packages
of their own. Consequently, they need to be installed separately.
The distribution of these components is left at the discretion of the component
contributors. Please refer to their documentation and/or their codebase
to follow the recommended way of installing them.
