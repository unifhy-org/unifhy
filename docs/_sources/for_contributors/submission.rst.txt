.. currentmodule:: cm4twc
.. default-role:: obj

Submission
==========

This section details the procedure to follow to submit a prepared
contribution for inclusion in the science repository of the framework.

The `cm4twc` package is hosted on `GitHub <https://github.com/>`_ and
the version control system `git <https://git-scm.com/>`_ is used. Hence,
to submit your contribution, you will need a GitHub account (free
registration available) as well as some basic knowledge of git usage.

You can then follow the steps below to share your component contribution:

.. contents::
   :backlinks: none
   :local:


Get your own copy of the framework repository
---------------------------------------------

First, you need to get your own copy of the repository on your GitHub
account. To do so, simply go to https://github.com/hydro-jules/cm4twc
and click "Fork" in the upper right hand corner of the page. You now
have your own online copy of the repository, hosted on GitHub under
your account.

Then, you need to get a local copy of your online copy in order to
include your contribution(s) to the framework. To do so, you need to use
the git clone command. On your local machine, run the following command
in your terminal to get a copy of the repository in your current working
directory in a folder name `cm4twc`:

.. code-block:: bash

   git clone https://github.com/<username>/cm4twc.git

where `<username>` needs to be replaced with your GitHub username.


Create a branch on your copy
----------------------------

Like the `cm4twc` repository, your local copy of it comes with two
branches 'master' and 'dev'. It is recommended that you create a new
branch to work on each time you work on a new component. To do so,
navigate to the root of your local copy using the following command:

.. code-block:: bash

   cd cm4twc

The 'master' branch contains stable releases of the framework, so we
recommend you branch from the 'master' branch rather than the 'dev' branch.
To do so, run the following commands:

.. code-block:: bash

   git checkout -b <new_branch> master

where `<new_branch>` needs to be replaced with the name you want to give
to your branch.


Commit your component to your branch in your local copy
-------------------------------------------------------

The Python script containing your component implementation needs to be
added to the repository in 'cm4twc/components/surfacelayer',
'cm4twc/components/subsurface', or 'cm4twc/components/openwater'
depending on the part of the terrestrial water cycle it covers.

For example, for a surface layer component named 'My Contribution',
create a Python script named 'my_contribution.py' (please use a snake
case naming style for the file name, for acronyms use all lowercase) in
'cm4twc/components/surfacelayer' and implement your class named
`MyContribution` (please use a camel case naming style for the class
name, for acronyms use all uppercase) in this Python script (see section
:doc:`preparation` for more details on how to implement it).

TODO: Add to __init__.py or to components.yml?

Then, stage and commit your changes to your branch in your local copy, see e.g.
https://github.com/git-guides/git-commit for details on `git commit`
commands. In its simplest form, you could use the following commands:

.. code-block:: bash

   git add --all
   git commit -m "add new surface layer component MyContribution"


Push your changes to your remote copy
-------------------------------------

Once you have included your component to your local copy, you need to
propagate your changes to your remote copy (i.e. the one hosted on GitHub).
To do so, simply use the command:

.. code-block:: bash

   git push origin <new_branch>

Note, 'origin' is the default alias used by git to refer to the server you
cloned from.


Open a pull request to merge your component in the framework
------------------------------------------------------------

This last step happens online on GitHub, you need to go to
https://github.com/<username>/cm4twc/tree/<new_branch> (where `<username>`
and `<new_branch>` need to be replaced appropriately) and click "Pull Request"
to merge your changes into the base repository 'hydro-jules/cm4twc'
under the base branch 'dev', and not the branch 'master' (see GitHub help
section  `Creating a pull request <https://docs.github.com/en/
free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/
creating-a-pull-request>`_ for more details).
