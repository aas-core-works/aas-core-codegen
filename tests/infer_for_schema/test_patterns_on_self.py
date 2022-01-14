import textwrap
import unittest
from typing import MutableMapping, List

import tests.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.common import Identifier


def infer_patterns_on_self_of_class_something(
    source: str,
) -> List[infer_for_schema.PatternConstraint]:
    """Translate the ``source`` into inferred constraints of the class ``Something``."""
    symbol_table, error = tests.common.translate_source_to_intermediate(source=source)
    assert error is None, tests.common.most_underlying_messages(error)
    assert symbol_table is not None
    symbol = symbol_table.must_find(Identifier("Something"))
    assert isinstance(symbol, intermediate.ConstrainedPrimitive)

    pattern_verifications_by_name = infer_for_schema.map_pattern_verifications_by_name(
        verifications=symbol_table.verification_functions
    )

    return infer_for_schema.infer_patterns_on_self(
        constrained_primitive=symbol,
        pattern_verifications_by_name=pattern_verifications_by_name,
    )


class Test_expected(unittest.TestCase):
    def test_no_pattern(self) -> None:
        source = textwrap.dedent(
            """\
            class Something(str):
                pass


            class Reference:
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            associate_ref_with(Reference)
            """
        )

        patterns = infer_patterns_on_self_of_class_something(source=source)

        text = infer_for_schema.dump_patterns(patterns)
        self.assertEqual("[]", text)

    def test_single_pattern(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def is_something(text: str) -> bool:
                prefix = "something"
                return match(f"{prefix}-[a-zA-Z]+", text) is not None


            @invariant(lambda self: is_something(self))
            class Something(str):
                pass


            class Reference:
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            associate_ref_with(Reference)
            """
        )

        patterns = infer_patterns_on_self_of_class_something(source=source)

        text = infer_for_schema.dump_patterns(patterns)
        self.assertEqual(
            textwrap.dedent(
                """\
                [
                  PatternConstraint(
                    pattern='something-[a-zA-Z]+')
                ]"""
            ),
            text,
        )

    def test_two_patterns(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def is_something(text: str) -> bool:
                return match("something-[a-zA-Z]+", text) is not None

            @verification
            def is_acme(text: str) -> bool:
                return match(".*acme.*", text) is not None


            @invariant(lambda self: is_acme(self))
            @invariant(lambda self: is_something(self))
            class Something(str):
                pass


            class Reference:
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            associate_ref_with(Reference)
            """
        )

        patterns = infer_patterns_on_self_of_class_something(source=source)

        text = infer_for_schema.dump_patterns(patterns)
        self.assertEqual(
            textwrap.dedent(
                """\
                [
                  PatternConstraint(
                    pattern='something-[a-zA-Z]+'),
                  PatternConstraint(
                    pattern='.*acme.*')
                ]"""
            ),
            text,
        )

    def test_inheritance(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def is_something(text: str) -> bool:
                return match("something-[a-zA-Z]+", text) is not None

            @verification
            def is_acme(text: str) -> bool:
                return match(".*acme.*", text) is not None

            @invariant(lambda self: is_something(self))
            class Parent(str):
                pass

            @invariant(lambda self: is_acme(self))
            class Something(Parent):
                pass

            class Reference:
                pass

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            associate_ref_with(Reference)
            """
        )

        patterns = infer_patterns_on_self_of_class_something(source=source)

        text = infer_for_schema.dump_patterns(patterns)

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.

        self.assertEqual(
            textwrap.dedent(
                """\
                [
                  PatternConstraint(
                    pattern='.*acme.*')
                ]"""
            ),
            text,
        )


if __name__ == "__main__":
    unittest.main()
