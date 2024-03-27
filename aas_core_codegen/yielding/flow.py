"""Provide  structures to model the control flow."""

from typing import Optional, Union, Final, Sequence

from icontract import require

from aas_core_codegen.common import Stripped


class Command:
    """
    Represent a command block to be executed which does not affect control flow.

    We refer to control flow here in terms of yielding. The command block *can* include
    statements changing the *execution* control flow as long as they do not affect
    the co-routines. For example, it can contain an if-statement which does not
    have any yield statements in its body.
    """

    def __init__(self, code: Stripped) -> None:
        """Initialize with the given values."""
        self.code = code


class IfTrue:
    """
    Represent an if-statement in the control flow.

    The condition should *not* contain any code that affects the control flow.
    """

    condition: Final[Stripped]
    body: Final[Sequence["Node"]]
    or_else: Final[Optional[Sequence["Node"]]]

    @require(
        lambda body: len(body) >= 1,
        "If-node should always execute something in the body. If the body is empty, "
        "this node needs to be reformulated",
    )
    def __init__(
        self,
        condition: str,
        body: Sequence["Node"],
        or_else: Optional[Sequence["Node"]] = None,
    ) -> None:
        """Initialize with the given values."""
        self.condition = Stripped(condition.strip())
        self.body = body
        self.or_else = or_else


class IfFalse:
    """
    Represent an if-statement with the negated condition in the control flow.

    The condition should *not* contain any code that affects the control flow.

    We distinguish between if-true and if-false so that we can avoid redundant
    double negations of the condition in the compiled code.
    """

    condition: Final[Stripped]
    body: Final[Sequence["Node"]]
    or_else: Final[Optional[Sequence["Node"]]]

    @require(
        lambda body: len(body) >= 1,
        "If-node should always execute something in the body. If the body is empty, "
        "this node needs to be reformulated",
    )
    def __init__(
        self,
        condition: str,
        body: Sequence["Node"],
        or_else: Optional[Sequence["Node"]] = None,
    ) -> None:
        """Initialize with the given values."""
        self.condition = Stripped(condition.strip())
        self.body = body
        self.or_else = or_else


class For:
    """
    Represent a for-loop in a control flow.

    The ``init``, ``condition`` and ``iteration`` should *not* contain any code that
    affects the control flow.
    """

    init: Final[Optional[Stripped]]
    condition: Final[Stripped]
    iteration: Final[Stripped]
    body: Final[Sequence["Node"]]

    def __init__(
        self,
        condition: str,
        iteration: str,
        body: Sequence["Node"],
        init: Optional[str] = None,
    ) -> None:
        """Initialize with the given values."""
        self.init = Stripped(init) if init is not None else None
        self.condition = Stripped(condition.strip())
        self.iteration = Stripped(iteration.strip())
        self.body = body


class While:
    """Represent a while-loop in a control flow."""

    condition: Final[Stripped]
    body: Final[Sequence["Node"]]

    def __init__(self, condition: str, body: Sequence["Node"]) -> None:
        """Initialize with the given values."""
        self.condition = Stripped(condition.strip())
        self.body = body


class Yield:
    """
    Represent the yield statement.

    Since we want to be as general as possible, we do not include a value to be
    yielded here, as we do not know *how* the compiled code should return the value.
    Therefore, this statement simply indicates that the control is yielded, not
    the value.
    """


Node = Union[Command, IfTrue, IfFalse, For, While, Yield]


def command_from_text(text: str) -> Command:
    """Strip the text and create a command out of the stripped text."""
    return Command(Stripped(text.strip()))
