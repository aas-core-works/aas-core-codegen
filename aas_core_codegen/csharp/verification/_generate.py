"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
from typing import (
    Tuple,
    Optional,
    List,
    Sequence,
    Set,
    Mapping,
    Union,
)

from icontract import ensure

from aas_core_codegen import intermediate, specific_implementations, naming
from aas_core_codegen.common import (
    Error,
    Stripped,
    assert_never,
    Identifier,
    indent_but_first_line,
)
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    description as csharp_description,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference
from aas_core_codegen.parse import tree as parse_tree


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
                    f"Verification/{func.name}.cs"
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


class _PatternVerificationTranspiler(parse_tree.RestrictedTransformer[Stripped]):
    """Transpile a statement of a pattern verification into C#."""

    def __init__(self, defined_variables: Set[Identifier]) -> None:
        """
        Initialize with the given values.

        The ``initialized_variables`` are shared between different statement
        transpilations. It is also mutated when assignments are transpiled. We need to
        keep track of variables so that we know when we have to define them, and when
        we can simply assign them a value, if they have been already defined.
        """
        self.defined_variables = defined_variables

    def transform_constant(self, node: parse_tree.Constant) -> Stripped:
        if isinstance(node.value, str):
            return Stripped(csharp_common.string_literal(node.value))
        else:
            raise AssertionError(f"Unexpected {node=}")

    def transform_name(self, node: parse_tree.Name) -> Stripped:
        return Stripped(csharp_naming.variable_name(node.identifier))

    def transform_joined_str(self, node: parse_tree.JoinedStr) -> Stripped:
        parts = []  # type: List[str]
        for value in node.values:
            if isinstance(value, str):
                string_literal = csharp_common.string_literal(
                    value.replace("{", "{{").replace("}", "}}")
                )

                # We need to remove double-quotes since we are joining everything
                # ourselves later.

                assert string_literal.startswith('"') and string_literal.endswith('"')

                string_literal_wo_quotes = string_literal[1:-1]
                parts.append(string_literal_wo_quotes)

            elif isinstance(value, parse_tree.FormattedValue):
                code = self.transform(value.value)
                assert (
                    "\n" not in code
                ), f"New-lines are not expected in formatted values, but got: {code}"

                parts.append(f"{{{code}}}")
            else:
                assert_never(value)

        writer = io.StringIO()
        writer.write('$"')
        for part in parts:
            writer.write(part)

        writer.write('"')

        return Stripped(writer.getvalue())

    def transform_assignment(self, node: parse_tree.Assignment) -> Stripped:
        assert isinstance(node.target, parse_tree.Name)
        variable = csharp_naming.variable_name(node.target.identifier)
        code = self.transform(node.value)

        if node.target.identifier in self.defined_variables:
            return Stripped(f"{variable} = {code};")

        else:
            self.defined_variables.add(node.target.identifier)
            return Stripped(f"var {variable} = {code};")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_pattern_verification(
    verification: intermediate.PatternVerification,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verification function that checks the regular expressions."""
    # NOTE (mristin, 2021-12-19):
    # We assume that we performed all the checks at the intermediate stage.

    construct_name = csharp_naming.private_method_name(
        Identifier(f"construct_{verification.name}")
    )

    blocks = []  # type: List[Stripped]

    # region Construct block

    writer = io.StringIO()
    writer.write(
        f"""\
private static Regex {construct_name}()
{{
"""
    )

    defined_variables = set()  # type: Set[Identifier]
    transpiler = _PatternVerificationTranspiler(defined_variables=defined_variables)

    for i, stmt in enumerate(verification.parsed.body):
        if i == len(verification.parsed.body) - 1:
            break

        code = transpiler.transform(stmt)
        writer.write(textwrap.indent(code, I))
        writer.write("\n")

    if len(verification.parsed.body) >= 2:
        writer.write("\n")

    assert len(verification.parsed.body) >= 1

    assert isinstance(verification.parsed.body[-1], parse_tree.Return)
    # noinspection PyUnresolvedReferences
    assert isinstance(verification.parsed.body[-1].value, parse_tree.IsNotNone)
    # noinspection PyUnresolvedReferences
    assert isinstance(verification.parsed.body[-1].value.value, parse_tree.FunctionCall)
    # noinspection PyUnresolvedReferences
    assert verification.parsed.body[-1].value.value.name.identifier == "match"

    # noinspection PyUnresolvedReferences
    match_call = verification.parsed.body[-1].value.value

    assert isinstance(
        match_call, parse_tree.FunctionCall
    ), f"{parse_tree.dump(match_call)}"
    assert match_call.name.identifier == "match"

    assert isinstance(match_call.args[0], parse_tree.Expression)
    pattern_expr = transpiler.transform(match_call.args[0])

    # A pragmatic heuristics for breaking lines
    if len(pattern_expr) < 50:
        writer.write(textwrap.indent(f"return new Regex({pattern_expr});\n", I))
    else:
        writer.write(textwrap.indent(f"return new Regex(\n{I}{pattern_expr});\n", I))

    writer.write("}")

    blocks.append(Stripped(writer.getvalue()))

    # endregion

    # region Initialize the regex

    regex_name = csharp_naming.private_property_name(
        Identifier(f"regex_{verification.name}")
    )

    blocks.append(
        Stripped(f"private static readonly Regex {regex_name} = {construct_name}();")
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

    arg_name = csharp_naming.argument_name(verification.arguments[0].name)

    writer = io.StringIO()
    if verification.description is not None:
        comment, comment_errors = csharp_description.generate_signature_comment(
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

    method_name = csharp_naming.method_name(verification.name)

    writer.write(
        f"""\
public static bool {method_name}(string {arg_name})
{{
{I}return {regex_name}.IsMatch({arg_name});
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


class _InvariantTranspiler(
    parse_tree.RestrictedTransformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile an invariant expression into a code, or an error."""

    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: intermediate_type_inference.Environment,
    ) -> None:
        """Initialize with the given values."""
        self.type_map = type_map
        self.environment = environment

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_member(
        self, node: parse_tree.Member
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        instance, error = self.transform(node.instance)
        if error is not None:
            return None, error

        instance_type = self.type_map[node.instance]
        # Ignore optionals as they need to be checked before in the code
        while isinstance(
            instance_type, intermediate_type_inference.OptionalTypeAnnotation
        ):
            instance_type = instance_type.value

        member_type = self.type_map[node]
        while isinstance(
            member_type, intermediate_type_inference.OptionalTypeAnnotation
        ):
            member_type = member_type.value

        # noinspection PyUnusedLocal
        member_name = None  # type: Optional[str]

        if isinstance(
            instance_type, intermediate_type_inference.OurTypeAnnotation
        ) and isinstance(instance_type.symbol, intermediate.Enumeration):
            # The member denotes a literal of an enumeration.
            member_name = csharp_naming.enum_literal_name(node.name)

        elif isinstance(member_type, intermediate_type_inference.MethodTypeAnnotation):
            member_name = csharp_naming.method_name(node.name)

        elif isinstance(
            instance_type, intermediate_type_inference.OurTypeAnnotation
        ) and isinstance(instance_type.symbol, intermediate.Class):
            if node.name in instance_type.symbol.properties_by_name:
                member_name = csharp_naming.property_name(node.name)
            else:
                return None, Error(
                    node.original_node,
                    f"The property {node.name!r} has not been defined "
                    f"in the class {instance_type.symbol.name!r}",
                )

        elif isinstance(
            instance_type, intermediate_type_inference.EnumerationAsTypeTypeAnnotation
        ):
            if node.name in instance_type.enumeration.literals_by_name:
                member_name = csharp_naming.enum_literal_name(node.name)
            else:
                return None, Error(
                    node.original_node,
                    f"The property {node.name!r} has not been defined "
                    f"in the class {instance_type.enumeration.name!r}",
                )
        else:
            return None, Error(
                node.original_node,
                f"We do not know how to generate the member access. The inferred type "
                f"of the instance was {instance_type}, while the member type "
                f"was {member_type}. However, we do not know how to resolve "
                f"the member {node.name!r} in {instance_type}.",
            )

        assert member_name is not None

        return Stripped(f"{instance}.{member_name}"), None

    _CSHARP_COMPARISON_MAP = {
        parse_tree.Comparator.LT: "<",
        parse_tree.Comparator.LE: "<=",
        parse_tree.Comparator.GT: ">",
        parse_tree.Comparator.GE: ">=",
        parse_tree.Comparator.EQ: "==",
        parse_tree.Comparator.NE: "!=",
    }

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_comparison(
        self, node: parse_tree.Comparison
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        comparator = _InvariantTranspiler._CSHARP_COMPARISON_MAP[node.op]

        errors = []

        left, error = self.transform(node.left)
        if error is not None:
            errors.append(error)

        right, error = self.transform(node.right)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the comparison", errors
            )

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Constant,
        )

        if isinstance(node.left, no_parentheses_types) and isinstance(
            node.right, no_parentheses_types
        ):
            return Stripped(f"{left} {comparator} {right}"), None

        return Stripped(f"({left}) {comparator} ({right})"), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_implication(
        self, node: parse_tree.Implication
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []

        antecedent, error = self.transform(node.antecedent)
        if error is not None:
            errors.append(error)

        consequent, error = self.transform(node.consequent)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the implication", errors
            )

        assert antecedent is not None
        assert consequent is not None

        no_parentheses_types_in_this_context = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
        )

        if isinstance(node.antecedent, no_parentheses_types_in_this_context):
            not_antecedent = f"!{antecedent}"
        else:
            # NOTE (mristin, 2022-04-07):
            # This is a very rudimentary heuristic for breaking the lines, and can be
            # greatly improved by rendering into C# code. However, at this point, we
            # lack time for more sophisticated reformatting approaches.
            if "\n" in antecedent:
                not_antecedent = f"""\
!(
{I}{indent_but_first_line(antecedent, I)}
)"""
            else:
                not_antecedent = f"!({antecedent})"

        if not isinstance(node.consequent, no_parentheses_types_in_this_context):
            # NOTE (mristin, 2022-04-07):
            # This is a very rudimentary heuristic for breaking the lines, and can be
            # greatly improved by rendering into C# code. However, at this point, we
            # lack time for more sophisticated reformatting approaches.
            if "\n" in consequent:
                consequent = Stripped(
                    f"""\
(
{I}{indent_but_first_line(consequent, I)}
)"""
                )
            else:
                consequent = Stripped(f"({consequent})")

        return Stripped(f"{not_antecedent}\n|| {consequent}"), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_method_call(
        self, node: parse_tree.MethodCall
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        instance, error = self.transform(node.member.instance)
        if error is not None:
            errors.append(error)

        args = []  # type: List[Stripped]
        for arg_node in node.args:
            arg, error = self.transform(arg_node)
            if error is not None:
                errors.append(error)
                continue

            assert arg is not None

            args.append(arg)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the method call", errors
            )

        assert instance is not None

        if not isinstance(node.member.instance, (parse_tree.Name, parse_tree.Member)):
            instance = Stripped(f"({instance})")

        method_name = csharp_naming.method_name(node.member.name)

        joined_args = ", ".join(args)

        # Apply heuristic for breaking the lines
        if len(joined_args) > 50:
            writer = io.StringIO()
            writer.write(f"{instance}.{method_name}(\n")

            for i, arg in enumerate(args):
                writer.write(f"{I}{arg}")

                if i == len(args) - 1:
                    writer.write(")")
                else:
                    writer.write(",\n")

            return Stripped(writer.getvalue()), None
        else:
            return Stripped(f"{instance}.{method_name}({joined_args})"), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_function_call(
        self, node: parse_tree.FunctionCall
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        args = []  # type: List[Stripped]
        for arg_node in node.args:
            arg, error = self.transform(arg_node)
            if error is not None:
                errors.append(error)
                continue

            assert arg is not None

            args.append(arg)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the function call", errors
            )

        # NOTE (mristin, 2021-12-16):
        # The validity of the arguments is checked in
        # :py:func:`aas_core_codegen.intermediate._translate.translate`, so we do not
        # have to test for argument arity here.

        func_type = self.type_map[node.name]

        if not isinstance(
            func_type, intermediate_type_inference.FunctionTypeAnnotationUnionAsTuple
        ):
            return None, Error(
                node.name.original_node,
                f"Expected the name to refer to a function, "
                f"but its inferred type was {func_type}",
            )

        if isinstance(
            func_type, intermediate_type_inference.VerificationTypeAnnotation
        ):
            method_name = csharp_naming.method_name(func_type.func.name)

            joined_args = ", ".join(args)

            # Apply heuristic for breaking the lines
            if len(joined_args) > 50:
                writer = io.StringIO()
                writer.write(f"Verification.{method_name}(\n")

                for i, arg in enumerate(args):
                    writer.write(f"{I}{arg}")

                    if i == len(args) - 1:
                        writer.write(")")
                    else:
                        writer.write(",\n")

                return Stripped(writer.getvalue()), None
            else:
                return Stripped(f"Verification.{method_name}({joined_args})"), None

        elif isinstance(
            func_type, intermediate_type_inference.BuiltinFunctionTypeAnnotation
        ):
            if func_type.func.name == "len":
                assert len(args) == 1, (
                    f"Expected exactly one argument, but got: {args}; "
                    f"this should have been caught before."
                )

                collection_node = node.args[0]
                if not isinstance(
                    collection_node,
                    (parse_tree.Name, parse_tree.Member, parse_tree.MethodCall),
                ):
                    collection = f"({args[0]})"
                else:
                    collection = args[0]

                arg_type = self.type_map[node.args[0]]
                while isinstance(
                    arg_type, intermediate_type_inference.OptionalTypeAnnotation
                ):
                    arg_type = arg_type.value

                if (
                    isinstance(
                        arg_type, intermediate_type_inference.PrimitiveTypeAnnotation
                    )
                    and arg_type.a_type == intermediate_type_inference.PrimitiveType.STR
                ):
                    return Stripped(f"{collection}.Length"), None

                elif (
                    isinstance(arg_type, intermediate_type_inference.OurTypeAnnotation)
                    and isinstance(arg_type.symbol, intermediate.ConstrainedPrimitive)
                    and arg_type.symbol.constrainee == intermediate.PrimitiveType.STR
                ):
                    return Stripped(f"{collection}.Length"), None

                elif isinstance(
                    arg_type, intermediate_type_inference.ListTypeAnnotation
                ):
                    return Stripped(f"{collection}.Count"), None

                else:
                    return None, Error(
                        node.original_node,
                        f"We do not know how to compute the length on type {arg_type}",
                        errors,
                    )
            else:
                return None, Error(
                    node.original_node,
                    f"The handling of the built-in function {node.name!r} has not "
                    f"been implemented",
                )
        else:
            assert_never(func_type)

        raise AssertionError("Should not have gotten here")

    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if isinstance(node.value, bool):
            return Stripped("true" if node.value else "false"), None
        elif isinstance(node.value, (int, float)):
            return Stripped(str(node.value)), None
        elif isinstance(node.value, str):
            return Stripped(csharp_common.string_literal(node.value)), None
        else:
            assert_never(node.value)

        raise AssertionError("Should not have gotten here")

    def transform_is_none(
        self, node: parse_tree.IsNone
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        value, error = self.transform(node.value)
        if error is not None:
            return None, error

        no_parentheses_types = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
        )
        if isinstance(node.value, no_parentheses_types):
            return Stripped(f"{value} == null"), None
        else:
            return Stripped(f"({value}) == null"), None

    def transform_is_not_none(
        self, node: parse_tree.IsNotNone
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        value, error = self.transform(node.value)
        if error is not None:
            return None, error

        no_parentheses_types_in_this_context = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
        )
        if isinstance(node.value, no_parentheses_types_in_this_context):
            return Stripped(f"{value} != null"), None
        else:
            return Stripped(f"({value}) != null"), None

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier == "self":
            # The ``that`` refers to the argument of the verification function.
            return Stripped("that"), None

        name = None  # type: Optional[Identifier]

        type_in_env = self.environment.find(node.identifier)
        if type_in_env is None:
            name = csharp_naming.variable_name(node.identifier)
        else:
            while isinstance(
                type_in_env, intermediate_type_inference.OptionalTypeAnnotation
            ):
                type_in_env = type_in_env.value

            assert not isinstance(
                type_in_env, intermediate_type_inference.OptionalTypeAnnotation
            )

            if isinstance(
                type_in_env,
                (
                    intermediate_type_inference.PrimitiveTypeAnnotation,
                    intermediate_type_inference.OurTypeAnnotation,
                    intermediate_type_inference.VerificationTypeAnnotation,
                    intermediate_type_inference.BuiltinFunctionTypeAnnotation,
                    intermediate_type_inference.MethodTypeAnnotation,
                    intermediate_type_inference.ListTypeAnnotation,
                ),
            ):
                name = csharp_naming.variable_name(node.identifier)
            elif isinstance(
                type_in_env, intermediate_type_inference.EnumerationAsTypeTypeAnnotation
            ):
                name = csharp_naming.enum_name(node.identifier)
            else:
                assert_never(type_in_env)

        assert name is not None

        return Stripped(name), None

    def transform_and(
        self, node: parse_tree.And
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]
        values = []  # type: List[Stripped]

        for value_node in node.values:
            value, error = self.transform(value_node)
            if error is not None:
                errors.append(error)
                continue

            assert value is not None

            no_parentheses_types_in_this_context = (
                parse_tree.Member,
                parse_tree.MethodCall,
                parse_tree.FunctionCall,
                parse_tree.Comparison,
                parse_tree.Name,
            )

            if not isinstance(value_node, no_parentheses_types_in_this_context):
                # NOTE (mristin, 2022-04-07):
                # This is a very rudimentary heuristic for breaking the lines, and can
                # be greatly improved by rendering into C# code. However, at this point,
                # we lack time for more sophisticated reformatting approaches.
                if "\n" in value:
                    value = Stripped(
                        f"""\
(
{I}{indent_but_first_line(value, I)}
)"""
                    )
                else:
                    value = Stripped(f"({value})")

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors
            )

        writer = io.StringIO()
        for i, value in enumerate(values):
            if i == 0:
                writer.write(value)
            else:
                writer.write(f"\n&& {value}")

        return Stripped(writer.getvalue()), None

    def transform_or(
        self, node: parse_tree.Or
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]
        values = []  # type: List[Stripped]

        for value_node in node.values:
            value, error = self.transform(value_node)
            if error is not None:
                errors.append(error)
                continue

            assert value is not None

            no_parentheses_types_in_this_context = (
                parse_tree.Member,
                parse_tree.MethodCall,
                parse_tree.FunctionCall,
                parse_tree.Comparison,
                parse_tree.Name,
            )

            if not isinstance(value_node, no_parentheses_types_in_this_context):
                # NOTE (mristin, 2022-04-07):
                # This is a very rudimentary heuristic for breaking the lines, and can
                # be greatly improved by rendering into C# code. However, at this point,
                # we lack time for more sophisticated reformatting approaches.
                if "\n" in value:
                    value = Stripped(
                        f"""\
(
{I}{indent_but_first_line(value, I)}
)"""
                    )
                else:
                    value = Stripped(f"({value})")

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors
            )

        writer = io.StringIO()
        for i, value in enumerate(values):
            if i == 0:
                writer.write(value)
            else:
                writer.write(f"\n|| {value}")

        return Stripped(writer.getvalue()), None

    def transform_joined_str(
        self, node: parse_tree.JoinedStr
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        parts = []  # type: List[str]
        for value in node.values:
            if isinstance(value, str):
                string_literal = csharp_common.string_literal(
                    value.replace("{", "{{").replace("}", "}}")
                )

                # We need to remove double-quotes since we are joining everything
                # ourselves later.

                assert string_literal.startswith('"') and string_literal.endswith('"')

                string_literal_wo_quotes = string_literal[1:-1]
                parts.append(string_literal_wo_quotes)

            elif isinstance(value, parse_tree.FormattedValue):
                code, error = self.transform(value.value)
                if error is not None:
                    return None, error

                assert code is not None

                assert (
                    "\n" not in code
                ), f"New-lines are not expected in formatted values, but got: {code}"

                parts.append(f"{{{code}}}")
            else:
                assert_never(value)

        writer = io.StringIO()
        writer.write('$"')
        for part in parts:
            writer.write(part)

        writer.write('"')

        return Stripped(writer.getvalue()), None

    def _transform_any_or_all(
        self, node: Union[parse_tree.Any, parse_tree.All]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]

        variable, error = self.transform(node.for_each.variable)
        if error is not None:
            errors.append(error)

        iteration, error = self.transform(node.for_each.iteration)
        if error is not None:
            errors.append(error)

        condition, error = self.transform(node.condition)
        if error is not None:
            errors.append(error)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the ``all``", errors
            )

        assert variable is not None
        assert iteration is not None
        assert condition is not None

        no_parentheses_types_in_this_context = (
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
            parse_tree.Name,
        )

        if not isinstance(
            node.for_each.iteration, no_parentheses_types_in_this_context
        ):
            iteration = Stripped(f"({iteration})")

        qualifier_function = None  # type: Optional[str]
        if isinstance(node, parse_tree.Any):
            qualifier_function = "Any"
        elif isinstance(node, parse_tree.All):
            qualifier_function = "All"
        else:
            assert_never(node)

        return (
            Stripped(
                f"""\
{iteration}.{qualifier_function}(
{I}{variable} => {indent_but_first_line(condition, II)})"""
            ),
            None,
        )

    def transform_any(
        self, node: parse_tree.Any
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_any_or_all(node)

    def transform_all(
        self, node: parse_tree.All
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return self._transform_any_or_all(node)


# noinspection PyProtectedMember,PyProtectedMember
assert all(
    op in _InvariantTranspiler._CSHARP_COMPARISON_MAP for op in parse_tree.Comparator
)


@ensure(lambda text, result: text == "".join(result))
def _wrap_invariant_description(text: str) -> List[str]:
    """
    Wrap the invariant description as ``text`` into multiple tokens.

    The tokens are split based on the whitespace. We make sure the articles are not
    left hanging between the lines. A line should observe a pre-defined line limit,
    if possible.

    No new lines are added — the description should be given to the user in the original
    formatting. We merely split it in string literals for better code readability.
    """
    parts = text.split(" ")
    if len(parts) == 1:
        return [text]

    # NOTE (mristin, 2022-04-08):
    # We do not want to cut out "the", "a" and "an" on separate lines, so we split
    # the text once more in tokens where the articles are kept in the same token as
    # the word.
    tokens = []  # type: List[str]

    article = None  # type: Optional[str]
    for part in parts:
        if article is None:
            if part in ("a", "an", "the"):
                article = part
                continue
            else:
                tokens.append(part)
        else:
            if part in ("a", "an", "the"):
                # Append the previously observed ``article``;
                # the ``part`` becomes a new article.
                tokens.append(article)
                article = part
                continue

            tokens.append(f"{article} {part}")
            article = None

    if article is not None:
        tokens.append(article)

    # NOTE (mristin, 2022-04-08):
    # We add space to the tokens so that it is easier to re-flow them.
    tokens = [
        f"{token} " if i < len(tokens) - 1 else token for i, token in enumerate(tokens)
    ]
    assert "".join(tokens) == text

    # NOTE (mristin, 2022-04-08):
    # The line width of 60 characters is an arbitrary, but plausible limit. Please
    # consider that the text will be indented, so you have to add some slack.
    line_width = 60

    segments = []  # type: List[str]

    accumulation_len = 0
    accumulation = []  # type: List[str]

    for token in tokens:
        if len(token) > line_width:
            segments.append("".join(accumulation))
            segments.append(token)
            accumulation_len = 0
            accumulation = []

        elif accumulation_len + len(token) > line_width:
            segments.append("".join(accumulation))
            accumulation_len = len(token)
            accumulation = [token]
        else:
            accumulation_len += len(token)
            accumulation.append(token)

    if accumulation_len > 0:
        segments.append("".join(accumulation))

    return segments


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_invariant(
    invariant: intermediate.Invariant,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Translate the invariant from the meta-model into C# code."""
    # NOTE (mristin, 2021-10-24):
    # We manually transpile the invariant from our custom syntax without additional
    # semantic analysis in the :py:mod:`aas_core_codegen.intermediate` layer.
    #
    # While this might seem repetitive ("unDRY"), we are still not sure about
    # the appropriate abstraction. After we implement the code generation for a couple
    # of languages, we hope to have a much better understanding about the necessary
    # abstractions.

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table, environment=environment
    )
    _ = type_inferrer.transform(invariant.body)
    if len(type_inferrer.errors):
        return None, Error(
            invariant.parsed.node,
            "Failed to infer the types in the invariant",
            type_inferrer.errors,
        )

    transpiler = _InvariantTranspiler(
        type_map=type_inferrer.type_map, environment=environment
    )
    expr, error = transpiler.transform(invariant.parsed.body)
    if error is not None:
        return None, error

    assert expr is not None

    writer = io.StringIO()
    if len(expr) > 50 or "\n" in expr:
        writer.write("if (!(\n")
        writer.write(textwrap.indent(expr, I))
        writer.write("))\n{\n")
    else:
        no_parenthesis_type_in_this_context = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
        )

        if isinstance(invariant.parsed.body, no_parenthesis_type_in_this_context):
            not_expr = f"!{expr}"
        else:
            not_expr = f"!({expr})"

        writer.write(f"if ({not_expr})\n{{\n")

    writer.write(
        textwrap.indent(
            f"""\
yield return new Reporting.Error(
{I}"Invariant violated:\\n" +
""",
            I,
        )
    )

    message_literals = []  # type: List[Stripped]
    if invariant.description is not None:
        # NOTE (mristin, 2022-04-08):
        # We need to wrap the description in multiple literals as a single long
        # string literal is often too much for the readability.
        invariant_description_lines = _wrap_invariant_description(invariant.description)
        for i, line in enumerate(invariant_description_lines):
            if i < len(invariant_description_lines) - 1:
                message_literals.append(csharp_common.string_literal(line))
            else:
                message_literals.append(csharp_common.string_literal(f"{line}\n"))

    expr_lines = expr.splitlines()
    for i, line in enumerate(expr_lines):
        if i < len(expr_lines) - 1:
            literal = csharp_common.string_literal(line + "\n")
        else:
            literal = csharp_common.string_literal(line)

        message_literals.append(literal)

    for i, literal in enumerate(message_literals):
        if i < len(message_literals) - 1:
            writer.write(f"{II}{literal} +\n")
        else:
            writer.write(f"{II}{literal});")

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_enum_value_sets(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate a class that pre-computes the sets of allowed enumeration literals."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Enumeration):
            continue

        enum_name = csharp_naming.enum_name(symbol.name)

        if len(symbol.literals) == 0:
            blocks.append(
                Stripped(
                    f"internal static HashSet<int> For{enum_name} = new HashSet<int>();"
                )
            )
        else:
            hash_set_writer = io.StringIO()
            hash_set_writer.write(
                f"internal static HashSet<int> For{enum_name} = new HashSet<int>\n{{\n"
            )

            for i, literal in enumerate(symbol.literals):
                literal_name = csharp_naming.enum_literal_name(literal.name)
                hash_set_writer.write(f"{I}(int)Aas.{enum_name}.{literal_name}")
                if i < len(symbol.literals) - 1:
                    hash_set_writer.write(",\n")
                else:
                    hash_set_writer.write("\n")

            hash_set_writer.write("};")

            blocks.append(Stripped(hash_set_writer.getvalue()))

    writer = io.StringIO()
    writer.write(
        """\
/// <summary>
/// Hash allowed enum values for efficient validation of enums.
/// </summary>
internal static class EnumValueSet
{
"""
    )
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // internal static class EnumValueSet")

    return Stripped(writer.getvalue())


def _generate_verify_method(symbol: intermediate.Symbol) -> Stripped:
    """Generate the name of the ``Verification.Verify*`` method."""
    if isinstance(symbol, intermediate.Enumeration):
        name = csharp_naming.enum_name(symbol.name)
        return Stripped(f"Verification.Verify{name}")

    elif isinstance(symbol, intermediate.ConstrainedPrimitive):
        name = csharp_naming.class_name(symbol.name)
        return Stripped(f"Verification.Verify{name}")

    elif isinstance(symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)):
        return Stripped("Verification.Verify")
    else:
        assert_never(symbol)

    raise AssertionError("Unexpected execution path")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transform_property(
    prop: intermediate.Property,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the snippet to transform a property to errors."""
    # NOTE (mristin, 2022-03-10):
    # Instead of writing here a complex but general solution with unrolling we choose
    # to provide a simple, but limited, solution. First, the meta-model is quite
    # limited itself at the moment, so the complexity of the general solution is not
    # warranted. Second, we hope that there will be fewer bugs in the simple solution
    # which is particularly important at this early adoption stage.
    #
    # We anticipate that in the future we will indeed need a general and complex
    # solution. Here are just some thoughts on how to approach it:
    # * Leave the pattern matching to produce more readable code for simple cases,
    # * Unroll only in case of composite types and optional composite types.

    type_anno = (
        prop.type_annotation
        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
        else prop.type_annotation.value
    )

    if isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        return None, Error(
            prop.parsed.node,
            "We currently implemented verification based on a very limited "
            "pattern matching due to code simplicity. We did not handle "
            "the case of nested optional values. Please contact "
            "the developers if you need this functionality.",
        )
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        if isinstance(type_anno.items, intermediate.OptionalTypeAnnotation):
            return None, Error(
                prop.parsed.node,
                "We currently implemented verification based on a very limited "
                "pattern matching due to code simplicity. We did not handle "
                "the case of lists of optional values. Please contact "
                "the developers if you need this functionality.",
            )
        elif isinstance(type_anno.items, intermediate.ListTypeAnnotation):
            return None, Error(
                prop.parsed.node,
                "We currently implemented verification based on a very limited "
                "pattern matching due to code simplicity. We did not handle "
                "the case of lists of lists. Please contact "
                "the developers if you need this functionality.",
            )
        else:
            pass
    else:
        pass

    stmts = []  # type: List[Stripped]

    prop_name = csharp_naming.property_name(prop.name)
    prop_literal = csharp_common.string_literal(naming.json_property(prop.name))

    # NOTE (mristin, 2022-03-12):
    # For some unexplainable reason, C# compiler can not infer that properties which
    # are enumerations are not null after an ``if (that.someProperty != null)``.
    # Hence we need to add a null-coalescing for these particular cases.
    # Otherwise, we can just stick to ``that.someProperty``.

    needs_null_coalescing = (
        isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
        and isinstance(prop.type_annotation.value, intermediate.OurTypeAnnotation)
        and isinstance(prop.type_annotation.value.symbol, intermediate.Enumeration)
    )
    if needs_null_coalescing:
        source_expr = Stripped("value")
    else:
        source_expr = Stripped(f"that.{prop_name}")

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        # There is nothing that we check for primitive types.
        return Stripped(""), None
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        verify_method = _generate_verify_method(symbol=type_anno.symbol)

        foreach_error_in_verify = (
            f"foreach (var error in {verify_method}({source_expr}))"
        )
        # Heuristic to break the lines, very rudimentary
        if len(foreach_error_in_verify) > 80:
            foreach_error_in_verify = textwrap.dedent(
                f"""\
                foreach (
                    {I}var error in {verify_method}(
                    {II}{source_expr}))"""
            )

        # We can't use textwrap.dedent due to foreach_snippet.
        stmts.append(
            Stripped(
                f"""\
{foreach_error_in_verify}
{{
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{prop_literal}));
{I}yield return error;
}}"""
            )
        )

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_anno.items,
            (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
        ), (
            "We chose to implement only a very limited pattern matching; "
            "see the note above in the code."
        )

        # NOTE (mristin, 2022-03-16):
        # We only descend into our classes here.
        if not isinstance(type_anno.items, intermediate.OurTypeAnnotation):
            return Stripped(""), None

        index_var = csharp_naming.variable_name(Identifier(f"index_{prop.name}"))
        verify_method = _generate_verify_method(type_anno.items.symbol)

        foreach_item_in_source_expr = f"foreach (var item in {source_expr})"
        # Rudimentary heuristics for line breaking
        if len(foreach_item_in_source_expr) > 80:
            foreach_item_in_source_expr = textwrap.dedent(
                f"""\
                foreach(
                {I}var item in {source_expr})"""
            )

        foreach_error_in_verify_item = f"foreach (var error in {verify_method}(item))"
        if len(foreach_error_in_verify_item) > 70:
            foreach_error_in_verify_item = textwrap.dedent(
                f"""\
                foreach (
                {I}var error in {verify_method}(item))"""
            )

        stmts.append(
            Stripped(
                f"""\
int {index_var} = 0;
{foreach_item_in_source_expr}
{{
{I}{indent_but_first_line(foreach_error_in_verify_item, I)}
{I}{{
{II}error._pathSegments.AddFirst(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}error._pathSegments.AddFirst(
{III}new Reporting.NameSegment(
{IIII}{prop_literal}));
{II}yield return error;
{I}}}
{I}{index_var}++;
}}"""
            )
        )

    else:
        assert_never(type_anno)

    verify_block = Stripped("\n".join(stmts))
    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        if needs_null_coalescing:
            value_type = csharp_common.generate_type(prop.type_annotation.value)
            if isinstance(prop.type_annotation.value, intermediate.OurTypeAnnotation):
                symbol = prop.type_annotation.value.symbol
                if isinstance(
                    symbol,
                    (
                        intermediate.Enumeration,
                        intermediate.AbstractClass,
                        intermediate.ConcreteClass,
                    ),
                ):
                    value_type = Stripped(f"Aas.{value_type}")

            return (
                Stripped(
                    f"""\
if (that.{prop_name} != null)
{{
{I}// We need to help the static analyzer with a null coalescing.
{I}{value_type} value = that.{prop_name}
{II}?? throw new System.InvalidOperationException();
{I}{indent_but_first_line(verify_block, I)}
}}"""
                ),
                None,
            )

        else:
            return (
                Stripped(
                    f"""\
if (that.{prop_name} != null)
{{
{I}{indent_but_first_line(verify_block, I)}
}}"""
                ),
                None,
            )
    else:
        return verify_block, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transform_for_class(
    cls: intermediate.ConcreteClass,
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the transform method to errors for the given concrete class."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    name = csharp_naming.class_name(cls.name)

    environment = intermediate_type_inference.MutableEnvironment(
        parent=base_environment
    )

    assert environment.find(Identifier("self")) is None
    environment.set(
        identifier=Identifier("self"),
        type_annotation=intermediate_type_inference.OurTypeAnnotation(symbol=cls),
    )

    for invariant in cls.invariants:
        invariant_code, error = _transpile_invariant(
            invariant=invariant, symbol_table=symbol_table, environment=environment
        )
        if error is not None:
            errors.append(error)
            continue

        assert invariant_code is not None

        blocks.append(invariant_code)

    if len(errors) > 0:
        return None, errors

    for prop in cls.properties:
        block, error = _generate_transform_property(prop=prop)
        if error is not None:
            errors.append(error)
        else:
            assert block is not None
            if block != "":
                blocks.append(block)

    if len(errors) > 0:
        return None, errors

    if len(blocks) == 0:
        blocks.append(
            Stripped(
                f"""\
// No verification has been defined for {name}.
yield break;"""
            )
        )

    writer = io.StringIO()
    writer.write(
        f"""\
public override IEnumerable<Reporting.Error> Transform(
{I}Aas.{name} that)
{{
"""
    )

    for i, stmt in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(stmt, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_transformer(
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a transformer to double-dispatch an instance to errors."""
    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # The abstract classes are directly dispatched by the transformer,
            # so we do not need to handle them separately.
            pass

        elif isinstance(symbol, intermediate.ConcreteClass):
            if symbol.is_implementation_specific:
                transform_key = specific_implementations.ImplementationKey(
                    f"Verification/transform_{symbol.name}.cs"
                )

                implementation = spec_impls.get(transform_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The transformation snippet is missing "
                            f"for the implementation-specific "
                            f"class {symbol.name}: {transform_key}",
                        )
                    )
                    continue

                blocks.append(spec_impls[transform_key])
            else:
                block, cls_errors = _generate_transform_for_class(
                    cls=symbol,
                    symbol_table=symbol_table,
                    base_environment=base_environment,
                )
                if cls_errors is not None:
                    errors.extend(cls_errors)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        f"""\
private class Transformer
{I}: Visitation.AbstractTransformer<IEnumerable<Reporting.Error>>
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // private class Transformer")

    return Stripped(writer.getvalue()), None


def _generate_verify_enumeration(enumeration: intermediate.Enumeration) -> Stripped:
    """Generate the verify method to check that an enum is valid."""
    name = csharp_naming.enum_name(enumeration.name)

    return Stripped(
        f"""\
/// <summary>
/// Verify that <paramref name="that" /> is a valid enumeration value.
/// </summary>
public static IEnumerable<Reporting.Error> Verify{name}(
{I}Aas.{name} that)
{{
{I}if (!EnumValueSet.For{name}.Contains(
{II}(int)that))
{I}{{
{II}yield return new Reporting.Error(
{III}$"Invalid {name}: {{that}}");
{I}}}
}}"""
    )


def _generate_verify_constrained_primitive(
    constrained_primitive: intermediate.ConstrainedPrimitive,
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the verify function for the constrained primitives."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    environment = intermediate_type_inference.MutableEnvironment(
        parent=base_environment
    )

    assert environment.find(Identifier("self")) is None
    environment.set(
        identifier=Identifier("self"),
        type_annotation=intermediate_type_inference.OurTypeAnnotation(
            symbol=constrained_primitive
        ),
    )

    for invariant in constrained_primitive.invariants:
        invariant_code, error = _transpile_invariant(
            invariant=invariant, symbol_table=symbol_table, environment=environment
        )
        if error is not None:
            errors.append(error)
            continue

        assert invariant_code is not None

        blocks.append(invariant_code)

    if len(errors) > 0:
        return None, errors

    if len(blocks) == 0:
        blocks.append(
            Stripped(
                """\
// There is no verification specified.
yield break;"""
            )
        )

    # NOTE (mristin, 2022-03-16):
    # Constrained primitives are not really classes, but we simply use the naming
    # for classes here since we need to pick *something*.
    name = csharp_naming.class_name(constrained_primitive.name)

    that_type = csharp_common.PRIMITIVE_TYPE_MAP[constrained_primitive.constrainee]

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Verify the constraints of <paramref name="that" />.
/// </summary>
public static IEnumerable<Reporting.Error> Verify{name} (
{I}{that_type} that)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    assert len(errors) == 0
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
    namespace: csharp_common.NamespaceIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the AAS C# namespace.
    """
    blocks = [
        csharp_common.WARNING,
        # Don't use textwrap.dedent since we add a newline in-between.
        Stripped(
            f"""\
using Regex = System.Text.RegularExpressions.Regex;
using System.Collections.Generic;  // can't alias
using System.Linq;  // can't alias

using Aas = {namespace};
using Reporting = {namespace}.Reporting;
using Visitation = {namespace}.Visitation;"""
        ),
    ]  # type: List[Stripped]

    verification_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    for verification in symbol_table.verification_functions:
        if isinstance(verification, intermediate.ImplementationSpecificVerification):
            implementation_key = specific_implementations.ImplementationKey(
                f"Verification/{verification.name}.cs"
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

        else:
            assert_never(verification)

    base_environment = intermediate_type_inference.populate_base_environment(
        symbol_table=symbol_table
    )

    verification_blocks.append(_generate_enum_value_sets(symbol_table=symbol_table))

    verification_blocks.append(
        Stripped(
            f"""\
private static readonly Verification.Transformer _transformer = (
{I}new Verification.Transformer());"""
        )
    )

    transformer_block, transformer_errors = _generate_transformer(
        symbol_table=symbol_table,
        base_environment=base_environment,
        spec_impls=spec_impls,
    )
    if transformer_errors is not None:
        errors.extend(transformer_errors)
    else:
        assert transformer_block is not None
        verification_blocks.append(transformer_block)

    verification_blocks.append(
        Stripped(
            f"""\
/// <summary>
/// Verify the constraints of <paramref name="that" /> recursively.
/// </summary>
/// <param name="that">
/// The instance of the meta-model to be verified
/// </param>
public static IEnumerable<Reporting.Error> Verify(Aas.IClass that)
{{
{I}foreach (var error in _transformer.Transform(that))
{I}{{
{II}yield return error;
{I}}}
}}"""
        )
    )

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            verification_blocks.append(_generate_verify_enumeration(enumeration=symbol))
        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            (
                constrained_primitive_block,
                constrained_primitive_errors,
            ) = _generate_verify_constrained_primitive(
                constrained_primitive=symbol,
                symbol_table=symbol_table,
                base_environment=base_environment,
            )

            if constrained_primitive_errors is not None:
                errors.extend(constrained_primitive_errors)
            else:
                assert constrained_primitive_block is not None
                verification_blocks.append(constrained_primitive_block)

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # We provide a general dispatch function.
            pass
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    verification_writer = io.StringIO()
    verification_writer.write(
        f"""\
namespace {namespace}
{{
{I}/// <summary>
{I}/// Verify that the instances of the meta-model satisfy the invariants.
{I}/// </summary>
"""
    )

    # region Write an example usage

    first_cls = None  # type: Optional[intermediate.ClassUnion]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)):
            first_cls = symbol
            break

    if first_cls is not None:
        cls_name = None  # type: Optional[str]
        if isinstance(first_cls, intermediate.AbstractClass):
            cls_name = csharp_naming.interface_name(first_cls.name)
        elif isinstance(first_cls, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(first_cls.name)
        else:
            assert_never(first_cls)

        an_instance_variable = csharp_naming.variable_name(Identifier("an_instance"))

        verification_writer.write(
            # We can not use textwrap.dedent since we indent everything including the
            # first line.
            f"""\
{I}/// <example>
{I}/// Here is an example how to verify an instance of {cls_name}:
{I}/// <code>
{I}/// var {an_instance_variable} = new Aas.{cls_name}(
{I}///     // ... some constructor arguments ...
{I}/// );
{I}/// foreach (var error in Verification.Verify({an_instance_variable}))
{I}/// {{
{I}/// {I}System.Console.Writeln(
{I}/// {II}$"{{error.Cause}} at: " +
{I}/// {II}Reporting.GenerateJsonPath(error.PathSegments));
{I}/// }}
{I}/// </code>
{I}/// </example>
"""
        )

    # endregion

    verification_writer.write(
        f"""\
{I}public static class Verification
{I}{{
"""
    )

    for i, verification_block in enumerate(verification_blocks):
        if i > 0:
            verification_writer.write("\n\n")

        verification_writer.write(textwrap.indent(verification_block, II))

    verification_writer.write(f"\n{I}}}  // public static class Verification")
    verification_writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(verification_writer.getvalue()))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        out.write(block)

    out.write("\n")

    return out.getvalue(), None


# endregion
