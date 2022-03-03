************
Contributing
************

Coordinate First
================

Before you create a pull request, please `create a new issue`_ first to coordinate.

It might be that we are already working on the same or similar feature, but we 
haven't made our work visible yet.

.. _create a new issue: https://github.com/aas-core-works/aas-core-codegen/issues/new

Create a Development Environment
================================

We usually develop in a `virtual environment`_.
To create one, change to the root directory of the repository and invoke:

.. code-block::

    python -m venv venv


You need to activate it. On *nix (Linux, Mac, *etc.*):

.. code-block::

    source venv/bin/activate

and on Windows:

.. code-block::

    venv\Scripts\activate

.. _virtual environment: https://docs.python.org/3/tutorial/venv.html

Install Development Dependencies
================================

Once you activated the virtual environment, you can install the development 
dependencies using ``pip``:

.. code-block::

    pip3 install --editable .[dev]

The `--editable <pip-editable_>`_ option is necessary so that all the changes
made to the repository are automatically reflected in the virtual environment 
(see also `this StackOverflow question <pip-editable-stackoverflow_>`_).

.. _pip-editable: https://pip.pypa.io/en/stable/reference/pip_install/#install-editable
.. _pip-editable-stackoverflow: https://stackoverflow.com/questions/35064426/when-would-the-e-editable-option-be-useful-with-pip-install

Pre-commit Checks
=================

We provide a battery of pre-commit checks to make the code uniform and consistent across the code base.

We use `black`_ to format the code and use the default maximum line length of 88 characters.

.. _black: https://pypi.org/project/black/

The docstrings need to conform to `PEP 257`_.
We use `Sphinx docstring format`_ to mark special fields (such as function arguments, return values *etc.*).
Please annotate your function with type annotations instead of writing the types in the docstring.

.. _PEP 257: https://www.python.org/dev/peps/pep-0257/
.. _Sphinx docstring format: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html

To run all pre-commit checks, run from the root directory:

.. code-block::

    python continuous_integration/precommit.py

You can automatically re-format the code and fix certain files automatically with:

.. code-block::

    python continuous_integration/precommit.py --overwrite

The pre-commit script also runs as part of our continuous integration pipeline.

Write Commit Message
====================

We follow Chris Beams' `guidelines on commit messages`_:

1) Separate subject from body with a blank line
2) Limit the subject line to 50 characters
3) Capitalize the subject line
4) Do not end the subject line with a period
5) Use the imperative mood in the subject line
6) Wrap the body at 72 characters
7) Use the body to explain *what* and *why* vs. *how*

.. _guidelines on commit messages: https://chris.beams.io/posts/git-commit/

Development Scripts
===================
We need to frequently back-propagate test data from `aas-core-meta`_ repository.
To facilitate fetching and re-recording test output whenever the meta-models change, we wrote a couple of scripts in `dev_scripts/`_.

The scripts are hopefully self-explaining.
Please let us know if you need more information so that we can improve this documentation accordingly.

.. _aas-core-meta: https://github.com/aas-core-works/aas-core-meta/
.. _dev_scripts/: https://github.com/aas-core-works/aas-core-codegen/tree/main/dev_scripts
