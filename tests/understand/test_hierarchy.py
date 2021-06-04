import textwrap
import unittest

import aas_core_csharp_codegen.understand.hierarchy as understand_hierarchy
import tests.common
from aas_core_csharp_codegen.common import Identifier


class Test_ontology_ok(unittest.TestCase):
    def test_no_antecedents(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                '''\
                class Something:
                    pass
                '''))

        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = understand_hierarchy.symbol_table_to_ontology(symbol_table)
        assert errors is None, f"{errors=}"
        assert ontology is not None

        antecedents = ontology.list_antecedents(
            entity=symbol_table.must_find_entity(Identifier("Something")))

        antecedent_names = [entity.name for entity in antecedents]
        self.assertListEqual([], antecedent_names)

    def test_complex_graph(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                '''\
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
                '''))

        assert symbol_table is not None

        ontology, errors = understand_hierarchy.symbol_table_to_ontology(symbol_table)
        assert errors is None, f"{errors=}"
        assert ontology is not None

        antecedents = ontology.list_antecedents(
            entity=symbol_table.must_find_entity(Identifier("Something")))

        antecedent_names = [entity.name for entity in antecedents]

        self.assertListEqual(
            ['Another_grand_parent', 'Grand_parent', 'Another_parent',
             'Another_grand_parent', 'Grand_parent', 'Parent'],
            antecedent_names)


class Test_ontology_fail(unittest.TestCase):
    def test_duplicate_properties_in_antecedents(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                '''\
                @abstract
                class Abstract:
                    x: int

                @abstract
                class Something(Abstract):
                    x: int
                '''))
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = understand_hierarchy.symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "The property has already been defined "
            "in the antecedent entity Abstract: x",
            tests.common.most_underlying_message(errors[0]))

    def test_duplicate_methods_in_antecedents(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                '''\
                @abstract
                class Abstract:
                    def do_something(self) -> None:
                        pass

                @abstract
                class Something(Abstract):
                    def do_something(self) -> None:
                        pass
                '''))
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = understand_hierarchy.symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "The method has already been defined "
            "in the antecedent entity Abstract: do_something",
            tests.common.most_underlying_message(errors[0]))

    def test_missing_constructor_when_the_parent_has_one(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                '''\
                @abstract
                class Abstract:
                    def __init__(self, x: int) -> None:
                        pass

                class Something(Abstract):
                    pass
                '''))
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = understand_hierarchy.symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "The entity Something does not specify a constructor, "
            "but the antecedent entity Abstract specifies a constructor "
            "with arguments: self, x",
            tests.common.most_underlying_message(errors[0]))

    def test_cycle_inheritance(self) -> None:
        symbol_table, error = tests.common.parse_source(
            textwrap.dedent(
                '''\
                @abstract
                class Cycle(Something):
                    pass

                @abstract
                class Something(Cycle):
                    pass
                '''))
        assert error is None, f"{error=}"
        assert symbol_table is not None

        ontology, errors = understand_hierarchy.symbol_table_to_ontology(symbol_table)
        assert errors is not None and len(errors) == 1

        self.assertEqual(
            "Expected no cycles in the inheritance, "
            "but the entity Cycle has been observed in a cycle",
            tests.common.most_underlying_message(errors[0]))


class Test_against_real_meta_models(unittest.TestCase):
    def test_smoke_on_files(self) -> None:
        for meta_model_pth in tests.common.list_valid_meta_models_from_test_data():
            source = meta_model_pth.read_text()

            symbol_table, error = tests.common.parse_source(source)
            assert error is None, f"{meta_model_pth=}, {error=}"
            assert symbol_table is not None

            _, errors = understand_hierarchy.symbol_table_to_ontology(
                symbol_table)

            assert errors is None, f"{meta_model_pth=}, {errors=}"


if __name__ == "__main__":
    unittest.main()
