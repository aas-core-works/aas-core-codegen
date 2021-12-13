"""Format the source code to have a consistent formatting throughout the code base."""
import argparse
import ast
import io
import pathlib
import sys
import textwrap
from typing import List, Iterator, Optional, Any, cast, Tuple, Sequence

import asttokens
import black
from icontract import require, ensure


def _is_return_error(node: ast.Return) -> bool:
    """Match ``return Error(...)``."""
    return (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == 'Error')


def _is_return_none_error(node: ast.Return) -> bool:
    """Match ``return None, Error(...)``."""
    return (
            isinstance(node.value, ast.Tuple)
            and len(node.value.elts) == 2
            and isinstance(node.value.elts[0], ast.Constant)
            and node.value.elts[0].value is None
            and isinstance(node.value.elts[1], ast.Call)
            and isinstance(node.value.elts[1].func, ast.Name)
            and node.value.elts[1].func.id == 'Error'
    )


class _ReturnError(ast.Return):
    """Represent a match of ``return Error(...)``."""

    @require(lambda node: _is_return_error(node))
    def __new__(cls, node: ast.Return) -> '_ReturnError':
        """Enforce pre-conditions."""
        return cast(_ReturnError, node)


class _ReturnNoneError(ast.Return):
    """Represent a match of ``return None, Error(...)``."""

    @require(lambda node: _is_return_none_error(node))
    def __new__(cls, node: ast.Return) -> '_ReturnNoneError':
        """Enforce pre-conditions."""
        return cast(_ReturnNoneError, node)


class _Visitor(ast.NodeVisitor):
    """Match all the return and append statements involving an Error."""

    #: Set if ``Error`` imported from ``aas_core_codegen.common``.
    #: Otherwise, we ignore reformatting the file.
    found_import_of_error: bool

    #: List of matches like ``return Error(...)``
    list_of_return_error: List[_ReturnError]

    # TODO: adapt once the classes are there
    #: List of matches like ``return None, Error(...)``
    list_of_return_none_error: List[ast.Return]

    # TODO: adapt once the classes are there
    #: List of matches like ``errors.append(Error(...))``
    list_of_append_error: List[ast.Call]

    def __init__(self) -> None:
        self.found_import_of_error = False
        self.list_of_return_error = []
        self.list_of_return_none_error = []
        self.list_of_append_error = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for name in node.names:
            assert isinstance(name, ast.alias)
            # Ignore ``from ... import ... as ...``
            if name.asname is not None:
                continue

            if name.name == 'Error' and node.module == 'aas_core_codegen.common':
                self.found_import_of_error = True

    def visit_Return(self, node: ast.Return) -> Any:
        if not self.found_import_of_error:
            return

        if _is_return_error(node):
            self.list_of_return_error.append(_ReturnError(node))
        elif _is_return_none_error(node):
            self.list_of_return_none_error.append(_ReturnNoneError(node))
        else:
            # Ignore the return statement as we do not know how to match it
            pass


class _Patch:
    """Represent a reformatting patch."""

    def __init__(self, start: int, end: int, new_text: str) -> None:
        """Initialize with the given values."""
        self.start = start
        self.end = end
        self.new_text = new_text


def _reformat_return_error(
        atok: asttokens.ASTTokens,
        return_error: _ReturnError
) -> _Patch:
    """Create a patch to reformat the statement returning an error."""
    error_call = return_error.value
    assert isinstance(error_call, ast.Call)
    print(f"ast.dump(error_node) is {ast.dump(error_call)!r}")  # TODO: debug

    node_arg = None  # type: Optional[ast.AST]
    message_arg = None  # type: Optional[ast.AST]
    underlying_arg = None  # type: Optional[ast.AST]

    # region Determine the arguments

    if len(error_call.args) >= 1:
        node_arg = error_call.args[0]

    if len(error_call.args) >= 2:
        message_arg = error_call.args[1]

    if len(error_call.args) >= 3:
        underlying_arg = error_call.args[2]

    for keyword in error_call.keywords:
        if keyword.arg == 'node':
            node_arg = keyword.value

        elif keyword.arg == 'message':
            message_arg = keyword.value

        elif keyword.arg == 'underlying':
            underlying_arg = keyword.value

    # endregion

    # Write all arguments as positional arguments, each on a separate line
    args = []  # type: List[ast.AST]
    if node_arg is not None:
        args.append(node_arg)

    if message_arg is not None:
        args.append(message_arg)

    if underlying_arg is not None:
        args.append(underlying_arg)

    reformatted_args = []  # type: List[str]
    for arg in args:
        arg_text = atok.get_text(arg)
        try:
            reformatted_arg = black.format_str(arg_text, mode=black.FileMode())
        except black.NothingChanged:
            reformatted_arg = arg_text

        reformatted_args.append(reformatted_arg)

    writer = io.StringIO()
    writer.write("return Error(\n")
    for i, reformatted_arg in enumerate(reformatted_args):
        writer.write(textwrap.indent(reformatted_arg, '    '))

        if i == len(reformatted_args) - 1:
            writer.write(')')
        else:
            writer.write(',\n')

    start, end = atok.get_text_range(return_error)
    return _Patch(start=start, end=end, new_text=writer.getvalue())


def _apply_patches(text: str, patches: Sequence[_Patch]) -> str:
    """Apply the patches in linear time complexity."""
    

def reformat(text: str) -> str:
    """
    Reformat the ``text`` with black and our custom rules.

    Return the formatted text, or error if any.
    """
    blacked = None  # type: Optional[str]
    try:
        blacked = black.format_file_contents(text, fast=False, mode=black.FileMode())
    except black.NothingChanged:
        return text

    assert blacked is not None

    atok = asttokens.ASTTokens(blacked, parse=True)

    visitor = _Visitor()
    visitor.visit(atok.tree)

    if not visitor.found_import_of_error:
        return blacked

    patches = []  # type: List[_Patch]
    for return_error in visitor.list_of_return_error:
        patches.append(_reformat_return_error(atok=atok, return_error=return_error))

    for return_none_error in visitor.list_of_return_none_error:
        patches.append(
            _reformat_return_none_error(
                atok=atok, return_none_error=return_none_error))

    for append_error in visitor.list_of_append_error:
        patches.append(
            _reformat_append_error(
                atok=atok, append_error=append_error))

    return _apply_patches(text=blacked, patches=patches)


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        help="Re-format the file(s) in-place; "
             "if not set, throws an error if one or more files diverge",
        action="store_true")
    parser.add_argument('paths', nargs='+', help="Files or directories to reformat")
    args = parser.parse_args()

    paths = [pathlib.Path(pth) for pth in args.paths]
    overwrite = bool(args.overwrite)

    def over_paths() -> Iterator[pathlib.Path]:
        """Iterate over ``paths`` and recurse into directories."""
        for pth in paths:
            if pth.is_file():
                yield pth
            elif pth.is_dir():
                for sub_pth in pth.glob("**/*.py"):
                    yield sub_pth
            else:
                raise RuntimeError(f"Unexpected neither file nor directory: {pth}")

    different_files = 0
    for pth in over_paths():
        text = None  # type: Optional[str]
        try:
            text = pth.read_text(encoding='utf-8')
        except Exception as err:
            print(f"Failed to read from {pth}: {err}", file=sys.stderr)
            return 1

        assert text is not None

        try:
            formatted = reformat(text=text)
        except Exception as err:
            print(f"Failed to re-format {pth}: {err}", file=sys.stderr)
            return 1

        if formatted != text:
            if overwrite:
                try:
                    pth.write_text(formatted, encoding='utf-8')
                except Exception as err:
                    print(f"Failed to write to {pth}: {err}", file=sys.stderr)
                    return 1

                print(f"Re-formatted: {pth}")

            else:
                different_files += 1
                print(f"Not formatted properly: {pth}", file=sys.stderr)

        if overwrite and different_files > 0:
            print(
                f"There were {different_files} which did not conform to "
                f"the formatting rules. Please consider "
                f"re-running ``{sys.executable} reformat.py --overwrite``.",
                file=sys.stderr)
            return 1

        return 0


if __name__ == "__main__":
    sys.exit(main())
