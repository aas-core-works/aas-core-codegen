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
def infer_constraints_on_self_of_class_something(
    source: str,
) -> Tuple[Optional[infer_for_schema_len.LenConstraint], Optional[List[Error]]]:
    """Translate the ``source`` into inferred constraints on the class ``Something``."""
    symbol_table, error = tests.common.translate_source_to_intermediate(source=source)
    assert error is None, tests.common.most_underlying_messages(error)
    assert symbol_table is not None
    symbol = symbol_table.must_find(Identifier("Something"))
    assert isinstance(symbol, intermediate.ConstrainedPrimitive)

    result = infer_for_schema_len.infer_len_constraint_of_self(
        constrained_primitive=symbol
    )

    return result


class Test_expected(unittest.TestCase):
    def test_no_constraints(self) -> None:
        source = textwrap.dedent(
            """\
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=None,
                  max_value=None)"""
            ),
            text,
        )

    def test_min_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 < len(self))
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=11,
                  max_value=None)"""
            ),
            text,
        )

    def test_min_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 10)
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=11,
                  max_value=None)"""
            ),
            text,
        )

    def test_max_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) < 10)
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=None,
                  max_value=9)"""
            ),
            text,
        )

    def test_max_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 > len(self))
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=None,
                  max_value=9)"""
            ),
            text,
        )

    def test_exact_value_constant_left(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: 10 == len(self))
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                        LenConstraint(
                          min_value=10,
                          max_value=10)"""
            ),
            text,
        )

    def test_exact_value_constant_right(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) == 10)
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=10,
                  max_value=10)"""
            ),
            text,
        )

    def test_inheritance(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 3)
            class Parent(str):
                pass


            @invariant(lambda self: len(self) > 5)
            class Something(Parent):
                pass


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        constraint, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is None, tests.common.most_underlying_messages(errors)
        assert constraint is not None

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.

        text = infer_for_schema.dump(constraint)
        self.assertEqual(
            textwrap.dedent(
                """\
                LenConstraint(
                  min_value=6,
                  max_value=None)"""
            ),
            text,
        )


class Test_unexpected(unittest.TestCase):
    def test_conflicting_min_and_max(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 10)
            @invariant(lambda self: len(self) < 3)
            class Something(str):
                pass


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        _, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is not None
        self.assertEqual(
            "There are conflicting invariants on the length: "
            "the minimum length, 11, contradicts the maximum length 2.",
            tests.common.most_underlying_messages(errors),
        )

    def test_conflicting_min_and_exact(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) > 10)
            @invariant(lambda self: len(self) == 3)
            class Something(str):
                pass


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        _, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is not None
        self.assertEqual(
            "There are conflicting invariants on the length: "
            "the minimum length, 11, contradicts the exactly expected length 3.",
            tests.common.most_underlying_messages(errors),
        )

    def test_conflicting_max_and_exact(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(lambda self: len(self) < 10)
            @invariant(lambda self: len(self) == 30)
            class Something(str):
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        _, errors = infer_constraints_on_self_of_class_something(source=source)

        assert errors is not None
        self.assertEqual(
            "There are conflicting invariants on the length: "
            "the maximum length, 9, contradicts the exactly expected length 30.",
            tests.common.most_underlying_messages(errors),
        )


if __name__ == "__main__":
    unittest.main()
