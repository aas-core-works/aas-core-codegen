# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import io
import os
import pathlib
import unittest

import aas_core_meta.v3rc1
import aas_core_meta.v3rc2

from aas_core_codegen.smoke import main as smoke_main


class Test_against_recorded(unittest.TestCase):
    RERECORD = os.environ.get("AAS_CORE_CODEGEN_RERECORD", "").lower() in (
        "1",
        "true",
        "on",
    )

    def test_cases(self) -> None:
        repo_dir = pathlib.Path(os.path.realpath(__file__)).parent.parent.parent

        parent_case_dir = repo_dir / "test_data" / "smoke" / "test_main"
        assert parent_case_dir.exists() and parent_case_dir.is_dir(), parent_case_dir

        expected_dir = parent_case_dir / "expected"

        model_paths_of_the_expected = sorted(
            list(expected_dir.glob("**/*.py"))
            + [
                pathlib.Path(aas_core_meta.v3rc1.__file__),
                pathlib.Path(aas_core_meta.v3rc2.__file__),
            ]
        )

        for model_pth in model_paths_of_the_expected:
            assert model_pth.is_file(), f"{model_pth=}"

            stderr = io.StringIO()
            return_code = smoke_main.execute(model_path=model_pth, stderr=stderr)
            if return_code != 0:
                parts = [
                    f"Unexpected non-zero return code from the smoke script "
                    f"on {model_pth}: {return_code}"
                ]
                if stderr.getvalue():
                    parts.append(f"The captured STDERR was:\n{stderr.getvalue()}")

                raise AssertionError("\n\n".join(parts))

        unexpected_dir = parent_case_dir / "unexpected"

        for model_pth in sorted(unexpected_dir.glob("**/*.py")):
            stderr = io.StringIO()

            return_code = smoke_main.execute(model_path=model_pth, stderr=stderr)

            if return_code == 0:
                parts = [
                    f"Unexpected zero return code from the smoke script "
                    f"on {model_pth}: {return_code}"
                ]
                if stderr.getvalue():
                    parts.append(f"The captured STDERR was:\n{stderr.getvalue()}")

                raise AssertionError("\n\n".join(parts))

            if stderr.getvalue() == "":
                raise AssertionError(
                    f"Unexpected no STDERR from the smoke script on {model_pth}"
                )

            stderr_pth = model_pth.parent / "expected_stderr.txt"

            normalized_stderr = stderr.getvalue().replace(
                str(model_pth), f"<{model_pth.name}>"
            )

            if Test_against_recorded.RERECORD:
                stderr_pth.write_text(normalized_stderr, encoding="utf-8")
            else:
                self.assertEqual(
                    normalized_stderr,
                    stderr_pth.read_text(encoding="utf-8"),
                    stderr_pth,
                )


if __name__ == "__main__":
    unittest.main()
