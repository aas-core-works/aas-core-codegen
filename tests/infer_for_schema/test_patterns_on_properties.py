# pylint: disable=missing-docstring

import textwrap
import unittest
from typing import MutableMapping, List

import tests.common
from aas_core_codegen import intermediate, infer_for_schema
from aas_core_codegen.infer_for_schema import _pattern as infer_for_schema_pattern
from aas_core_codegen.common import Identifier


def infer_patterns_by_properties_of_class_something(
    source: str,
) -> MutableMapping[
    intermediate.Property, List[infer_for_schema_pattern.PatternConstraint]
]:
    """Translate the ``source`` into inferred constraints of the class ``Something``."""
    symbol_table, error = tests.common.translate_source_to_intermediate(source=source)
    assert error is None, tests.common.most_underlying_messages(error)
    assert symbol_table is not None
    symbol = symbol_table.must_find(Identifier("Something"))
    assert isinstance(symbol, intermediate.Class)

    pattern_verifications_by_name = (
        infer_for_schema_pattern.map_pattern_verifications_by_name(
            verifications=symbol_table.verification_functions
        )
    )

    return infer_for_schema_pattern.patterns_from_invariants(
        cls=symbol, pattern_verifications_by_name=pattern_verifications_by_name
    )


class Test_expected(unittest.TestCase):
    def test_no_pattern(self) -> None:
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

        by_props = infer_patterns_by_properties_of_class_something(source=source)

        assert by_props is not None

        text = infer_for_schema.dump_patterns_by_properties(by_props)
        self.assertEqual("{}", text)

    def test_single_pattern(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def is_something(text: str) -> bool:
                prefix = "something"
                return match(f"{prefix}-[a-zA-Z]+", text) is not None


            @invariant(lambda self: is_something(self.some_property))
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props = infer_patterns_by_properties_of_class_something(source=source)

        assert by_props is not None

        text = infer_for_schema.dump_patterns_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                {
                  'some_property':
                  [
                    PatternConstraint(
                      pattern='something-[a-zA-Z]+')
                  ]
                }"""
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


            @invariant(lambda self: is_acme(self.some_property))
            @invariant(lambda self: is_something(self.some_property))
            class Something:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props = infer_patterns_by_properties_of_class_something(source=source)

        assert by_props is not None

        text = infer_for_schema.dump_patterns_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                {
                  'some_property':
                  [
                    PatternConstraint(
                      pattern='something-[a-zA-Z]+'),
                    PatternConstraint(
                      pattern='.*acme.*')
                  ]
                }"""
            ),
            text,
        )

    def test_conditioned_on_property(self) -> None:
        source = textwrap.dedent(
            """\
            @verification
            def is_something(text: str) -> bool:
                return match("something-[a-zA-Z]+", text) is not None

            @invariant(
                lambda self:
                not (self.some_property is not None)
                or  is_something(self.some_property)
            )
            class Something:
                some_property: Optional[str]

                def __init__(self, some_property: Optional[str] = None) -> None:
                    self.some_property = some_property


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props = infer_patterns_by_properties_of_class_something(source=source)

        assert by_props is not None

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.

        text = infer_for_schema.dump_patterns_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                {
                  'some_property':
                  [
                    PatternConstraint(
                      pattern='something-[a-zA-Z]+')
                  ]
                }"""
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

            @invariant(lambda self: is_something(self.some_property))
            class Parent:
                some_property: str

                def __init__(self, some_property: str) -> None:
                    self.some_property = some_property


            @invariant(lambda self: is_acme(self.some_property))
            class Something(Parent):
                def __init__(self, some_property: str) -> None:
                    Parent.__init__(self, some_property=some_property)


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        by_props = infer_patterns_by_properties_of_class_something(source=source)

        assert by_props is not None

        # NOTE (mristin, 2022-01-02):
        # We infer only the constraints as specified in the class itself, and
        # ignore the constraints of the ancestors in *this particular kind of
        # inference*.

        text = infer_for_schema.dump_patterns_by_properties(by_props)
        self.assertEqual(
            textwrap.dedent(
                """\
                {
                  'some_property':
                  [
                    PatternConstraint(
                      pattern='.*acme.*')
                  ]
                }"""
            ),
            text,
        )


if __name__ == "__main__":
    unittest.main()
