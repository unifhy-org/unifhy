.. currentmodule:: unifhy
.. default-role:: obj

Packaging
=========

This section details the steps required to turn your component
contribution(s) into a Python package.

You can follow the steps below to package your component contribution(s):

.. contents::
   :backlinks: none
   :local:


Create a local git repository
-----------------------------

First, choose a name for the model your component(s) originate(s) from,
following `PEP 8 naming convention <https://www.python.org/dev/peps/pep-0008/#package-and-module-names>`_,
i.e. all-lowercase names with underscores if this improves readability only.

Then, create a new directory using your model name and appending the
prefix *unifhycontrib-* to it:

.. code-block:: bash

   mkdir unifhycontrib-<model_name>

where *<model_name>* should be replaced with your chosen model name.

Retrieve the component package template
---------------------------------------

Download the `template source <https://github.com/unifhy-org/unifhycontrib-template>`_
and copy the unzipped source in the newly created directory.

.. code-block:: bash

   wget https://github.com/unifhy-org/unifhycontrib-template/archive/main.zip
   unzip unifhycontrib-template-main.zip
   mv unifhycontrib-template-main/* unifhycontrib-<model_name>
   cd unifhycontrib-<model_name>

.. note::

   You can also download the template source manually: go to
   https://github.com/unifhy-org/unifhycontrib-template, click 'Code',
   then 'Download ZIP'.

The template source directory is structured as follows:

.. code-block:: text

   unifhycontrib-template
   ├── unifhycontrib
   │   └── template
   │       ├── __init__.py
   │       ├── surfacelayer.py
   │       ├── subsurface.py
   │       ├── openwater.py
   │       └── version.py
   ├── README.rst
   ├── requirements.txt
   └── setup.py

Rename the existing Python package using your model name:

.. code-block:: bash

   mv unifhycontrib/template unifhycontrib/<model_name>

Add and commit those files to the repository:

.. code-block:: bash

   git commit -am "start with template"

Bring in your component contribution(s)
---------------------------------------

The template features three trivial components `SurfaceLayerComponent`,
`SubSurfaceComponent`, and `OpenWaterComponent`.

Depending on the number of components your contribution overlaps with,
keep only the relevant ones and delete the other ones.

For example, if your contribution simulates the surface layer and the
subsurface parts of the terrestrial water cycle:

- delete the module *openwater.py*, and
- remove `from .openwater import OpenWaterComponent` in *__init__.py*.

Then, bring in your own components:

- replace the trivial template components `SurfaceLayerComponent` and
  `SubSurfaceComponent`, in the modules *surfacelayer.py* and
  *subsurface.py*, respectively, with your own classes developed as
  per the :doc:`development` section.

.. note::

   If your component(s) require(s) Python packages that are not available
   in the `Python Standard Library <https://docs.python.org/3/library/index.html>`_,
   you need to list these in *requirements.txt* (one package per line only),
   e.g.:

   .. code-block:: text

      unifhy
      numpy
      pandas

Specify the version number for your component contribution(s) in the
module *version.py* following the `Semantic Versioning <https://semver.org/>`_
guidelines.

Finally, overwrite the content of *README.rst* to provide a description
for your model components.

Once this is done, commit your component contribution(s) to the git repository:

.. code-block:: bash

   git commit -am "bring in my own components"

Populate the package metadata
-----------------------------

Modify the first section in the `setup.py
<https://github.com/unifhy-org/unifhycontrib-template/blob/main/setup.py#L4-L20>`_
module with the relevant metadata for your package. This will be used when
your package is uploaded to the `Python Package Index (PyPI) <https://pypi.org/>`_.

Now that your component(s) has (have) been turned into a Python package,
please consider :doc:`sharing <sharing>` it (them) with the `unifhy` community.
