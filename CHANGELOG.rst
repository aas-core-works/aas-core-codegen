..
    NOTE (mristin, 2021-12-27):
    Please keep this file at 72 line width so that we can copy-paste
    the release logs directly into commit messages.

0.0.7 (2022-04-09)
==================
* Render the descriptions with smoke at intermediate (#142)

C#
--
* Represent string constants as literals in C# (#136)
* Fix formatting of multi-line invariants in C# (#137)
* Break lines on invariants in C# (#139)
* Wrap the invariant descriptions in C# (#140)

JSON Schema
-----------
* Make ``modelType``'s strings in JSON schema (#143)

XSD
---
* Write XSD generator (#126)
* Fix interfaces in XSD (#128)
* Fix XSD to use correct environment type (#130)
* Undo escaping of ``\x??`` in XSD (#131)


0.0.6 (2022-03-28)
==================
* Script smoke-testing a meta-model (#119)
* Fix swallowed errors in ``infer_for_schema`` (#118)

0.0.5 (2022-03-28)
==================

* Infer schema constraints only for strings (#115)
* Return errors instead of raising in C# jsonization (#114)
* Exclude ``ast`` class names from errors (#112)
* Produce better errors on unexpected enum elements (#111)
* Check the order of properties and constructor args (#107)
* Extract structure information from docstrings (#106)
* Handle ``all`` in intermediate representation (#95)
* Introduce ``constraintref`` role in the docs (#71)
* Parse ``reference_in_the_book`` (#69)
* Remove ``ID`` from abbreviations in ``naming`` (#60)
* Fix naming for set of symbols used in properties (#57)

C#
--
* Refactor verification in ``IEnumerable`` in C# (#93)
* Refactor errors to ``Reporting`` in C# (#92)
* Generate JSON paths for C# jsonization errors (#91)
* Optimize path handling in C# JSON deserialization (#90)
* Re-write two-pass serialization based on NET6 (#89)

JSON Schema
-----------
* Enforce base64 encoding for bytearrays in JSON (#87)
* Fix ``ModelTypes`` enumeration in JSON (#82)
* Remove ``*_abstract`` definitions from JSON (#78)
* In-line constrained primitives in JSON Schema (#77)
* Nest constrained primitives in JSON (#67)
* Skip unused symbols in JSON schema (#58)
* Use ``oneOf`` instead of ``anyOf`` in JSON schema (#56)
* Add ``modelType`` in JSON schema (#55)
* Remove redundant ``type`` property in JSON schema (#54)

RDF+SHACL
---------
* Update RDF gen after review of V3RC01 (#62)

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
