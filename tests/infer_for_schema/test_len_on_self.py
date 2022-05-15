# pylint: disable=missing-docstring

import textwrap
import unittest

import tests.common
import tests.infer_for_schema.common
from aas_core_codegen import infer_for_schema


class Test_expected(unittest.TestCase):
    def test_no_constraints(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_min_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 < len(self))
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=11,
                      max_value=None)},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_min_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 10)
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=11,
                      max_value=None)},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_max_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) < 10)
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=None,
                      max_value=9)},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_max_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 > len(self))
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=None,
                      max_value=9)},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_exact_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 == len(self))
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=10,
                      max_value=10)},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_exact_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) == 10)
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=10,
                      max_value=10)},
                  patterns_by_property={})"""
            ),
            text,
        )

    def test_inheritance_between_constrained_primitives_by_default(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 3)
            class Parent_constrained_primitive(str):
                pass


            @invariant(lambda self: len(self) < 6)
            class Some_constrained_primitive(Parent_constrained_primitive):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        # NOTE (mristin, 2022-05-15):
        # In contrast to classes, we do inherit the constraints among the constrained
        # primitives as we in-line them later in the schema classes.

        (
            _,
            something_cls,
            constraints_by_class,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls_and_constraints_by_class(
            source=source
        )

        constraints_by_props = constraints_by_class[something_cls]
        text = infer_for_schema.dump(constraints_by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                ConstraintsByProperty(
                  len_constraints_by_property={
                    'some_property': LenConstraint(
                      min_value=4,
                      max_value=5)},
                  patterns_by_property={})"""
            ),
            text,
        )


class Test_unexpected(unittest.TestCase):
    def test_conflicting_min_and_max(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 10)
            @invariant(lambda self: len(self) < 3)
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            symbol_table,
            _,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls(
            source=source
        )

        _, error = infer_for_schema.infer_constraints_by_class(
            symbol_table=symbol_table
        )

        assert error is not None
        self.assertEqual(
            "There are conflicting invariants on the length: "
            "the minimum length, 11, contradicts the maximum length 2.",
            tests.common.most_underlying_messages(error),
        )

    def test_conflicting_min_and_exact(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 10)
            @invariant(lambda self: len(self) == 3)
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            symbol_table,
            _,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls(
            source=source
        )

        _, error = infer_for_schema.infer_constraints_by_class(
            symbol_table=symbol_table
        )

        assert error is not None
        self.assertEqual(
            "There are conflicting invariants on the length: "
            "the minimum length, 11, contradicts the exactly expected length 3.",
            tests.common.most_underlying_messages(error),
        )

    def test_conflicting_max_and_exact(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) < 10)
            @invariant(lambda self: len(self) == 30)
            class Some_constrained_primitive(str):
                pass


            class Something:
                some_property: Some_constrained_primitive

                def __init__(self, some_property: Some_constrained_primitive) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        (
            symbol_table,
            _,
        ) = tests.infer_for_schema.common.parse_to_symbol_table_and_something_cls(
            source=source
        )

        _, error = infer_for_schema.infer_constraints_by_class(
            symbol_table=symbol_table
        )

        assert error is not None
        self.assertEqual(
            "There are conflicting invariants on the length: "
            "the maximum length, 9, contradicts the exactly expected length 30.",
            tests.common.most_underlying_messages(error),
        )


if __name__ == "__main__":
    unittest.main()
