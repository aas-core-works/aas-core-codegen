# pylint: disable=missing-docstring

import textwrap
import unittest
from typing import Tuple, Optional, MutableMapping, List

from icontract import ensure

import tests.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.infer_for_schema import _len as infer_for_schema_len
from aas_core_codegen.common import Identifier, Error


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_constraints_by_properties_of_class_something(
    source: str,
) -> Tuple[
    Optional[MutableMapping[intermediate.Property, infer_for_schema_len.LenConstraint]],
    Optional[List[Error]],
]:
    """Translate the ``source`` into inferred constraints of the class ``Something``."""
    symbol_table, error = tests.common.translate_source_to_intermediate(source=source)
    assert error is None, tests.common.most_underlying_messages(error)
    assert symbol_table is not None
    symbol = symbol_table.must_find(Identifier("Something"))
    assert isinstance(symbol, intermediate.Class)

    result = infer_for_schema_len.len_constraints_from_invariants(cls=symbol)

    return result


class Test_expected(unittest.TestCase):
    def test_no_constraints(self) -> None:
        source = textwrap.dedent(
            """\
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual("{}", text)

    def test_min_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 < len(self.some_property))
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=11,
                max_value=None)
            }"""
            ),
            text,
        )

    def test_min_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) > 10)
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=11,
                max_value=None)
            }"""
            ),
            text,
        )

    def test_max_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) < 10)
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=None,
                max_value=9)
            }"""
            ),
            text,
        )

    def test_max_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 > len(self.some_property))
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=None,
                max_value=9)
            }"""
            ),
            text,
        )

    def test_exact_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 == len(self.some_property))
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=10,
                max_value=10)
            }"""
            ),
            text,
        )

    def test_exact_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) == 10)
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=10,
                max_value=10)
            }"""
            ),
            text,
        )

    def test_conditioned_on_property(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(
                lambda self:
                not (self.some_property is not None)
                or len(self.some_property) == 10
            )
            class Something:
                some_property: Optional[str]

                def __init__(self, some_property: Optional[str] = None) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
            {
              'some_property':
              LenConstraint(
                min_value=10,
                max_value=10)
            }"""
            ),
            text,
        )

    def test_inheritance(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) > 3)
            class Parent:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            @invariant(lambda self: len(self.some_property) > 5)
            class Something(Parent):
                def __init__(self, some_property: str) -> None:
                    Parent.__init__(
                        self,
                        some_property=some_property
                    )


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props, errors = infer_constraints_by_properties_of_class_something(
            source=source
        )

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert by_props is not None

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.

        text = infer_for_schema.dump_len_constraints_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                {
                  'some_property':
                  LenConstraint(
                    min_value=6,
                    max_value=None)
                }"""
            ),
            text,
        )


class Test_unexpected(unittest.TestCase):
    def test_conflicting_min_and_max(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) > 10)
            @invariant(lambda self: len(self.some_property) < 3)
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        _, errors = infer_constraints_by_properties_of_class_something(source=source)

        assert errors is not None
        self.assertEqual(
            "The property some_property has conflicting invariants on the length: "
            "the minimum length, 11, contradicts the maximum length 2.",
            tests.common.most_underlying_messages(errors),
        )

    def test_conflicting_min_and_exact(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) > 10)
            @invariant(lambda self: len(self.some_property) == 3)
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        _, errors = infer_constraints_by_properties_of_class_something(source=source)

        assert errors is not None
        self.assertEqual(
            "The property some_property has conflicting invariants on the length: "
            "the minimum length, 11, contradicts the exactly expected length 3.",
            tests.common.most_underlying_messages(errors),
        )

    def test_conflicting_max_and_exact(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self.some_property) < 10)
            @invariant(lambda self: len(self.some_property) == 30)
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        _, errors = infer_constraints_by_properties_of_class_something(source=source)

        assert errors is not None
        self.assertEqual(
            "The property some_property has conflicting invariants on the length: "
            "the maximum length, 9, contradicts the exactly expected length 30.",
            tests.common.most_underlying_messages(errors),
        )


if __name__ == "__main__":
    unittest.main()
