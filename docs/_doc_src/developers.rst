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
