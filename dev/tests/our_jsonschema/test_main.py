# pylint: disable=missing-docstring

import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest
import warnings

import tests.common

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # NOTE (mristin, 2022-04-08):
    # We need to disable warnings. Jsonschema package at the latest version (4.4.0) has
    # a problem with JSON schema draft 2019-09 and crashes with an recursion error,
    # see: https://github.com/python-jsonschema/jsonschema/issues/847.
    #
    # We revert back to jsonschema 3.2.0, which can not handle 2019-09, but still seems
    # to validate correctly our examples.
    import jsonschema

import aas_core_codegen.main
import aas_core_codegen.jsonschema.main


class Test_against_recorded(unittest.TestCase):
    _REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent.parent
    PARENT_CASE_DIR = _REPO_DIR / "dev" / "test_data" / "jsonschema" / "test_main"

    def test_against_meta_models(self) -> None:
        test_cases = tests.common.test_cases_from_base_case_dir(
            base_case_dir=Test_against_recorded.PARENT_CASE_DIR
        ) + tests.common.test_cases_from_real_world_models(
            base_case_dir=Test_against_recorded.PARENT_CASE_DIR,
            real_meta_model_paths=tests.common.REAL_META_MODEL_PATHS,
        )

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
                    target=aas_core_codegen.main.Target.JSONSCHEMA,
                    snippets_dir=snippets_dir,
                    output_dir=output_dir,
                    cache_model=tests.common.CACHE_MAIN_MODELS,
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

                for relevant_rel_pth in [
                    pathlib.Path("schema.json"),
                ]:
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

    def test_on_examples(self) -> None:
        assert (
            Test_against_recorded.PARENT_CASE_DIR.exists()
            and Test_against_recorded.PARENT_CASE_DIR.is_dir()
        ), f"{Test_against_recorded.PARENT_CASE_DIR=}"

        for case_dir in Test_against_recorded.PARENT_CASE_DIR.iterdir():
            assert case_dir.is_dir(), case_dir

            schema_pth = case_dir / "expected_output" / "schema.json"

            with schema_pth.open("rt", encoding="utf-8") as fid:
                schema = json.load(fid)

            for data_pth in sorted(
                (case_dir / "examples" / "expected").glob("**/*.json")
            ):
                with data_pth.open("rt", encoding="utf-8") as fid:
                    instance = json.load(fid)

                try:
                    jsonschema.validate(instance=instance, schema=schema)
                except jsonschema.ValidationError as err:
                    raise AssertionError(
                        f"Failed to validate {data_pth} against {schema_pth}"
                    ) from err


class Test_pattern_transpilation(unittest.TestCase):
    def test_unescaped_above_ascii_character_in_bmp(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16("\ud7ff")
        self.assertEqual("\ud7ff", pattern)

    def test_escaped_above_ascii_character_in_bmp(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16("\\ud7ff")
        self.assertEqual("\\ud7ff", pattern)

    def test_unescaped_range_in_bmp(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16(
            "[\x20-\uD7FF]"
        )
        self.assertEqual("[\x20-\uD7FF]", pattern)

    def test_escaped_range_in_bmp(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16(
            "[\\x20-\\ud7ff]"
        )
        self.assertEqual("[\\x20-\\ud7ff]", pattern)

    def test_escaped_range_in_bmp_always_lowercase(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16(
            "[\\x20-\\uD7FF]"
        )
        self.assertEqual("[\\x20-\\ud7ff]", pattern)

    def test_unescaped_above_bmp(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16(
            "[\U00010000-\U0010FFFF]"
        )
        self.assertEqual(
            "(\\ud800[\\udc00-\\udfff]|[\\ud801-\\udbfe][\\udc00-\\udfff]"
            "|\\udbff[\\udc00-\\udfff])",
            pattern,
        )

    def test_escaped_above_bmp(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16(
            "[\\U00010000-\\U0010FFFF]"
        )
        self.assertEqual(
            "(\\ud800[\\udc00-\\udfff]|[\\ud801-\\udbfe][\\udc00-\\udfff]"
            "|\\udbff[\\udc00-\\udfff])",
            pattern,
        )

    def test_unescaped_special_ascii_characters(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16("[\t\n\r]")
        self.assertEqual("[\\t\\n\\r]", pattern)

    def test_escaped_special_ascii_characters(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16("[\\t\\n\\r]")
        self.assertEqual("[\\t\\n\\r]", pattern)

    def test_on_XML_string_pattern(self) -> None:
        pattern = aas_core_codegen.jsonschema.main.fix_pattern_for_utf16(
            r"^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*$"
        )
        self.assertEqual(
            "^([\\x09\\x0a\\x0d\\x20-\\ud7ff\\ue000-\\ufffd]|\\ud800[\\udc00-\\udfff]"
            "|[\\ud801-\\udbfe][\\udc00-\\udfff]|\\udbff[\\udc00-\\udfff])*$",
            pattern,
        )

        # NOTE (mristin, 2024-05-08):
        # We also test for the JSON representation to test against a possible bug
        # reported in:
        # https://github.com/admin-shell-io/aas-specs/pull/426 and
        # https://github.com/aas-core-works/aas-core-codegen/issues/485

        pattern_json = json.dumps(pattern)
        self.assertEqual(
            # NOTE (mristin, 2024-05-08):
            # Mind the ``r`` modifier for the string literals!
            r'"^([\\x09\\x0a\\x0d\\x20-\\ud7ff\\ue000-\\ufffd]'
            r"|\\ud800[\\udc00-\\udfff]|[\\ud801-\\udbfe][\\udc00-\\udfff]"
            r'|\\udbff[\\udc00-\\udfff])*$"',
            pattern_json,
        )


if __name__ == "__main__":
    unittest.main()
