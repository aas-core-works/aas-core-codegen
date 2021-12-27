#!/usr/bin/env python3

"""Check that the distribution and aas_core_codegen/__init__.py are in sync."""
import os
import pathlib
import subprocess
import sys
from typing import Optional, Dict

import aas_core_codegen


def main() -> int:
    """Execute the main routine."""
    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    setup_py_pth = repo_root / "setup.py"
    if not setup_py_pth.exists():
        raise RuntimeError(f"Could not find the setup.py: {setup_py_pth}")

    success = True

    ##
    # Check basic fields
    ##

    setup_py_map = dict()  # type: Dict[str, str]

    fields = ["version", "author", "license", "description"]
    for field in fields:
        out = subprocess.check_output(
            [sys.executable, str(repo_root / "setup.py"), f"--{field}"],
            encoding="utf-8",
        ).strip()

        setup_py_map[field] = out

    if setup_py_map["version"] != aas_core_codegen.__version__:
        print(
            f"The version in the setup.py is {setup_py_map['version']}, "
            f"while the version in aas_core_codegen/__init__.py is: "
            f"{aas_core_codegen.__version__}",
            file=sys.stderr,
        )
        success = False

    if setup_py_map["author"] != aas_core_codegen.__author__:
        print(
            f"The author in the setup.py is {setup_py_map['author']}, "
            f"while the author in aas_core_codegen/__init__.py is: "
            f"{aas_core_codegen.__author__}",
            file=sys.stderr,
        )
        success = False

    if setup_py_map["license"] != aas_core_codegen.__license__:
        print(
            f"The license in the setup.py is {setup_py_map['license']}, "
            f"while the license in aas_core_codegen/__init__.py is: "
            f"{aas_core_codegen.__license__}",
            file=sys.stderr,
        )
        success = False

    if setup_py_map["description"] != aas_core_codegen.__doc__:
        print(
            f"The description in the setup.py is {setup_py_map['description']}, "
            f"while the description in aas_core_codegen/__init__.py is: "
            f"{aas_core_codegen.__doc__}",
            file=sys.stderr,
        )
        success = False

    ##
    # Classifiers need special attention as there are multiple.
    ##

    # This is the map from the distribution to expected status in __init__.py.
    status_map = {
        "Development Status :: 1 - Planning": "Planning",
        "Development Status :: 2 - Pre-Alpha": "Pre-Alpha",
        "Development Status :: 3 - Alpha": "Alpha",
        "Development Status :: 4 - Beta": "Beta",
        "Development Status :: 5 - Production/Stable": "Production/Stable",
        "Development Status :: 6 - Mature": "Mature",
        "Development Status :: 7 - Inactive": "Inactive",
    }

    classifiers = (
        subprocess.check_output(
            [sys.executable, str(setup_py_pth), f"--classifiers"], encoding="utf-8"
        )
        .strip()
        .splitlines()
    )

    status_classifier = None  # type: Optional[str]
    for classifier in classifiers:
        if classifier in status_map:
            status_classifier = classifier
            break

    if status_classifier is None:
        print(
            f"Expected a status classifier in setup.py "
            f"(e.g., 'Development Status :: 3 - Alpha'), but found none.",
            file=sys.stderr,
        )
        success = False
    else:
        expected_status_in_init = status_map[status_classifier]

        if expected_status_in_init != aas_core_codegen.__status__:
            print(
                f"Expected status {expected_status_in_init} "
                f"according to setup.py in aas_core_codegen/__init__.py, "
                f"but found: {aas_core_codegen.__status__}"
            )
            success = False

    if not success:
        return -1

    return 0


if __name__ == "__main__":
    sys.exit(main())
