import os
import pathlib
import textwrap
import unittest
from typing import Tuple, Optional

from icontract import ensure

import tests.common
from aas_core_csharp_codegen import intermediate, parse
from aas_core_csharp_codegen.common import Error, Identifier
import aas_core_csharp_codegen.understand.constructor as understand_constructor
import aas_core_csharp_codegen.understand.hierarchy as understand_hierarchy


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def translate_source(
        source: str
) -> Tuple[Optional[intermediate.SymbolTable], Optional[Error]]:
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception

    assert atok is not None

    parsed_symbol_table, error = tests.common.parse_atok(atok=atok)
    assert error is None, f"{error=}"
    assert parsed_symbol_table is not None

    ontology, errors = understand_hierarchy.symbol_table_to_ontology(
        symbol_table=parsed_symbol_table)
    assert errors is None, f"{errors=}"
    assert ontology is not None

    constructor_table, error = understand_constructor.understand_all(
        symbol_table=parsed_symbol_table,
        atok=atok)

    assert error is None, f"{error=}"
    assert constructor_table is not None

    return intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        ontology=ontology,
        constructor_table=constructor_table,
        atok=atok
    )


class Test_in_lining_of_constructor_statements(unittest.TestCase):
    def test_case(self) -> None:
        source = textwrap.dedent("""\
            @abstract
            class VeryAbstract:
                some_property: int
            
                @require(lambda some_property: some_property > 0)
                def __init__(self, some_property: int) -> None:
                    self.some_property = some_property
            
            
            @abstract
            class Abstract(VeryAbstract):
                another_property: int
            
                @require(lambda another_property: another_property > 0)
                def __init__(self, some_property: int, another_property: int) -> None:
                    VeryAbstract.__init__(self, some_property)
                    self.another_property = another_property
                    
            class Concrete(Abstract):
                yet_another_property: int
            
                @require(lambda yet_another_property: yet_another_property > 0)
                def __init__(
                        self, 
                        some_property: int, 
                        another_property: int,
                        yet_another_property: int
                ) -> None:
                    Abstract.__init__(self, some_property, another_property)
                    self.yet_another_property = yet_another_property
            """)

        symbol_table, error = translate_source(source=source)
        assert error is None, f"{error=}"

        assert symbol_table is not None

        concrete = symbol_table.must_find(Identifier('Concrete'))
        assert isinstance(concrete, intermediate.Class)

        self.assertEqual(
            ['some_property', 'another_property', 'yet_another_property'],
            [stmt.name for stmt in concrete.constructor.statements])


class Test_against_recorded(unittest.TestCase):
    # Set this variable to True if you want to re-record the test data,
    # without any checks
    RERECORD = True  # TODO: undo

    def test_cases(self) -> None:
        this_dir = pathlib.Path(os.path.realpath(__file__)).parent
        test_cases_dir = this_dir.parent / "test_data/test_intermediate"

        assert test_cases_dir.exists(), f"{test_cases_dir=}"
        assert test_cases_dir.is_dir(), f"{test_cases_dir=}"

        for source_pth in test_cases_dir.glob("**/source.py"):
            case_dir = source_pth.parent

            expected_symbol_table_pth = case_dir / "expected_symbol_table.txt"
            expected_error_pth = case_dir / "expected_error.txt"

            source = source_pth.read_text()
            symbol_table, error = translate_source(source=source)

            symbol_table_str = (
                "" if symbol_table is None
                else intermediate.dump(symbol_table)
            )

            error_str = (
                "" if error is None
                else tests.common.most_underlying_message(error)
            )

            if Test_against_recorded.RERECORD:
                expected_symbol_table_pth.write_text(symbol_table_str)
                expected_error_pth.write_text(error_str)
            else:
                expected_symbol_table_str = expected_symbol_table_pth.read_text()
                self.assertEqual(
                    expected_symbol_table_str, symbol_table_str,
                    f"{case_dir=}, {error=}")

                expected_error_str = expected_error_pth.read_text()
                self.assertEqual(expected_error_str, error_str, f"{case_dir=}")



if __name__ == "__main__":
    unittest.main()
