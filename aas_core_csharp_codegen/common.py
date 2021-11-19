"""Provide common functions and types for the code generation."""
import ast
import io
import re
import textwrap
from typing import (
    Optional,
    Tuple,
    cast,
    List,
    overload,
    Union,
    Iterator,
    Sequence,
    NoReturn, )

import asttokens
from icontract import require, DBC, ensure
import inflect

IDENTIFIER_RE = re.compile(r"[a-zA-Z_][a-zA-Z_0-9]*")


class Identifier(DBC, str):
    """Represent an identifier."""

    @require(lambda value: IDENTIFIER_RE.fullmatch(value))
    def __new__(cls, value: str) -> "Identifier":
        return cast(Identifier, value)


class Error:
    """
    Represent an unexpected input.

    For example, the code of the meta-model can be a valid Python code, but we
    can only process a subset of language constructs.
    """

    def __init__(
            self, node: Optional[ast.AST], message: str,
            underlying: Optional[List["Error"]] = None
    ) -> None:
        self.node = node
        self.message = message
        self.underlying = underlying

    def __repr__(self) -> str:
        return (
            f"Error("
            f"node={self.node!r}, "
            f"message={self.message!r}, "
            f"underlying={self.underlying!r})"
        )


class LinenoColumner:
    """Map the source code to line number and column for precise error messages."""

    def __init__(self, atok: asttokens.ASTTokens) -> None:
        positions = []  # type: List[Tuple[int, int]]
        lineno = 1
        column = 0
        for character in atok.get_text(atok.tree):
            if character == "\n":
                column = 1
                lineno += 1
            else:
                column += 1

            positions.append((lineno, column))

        self.atok = atok
        self.positions = positions

    def error_message(self, error: Error) -> str:
        """Generate the error message based on the unexpected observation."""
        prefix = ""
        if error.node is not None:
            start, _ = self.atok.get_text_range(node=error.node)
            lineno, column = self.positions[start]

            prefix = f"At line {lineno} and column {column}: "

        if error.underlying is None or len(error.underlying) == 0:
            return f"{prefix}{error.message}"
        else:
            writer = io.StringIO()
            writer.write(f"{prefix}{error.message}\n")
            for i, underlying_error in enumerate(error.underlying):
                if i > 0:
                    writer.write("\n")
                indented = textwrap.indent(self.error_message(underlying_error), "  ")
                writer.write(indented)

            return writer.getvalue()


class Lines(DBC):
    """Represent a sequence of text lines."""

    # fmt: off
    @require(
        lambda lines:
        all('\n' not in line and '\r' not in line for line in lines)
    )
    # fmt: on
    def __new__(cls, lines: Sequence[str]) -> "Lines":
        r"""
        Ensure the properties on the ``lines``.

        Please make sure that you transfer the "ownership" immediately to Lines
        and don't modify the original list of strings any more:

        .. code-block:: python

            ##
            # OK
            ##

            lines = Lines(some_text.splitlines())

            ##
            # Not OK
            ##

            some_lines = some_text.splitlines()
            lines = Lines(some_lines)
            # ... do something assuming ``lines`` is immutable ...

            some_lines[0] = "This will break \n your logic"
            # ERROR! lines[0] now contains a new-line which is unexpected!

        """
        return cast(Lines, lines)

    def __add__(self, other: "Lines") -> "Lines":
        """Concatenate two list of lines."""
        raise NotImplementedError("Only for type annotations")

    # pylint: disable=function-redefined

    @overload
    def __getitem__(self, index: int) -> str:
        """Get the item at the given integer index."""
        raise NotImplementedError("Only for type annotations")

    @overload
    def __getitem__(self, index: slice) -> "Lines":
        """Get the slice of the lines."""
        raise NotImplementedError("Only for type annotations")

    def __getitem__(self, index: Union[int, slice]) -> Union[str, "Lines"]:
        """Get the line(s) at the given index."""
        raise NotImplementedError("Only for type annotations")

    def __len__(self) -> int:
        """Return the number of the lines."""
        raise NotImplementedError("Only for type annotations")

    def __iter__(self) -> Iterator[str]:
        """Iterate over the lines."""
        raise NotImplementedError("Only for type annotations")


def assert_never(value: NoReturn) -> NoReturn:
    """
    Signal to mypy to perform an exhaustive matching.

    Please see the following page for more details:
    https://hakibenita.com/python-mypy-exhaustive-checking
    """
    assert False, f"Unhandled value: {value} ({type(value).__name__})"


class Rstripped(str):
    """
    Represent a block of text without trailing whitespace.

    The block can be both single-line or multi-line.
    """

    @require(
        lambda block:
        not block.endswith('\n')
        and not block.endswith(' ')
        and not block.endswith('\t')
    )
    def __new__(cls, block: str) -> 'Rstripped':
        return cast(Rstripped, block)


class Stripped(Rstripped):
    """
    Represent a block of text without leading and trailing whitespace.

    The block of text can be both single-line and multi-line.
    """

    # fmt: off
    @require(
        lambda block:
        not block.startswith('\n')
        and not block.startswith(' ')
        and not block.startswith('\t')
    )
    @require(
        lambda block:
        not block.endswith('\n')
        and not block.endswith(' ')
        and not block.endswith('\t')
    )
    # fmt: on
    def __new__(cls, block: str) -> 'Stripped':
        return cast(Stripped, block)


def indent_but_first_line(text: str, indention: str) -> str:
    """
    Indent all but the first of the given ``text`` by ``indention``.

    For example, this helps you insert indented blocks into formatted string literals.
    """
    return "\n".join(
        indention + line if i > 0 else line
        for i, line in enumerate(text.splitlines())
    )


_INFLECT_ENGINE = inflect.engine()


@ensure(lambda identifier, result: plural_to_singular(result) == identifier)
def singular_to_plural(identifier: Identifier) -> Identifier:
    """Translate the singular form of the identifier to its plural form."""
    text = identifier.replace('_', ' ')

    if text == 'permissions per object':
        result = 'permissions per objects'
    elif text == 'bill of material item':
        result = 'bill of material'
    elif text == 'is case of':
        result = 'is cases of'
    else:
        result = _INFLECT_ENGINE.plural(text)

    return Identifier('_'.join(result.split(' ')))


@ensure(lambda identifier, result: singular_to_plural(result) == identifier)
def plural_to_singular(identifier: Identifier) -> Identifier:
    """Translate the plural form of the identifier to its singular form."""
    text = identifier.replace('_', ' ')

    if text == 'permissions per objects':
        result = 'permissions per object'
    elif text == 'bill of material':
        result = 'bill of material item'
    elif text == 'is cases of':
        result = 'is case of'
    else:
        result = _INFLECT_ENGINE.singular_noun(text)

    if result is False:
        raise RuntimeError(f"Failed to find the singular noun of: {identifier=}")

    assert isinstance(result, str)
    return Identifier('_'.join(result.split(' ')))
