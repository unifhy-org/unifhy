.. currentmodule:: cm4twc
.. default-role:: obj

Sharing
=======

This section details the procedure to follow to share successfully
:doc:`developed <development>` and :doc:`packaged <packaging>`
component contribution(s) with the `cm4twc` community.

A GitHub organisation for `cm4twc` has been created to gather all repositories
relevant to the community of users of the framework, hence it is encouraged
to :ref:`push your contribution(s) to repositories under this GitHub
organisation <push_github_org>`. In addition, it is recommended that you
:ref:`upload your contribution to PyPI <upload_pypi>`.

However, you can host your source code under a different GitHub
organisation/user, or you can host it elsewhere, e.g. on GitLab or BitBucket.
If this is the case, we still recommend that you :ref:`upload your
contribution(s) to PyPI <upload_pypi>` as a way to allow users of the
`cm4twc` community to find it (them) easily.

.. _push_github_org:

Push your contribution to the cm4twc GitHub organisation
--------------------------------------------------------

If you would like to get a remote git repository hosted under the
`cm4twc GiHub organisation <https://github.com/cm4twc-org>`_ to
share your component contribution(s), please get in touch via email
(hydrojules(at)ceh.ac.uk) so that we can create a repository for you and
give you full admin rights on it.

Once the repository has been created for you, add it as a *community*
git remote, and push your commits to this remote repository:

.. code-block:: bash

   git remote add community https://github.com/cm4twc-org/cm4twccontrib-<model_name>.git
   git push -u community main

.. _upload_pypi:

Upload your contribution to the Python Package Index
----------------------------------------------------

If you would like to share your component contribution(s) on the
`Python Package Index (PyPI) <https://pypi.org/>`_, you need to
install a few Python packages:

.. code-block:: bash

   python -m pip install setuptools wheel twine

Then, you need to generate distribution archives, to do so, go to your
repository root (i.e. where *setup.py* is) and run:

.. code-block:: bash

   python setup.py sdist bdist_wheel

Finally, upload the distribution archives to PyPI:

.. code-block:: bash

   python -m twine upload dist/*

.. hint::

   You will need to create an account on PyPI before being able to
   upload your distribution archives, more details can be found on
   the `official Python website
   <https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives>`_.

   As advised on their website, we recommend that you upload your contribution
   to https://test.pypi.org before uploading it to https://pypi.org to make
   sure everything is in order.
