"""Provide common functionality across different tests."""
import os
import pathlib
from typing import List, Tuple, Optional, Union, Sequence, Final

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


@require(lambda base_case_dir: base_case_dir.exists() and base_case_dir.is_dir())
def test_cases_from_base_case_dir(
    base_case_dir: pathlib.Path,
) -> List[TestCaseWithDirectoryAndMetaModel]:
    """
    Find meta-model files beneath the ``base_case_dir``.

    We resolve the meta-model source by checking for each test case directory if
    the file ``meta_model.py`` exists.

    :param base_case_dir: parent directory where test cases reside
    :return: list of found test cases
    """
    test_cases = []  # type: List[TestCaseWithDirectoryAndMetaModel]

    for case_dir in sorted(pth for pth in base_case_dir.iterdir() if pth.is_dir()):
        model_pth = case_dir / "meta_model.py"  # type: Optional[pathlib.Path]
        assert model_pth is not None

        if model_pth.exists():
            test_cases.append(
                TestCaseWithDirectoryAndMetaModel(
                    case_dir=case_dir, model_path=model_pth
                )
            )
            continue

    return test_cases


@require(lambda base_case_dir: base_case_dir.exists() and base_case_dir.is_dir())
def test_cases_from_real_world_models(
    base_case_dir: pathlib.Path, real_meta_model_paths: Sequence[pathlib.Path]
) -> List[TestCaseWithDirectoryAndMetaModel]:
    """
    Find the test cases for the given real-world models.

    The meta-model path will point to the real-world model, which is shared across many
    different tests, while the case directory will be situated beneath
    the ``base_case_dir`` corresponding to the file name of the real-world model.
    """
    return [
        TestCaseWithDirectoryAndMetaModel(
            case_dir=base_case_dir / model_pth.stem, model_path=model_pth
        )
        for model_pth in real_meta_model_paths
    ]


def _repo_root() -> pathlib.Path:
    return pathlib.Path(os.path.realpath(__file__)).parent.parent.parent


REAL_META_MODEL_PATHS: Final[Sequence[pathlib.Path]] = [
    _repo_root() / "dev/test_data/real_meta_models/aas_core_meta.v3.py"
]
