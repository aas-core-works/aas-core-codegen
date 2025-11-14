"""Check the JSON schema against the given JSON file."""
import argparse
import json
import pathlib
import sys
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # NOTE (mristin):
    # We need to disable warnings. Jsonschema package at the latest version (4.4.0) has
    # a problem with JSON schema draft 2019-09 and crashes with a recursion error,
    # see: https://github.com/python-jsonschema/jsonschema/issues/847.
    #
    # We revert to jsonschema 3.2.0, which can not handle 2019-09, but still seems
    # to validate correctly our examples.
    import jsonschema


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model_path",
        help="Path to a model to be validated against the generated JSON schema",
        required=True,
    )
    parser.add_argument("--schema_path", help="Path to the JSON schema", required=True)
    args = parser.parse_args()
    model_path = pathlib.Path(args.model_path)
    schema_path = pathlib.Path(args.schema_path)

    if not model_path.exists():
        print(f"--model_path does not exist: {model_path}", file=sys.stderr)
        sys.exit(1)

    if not schema_path.exists():
        print(f"--schema_path does not exist: {schema_path}", file=sys.stderr)
        sys.exit(1)

    with schema_path.open("rt") as fid:
        schema = json.load(fid)

    with model_path.open("rt") as fid:
        instance = json.load(fid)

    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as err:
        raise AssertionError(
            f"Failed to validate {model_path} against {schema_path}"
        ) from err


if __name__ == "__main__":
    main()
