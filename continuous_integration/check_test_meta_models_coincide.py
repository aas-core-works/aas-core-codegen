"""
Check that the test meta-models coincide.

The meta-models are grouped by the version. All the meta-models within a group must
coincide.
"""

import argparse
import collections
import difflib
import os
import pathlib
import sys

_REPO_DIR = pathlib.Path(os.path.realpath(__file__)).parent.parent

META_MODEL_GROUPS = collections.OrderedDict(
    [
        (
            "V3RC01",
            [
                _REPO_DIR / "test_data/jsonschema/test_main/v3rc1/input/meta_model.py",
                _REPO_DIR / "test_data/rdf_shacl/test_main/v3rc1/input/meta_model.py",
                _REPO_DIR / "test_data/smoke/test_main/expected/v3rc1.py",
            ],
        ),
        (
            "V3RC02",
            [
                _REPO_DIR / "test_data/csharp/test_main/v3rc2/input/meta_model.py",
                (
                    _REPO_DIR / "test_data/intermediate/"
                    "expected/real_meta_models/v3rc2/meta_model.py"
                ),
                _REPO_DIR / "test_data/jsonschema/test_main/v3rc2/input/meta_model.py",
                (
                    _REPO_DIR / "test_data/parse/"
                    "expected/real_meta_models/v3rc2/meta_model.py"
                ),
                _REPO_DIR / "test_data/smoke/test_main/expected/v3rc2.py",
            ],
        ),
    ]
)


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    for version, group in META_MODEL_GROUPS.items():
        assert len(group) >= 1, f"At least one path expected in the group {version!r}."

        expected = group[0].read_text(encoding="utf-8").splitlines()
        for pth in group[1:]:
            got = pth.read_text(encoding="utf-8").splitlines()
            if expected != got:
                print(f"The files {group[0]} and {pth} do not match:", file=sys.stderr)
                diff = difflib.context_diff(
                    expected, got, fromfile=str(group[0]), tofile=str(pth)
                )

                for line in diff:
                    print(line, file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
