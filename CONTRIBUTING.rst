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

Background Literature
=====================
Please make yourself familiar with a general literature on compiler design.

For example, `Crafting Interpreters`_ is a good book.

.. _Crafting Interpreters: https://craftinginterpreters.com/

Please also read relevant publications related to the aas-core-codegen:

* https://www.researchgate.net/publication/375497058_Empowering_Industry_40_with_Generative_and_Model-Driven_SDK_Development
* https://www.researchgate.net/publication/356039469_Generative_and_Model-driven_SDK_development_for_the_Industrie_40_Digital_Twin,
* https://www.researchgate.net/publication/373325991_Generation_of_Digital_Twins_for_Information_Exchange_Between_Partners_in_the_Industrie_40_Value_Chain,


Coding Style Guide
==================
Typing
------
Always write explicit types in function arguments.
If you really expect any type, mark that explicitly with ``Any``.
Also always mark your local variables with a type if it can not be deduced.

For example:

.. code-block:: python

    lst = []  # type: List[str]

For files, use ``typing.IO``.

We prefer to put types in comments if they are short for readability.
However, put them in code when they are multi-line:

.. code-block:: python

    some_map: Optional[
        Dict[
          SomeType,
          AnotherType
        ]
    ] = None

Variable Names
--------------
Put ``_set`` for sets.

Prefer to designate the key with ``_by_`` suffix.
For example, ``our_types_by_name`` is a mapping string (a name) 🠒 ``OurType``.

Method Names
------------
Do not put ``get_`` in method names.
If you want to make sure that the reader understands that some method is going to take longer than just a simple getter, prefix it with a meaningful verb such as ``compute_...``, ``collect_...`` or ``retrieve_...``.

Property Names
--------------
Do not duplicate module (package) or class names in the property names.

For example, if you have a class called ``Features``, and want to add property to hold feature names, call the property simply ``names`` and not ``feature_names``.
The caller code would otherwise redundantly read ``Features.feature_names`` or ``features.feature_names``.

Module Names
------------
Do not call your modules, classes or functions ``..._helpers`` or ``..._utils``.
A general name is most probably an indicator that there is either a flaw in the design (*e.g.*, tight coupling which should be decoupled) or that there needs to be more thought spent on the naming.

If you have shared functionality in a module used by all or most of the submodules, put it in ``common`` submodule.

Programming Paradigm
--------------------
* Prefer functional programming to object-oriented programming.
    * Better be explicit about the data flow than implicit.
* Prefer namespaced functions in a (sub)module instead of class methods.
    * Side effects are difficult to trace.
    * Context of a function is immediately visible when you look at arguments.
      A function is much easier to isolate and unit test than a class method.
* Use inheritance only when you need polymorphism.
    * Do not use inheritance to share implementation; use namespaced functions for that.
    * Prefer simplicity with a small number of classes; see http://thedailywtf.com/articles/Enterprise-Dependency-The-Next-Generation
    * Use stateful objects in moderation.
    * Some thoughts: https://medium.com/@cscalfani/goodbye-object-oriented-programming-a59cda4c0e53

Anti-patterns from Clean Code
-----------------------------
Do not split script-like parts of the code into small chunks of one-time usage functions.

Use comments or regions to give overview.

It's ok to have long scripts that are usually more readable than a patchwork of small functions.
Jumping around a file while keeping the context in head is difficult and error-prone.

No Stateful Singletons
----------------------
Do not *ever* use stateful singletons.
Pass objects down the calling stack even if it seems tedious at first.

Imports
-------
Very common symbols such as ``Error`` or ``Identifier`` can be imported without prefix.
Usually, these symbols reside in ``aas_core_codegen.common``.

In addition, do not prefix ``typing`` symbols such as ``List`` or ``Mapping``, and the assertion functions from `icontract`_ design-by-contract library (see below).
Otherwise, the code would be completely unreadable.

All other symbols should be imported with an aliased prefix corresponding to the module.
For example:

.. code-block::python

    from aas_core_codegen.golang import (
        common as golang_common,
        naming as golang_naming
    )

The indention constants (``I``, ``II`` *etc.*) are the only aliases allowed for symbols.
No other symbol should be aliased.

Filesystem
----------
Use ``pathlib``, not ``os.path``.

Design-by-contract
------------------
Use `design-by-contract`_ as much as possible.
We use `icontract`_ library.

.. _design-by-contract: https://en.wikipedia.org/wiki/Design_by_contract
.. _icontract: https://icontract.readthedocs.io/

``Final`` and Constant Containers
---------------------------------
Prefer immutable to mutable objects and structures.

Distinguish between internally and externally mutable structures.
Annotate for immutability if the structures are only internally mutable.

For example, ``aas_core_codegen.intermediate._types`` are all marked as immutable since they should not be mutated *after* the intermediate translation phase.
They are, however, mutated within ``aas_core_codegen.intermediate._translate``.

Avoid Double-Asterisk (``**``) Operator
---------------------------------------
Double-asterisks are unpredictable for the reader, as all the keys need to be kept in mind, and overridden keys are simply ignored.

Please do not use ``**`` operator unless it is utterly necessary, and explain in the comment why it is necessary.
Check for overwriting keys where appropriate.

Classes over ``TypedDict``
---------------------------
Always use classes in the code.

Use ``TypedDict`` only if you have to deal with serialization (*e.g.*, to JSON).

Code Regions
------------
We intensively use PyCharms ``# region ...`` and ``# endregion`` to structure code into regions.

Comments
--------
Mark notes with ``# NOTE ({github username}, {date in ISO 8601}):``.

No ``# TODO`` in the code, please.

Comment only where the comments really add information.
Do not write self-evident comments.

Comments should be in proper English.
Write in simple present tense; avoid imperative mood.

Be careful about the capitals.
Start the sentence with a capital.
If you list bullet points, start with a capital, and do not forget conjectures:

.. code-block:: python

    #    * We ...,
    #    * Then, ..., and finally
    #    * We ...

The abbreviations are to be written properly in capitals (*e.g.*, ``JSON`` and not ``json``).

No code is allowed in the comments since it always rots.

Docstrings
----------
You can write full-blown Sphinx docstrings, if you wish.

In many cases, a short docstring is enough.
We are not religious about ``:param ...:`` and ``:return`` fields.

Follow `PEP 287`_.
Use imperative mood in the docstrings.

.. _PEP 287: https://peps.python.org/pep-0287/

Testing
-------
Write unit tests for everything that can be obviously tested at the function/class level.

For many inter-dependent code regions, writing unit tests is too tedious or nigh impossible to later maintain.
For such parts of the system, prefer integration tests with comparisons against initially recorded and reviewed golden data.
See, for example, ``tests/csharp/test_main.py`` or ``tests/intermediate/test_translate.py``.

The golden test data resides in ``test_data/``.
The structure of the test data directory follows in general the test module structure.

Pre-commit Checks
=================

We provide a battery of pre-commit checks to make the code uniform and consistent across the code base.

We use `black`_ to format the code and use the default maximum line length of 88 characters.

.. _black: https://pypi.org/project/black/

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
5) Use the imperative mood in the subject line, full sentences in the body
6) Wrap the body at 72 characters
7) Use the body to explain *what* and *why* vs. *how*

.. _guidelines on commit messages: https://chris.beams.io/posts/git-commit/

If you are merging in a pull request, please squash before merging.
We want to keep the Git history as simple as possible, and the commits during the development are rarely insightful later.

Development Scripts
===================
We need to frequently back-propagate test data from `aas-core-meta`_ repository.
To facilitate fetching and re-recording test output whenever the meta-models change, we wrote a couple of scripts in `dev_scripts/`_.

The scripts are hopefully self-explaining.
Please let us know if you need more information so that we can improve this documentation accordingly.

.. _aas-core-meta: https://github.com/aas-core-works/aas-core-meta/
.. _dev_scripts/: https://github.com/aas-core-works/aas-core-codegen/tree/main/dev_scripts
