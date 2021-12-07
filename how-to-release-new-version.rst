How to release a new version for `unifhy`
=========================================

Between releases, changes are made on the 'dev' branch and recorded in
the `<changelog.rst>`_ in the *latest* section. This follows the
`successful Git branching model by Vincent Driessen
<https://nvie.com/posts/a-successful-git-branching-model/>`_.

Once the 'dev' branch has reached a stage where a new release is
justified or required, the following steps must be followed.

.. warning::

   Always replace #.#.# with the actual version number in the steps below.
   Version numbers must follow `Semantic Versioning <https://semver.org/>`_
   guidelines.

1. create and checkout a 'release-v#.#.#' branch from the 'dev' branch:

   .. code-block:: bash

      git checkout -b release-v#.#.# dev

2. update the version in `<unifhy/version.py>`_:

   .. code-block:: python

      __version__ = '#.#.#'

3. make sure that the `<changelog.rst>`_ file contains all the noteworthy
   changes since the last release, change 'latest' to 'v#.#.#' and add
   "Released on YYYY-MM-DD." (replace with release date) below the version
   number:

   .. code-block:: rst

      v#.#.#
      ------

      Released on YYYY-MM-DD.

4. commit these changes to the release branch and push to remote, e.g. 'origin':

   .. code-block:: bash

      git commit -am "update version for release"
      git push -u origin release-v#.#.#

5. build the documentation for this version by running Actions workflow
   using GitHub CLI (see `<how-to-build-documentation.rst>`_ for details):

   .. code-block:: bash

      gh workflow run build_docs.yml --ref release-v#.#.# -f branch=release-v#.#.# -f release=#.#.#

6. create a draft pull request on GitHub to merge the release branch
   in 'main' branch

7. in the pull request, click "Ready for review" to trigger the advanced
   testing workflow in GitHub Actions

8. if tests have failed, fix accordingly, and re-run the GitHub Actions workflow

9. once tests have passed, merge pull request into 'main' branch by
   choosing the option "Create a merge commit"

10. draft a release on GitHub using 'v#.#.#' for both the tag version
    and the release title, and use 'v#.#.# release' for the release
    description and click "Publish release"

11. merge 'main' branch into 'dev' branch to update live documentation
    living on 'dev' branch:

    .. code-block:: bash

       git fetch origin main
       git merge origin/main
       git checkout dev
       git merge main
       git fetch origin dev
       git push origin dev
