# pylint: disable=missing-docstring
# pylint: disable=no-self-use

import textwrap
import unittest

import tests.common
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference


class Test_with_smoke(unittest.TestCase):
    @staticmethod
    def execute(source: str) -> None:
        """Execute a smoke test on all the invariants of all the classes."""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        base_environment = intermediate_type_inference.populate_base_environment(
            symbol_table=symbol_table
        )

        for symbol in symbol_table.symbols:
            if isinstance(
                symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                environment = intermediate_type_inference.MutableEnvironment(
                    parent=base_environment
                )
                environment.set(
                    Identifier("self"),
                    intermediate_type_inference.OurTypeAnnotation(symbol=symbol),
                )

                for invariant in symbol.invariants:
                    canonicalizer = intermediate_type_inference.Canonicalizer()
                    canonicalizer.transform(invariant.body)

                    inferrer = intermediate_type_inference.Inferrer(
                        symbol_table=symbol_table,
                        environment=environment,
                        representation_map=canonicalizer.representation_map,
                    )

                    inferrer.transform(invariant.body)
                    assert (
                        len(inferrer.errors) == 0
                    ), tests.common.most_underlying_messages(inferrer.errors)

    def test_enumeration_literal_as_member(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_enum(Enum):
                Literal_a = "LITERAL-A"
                Literal_b = "LITERAL-B"
                Literal_c = "LITERAL-C"

            @invariant(
                lambda self:
                self.something == Some_enum.Literal_a
                or self.something == Some_enum.Literal_b
            )
            class Some_class:
                something: Some_enum

                def __init__(self, something: Some_enum) -> None:
                    self.something = something


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        Test_with_smoke.execute(source=source)

    def test_class_member(self) -> None:
        source = textwrap.dedent(
            """\
            @invariant(
                lambda self:
                self.something > 0
            )
            class Some_class:
                something: int

                def __init__(self, something: int) -> None:
                    self.something = something


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        Test_with_smoke.execute(source=source)

    def test_non_nullness_of_members_member_in_implication(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_class:
                something: Optional[str]

                def __init__(self, something: Optional[str] = None) -> None:
                    self.something = something

            @invariant(
                lambda self:
                not (
                    self.some_instance is not None
                    and self.some_instance.something is not None
                ) or (
                    self.some_instance.something == "some-literal"
                )
            )
            class Another_class:
                some_instance: Optional[Some_class]

                def __init__(self, some_instance: Optional[Some_class] = None) -> None:
                    self.some_instance = some_instance


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        Test_with_smoke.execute(source=source)

    def test_non_nullness_of_members_member_in_conjunction(self) -> None:
        source = textwrap.dedent(
            """\
            class Some_class:
                something: Optional[str]

                def __init__(self, something: Optional[str] = None) -> None:
                    self.something = something

            @invariant(
                lambda self:
                self.some_instance is not None
                and self.some_instance.something is not None
                and self.some_instance.something == "some-literal"
            )
            class Another_class:
                some_instance: Optional[Some_class]

                def __init__(self, some_instance: Optional[Some_class] = None) -> None:
                    self.some_instance = some_instance


            __book_url__ = "dummy"
            __book_version__ = "dummy"
            """
        )

        Test_with_smoke.execute(source=source)


if __name__ == "__main__":
    unittest.main()
