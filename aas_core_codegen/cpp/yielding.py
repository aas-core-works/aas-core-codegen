"""Generate the C++ code for linearized control flows."""

import io
from typing import Sequence, List, Optional

from aas_core_codegen.common import (
    Identifier,
    Stripped,
    pairwise,
    indent_but_first_line,
    assert_never,
)
from aas_core_codegen.yielding import flow as yielding_flow, linear as yielding_linear
from aas_core_codegen.cpp.common import INDENT as I, INDENT2 as II, INDENT3 as III
from aas_core_codegen.cpp import common as cpp_common


def _generate_subroutine_body(
    subroutine: yielding_linear.Subroutine,
    next_subroutine: Optional[yielding_linear.Subroutine],
    state_member: Identifier,
) -> Stripped:
    """Generate the body of the case block for the given subroutine."""
    blocks = []  # type: List[Stripped]

    for i, statement in enumerate(subroutine):
        if isinstance(statement, yielding_linear.Command):
            blocks.append(statement.code)

        elif isinstance(statement, yielding_linear.If):
            if statement.on_true is not None and statement.on_false is not None:
                condition = statement.condition
            elif statement.on_true is not None and statement.on_false is None:
                condition = statement.condition
            elif statement.on_true is None and statement.on_false is not None:
                condition = Stripped(f"!({statement.condition})")
            else:
                raise AssertionError("Unexpected if-statement without target")

            writer = io.StringIO()
            if "\n" in statement.condition or len(statement.condition) > 50:
                writer.write(
                    f"""\
if (
{I}{indent_but_first_line(condition, I)}
) {{
"""
                )
            else:
                writer.write(f"if ({condition}) {{\n")

            if statement.on_true is not None and statement.on_false is not None:
                writer.write(
                    f"""\
{I}{state_member} = {statement.on_true};
}} else {{
{I}{state_member} = {statement.on_false};
}}
continue;"""
                )
            elif statement.on_true is not None and statement.on_false is None:
                writer.write(
                    f"""\
{I}{state_member} = {statement.on_true};
{I}continue;
}}"""
                )
            elif statement.on_true is None and statement.on_false is not None:
                writer.write(
                    f"""\
{I}{state_member} = {statement.on_false};
{I}continue;
}}"""
                )
            else:
                raise AssertionError("Unexpected if-statement without target")

            blocks.append(Stripped(writer.getvalue()))

        elif isinstance(statement, yielding_linear.Jump):
            blocks.append(
                Stripped(
                    f"""\
{state_member} = {statement.target};
continue;"""
                )
            )

        elif isinstance(statement, yielding_linear.Yield):
            if next_subroutine is None:
                assert subroutine[0].label is not None

                blocks.append(
                    Stripped(
                        f"""\
{state_member} = {subroutine[0].label + 1};  // Invalidate state
return;"""
                    )
                )
            else:
                blocks.append(
                    Stripped(
                        f"""\
{state_member} = {next_subroutine[0].label};
return;"""
                    )
                )
        elif isinstance(statement, yielding_linear.Noop):
            if statement.comment is None:
                blocks.append(Stripped("// Noop"))
            else:
                blocks.append(
                    Stripped(cpp_common.non_documentation_comment(statement.comment))
                )
        else:
            assert_never(statement)

        if (
            i == len(subroutine) - 1
            and next_subroutine is None
            and isinstance(statement, yielding_linear.Command)
        ):
            assert subroutine[0].label is not None

            blocks.append(
                Stripped(
                    f"""\
// We invalidate the state since we reached the end of the routine.
{state_member} = {subroutine[0].label + 1};
return;"""
                )
            )

    return Stripped("\n\n".join(blocks))


def generate_execute_body(
    flow: Sequence[yielding_flow.Node], state_member: Identifier
) -> Stripped:
    """
    Generate the code of the ``Execute()`` method which executes the flow with yields.

    The member that holds the state to be executed is indicated by ``state_member``.
    Both the state member and the ``Execute()`` method are usually private.
    """
    if len(flow) == 0:
        return Stripped("// Intentionally empty.")

    subroutines = yielding_linear.linearize_to_subroutines(flow=flow)

    case_blocks = []  # type: List[Stripped]
    for subroutine, next_subroutine in pairwise(subroutines):
        case_body = _generate_subroutine_body(
            subroutine=subroutine,
            next_subroutine=next_subroutine,
            state_member=state_member,
        )
        case_blocks.append(
            Stripped(
                f"""\
case {subroutine[0].label}: {{
{I}{indent_but_first_line(case_body, I)}
}}"""
            )
        )

    last_subroutine = subroutines[-1]
    case_body = _generate_subroutine_body(
        subroutine=last_subroutine, next_subroutine=None, state_member=state_member
    )
    case_blocks.append(
        Stripped(
            f"""\
case {last_subroutine[0].label}: {{
{I}{indent_but_first_line(case_body, I)}
}}"""
        )
    )

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}throw std::logic_error(
{II}common::Concat(
{III}"Invalid {state_member}: ",
{III}std::to_string({state_member})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n\n".join(case_blocks)

    return Stripped(
        f"""\
while (true) {{
{I}switch ({state_member}) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
}}"""
    )
