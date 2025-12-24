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


class TestMustFindConstant(unittest.TestCase):
    def test_empty(self) -> None:
        source = """\
__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        with self.assertRaises(KeyError):
            _ = symbol_table.must_find_constant(Identifier("Something"))

    def test_constant(self) -> None:
        source = """\
Something: int = constant_int(value=1984)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        result = symbol_table.must_find_constant(Identifier("Something"))
        assert isinstance(result, intermediate.Constant)

    def test_constant_primitive(self) -> None:
        source = """\
Something: int = constant_int(value=1984)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        result = symbol_table.must_find_constant_primitive(Identifier("Something"))
        assert isinstance(result, intermediate.ConstantPrimitive)

        with self.assertRaises(TypeError):
            _ = symbol_table.must_find_constant_set_of_primitives(
                Identifier("Something")
            )

        with self.assertRaises(TypeError):
            _ = symbol_table.must_find_constant_set_of_enumeration_literals(
                Identifier("Something")
            )

    def test_constant_set_of_primitives(self) -> None:
        source = """\
Something: Set[str] = constant_set(
    values=["hello", "world"]
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
        """
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        result = symbol_table.must_find_constant_set_of_primitives(
            Identifier("Something")
        )
        assert isinstance(result, intermediate.ConstantSetOfPrimitives)

        with self.assertRaises(TypeError):
            _ = symbol_table.must_find_constant_primitive(Identifier("Something"))

        with self.assertRaises(TypeError):
            _ = symbol_table.must_find_constant_set_of_enumeration_literals(
                Identifier("Something")
            )

    def test_constant_set_of_enumeration_literals(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"
    Yet_another_literal = "YET-ANOTHER-LITERAL"


Something: Set[SomeEnum] = constant_set(
    values=[SomeEnum.Some_literal, SomeEnum.Another_literal]
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
        """
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        result = symbol_table.must_find_constant_set_of_enumeration_literals(
            Identifier("Something")
        )
        assert isinstance(result, intermediate.ConstantSetOfEnumerationLiterals)

        with self.assertRaises(TypeError):
            _ = symbol_table.must_find_constant_primitive(Identifier("Something"))

        with self.assertRaises(TypeError):
            _ = symbol_table.must_find_constant_set_of_primitives(
                Identifier("Something")
            )


class TestIsEnumerationLiteralOf(unittest.TestCase):
    def test_enumeration_literal_in_enumeration(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_enum = symbol_table.must_find_enumeration(Identifier("SomeEnum"))
        some_literal = some_enum.literals_by_name["Some_literal"]
        another_literal = some_enum.literals_by_name["Another_literal"]

        self.assertTrue(
            symbol_table.is_enumeration_literal_of(
                literal=some_literal,
                enumeration_or_constant_set_name=Identifier("SomeEnum"),
            )
        )
        self.assertTrue(
            symbol_table.is_enumeration_literal_of(
                literal=another_literal,
                enumeration_or_constant_set_name=Identifier("SomeEnum"),
            )
        )

    def test_enumeration_literal_not_in_different_enumeration(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"

class AnotherEnum(Enum):
    Different_literal = "DIFFERENT-LITERAL"

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_enum = symbol_table.must_find_enumeration(Identifier("SomeEnum"))
        another_enum = symbol_table.must_find_enumeration(Identifier("AnotherEnum"))

        some_literal = some_enum.literals_by_name["Some_literal"]
        different_literal = another_enum.literals_by_name["Different_literal"]

        self.assertFalse(
            symbol_table.is_enumeration_literal_of(
                literal=some_literal,
                enumeration_or_constant_set_name=Identifier("AnotherEnum"),
            )
        )
        self.assertFalse(
            symbol_table.is_enumeration_literal_of(
                literal=different_literal,
                enumeration_or_constant_set_name=Identifier("SomeEnum"),
            )
        )

    def test_enumeration_literal_in_constant_set(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"
    Yet_another_literal = "YET-ANOTHER-LITERAL"

SomeSet: Set[SomeEnum] = constant_set(
    values=[SomeEnum.Some_literal, SomeEnum.Another_literal]
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_enum = symbol_table.must_find_enumeration(Identifier("SomeEnum"))
        some_literal = some_enum.literals_by_name["Some_literal"]
        another_literal = some_enum.literals_by_name["Another_literal"]
        yet_another_literal = some_enum.literals_by_name["Yet_another_literal"]

        # NOTE (mristin):
        # We check here for membership.
        self.assertTrue(
            symbol_table.is_enumeration_literal_of(
                literal=some_literal,
                enumeration_or_constant_set_name=Identifier("SomeSet"),
            )
        )
        self.assertTrue(
            symbol_table.is_enumeration_literal_of(
                literal=another_literal,
                enumeration_or_constant_set_name=Identifier("SomeSet"),
            )
        )

        # NOTE (mristin):
        # We check here for out-of-membership.
        self.assertFalse(
            symbol_table.is_enumeration_literal_of(
                literal=yet_another_literal,
                enumeration_or_constant_set_name=Identifier("SomeSet"),
            )
        )

    def test_type_error_for_concrete_class(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"

class SomeClass:
    pass

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_enum = symbol_table.must_find_enumeration(Identifier("SomeEnum"))
        some_literal = some_enum.literals_by_name["Some_literal"]

        with self.assertRaises(TypeError):
            _ = symbol_table.is_enumeration_literal_of(
                literal=some_literal,
                enumeration_or_constant_set_name=Identifier("SomeClass"),
            )

    def test_type_error_for_constant_primitive(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"

SomeConstant: int = constant_int(value=42)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_enum = symbol_table.must_find_enumeration(Identifier("SomeEnum"))
        some_literal = some_enum.literals_by_name["Some_literal"]

        with self.assertRaises(TypeError):
            _ = symbol_table.is_enumeration_literal_of(
                literal=some_literal,
                enumeration_or_constant_set_name=Identifier("SomeConstant"),
            )

    def test_type_error_for_constant_set_of_primitives(self) -> None:
        source = """\
class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"

SomeSet: Set[str] = constant_set(
    values=["hello", "world"]
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
"""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_enum = symbol_table.must_find_enumeration(Identifier("SomeEnum"))
        some_literal = some_enum.literals_by_name["Some_literal"]

        # Test that TypeError is raised when name refers to a constant set of primitives
        with self.assertRaises(TypeError):
            _ = symbol_table.is_enumeration_literal_of(
                literal=some_literal,
                enumeration_or_constant_set_name=Identifier("SomeSet"),
            )


if __name__ == "__main__":
    unittest.main()
