"""Run a smoke-test as a preliminary test that a meta-model is ready for generation."""

import argparse
import pathlib
import sys
from typing import TextIO, List

import aas_core_codegen
from aas_core_codegen import parse, run, intermediate, infer_for_schema
from aas_core_codegen.parse import retree as parse_retree, tree as parse_tree
from aas_core_codegen.common import LinenoColumner, Error
import aas_core_codegen.smoke

assert __doc__ == aas_core_codegen.smoke.__doc__


class _ParsePatternVisitor(parse_tree.Visitor):
    """Check that all the patterns could be successfully parsed."""

    def __init__(self) -> None:
        self.errors = []  # type: List[parse_retree.Error]

    def visit_joined_str(self, node: parse_tree.JoinedStr) -> None:
        """Check that the joined string is a valid regular expression."""
        _, error = parse_retree.parse(values=node.values)
        if error is not None:
            self.errors.append(error)

    def visit_constant(self, node: parse_tree.Constant) -> None:
        """Visit a constant."""
        if isinstance(node.value, str):
            _, error = parse_retree.parse(values=[node.value])
            if error is not None:
                self.errors.append(error)


def execute(model_path: pathlib.Path, stderr: TextIO) -> int:
    """Run the smoke test."""
    text = model_path.read_text(encoding="utf-8")

    # BEFORE-RELEASE (mristin, 2021-12-13):
    #  test all the following individual failure cases
    atok, parse_exception = parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            stderr.write(
                f"Failed to parse the meta-model {model_path}: "
                f"invalid syntax at line {parse_exception.lineno}\n"
            )
        else:
            stderr.write(
                f"Failed to parse the meta-model {model_path}: " f"{parse_exception}\n"
            )

        return 1

    import_errors = parse.check_expected_imports(atok=atok)
    if import_errors:
        run.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=stderr,
        )

        return 1

    lineno_columner = LinenoColumner(atok=atok)

    parsed_symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        run.write_error_report(
            message=f"Failed to construct the symbol table from {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        run.write_error_report(
            message=f"Failed to translate the parsed symbol table "
            f"to intermediate symbol table "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert ir_symbol_table is not None

    _, errors = infer_for_schema.infer_constraints_by_class(
        symbol_table=ir_symbol_table
    )
    if errors is not None:
        run.write_error_report(
            message=f"Failed to infer the constraints by class for the schemas "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )

        return 1

    errors = []
    for verification in ir_symbol_table.verification_functions:
        if isinstance(verification, intermediate.PatternVerification):
            for stmt in verification.parsed.body:
                visitor = _ParsePatternVisitor()
                visitor.visit(stmt)

                if len(visitor.errors) > 0:
                    for visitor_error in visitor.errors:
                        regex_line, pointer_line = parse_retree.render_pointer(
                            visitor_error.cursor
                        )

                        errors.append(
                            Error(
                                stmt.original_node,
                                (
                                    f"{visitor_error.message}\n"
                                    f"{regex_line}\n"
                                    f"{pointer_line}"
                                ),
                            )
                        )

    if len(errors) > 0:
        run.write_error_report(
            message=f"Failed to parse the regular expressions "
            f"in one or more pattern verification functions "
            f"based on {model_path}",
            errors=[lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )

        return 1

    return 0


def main(prog: str) -> int:
    """Execute the main routine."""
    # NOTE (mristin, 2022-03-28):
    # The module ``argparse`` is not flexible enough to understand special options such
    # as ``--version`` so we manually hard-wire.
    if "--version" in sys.argv and "--help" not in sys.argv:
        print(aas_core_codegen.__version__)
        return 0

    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--version", help="show the current version and exit", action="store_true"
    )
    args = parser.parse_args()

    return execute(model_path=pathlib.Path(args.model_path), stderr=sys.stderr)


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="aas-core-codegen-smoke")


if __name__ == "__main__":
    sys.exit(main(prog="aas-core-codegen-smoke"))
