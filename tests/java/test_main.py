# pylint: disable=missing-docstring

from typing import List
import contextlib
import io
import os
import pathlib
import tempfile
import unittest

import aas_core_meta.v3

import aas_core_codegen.main

import tests.common

AAS_TYPES = [
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

AAS_ENUMS = [
    "AasSubmodelElements",
    "AssetKind",
    "DataTypeDefXsd",
    "DataTypeIec61360",
    "Direction",
    "EntityType",
    "KeyTypes",
    "ModellingKind",
    "QualifierKind",
    "ReferenceTypes",
    "StateOfEvent",
]


def generate_files(types: List[str], enums: List[str]):
    _CONSTANTS = [pathlib.Path("constants/Constants.java")]
    _COPYING = [pathlib.Path("copying/Copying.java")]
    _ENHANCING = [pathlib.Path(f"enhancing/Enhanced{t}.java") for t in types] + [
        pathlib.Path("enhancing/Enhanced.java"),
        pathlib.Path("enhancing/Enhancer.java"),
        pathlib.Path("enhancing/Unwrapper.java"),
        pathlib.Path("enhancing/Wrapper.java"),
    ]
    # NOTE (empwilli 2024-03-26): we create generators only for types that have
    # non-mandatory attributes.
    _GENERATION = [
        pathlib.Path(f"generation/{t}Builder.java")
        for t in types
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
        [pathlib.Path(f"types/enums/{i}.java") for i in enums]
        + [pathlib.Path(f"types/impl/{t}.java") for t in types]
        + [pathlib.Path(f"types/model/I{t}.java") for t in types]
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

    return (
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
    _REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent
    PARENT_CASE_DIR = _REPO_DIR / "test_data" / "java" / "test_main"

    def test_against_meta_models(self) -> None:
        assert (
            Test_against_recorded.PARENT_CASE_DIR.exists()
            and Test_against_recorded.PARENT_CASE_DIR.is_dir()
        ), f"{Test_against_recorded.PARENT_CASE_DIR=}"

        # fmt: off
        test_cases = (
            tests.common.find_meta_models_in_parent_directory_of_test_cases_and_modules(
                parent_case_dir=Test_against_recorded.PARENT_CASE_DIR,
                aas_core_meta_modules=[aas_core_meta.v3]
            )
        )
        # fmt: on

        for test_case in test_cases:
            snippets_dir = test_case.case_dir / "input/snippets"
            assert snippets_dir.exists() and snippets_dir.is_dir(), snippets_dir

            expected_output_dir = test_case.case_dir / "expected_output"

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
                    model_path=test_case.model_path,
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

                if test_case.case_dir.name.endswith("aas_core_meta.v3"):
                    types = AAS_TYPES
                    enums = AAS_ENUMS
                else:
                    # TODO
                    types = []
                    enums = []

                for relevant_rel_pth in generate_files(types, enums):
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}"
                        )

                    if tests.common.RERECORD:
                        expected_pth.write_text(
                            output_pth.read_text(encoding="utf-8"), encoding="utf-8"
                        )
                    else:
                        self.assertEqual(
                            expected_pth.read_text(encoding="utf-8"),
                            output_pth.read_text(encoding="utf-8"),
                            f"The files {expected_pth} and {output_pth} do not match.",
                        )


if __name__ == "__main__":
    unittest.main()
