How to release a new version for `cm4twc`
=========================================

Between releases, changes are made on the *dev* branch.

Once the 'dev' branch has reached a staged where a new release is
justified or required, the following steps must be followed.

.. warning::

   Always replace #.#.# with the actual version number in the steps below.

1. create and checkout a 'release-v#.#.#' branch from the 'dev' branch:

.. code-block:: bash

   git checkout -b release-v#.#.# dev

2. update the version in *cm4twc/version.py*:

.. code-block:: python

   __version__ = '#.#.#'

3. make sure that the *changelog.rst* contains all the noteworthy
   changes since the last release, change 'latest' to 'v#.#.#' and add
   "Released on YYYY-MM-DD." (replace with release date):

   .. code-block:: rst

      v#.#.#
      ------

      Released on YYYY-MM-DD.

4. build the documentation for this version:

   a. set the environment variable `VERSION_RELEASE` to '#.#.#':

      .. code-block:: bash

         export VERSION_RELEASE='#.#.#'

   b. make sure all dependencies in *requirements-docs.txt* are satisfied

   c. use the makefile to build the documentation with sphinx locally:

      .. code-block:: bash

         cd ./docs && make local_html

   d. browse the documentation generated in *docs/_doc_build/html* to
      check that everything is in order

   e. if the documentation built is in order, build the documentation
      with sphinx again to create the files where GitHub Pages will
      look for them:

      .. code-block:: bash

         cd ./docs && make github_html

5. commit these changes to the release branch and push to remote, e.g. 'origin':

   .. code-block:: bash

      git commit -am "prepare docs for release"
      git push -u origin release-v#.#.#

6. create a draft pull request on GitHub to merge the release branch
   in 'main' branch

7. in the pull request, click "Ready for review" to trigger a testing
   workflow for GitHub Actions

8. if tests have failed, fix accordingly, and re-run the GitHub Actions workflow

9. once tests have passed, merge pull request into 'main' branch

10. draft a release on GitHub using 'v#.#.#' for both the tag version
    and the release title, and use 'v#.#.# release' for the release
    description and click "Publish release"
