# pylint: disable=missing-docstring


import textwrap
import unittest
from typing import Optional, MutableMapping

import tests.common
import tests.infer_for_schema.common
from aas_core_codegen import infer_for_schema, intermediate


class Test_property_in_set(unittest.TestCase):
    def test_no_constraints(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"

            class Something:
                some_property: Some_enum

                def __init__(self, some_property: Some_enum) -> None:
                    self.some_property = some_property

            __book_url__ = "dummy"
            __book_version__ = "dummy"
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

    def test_property_in_set(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B
                ])

            @invariant(lambda self: self.some_property in Some_set)
            class Something:
                some_property: Some_enum

                def __init__(self, some_property: Some_enum) -> None:
                    self.some_property = some_property

            __book_url__ = "dummy"
            __book_version__ = "dummy"
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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral A',
        'Reference to EnumerationLiteral B'])})""",
            text,
        )

    def test_property_in_set_in_conjunction(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B
                ])

            Another_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.B,
                    Some_enum.C
                ])


            @invariant(
                lambda self:
                self.some_property in Some_set
                and self.some_property in Another_set
            )
            class Something:
                some_property: Some_enum

                def __init__(self, some_property: Some_enum) -> None:
                    self.some_property = some_property

            __book_url__ = "dummy"
            __book_version__ = "dummy"
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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral B'])})""",
            text,
        )

    def test_property_in_set_in_implication(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B
                ])

            @invariant(
                lambda self:
                not (self.some_property is not None)
                or self.some_property in Some_set
            )
            class Something:
                some_property: Optional[Some_enum]

                def __init__(self, some_property: Optional[Some_enum] = None) -> None:
                    self.some_property = some_property

            __book_url__ = "dummy"
            __book_version__ = "dummy"
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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral A',
        'Reference to EnumerationLiteral B'])})""",
            text,
        )

    def test_property_in_set_in_implication_and_conjunction(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B
                ])

            Another_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.B,
                    Some_enum.C
                ])

            @invariant(
                lambda self:
                not (self.some_property is not None)
                or (
                    self.some_property in Some_set
                    and self.some_property in Another_set
                )
            )
            class Something:
                some_property: Optional[Some_enum]

                def __init__(self, some_property: Optional[Some_enum] = None) -> None:
                    self.some_property = some_property

            __book_url__ = "dummy"
            __book_version__ = "dummy"
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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral B'])})""",
            text,
        )


class Test_stacking(unittest.TestCase):
    def test_only_inherited_and_no_constraints_of_its_own(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B
                ])


            @invariant(
                lambda self:
                self.some_property in Some_set
            )
            class Parent(DBC):
                some_property: Some_enum

                def __init__(self, some_property: Some_enum) -> None:
                    self.some_property = some_property

            class Something(Parent):
                def __init__(self, some_property: Some_enum) -> None:
                    Parent.__init__(self, some_property)

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        # noinspection PyUnusedLocal
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None  # Necessary for mypy

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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral A',
        'Reference to EnumerationLiteral B'])})""",
            text,
        )

    def test_merge_with_parent(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B
                ])

            Another_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.B,
                    Some_enum.C
                ])

            @invariant(
                lambda self:
                self.some_property in Some_set
            )
            class Parent(DBC):
                some_property: Some_enum

                def __init__(self, some_property: Some_enum) -> None:
                    self.some_property = some_property

            @invariant(
                lambda self:
                self.some_property in Another_set
            )
            class Something(Parent):
                def __init__(self, some_property: Some_enum) -> None:
                    Parent.__init__(self, some_property)

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        # noinspection PyUnusedLocal
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None  # Necessary for mypy

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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral B'])})""",
            text,
        )

    def test_merge_with_parent_and_grand_parent(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                A = "A"
                B = "B"
                C = "C"
                D = "D"
                E = "E"

            Some_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.A,
                    Some_enum.B,
                    Some_enum.C,
                ])

            Another_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.B,
                    Some_enum.C,
                    Some_enum.D
                ])

            Yet_another_set: Set[Some_enum] = constant_set(
                values=[
                    Some_enum.C,
                    Some_enum.D,
                    Some_enum.E
                ])

            @invariant(
                lambda self:
                self.some_property in Some_set
            )
            class Grand_parent(DBC):
                some_property: Some_enum

                def __init__(self, some_property: Some_enum) -> None:
                    self.some_property = some_property

            @invariant(
                lambda self:
                self.some_property in Another_set
            )
            class Parent(Grand_parent):
                def __init__(self, some_property: Some_enum) -> None:
                    Grand_parent.__init__(self, some_property)

            @invariant(
                lambda self:
                self.some_property in Yet_another_set
            )
            class Something(Parent):
                def __init__(self, some_property: Some_enum) -> None:
                    Parent.__init__(self, some_property)


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        # noinspection PyUnusedLocal
        constraints_by_class: Optional[
            MutableMapping[
                intermediate.ClassUnion, infer_for_schema.ConstraintsByProperty
            ]
        ] = None  # Necessary for mypy

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
            """\
ConstraintsByProperty(
  len_constraints_by_property={},
  patterns_by_property={},
  set_of_primitives_by_property={},
  set_of_enumeration_literals_by_property={
    'some_property': SetOfEnumerationLiteralsConstraint(
      enumeration='Reference to Enumeration Some_enum',
      literals=[
        'Reference to EnumerationLiteral C'])})""",
            text,
        )


if __name__ == "__main__":
    unittest.main()
