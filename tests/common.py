"""Provide common functionality across different tests."""
import os
import pathlib
from types import ModuleType
from typing import List, Tuple, Optional, Union, Sequence, MutableMapping, Final

import asttokens
from icontract import ensure, require

from aas_core_codegen import parse, intermediate
from aas_core_codegen.common import Error


# pylint: disable=missing-function-docstring


def most_underlying_messages(error_or_errors: Union[Error, Sequence[Error]]) -> str:
    """Find the "leaf" errors and render them as a new-line separated list."""
    if isinstance(error_or_errors, Error):
        errors = [error_or_errors]  # type: Sequence[Error]
    else:
        errors = error_or_errors

    most_underlying_errors = []  # type: List[Error]

    for error in errors:
        if error.underlying is None or len(error.underlying) == 0:
            most_underlying_errors.append(error)
            continue

        stack = error.underlying  # type: List[Error]

        while len(stack) > 0:
            top_error = stack.pop()

            if top_error.underlying is not None:
                stack.extend(top_error.underlying)

            if top_error.underlying is None or len(top_error.underlying) == 0:
                most_underlying_errors.append(top_error)

    return "\n".join(
        most_underlying_error.message
        for most_underlying_error in most_underlying_errors
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def parse_atok(
    atok: asttokens.ASTTokens,
) -> Tuple[Optional[parse.SymbolTable], Optional[Error]]:
    """Parse the ``atok``, an abstract syntax tree of a meta-model."""
    import_errors = parse.check_expected_imports(atok=atok)
    if len(import_errors) > 0:
        import_errors_str = "\n".join(
            f"* {import_error}" for import_error in import_errors
        )

        raise AssertionError(
            f"Unexpected imports in the source code:\n{import_errors_str}"
        )

    symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    return symbol_table, error


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def parse_source(source: str) -> Tuple[Optional[parse.SymbolTable], Optional[Error]]:
    """Parse the given source text into a symbol table."""
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception  # pylint: disable=raising-bad-type

    assert atok is not None

    return parse_atok(atok=atok)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def translate_source_to_intermediate(
    source: str,
) -> Tuple[Optional[intermediate.SymbolTable], Optional[Error]]:
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception  # pylint: disable=raising-bad-type

    assert atok is not None

    parsed_symbol_table, error = parse_atok(atok=atok)
    assert error is None, f"{most_underlying_messages(error)}"
    assert parsed_symbol_table is not None

    return intermediate.translate(parsed_symbol_table=parsed_symbol_table, atok=atok)


def must_translate_source_to_intermediate(
    source: str,
) -> intermediate.SymbolTable:
    atok, parse_exception = parse.source_to_atok(source=source)
    if parse_exception:
        raise parse_exception  # pylint: disable=raising-bad-type

    assert atok is not None

    parsed_symbol_table, error = parse_atok(atok=atok)
    assert error is None, f"{most_underlying_messages(error)}"
    assert parsed_symbol_table is not None

    symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table, atok=atok
    )
    assert (
        error is None
    ), f"Unexpected error when parsing the source: {most_underlying_messages(error)}"
    assert symbol_table is not None
    return symbol_table


#: If set, this environment variable indicates that the golden files should be
#: re-recorded instead of checked against.
RERECORD = os.environ.get("AAS_CORE_CODEGEN_RERECORD", "").lower() in (
    "1",
    "true",
    "on",
)


class TestCaseWithDirectoryAndMetaModel:
    """Represent a test case with files in a test directory and a meta-model."""

    #: Path to the expected files and other test data
    case_dir: Final[pathlib.Path]

    #: Path to the meta-model file corresponding to the test case
    model_path: Final[pathlib.Path]

    def __init__(self, case_dir: pathlib.Path, model_path: pathlib.Path) -> None:
        """Initialize with the given values."""
        self.case_dir = case_dir
        self.model_path = model_path


@require(lambda parent_case_dir: parent_case_dir.is_dir())
def find_meta_models_in_parent_directory_of_test_cases_and_modules(
    parent_case_dir: pathlib.Path, aas_core_meta_modules: Sequence[ModuleType]
) -> List[TestCaseWithDirectoryAndMetaModel]:
    """
    Find meta-model files both from one of the ``test_data`` subdirectories and from
    imported aas-core-meta modules.

    We have two sources of metamodels. The main metamodels come from
    aas-core-meta package. For regression tests or more localized tests, we want
    to test against much smaller metamodels which are stored locally, as the test
    data.

    We resolve the metamodel source like the following. We first check for each
    test case directory if the file ``meta_model.py`` exists. If it does not, we
    look up whether the name of the test case directory corresponds to a module
    name from aas-core-meta.

    :param aas_core_meta_modules: list of relevant modules from aas-core-meta
    :param parent_case_dir: parent directory where test cases reside
    :return: list of found test cases
    """
    module_name_to_path = dict()  # type: MutableMapping[str, pathlib.Path]
    for module in aas_core_meta_modules:
        assert (
            module.__file__ is not None
        ), f"Expected module {module} to have the ``__file__`` attribute set."
        module_name_to_path[module.__name__] = pathlib.Path(module.__file__)

    test_cases = []  # type: List[TestCaseWithDirectoryAndMetaModel]

    for case_dir in sorted(pth for pth in parent_case_dir.iterdir() if pth.is_dir()):
        model_pth = case_dir / "meta_model.py"  # type: Optional[pathlib.Path]
        assert model_pth is not None

        if model_pth.exists():
            test_cases.append(
                TestCaseWithDirectoryAndMetaModel(
                    case_dir=case_dir, model_path=model_pth
                )
            )
            continue

        model_pth = module_name_to_path.get(case_dir.name, None)
        if model_pth is None:
            raise FileNotFoundError(
                f"We could not resolve the metamodel for the test case "
                f"{case_dir}. Neither meta_model.py exists in it, nor does "
                f"it correspond to any module "
                f"among {[module.__name__ for module in aas_core_meta_modules]!r}."
            )

        if not model_pth.exists():
            raise FileNotFoundError(
                f"The metamodel corresponding to the test case {case_dir} "
                f"does not exist: {model_pth}"
            )

        test_cases.append(
            TestCaseWithDirectoryAndMetaModel(case_dir=case_dir, model_path=model_pth)
        )

    return test_cases
