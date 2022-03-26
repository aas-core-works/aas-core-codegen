"""
Copy one meta-model over different locations in the ``test_data`` to sync them.

This is practical if you are developing and polishing a meta-model at the same time
and would like to finally propagate the changes once done.

The meta-models are grouped by version. You pick a "golden" meta-model from a group and
the remaining models in the group are synced. Meta-models from the other groups are left
unchanged.
"""

import argparse
import os
import pathlib
import shlex
import shutil
import sys

import continuous_integration.check_test_meta_models_coincide


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model_path",
        help="path to the golden meta-model which should be synced",
        required=True,
    )
    args = parser.parse_args()

    model_pth = pathlib.Path(os.path.realpath(args.model_path))

    choices = [
        pth
        for group in (
            continuous_integration.check_test_meta_models_coincide.META_MODEL_GROUPS.values()
        )
        for pth in group
    ]

    if model_pth not in choices:
        cwd = pathlib.Path(os.getcwd())
        choices_joined = "\n".join(
            str(pth.relative_to(cwd)) if cwd in pth.parents else str(pth)
            for pth in choices
        )

        print(
            f"The --model_path {shlex.quote(str(model_pth))} is not specified in "
            f"any of the groups. The specified model paths are:\n{choices_joined}",
            file=sys.stderr,
        )
        return 1

    if not model_pth.exists():
        print(f"The model path does not exist: {model_pth}", file=sys.stderr)
        return 1

    if not model_pth.is_file():
        print(f"The model path does not point to a file: {model_pth}", file=sys.stderr)
        return 1

    found = False
    for (
        group
    ) in (
        continuous_integration.check_test_meta_models_coincide.META_MODEL_GROUPS.values()
    ):
        if model_pth in group:
            found = True

            for pth in group:
                if pth == model_pth:
                    continue
                else:
                    # noinspection PyBroadException
                    try:
                        shutil.copy(src=str(model_pth), dst=str(pth))
                    except Exception as exception:
                        print(
                            f"Failed to copy the golden model {model_pth} "
                            f"to {pth}: {exception}",
                            file=sys.stderr,
                        )
                        return 1
    assert found, (
        "We should have found the model in the groups; "
        "otherwise our choices in the specification of the argparse are not correct."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
