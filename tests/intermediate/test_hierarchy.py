import textwrap
import unittest

import aas_core_codegen.intermediate._hierarchy as _hierarchy
import tests.common
from aas_core_codegen.common import Identifier


class Test_ontology_ok(unittest.TestCase):
    def test_no_ancestors(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                """\
                class Something:
                    pass
                    
                class Reference:
                    pass
                
                __book_url__ = "dummy"
                __book_version__ = "dummy"
                associate_ref_with(Reference)
                """
            )
        )

        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = _hierarchy.map_symbol_table_to_ontology(symbol_table)
        assert errors is None, f"{errors=}"
        assert ontology is not None

        ancestors = ontology.list_ancestors(
            cls=symbol_table.must_find_class(Identifier("Something"))
        )

        ancestor_names = [cls.name for cls in ancestors]
        self.assertListEqual([], ancestor_names)

    def test_complex_graph(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                """\
                @abstract
                class Another_grand_parent:
                    pass

                @abstract
                class Grand_parent:
                    pass

                @abstract
                class Parent(Grand_parent, Another_grand_parent):
                    pass

                @abstract
                class Another_parent(Grand_parent, Another_grand_parent):
                    pass

                class Something(Parent, Another_parent):
                    pass
                    
                class Reference:
                    pass
                
                __book_url__ = "dummy"
                __book_version__ = "dummy"
                associate_ref_with(Reference)
                """
            )
        )

        assert symbol_table is not None

        ontology, errors = _hierarchy.map_symbol_table_to_ontology(symbol_table)
        assert errors is None, f"{errors=}"
        assert ontology is not None

        ancestors = ontology.list_ancestors(
            cls=symbol_table.must_find_class(Identifier("Something"))
        )

        ancestor_names = [cls.name for cls in ancestors]

        self.assertListEqual(
            [
                "Another_grand_parent",
                "Grand_parent",
                "Another_parent",
                "Another_grand_parent",
                "Grand_parent",
                "Parent",
            ],
            ancestor_names,
        )


class Test_ontology_fail(unittest.TestCase):
    def test_duplicate_properties_in_ancestors(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                """\
                @abstract
                class Abstract:
                    x: int

                @abstract
                class Something(Abstract):
                    x: int
                    
                class Reference:
                    pass
                
                __book_url__ = "dummy"
                __book_version__ = "dummy"
                associate_ref_with(Reference)
                """
            )
        )
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = _hierarchy.map_symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "The property has already been defined "
            "in the ancestor class Abstract: x",
            tests.common.most_underlying_messages(errors[0]),
        )

    def test_duplicate_methods_in_ancestors(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                """\
                @abstract
                class Abstract:
                    def do_something(self) -> None:
                        pass

                @abstract
                class Something(Abstract):
                    def do_something(self) -> None:
                        pass
                        
                class Reference:
                    pass
                
                __book_url__ = "dummy"
                __book_version__ = "dummy"
                associate_ref_with(Reference)
                """
            )
        )
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = _hierarchy.map_symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "The method has already been defined "
            "in the ancestor class Abstract: do_something",
            tests.common.most_underlying_messages(errors[0]),
        )

    def test_missing_constructor_when_the_parent_has_one(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                """\
                @abstract
                class Abstract:
                    def __init__(self, x: int) -> None:
                        pass

                class Something(Abstract):
                    pass
                    
                class Reference:
                    pass
                
                __book_url__ = "dummy"
                __book_version__ = "dummy"
                associate_ref_with(Reference)
                """
            )
        )
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = _hierarchy.map_symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "The class Something does not specify a constructor, "
            "but the ancestor class Abstract specifies a constructor "
            "with arguments: self, x",
            tests.common.most_underlying_messages(errors[0]),
        )

    def test_cycle_inheritance(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                """\
                @abstract
                class Cycle(Something):
                    pass

                @abstract
                class Something(Cycle):
                    pass
                    
                class Reference:
                    pass
                
                __book_url__ = "dummy"
                __book_version__ = "dummy"
                associate_ref_with(Reference)
                """
            )
        )
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = _hierarchy.map_symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "Expected no cycles in the inheritance, "
            "but the class Cycle has been observed in a cycle",
            tests.common.most_underlying_messages(errors[0]),
        )


if __name__ == "__main__":
    unittest.main()
