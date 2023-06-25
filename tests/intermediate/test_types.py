# pylint: disable=missing-docstring

import textwrap
import unittest

import tests.common
from aas_core_codegen import intermediate
from aas_core_codegen.common import Identifier


class TestIsSubclassOf(unittest.TestCase):
    def test_no_inheritances(self) -> None:
        source = textwrap.dedent(
            """\
            class Concrete:
                pass


            class AnotherConcrete:
                pass


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        concrete = symbol_table.must_find_concrete_class(Identifier("Concrete"))

        another_concrete = symbol_table.must_find_concrete_class(
            Identifier("AnotherConcrete")
        )

        self.assertTrue(concrete.is_subclass_of(cls=concrete))
        self.assertFalse(concrete.is_subclass_of(cls=another_concrete))

    def test_one_level_ancestor(self) -> None:
        source = textwrap.dedent(
            """\
            class Parent:
                pass


            class Concrete(Parent):
                pass


            class AnotherConcrete:
                pass


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        parent = symbol_table.must_find_concrete_class(Identifier("Parent"))

        concrete = symbol_table.must_find_concrete_class(Identifier("Concrete"))

        another_concrete = symbol_table.must_find_concrete_class(
            Identifier("AnotherConcrete")
        )

        self.assertTrue(concrete.is_subclass_of(cls=concrete))
        self.assertTrue(concrete.is_subclass_of(cls=parent))
        self.assertFalse(concrete.is_subclass_of(cls=another_concrete))

    def test_two_level_ancestor(self) -> None:
        source = textwrap.dedent(
            """\
            class GrandParent:
                pass


            class Parent(GrandParent):
                pass


            class Concrete(Parent):
                pass


            class AnotherConcrete:
                pass


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        grand_parent = symbol_table.must_find_concrete_class(Identifier("GrandParent"))

        parent = symbol_table.must_find_concrete_class(Identifier("Parent"))

        concrete = symbol_table.must_find_concrete_class(Identifier("Concrete"))

        another_concrete = symbol_table.must_find_concrete_class(
            Identifier("AnotherConcrete")
        )

        self.assertTrue(concrete.is_subclass_of(cls=concrete))
        self.assertTrue(concrete.is_subclass_of(cls=parent))
        self.assertTrue(concrete.is_subclass_of(cls=grand_parent))
        self.assertFalse(concrete.is_subclass_of(cls=another_concrete))

    def test_common_ancestor_but_no_subclass(self) -> None:
        source = textwrap.dedent(
            """\
            class Parent:
                pass


            class Concrete(Parent):
                pass


            class AnotherConcrete(Parent):
                pass


            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)

        assert symbol_table is not None

        parent = symbol_table.must_find_concrete_class(Identifier("Parent"))

        concrete = symbol_table.must_find_concrete_class(Identifier("Concrete"))

        another_concrete = symbol_table.must_find_concrete_class(
            Identifier("AnotherConcrete")
        )

        self.assertTrue(concrete.is_subclass_of(cls=concrete))
        self.assertTrue(concrete.is_subclass_of(cls=parent))
        self.assertFalse(concrete.is_subclass_of(cls=another_concrete))


if __name__ == "__main__":
    unittest.main()
