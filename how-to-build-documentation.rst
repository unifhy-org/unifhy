How to build the documentation for `cm4twc`
===========================================

Using GitHub Actions workflow and GitHub CLI
--------------------------------------------

Once the GitHub Command-Line Interface (CLI) is installed (using e.g.
`conda install gh --channel conda-forge`) and configured, the following
command can be used to build the documentation automatically:

.. code-block:: bash

   gh workflow run build-docs.yml --ref dev

This will build the documentation based on the latest commit on the
'dev' branch and, as part of the workflow, will directly commit any
documentation changes to the 'dev' branch.
