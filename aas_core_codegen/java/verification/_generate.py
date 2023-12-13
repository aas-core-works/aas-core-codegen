"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
from typing import (
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from icontract import ensure

from aas_core_codegen import (
    intermediate,
    specific_implementations,
)
from aas_core_codegen.common import (
    assert_never,
    Error,
    Identifier,
    Stripped,
)
from aas_core_codegen.java import (
    common as java_common,
    description as java_description,
    naming as java_naming,
)
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
)
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference
from aas_core_codegen.parse import tree as parse_tree, retree as parse_retree

# region Verify


def verify(
    spec_impls: specific_implementations.SpecificImplementations,
    verification_functions: Sequence[intermediate.Verification],
) -> Optional[List[str]]:
    """Verify all the implementation snippets related to verification."""
    errors = []  # type: List[str]

    expected_keys = []  # type: List[specific_implementations.ImplementationKey]

    for func in verification_functions:
        if isinstance(func, intermediate.ImplementationSpecificVerification):
            expected_keys.append(
                specific_implementations.ImplementationKey(
                    f"Verification/{func.name}.java"
                ),
            )

    for key in expected_keys:
        if key not in spec_impls:
            errors.append(f"The implementation snippet is missing for: {key}")

    if len(errors) == 0:
        return None

    return errors


# endregion

# region Generate


class _PatternVerificationTranspiler(
    parse_tree.RestrictedTransformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile a statement of a pattern verification into Java."""

    def __init__(self, defined_variables: Set[Identifier]) -> None:
        """
        Initialize with the given values.

        The ``initialized_variables`` are shared between different statement
        transpilations. It is also mutated when assignments are transpiled. We need to
        keep track of variables so that we know when we have to define them, and when
        we can simply assign them a value, if they have been already defined.
        """
        self.defined_variables = defined_variables

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if isinstance(node.value, str):
            regex, parse_error = parse_retree.parse(values=[node.value])
            if parse_error is not None:
                regex_line, pointer_line = parse_retree.render_pointer(
                    parse_error.cursor
                )

                return (
                    None,
                    Error(
                        node.original_node,
                        f"The string constant could not be parsed "
                        f"as a regular expression: \n"
                        f"{parse_error.message}\n"
                        f"{regex_line}\n"
                        f"{pointer_line}",
                    ),
                )

            assert regex is not None
            parse_retree.fix_for_utf16_regex_in_place(regex)

            return self._transform_joined_str_values(
                values=parse_retree.render(regex=regex)
            )
        else:
            raise AssertionError(f"Unexpected {node=}")

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def _transform_joined_str_values(
        self, values: Sequence[Union[str, parse_tree.FormattedValue]]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        """Transform the values of a joined string to a Java string literal."""
        if all(isinstance(value, str) for value in values):
            return (
                Stripped(java_common.string_literal("".join(values))),  # type: ignore
                None,
            )

        parts = []  # type: List[str]
        for value in values:
            if isinstance(value, str):
                string_literal = java_common.string_literal(
                    value.replace("{", "{{").replace("}", "}}")
                )

                assert string_literal.startswith('"') and string_literal.endswith('"')

                parts.append(string_literal)

            elif isinstance(value, parse_tree.FormattedValue):
                code, error = self.transform(value.value)
                if error is not None:
                    return None, error
                assert code is not None

                assert (
                    "\n" not in code
                ), f"New-lines are not expected in formatted values, but got: {code}"

                no_parentheses = (
                    parse_tree.Member,
                    parse_tree.FunctionCall,
                    parse_tree.MethodCall,
                    parse_tree.Name,
                    parse_tree.Constant,
                    parse_tree.Index,
                    parse_tree.IsIn,
                )

                if isinstance(code, no_parentheses):
                    parts.append(f"{code}")
                else:
                    parts.append(f"({code})")
            else:
                assert_never(value)

        return Stripped(" + ".join(parts)), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return Stripped(java_naming.variable_name(node.identifier)), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_joined_str(
        self, node: parse_tree.JoinedStr
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        regex, parse_error = parse_retree.parse(values=node.values)
        if parse_error is not None:
            regex_line, pointer_line = parse_retree.render_pointer(parse_error.cursor)

            return (
                None,
                Error(
                    node.original_node,
                    f"The joined string could not be parsed "
                    f"as a regular expression: \n"
                    f"{parse_error.message}\n"
                    f"{regex_line}\n"
                    f"{pointer_line}",
                ),
            )

        assert regex is not None
        parse_retree.fix_for_utf16_regex_in_place(regex)

        return self._transform_joined_str_values(
            values=parse_retree.render(regex=regex)
        )

    def transform_assignment(
        self, node: parse_tree.Assignment
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        assert isinstance(node.target, parse_tree.Name)
        variable = java_naming.variable_name(node.target.identifier)
        code, error = self.transform(node.value)
        if error is not None:
            return None, error
        assert code is not None

        if node.target.identifier in self.defined_variables:
            return Stripped(f"{variable} = {code};"), None

        else:
            self.defined_variables.add(node.target.identifier)
            return Stripped(f"var {variable} = {code};"), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_pattern_verification(
    verification: intermediate.PatternVerification,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verification function that checks the regular expressions."""
    # We assume that we performed all the checks at the intermediate stage.

    construct_name = java_naming.private_method_name(
        Identifier(f"construct_{verification.name}")
    )

    blocks = []  # type: List[Stripped]

    # region Construct block

    writer = io.StringIO()
    writer.write(
        f"""\
private static Pattern {construct_name}()
{{
"""
    )

    defined_variables = set()  # type: Set[Identifier]
    transpiler = _PatternVerificationTranspiler(defined_variables=defined_variables)

    for i, stmt in enumerate(verification.parsed.body):
        if i == len(verification.parsed.body) - 1:
            break

        code, error = transpiler.transform(stmt)
        if error is not None:
            return None, error
        assert code is not None

        writer.write(textwrap.indent(code, I))
        writer.write("\n")

    if len(verification.parsed.body) >= 2:
        writer.write("\n")

    pattern_expr, error = transpiler.transform(verification.pattern_expr)
    if error is not None:
        return None, error
    assert pattern_expr is not None

    # A pragmatic heuristics for breaking lines
    if len(pattern_expr) < 50:
        writer.write(textwrap.indent(f"return Pattern.compile({pattern_expr});\n", I))
    else:
        writer.write(
            textwrap.indent(f"return Pattern.compile(\n{I}{pattern_expr});\n", I)
        )

    writer.write("}")

    blocks.append(Stripped(writer.getvalue()))

    # endregion

    # region Initialize the regex

    regex_name = java_naming.property_name(Identifier(f"regex_{verification.name}"))

    blocks.append(
        Stripped(f"private static final Pattern {regex_name} = {construct_name}();")
    )

    assert len(verification.arguments) == 1
    assert isinstance(
        verification.arguments[0].type_annotation, intermediate.PrimitiveTypeAnnotation
    )
    # noinspection PyUnresolvedReferences
    assert (
        verification.arguments[0].type_annotation.a_type
        == intermediate.PrimitiveType.STR
    )

    arg_name = java_naming.argument_name(verification.arguments[0].name)

    writer = io.StringIO()
    if verification.description is not None:
        comment, comment_errors = java_description.generate_comment_for_signature(
            verification.description
        )
        if comment_errors is not None:
            return None, Error(
                verification.description.parsed.node,
                "Failed to generate the documentation comment",
                comment_errors,
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    method_name = java_naming.method_name(verification.name)

    writer.write(
        f"""\
public static bool {method_name}(String {arg_name})
{{
{I}return {regex_name}.matcher({arg_name}).matches();
}}"""
    )

    blocks.append(Stripped(writer.getvalue()))

    # endregion

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    return Stripped(writer.getvalue()), None


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    package: java_common.PackageIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Java code of the structures based on the symbol table.

    The ``package`` defines the root Java package.
    """

    imports = [
        Stripped("import java.util.regex.Matcher;"),
        Stripped("import java.util.regex.Pattern;"),
    ]  # type: List[Stripped]

    verification_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    base_environment = intermediate_type_inference.populate_base_environment(
        symbol_table=symbol_table
    )

    for verification in symbol_table.verification_functions:
        if isinstance(verification, intermediate.ImplementationSpecificVerification):
            implementation_key = specific_implementations.ImplementationKey(
                f"Verification/{verification.name}.java"
            )

            implementation = spec_impls.get(implementation_key, None)
            if implementation is None:
                errors.append(
                    Error(
                        None,
                        f"The snippet for the verification function "
                        f"{verification.name!r} is missing: {implementation_key}",
                    )
                )
            else:
                verification_blocks.append(implementation)

        elif isinstance(verification, intermediate.PatternVerification):
            implementation, error = _transpile_pattern_verification(
                verification=verification
            )

            if error is not None:
                errors.append(error)
            else:
                assert implementation is not None
                verification_blocks.append(implementation)

        elif isinstance(verification, intermediate.TranspilableVerification):
            pass
            # implementation, error = _transpile_transpilable_verification(
            #     verification=verification,
            #     symbol_table=symbol_table,
            #     environment=base_environment,
            # )

            # if error is not None:
            #     errors.append(error)
            # else:
            #     assert implementation is not None
            #     verification_blocks.append(implementation)

        else:
            assert_never(verification)

    verification_writer = io.StringIO()
    verification_writer.write(
        f"""\
public class Verification
{I}{{
"""
    )

    for i, verification_block in enumerate(verification_blocks):
        if i > 0:
            verification_writer.write("\n\n")

        verification_writer.write(textwrap.indent(verification_block, I))

    verification_writer.write(f"\n{I}}}")
    verification_writer.write("\n}")

    if len(errors) > 0:
        return None, errors

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.Verification;"),
        Stripped("\n".join(imports)),
        Stripped(verification_writer.getvalue()),
        java_common.WARNING,
    ]  # type: List[Stripped]

    code = "\n\n".join(blocks)

    return f"{code}\n", None


# endregion
