# pylint: disable=missing-docstring

import textwrap
import unittest
from typing import Optional, MutableMapping

import tests.common
import tests.infer_for_schema.common
from aas_core_codegen import infer_for_schema, intermediate


class Test_expected(unittest.TestCase):
    def test_no_pattern(self) -> None:
        source = textwrap.dedent(
            """\
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # fmt: off
        (
            _,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_single_pattern(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                prefix = "something"
                return match(f"^{prefix}-[a-zA-Z]+$", text) is not None


            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # fmt: off
        (
            _,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_two_patterns(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                return match("^something-[a-zA-Z]+$", text) is not None

            @verification
            def matches_acme(text: str) -> bool:
                return match("^.*acme.*$", text) is not None


            @invariant(
                lambda self: matches_acme(self.some_property),
                "Some property must match acme."
            )
            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # fmt: off
        (
            _,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$'),
                      PatternConstraint(
                        pattern='^.*acme.*$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_conditioned_on_property(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                return match("^something-[a-zA-Z]+$", text) is not None

            @invariant(
                lambda self:
                not (self.some_property is not None)
                or  matches_something(self.some_property),
                "Some property must match something."
            )
            class Something:
                some_property: Optional[str]

                def __init__(self, some_property: Optional[str] = None) -> None:
                    self.some_property = some_property


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.

        # fmt: off
        (
            _,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_no_inheritance_by_default(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                return match("^something-[a-zA-Z]+$", text) is not None

            @verification
            def matches_acme(text: str) -> bool:
                return match("^.*acme.*$", text) is not None

            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class Parent:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            @invariant(
                lambda self: matches_acme(self.some_property),
                "Some property must match acme."
            )
            class Something(Parent):
                def __init__(self, some_property: str) -> None:
                    Parent.__init__(self, some_property=some_property)


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.
        #
        # This is necessary as we want to use these constraints to generate schemas
        # whereas it is the job of the schema engine to stack the constraints together.

        # fmt: off
        (
            _,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^.*acme.*$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )


class Test_stacking(unittest.TestCase):
    def test_no_inheritance_involved(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                prefix = "something"
                return match(f"^{prefix}-[a-zA-Z]+$", text) is not None


            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-05-18):
        # This definition here is necessary for mypy.
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None

        # fmt: off
        (
            symbol_table,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_class, error = infer_for_schema.merge_constraints_with_ancestors(
            symbol_table=symbol_table, constraints_by_class=constraints_by_class
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert constraints_by_class is not None

        constraints_by_props = constraints_by_class[something_cls]

        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_inheritance_from_parent_with_no_patterns_of_own(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                prefix = "something"
                return match(f"^{prefix}-[a-zA-Z]+$", text) is not None


            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-05-18):
        # This definition here is necessary for mypy.
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None

        # fmt: off
        (
            symbol_table,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_class, error = infer_for_schema.merge_constraints_with_ancestors(
            symbol_table=symbol_table, constraints_by_class=constraints_by_class
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert constraints_by_class is not None

        constraints_by_props = constraints_by_class[something_cls]

        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_merge_with_parent(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                return match("^something-[a-zA-Z]+$", text) is not None

            @verification
            def matches_acme(text: str) -> bool:
                return match("^.*acme.*$", text) is not None

            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class Parent:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            @invariant(
                lambda self: matches_acme(self.some_property),
                "Some property must match acme."
            )
            class Something(Parent):
                def __init__(self, some_property: str) -> None:
                    Parent.__init__(self, some_property=some_property)


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-05-18):
        # This definition here is necessary for mypy.
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None

        # fmt: off
        (
            symbol_table,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_class, error = infer_for_schema.merge_constraints_with_ancestors(
            symbol_table=symbol_table, constraints_by_class=constraints_by_class
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert constraints_by_class is not None

        constraints_by_props = constraints_by_class[something_cls]

        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^.*acme.*$'),
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_merge_with_parent_and_grand_parent(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                return match("^something-[a-zA-Z]+$", text) is not None

            @invariant(
                lambda self: matches_something(self.some_property),
                "Some property must match something."
            )
            class GrandParent:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property

            class Parent(GrandParent):
                def __init__(self, some_property: str) -> None:
                    GrandParent.__init__(self, some_property=some_property)

            class Something(Parent):
                def __init__(self, some_property: str) -> None:
                    Parent.__init__(self, some_property=some_property)


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-05-18):
        # This definition here is necessary for mypy.
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None

        # fmt: off
        (
            symbol_table,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_class, error = infer_for_schema.merge_constraints_with_ancestors(
            symbol_table=symbol_table, constraints_by_class=constraints_by_class
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert constraints_by_class is not None

        constraints_by_props = constraints_by_class[something_cls]

        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )

    def test_merge_with_parent_over_constrained_primitive(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def matches_something(text: str) -> bool:
                return match("^something-[a-zA-Z]+$", text) is not None

            @invariant(
                lambda self: matches_something(self),
                "Some property must match something."
            )
            class SomeConstrainedPrimitive(str):
                pass

            class Parent:
                some_property: SomeConstrainedPrimitive

                def __init__(self, some_property: SomeConstrainedPrimitive) -> None:
                    self.some_property = some_property

            class Something(Parent):
                def __init__(self, some_property: SomeConstrainedPrimitive) -> None:
                    Parent.__init__(self, some_property=some_property)


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        # NOTE (mristin, 2022-05-18):
        # This definition here is necessary for mypy.
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None

        # fmt: off
        (
            symbol_table,
            something_cls,
            constraints_by_class,
        ) = (
            tests.infer_for_schema.common
            .parse_to_symbol_table_and_something_cls_and_constraints_by_class(
                source=source
            )
        )
        # fmt: on

        constraints_by_class, error = infer_for_schema.merge_constraints_with_ancestors(
            symbol_table=symbol_table, constraints_by_class=constraints_by_class
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert constraints_by_class is not None

        constraints_by_props = constraints_by_class[something_cls]

        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={
                    'some_property': [
                      PatternConstraint(
                        pattern='^something-[a-zA-Z]+$')]},
                  set_of_primitives_by_property={},
                  set_of_enumeration_literals_by_property={})"""
            ),
            text,
        )


if __name__ == "__main__":
    unittest.main()
