# pylint: disable=missing-docstring

import contextlib
import io
import os
import pathlib
import tempfile
import unittest

import aas_core_meta.v3

import aas_core_codegen.main

import tests.common

_TYPES = [
    "AdministrativeInformation",
    "AnnotatedRelationshipElement",
    "AssetAdministrationShell",
    "AssetInformation",
    "BasicEventElement",
    "Blob",
    "Capability",
    "ConceptDescription",
    "DataSpecificationIec61360",
    "EmbeddedDataSpecification",
    "Entity",
    "Environment",
    "EventPayload",
    "Extension",
    "File",
    "Key",
    "LangStringDefinitionTypeIec61360",
    "LangStringNameType",
    "LangStringPreferredNameTypeIec61360",
    "LangStringShortNameTypeIec61360",
    "LangStringTextType",
    "LevelType",
    "MultiLanguageProperty",
    "Operation",
    "OperationVariable",
    "Property",
    "Qualifier",
    "Range",
    "ReferenceElement",
    "Reference",
    "RelationshipElement",
    "Resource",
    "SpecificAssetId",
    "SubmodelElementCollection",
    "SubmodelElementList",
    "Submodel",
    "ValueList",
    "ValueReferencePair",
]

_CONSTANTS = [pathlib.Path("constants/Constants.java")]
_COPYING = [pathlib.Path("copying/Copying.java")]
_ENHANCING = [pathlib.Path(f"enhancing/Enhanced{t}.java") for t in _TYPES] + [
    pathlib.Path("enhancing/Enhanced.java"),
    pathlib.Path("enhancing/Enhancer.java"),
    pathlib.Path("enhancing/Unwrapper.java"),
    pathlib.Path("enhancing/Wrapper.java"),
]
# NOTE (empwilli 2024-03-26): we create generators only for types that have
# non-mandatory attributes.
_GENERATION = [
    pathlib.Path(f"generation/{t}Builder.java")
    for t in _TYPES
    if t
    not in (
        "EmbeddedDataSpecification",
        "Key",
        "LangStringDefinitionTypeIec61360",
        "LangStringNameType",
        "LangStringPreferredNameTypeIec61360",
        "LangStringShortNameTypeIec61360",
        "LangStringTextType",
        "LevelType",
        "OperationVariable",
        "ValueList",
        "ValueReferencePair",
    )
]
_JSONIZATION = [pathlib.Path("jsonization/Jsonization.java")]
_REPORTING = [pathlib.Path("reporting/Reporting.java")]
_STRINGIFICATION = [pathlib.Path("stringification/Stringification.java")]
_VERIFICATION = [pathlib.Path("verification/Verification.java")]
_STRUCTURE = (
    [
        pathlib.Path("types/enums/AasSubmodelElements.java"),
        pathlib.Path("types/enums/AssetKind.java"),
        pathlib.Path("types/enums/DataTypeDefXsd.java"),
        pathlib.Path("types/enums/DataTypeIec61360.java"),
        pathlib.Path("types/enums/Direction.java"),
        pathlib.Path("types/enums/EntityType.java"),
        pathlib.Path("types/enums/KeyTypes.java"),
        pathlib.Path("types/enums/ModellingKind.java"),
        pathlib.Path("types/enums/QualifierKind.java"),
        pathlib.Path("types/enums/ReferenceTypes.java"),
        pathlib.Path("types/enums/StateOfEvent.java"),
    ]
    + [pathlib.Path(f"types/impl/{t}.java") for t in _TYPES]
    + [pathlib.Path(f"types/model/I{t}.java") for t in _TYPES]
)
_VISITATION = [
    pathlib.Path("visitation/AbstractTransformer.java"),
    pathlib.Path("visitation/AbstractTransformerWithContext.java"),
    pathlib.Path("visitation/AbstractVisitor.java"),
    pathlib.Path("visitation/AbstractVisitorWithContext.java"),
    pathlib.Path("visitation/ITransformer.java"),
    pathlib.Path("visitation/ITransformerWithContext.java"),
    pathlib.Path("visitation/IVisitor.java"),
    pathlib.Path("visitation/IVisitorWithContext.java"),
    pathlib.Path("visitation/VisitorThrough.java"),
]
XMLIZATION = [pathlib.Path("xmlization/Xmlization.java")]

GENERATED_FILES = (
    _CONSTANTS
    + _COPYING
    + _ENHANCING
    + _GENERATION
    + _JSONIZATION
    + _REPORTING
    + _STRINGIFICATION
    + _VERIFICATION
    + _STRUCTURE
    + _VISITATION
)


class Test_against_recorded(unittest.TestCase):
    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "test_data" / "java" / "test_main"
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        for module in [aas_core_meta.v3]:
            case_dir = parent_case_dir / module.__name__
            assert case_dir.is_dir(), case_dir

            assert (
                module.__file__ is not None
            ), f"Expected the module {module!r} to have a __file__, but it has None"
            model_pth = pathlib.Path(module.__file__)
            assert model_pth.exists() and model_pth.is_file(), model_pth

            snippets_dir = case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = case_dir / "expected_output"

            with contextlib.ExitStack() as exit_stack:
                if tests.common.RERECORD:
                    output_dir = expected_output_dir
                    expected_output_dir.mkdir(exist_ok=True, parents=True)
                else:
                    assert (
                        expected_output_dir.exists() and expected_output_dir.is_dir()
                    ), expected_output_dir

                    # pylint: disable=consider-using-with
                    tmp_dir = tempfile.TemporaryDirectory()
                    exit_stack.push(tmp_dir)
                    output_dir = pathlib.Path(tmp_dir.name)

                params = aas_core_codegen.main.Parameters(
                    model_path=model_pth,
                    target=aas_core_codegen.main.Target.JAVA,
                    snippets_dir=snippets_dir,
                    output_dir=output_dir,
                )

                stdout = io.StringIO()
                stderr = io.StringIO()

                return_code = aas_core_codegen.main.execute(
                    params=params, stdout=stdout, stderr=stderr
                )

                if stderr.getvalue() != "":
                    raise AssertionError(
                        f"Expected no stderr on valid models, but got:\n"
                        f"{stderr.getvalue()}"
                    )

                self.assertEqual(
                    0, return_code, "Expected 0 return code on valid models"
                )

                stdout_pth = expected_output_dir / "stdout.txt"
                normalized_stdout = stdout.getvalue().replace(
                    str(output_dir), "<output dir>"
                )

                if tests.common.RERECORD:
                    stdout_pth.write_text(normalized_stdout, encoding="utf-8")
                else:
                    self.assertEqual(
                        normalized_stdout,
                        stdout_pth.read_text(encoding="utf-8"),
                        stdout_pth,
                    )

                for relevant_rel_pth in GENERATED_FILES:
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}"
                        )

                    try:
                        output = output_pth.read_text(encoding="utf-8")
                    except Exception as exception:
                        raise RuntimeError(
                            f"Failed to read the output from {output_pth}"
                        ) from exception

                    if tests.common.RERECORD:
                        expected_pth.write_text(output, encoding="utf-8")
                    else:
                        try:
                            expected_output = expected_pth.read_text(encoding="utf-8")
                        except Exception as exception:
                            raise RuntimeError(
                                f"Failed to read the expected output "
                                f"from {expected_pth}"
                            ) from exception

                        self.assertEqual(
                            expected_output,
                            output,
                            f"The files {expected_pth} and {output_pth} do not match.",
                        )


if __name__ == "__main__":
    unittest.main()
