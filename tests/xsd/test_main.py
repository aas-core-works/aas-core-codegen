# pylint: disable=missing-docstring

import contextlib
import io
import os
import pathlib
import tempfile
import unittest

import xmlschema
import aas_core_meta.v3rc2

import aas_core_codegen.main
from aas_core_codegen.xsd import main as xsd_main


class Test_undo_escaping_x(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual("", xsd_main._undo_escaping_backslash_x_in_pattern(""))

    def test_no_escaped(self) -> None:
        self.assertEqual(
            "test me", xsd_main._undo_escaping_backslash_x_in_pattern("test me")
        )

    def test_only_escaped(self) -> None:
        self.assertEqual(
            "\xff", xsd_main._undo_escaping_backslash_x_in_pattern("\\xff")
        )

    def test_prefix(self) -> None:
        self.assertEqual(
            "A\xff", xsd_main._undo_escaping_backslash_x_in_pattern("A\\xff")
        )

    def test_suffix(self) -> None:
        self.assertEqual(
            "\xffB", xsd_main._undo_escaping_backslash_x_in_pattern("\\xffB")
        )

    def test_prefix_suffix(self) -> None:
        self.assertEqual(
            "A\xffB", xsd_main._undo_escaping_backslash_x_in_pattern("A\\xffB")
        )

    def test_multiple(self) -> None:
        self.assertEqual(
            "A\xf1B\xf2C",
            xsd_main._undo_escaping_backslash_x_in_pattern("A\\xf1B\\xf2C"),
        )

    def test_complex(self) -> None:
        pattern = (
            "([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+/([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+([ \t]*;"
            "[ \t]*([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+=(([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+|"
            '"(([\t !#-\\[\\]-~]|[\\x80-\\xff])|\\\\([\t !-~]|[\\x80-\\xff]))*"))*'
        )

        expected = (
            "([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+/([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+([ \t]*;"
            "[ \t]*([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+=(([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+|"
            '"(([\t !#-\\[\\]-~]|[\x80-\xff])|\\\\([\t !-~]|[\x80-\xff]))*"))*'
        )

        self.assertEqual(
            expected, xsd_main._undo_escaping_backslash_x_in_pattern(pattern)
        )


class Test_against_recorded(unittest.TestCase):
    RERECORD = os.environ.get("AAS_CORE_CODEGEN_RERECORD", "").lower() in (
        "1",
        "true",
        "on",
    )

    _REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent
    PARENT_CASE_DIR = _REPO_DIR / "test_data" / "xsd" / "test_main"

    def test_against_aas_core_meta(self) -> None:
        assert (
            Test_against_recorded.PARENT_CASE_DIR.exists()
            and Test_against_recorded.PARENT_CASE_DIR.is_dir()
        ), f"{Test_against_recorded.PARENT_CASE_DIR=}"

        for module in [aas_core_meta.v3rc2]:
            case_dir = Test_against_recorded.PARENT_CASE_DIR / module.__name__
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
                if Test_against_recorded.RERECORD:
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
                    target=aas_core_codegen.main.Target.XSD,
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

                if Test_against_recorded.RERECORD:
                    stdout_pth.write_text(normalized_stdout, encoding="utf-8")
                else:
                    self.assertEqual(
                        normalized_stdout,
                        stdout_pth.read_text(encoding="utf-8"),
                        stdout_pth,
                    )

                # BEFORE-RELEASE (mristin, 2021-12-13):
                #  check the remainder of the generated files
                for relevant_rel_pth in [
                    pathlib.Path("schema.xsd"),
                ]:
                    expected_pth = expected_output_dir / relevant_rel_pth
                    output_pth = output_dir / relevant_rel_pth

                    if not output_pth.exists():
                        raise FileNotFoundError(
                            f"The output file is missing: {output_pth}"
                        )

                    if Test_against_recorded.RERECORD:
                        expected_pth.write_text(
                            output_pth.read_text(encoding="utf-8"), encoding="utf-8"
                        )
                    else:
                        self.assertEqual(
                            expected_pth.read_text(encoding="utf-8"),
                            output_pth.read_text(encoding="utf-8"),
                            f"The files {expected_pth} and {output_pth} do not match.",
                        )

    def test_on_examples(self) -> None:  # pylint: disable=no-self-use
        assert (
            Test_against_recorded.PARENT_CASE_DIR.exists()
            and Test_against_recorded.PARENT_CASE_DIR.is_dir()
        ), f"{Test_against_recorded.PARENT_CASE_DIR=}"

        for case_dir in Test_against_recorded.PARENT_CASE_DIR.iterdir():
            assert case_dir.is_dir(), case_dir

            schema_pth = case_dir / "expected_output" / "schema.xsd"

            schema = xmlschema.XMLSchema(str(schema_pth))

            for data_pth in sorted(
                (case_dir / "examples" / "expected").glob("**/*.xml")
            ):
                try:
                    schema.validate(data_pth)
                except xmlschema.validators.exceptions.XMLSchemaValidationError as err:
                    raise AssertionError(
                        f"Failed to validate {data_pth} against {schema_pth}"
                    ) from err


if __name__ == "__main__":
    unittest.main()
