..
    NOTE (mristin, 2021-12-27):
    Please keep this file at 72 line width so that we can copy-paste
    the release logs directly into commit messages.

0.0.4 (2022-02-17)
==================

* Approximate RDF to aas-specs (#49)
* Fix RDF schema generation (#48)
* Generte RDF and SHACL schemas (#46)
* Introduce topologically sorted symbols in the table (#45)
* Upgrade docutils to 0.18.1 (#43)
* Remove ``RefTypeAnnotation`` from the IR (#39)
* Make jsonization in C# two-pass (#37)
* Fix double curly brackets in C# verification (#36)
* Infer type of enumeration literals in invariants (#32)
* Allow enumeration literals to be arbitrary strings (#31)

0.0.3 (2022-01-22)
==================

* Add support for Python 3.10 (#27)
* Add support for Python 3.9 (#26)
* Remove ``ExpressionWithDeclarations`` from our tree (#25)
* Revert lost `--version` command flag (#23)

0.0.2 (2022-01-15)
==================

* Provide generator for JSON schema (#13)
* Improve errors on unmatched verification functions (#21)
* Note the origin of the invariants (#20)
* Rename ``implemented_for`` to ``specified_for`` (#19)
* Reverse the invariants (#18)
* Ignore primitive types for origins in hierarchy (#17)
* Fix second pass to resolve descendants correctly (#16)
* Make ``indent_but_first_line`` ignore empty lines (#15)
* Fix encoding to ``utf-8`` on file I/O (#14)
* Add ``--version`` flag (#12)

0.0.1rc1.post1 (2021-12-27)
===========================

* A post release to test the publishing pipeline.

0.0.1rc1 (2021-12-27)
=====================

* The initial release candidate.
  This is actually an alpha release!
  Since the UAG Verwaltungsschale still needs to decide on fundamentals
  of the meta-model (such as basic primitive types) yet, this release
  is only meant for first experimental usage.
