"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
from typing import (
    Tuple,
    Optional,
    List,
    Sequence,
    Union,
    Final,
    Set,
    MutableMapping,
    Mapping,
)

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import Error, Stripped, assert_never, Identifier
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    unrolling as csharp_unrolling,
    description as csharp_description,
)
from aas_core_codegen.csharp.common import INDENT as I, INDENT2 as II, INDENT3 as III
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference
from aas_core_codegen.parse import tree as parse_tree


# region Verify


def verify(
    spec_impls: specific_implementations.SpecificImplementations,
    verification_functions: Sequence[intermediate.Verification],
) -> Optional[List[str]]:
    """Verify all the implementation snippets related to verification."""
    errors = []  # type: List[str]

    expected_keys = [
        specific_implementations.ImplementationKey("Verification/Error.cs"),
        specific_implementations.ImplementationKey("Verification/Errors.cs"),
    ]

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
        textwrap.dedent(
            f"""\
        private static Regex {construct_name}()
        {{
        """
        )
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
        comment, error = csharp_description.generate_comment(verification.description)
        if error is not None:
            return None, error

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    writer.write(
        textwrap.dedent(
            f"""\
            public static bool IsMimeType(string {arg_name})
            {{
            {I}return {regex_name}.IsMatch({arg_name});
            }}"""
        )
    )

    blocks.append(Stripped(writer.getvalue()))

    # endregion

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

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
                    f"public static HashSet<int> For{enum_name} = new HashSet<int>();"
                )
            )
        else:
            hash_set_writer = io.StringIO()
            hash_set_writer.write(
                f"public static HashSet<int> For{enum_name} = new HashSet<int>\n{{\n"
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
        textwrap.dedent(
            """\
        /// <summary>
        /// Hash allowed enum values for efficient validation of enums.
        /// </summary>
        private static class EnumValueSet
        {
        """
        )
    )
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // private static class EnumValueSet")

    return Stripped(writer.getvalue())


class _EnumerationCheckUnroller(csharp_unrolling.Unroller):
    #: Symbol to be used to represent references within an AAS
    _ref_association: Final[intermediate.ClassUnion]

    def __init__(self, ref_association: intermediate.ClassUnion) -> None:
        """Initialize with the given values."""
        self._ref_association = ref_association

    def _unroll_primitive_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.PrimitiveTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        # Primitives are not enumerations, so nothing to check here.
        return []

    # noinspection PyUnusedLocal
    def _unroll_our_type_or_ref_annotation(
        self,
        unrollee_expr: str,
        type_annotation: Union[
            intermediate.OurTypeAnnotation, intermediate.RefTypeAnnotation
        ],
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """
        Generate the code for both our atomic type annotations and references.

        We merged :py:method:`._unroll_our_type_annotation` and
        :py:method:`._unroll_ref_type_annotation` together since they differ in only
        which symbol is unrolled over.
        """
        symbol = None  # type: Optional[intermediate.Symbol]
        if isinstance(type_annotation, intermediate.OurTypeAnnotation):
            symbol = type_annotation.symbol
        elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
            symbol = self._ref_association
        else:
            assert_never(type_annotation)

        assert symbol is not None

        if not isinstance(symbol, intermediate.Enumeration):
            # NOTE (mristin, 2021-12-25):
            # We do not descend into other types as this is generating the code
            # only for the non-descend case.
            return []

        enum_name = csharp_naming.enum_name(symbol.name)
        joined_pth = "/".join(path)

        return [
            csharp_unrolling.Node(
                text=textwrap.dedent(
                    f"""\
                if (!Verification.Implementation.EnumValueSet.For{enum_name}.Contains(
                {II}(int){unrollee_expr}))
                {{
                {I}errors.Add(
                {II}new Verification.Error(
                {III}$"{{path}}/{joined_pth}",
                {III}$"Invalid {{nameof(Aas.{enum_name})}}: {{{unrollee_expr}}}"));
                }}"""
                ),
                children=[],
            )
        ]

    def _unroll_our_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OurTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        return self._unroll_our_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )

    def _unroll_list_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.ListTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        # Descend into the list items
        item_var = csharp_unrolling.Unroller._loop_var_name(
            level=item_level, suffix="Item"
        )

        children = self.unroll(
            unrollee_expr=item_var,
            type_annotation=type_annotation.items,
            path=path + [f"{{{item_var}}}"],
            item_level=item_level + 1,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        node = csharp_unrolling.Node(
            text=f"foreach (var {item_var} in {unrollee_expr})", children=children
        )

        return [node]

    def _unroll_optional_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OptionalTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        children = self.unroll(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation.value,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )

        if len(children) > 0:
            return [
                csharp_unrolling.Node(
                    text=f"if ({unrollee_expr} != null)", children=children
                )
            ]
        else:
            return []

    def _unroll_ref_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.RefTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        return self._unroll_our_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )


def _unroll_enumeration_check(
    prop: intermediate.Property, ref_association: intermediate.ClassUnion
) -> Stripped:
    """
    Generate the code for unrolling the enumeration checks for the given property.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    prop_name = csharp_naming.property_name(prop.name)

    unroller = _EnumerationCheckUnroller(ref_association=ref_association)

    roots = unroller.unroll(
        unrollee_expr=f"that.{prop_name}",
        type_annotation=prop.type_annotation,
        path=[prop_name],
        item_level=0,
        key_value_level=0,
    )

    if len(roots) == 0:
        return Stripped("")

    blocks = [csharp_unrolling.render(root) for root in roots]
    return Stripped("\n\n".join(blocks))


class _ConstrainedPrimitiveCheckUnroller(csharp_unrolling.Unroller):
    #: Symbol to be used to represent references within an AAS
    _ref_association: Final[intermediate.Class]

    def __init__(self, ref_association: intermediate.ClassUnion) -> None:
        """Initialize with the given values."""
        self._ref_association = ref_association

    def _unroll_primitive_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.PrimitiveTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        # Nothing to unroll for primitives.
        return []

    # noinspection PyUnusedLocal
    def _unroll_our_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OurTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """
        Generate the code for both our atomic type annotations and references.

        We merged :py:method:`._unroll_our_type_annotation` and
        :py:method:`._unroll_ref_type_annotation` together since they differ in only
        which symbol is unrolled over.
        """
        if not isinstance(type_annotation.symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2021-12-25):
            # We do not descend into other types as this is generating the code
            # only for the non-descend case. The recursive verifier will descend into
            # properties of other classes.
            return []

        cls_name = csharp_naming.class_name(type_annotation.symbol.name)

        joined_pth = "/".join(path)

        return [
            csharp_unrolling.Node(
                text=textwrap.dedent(
                    f"""\
                    Verification.Implementation.Verify{cls_name}(
                    {I}{unrollee_expr},
                    {I}$"{{path}}/{joined_pth}",
                    {I}errors);"""
                ),
                children=[],
            )
        ]

    def _unroll_list_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.ListTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        # Descend into the list items
        item_var = csharp_unrolling.Unroller._loop_var_name(
            level=item_level, suffix="Item"
        )

        children = self.unroll(
            unrollee_expr=item_var,
            type_annotation=type_annotation.items,
            path=path + [f"{{{item_var}}}"],
            item_level=item_level + 1,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        node = csharp_unrolling.Node(
            text=f"foreach (var {item_var} in {unrollee_expr})", children=children
        )

        return [node]

    def _unroll_optional_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OptionalTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        children = self.unroll(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation.value,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )

        if len(children) > 0:
            return [
                csharp_unrolling.Node(
                    text=f"if ({unrollee_expr} != null)", children=children
                )
            ]
        else:
            return []

    def _unroll_ref_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.RefTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        assert isinstance(
            self._ref_association, intermediate.Class
        ), "Assume that the ``ref_association`` is a class so that we don't unroll"

        # We do not descend into classes, this is done in the recursive verifier.
        return []


def _unroll_constrained_primitive_check(
    prop: intermediate.Property, ref_association: intermediate.ClassUnion
) -> Stripped:
    """
    Generate the code for unrolling checking primitive constraints on the property.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    prop_name = csharp_naming.property_name(prop.name)

    unroller = _ConstrainedPrimitiveCheckUnroller(ref_association=ref_association)

    roots = unroller.unroll(
        unrollee_expr=f"that.{prop_name}",
        type_annotation=prop.type_annotation,
        path=[prop_name],
        item_level=0,
        key_value_level=0,
    )

    if len(roots) == 0:
        return Stripped("")

    blocks = [csharp_unrolling.render(root) for root in roots]
    return Stripped("\n\n".join(blocks))


class _InvariantTranspiler(
    parse_tree.RestrictedTransformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile an invariant expression into a code, or an error."""

    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: Mapping[
            Identifier, intermediate_type_inference.TypeAnnotationUnion
        ],
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
            not_antecedent = f"!({antecedent})"

        if not isinstance(node.consequent, no_parentheses_types_in_this_context):
            consequent = Stripped(f"({consequent})")

        return Stripped(f"{not_antecedent}\n" f"|| {consequent}"), None

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
            return Stripped(repr(node.value)), None
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

        return Stripped(csharp_naming.variable_name(node.identifier)), None

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
                value = Stripped(f"({value})")

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors
            )

        # BEFORE-RELEASE (mristin, 2021-12-13):
        #  add heuristic for breaking the lines
        return Stripped(" && ".join(values)), None

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
                value = Stripped(f"({value})")

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors
            )

        # BEFORE-RELEASE (mristin, 2021-12-13):
        #  add heuristic for breaking the lines
        return Stripped(" || ".join(values)), None

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


# noinspection PyProtectedMember,PyProtectedMember
assert all(
    op in _InvariantTranspiler._CSHARP_COMPARISON_MAP for op in parse_tree.Comparator
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_invariant(
    invariant: intermediate.Invariant,
    symbol_table: intermediate.SymbolTable,
    environment: Mapping[Identifier, intermediate_type_inference.TypeAnnotationUnion],
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

    transformer = _InvariantTranspiler(
        type_map=type_inferrer.type_map, environment=environment
    )
    expr, error = transformer.transform(invariant.parsed.body)
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
            textwrap.dedent(
                f"""\
        errors.Add(
        {I}new Verification.Error(
        {II}path,
        {II}"Invariant violated:\\n" +
        """
            ),
            I,
        )
    )

    lines = []  # type: List[str]
    if invariant.description is not None:
        lines = invariant.description.splitlines()

    lines = lines + expr.splitlines()

    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            line_literal = csharp_common.string_literal(line + "\n")
            writer.write(f"{III}{line_literal} +\n")
        else:
            writer.write(f"{III}{csharp_common.string_literal(line)}));")

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation_verify(
    something: Union[intermediate.ConcreteClass, intermediate.ConstrainedPrimitive],
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verify function in the ``Implementation`` class."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    # Build up the environment;
    # see https://craftinginterpreters.com/resolving-and-binding.html
    environment: MutableMapping[
        Identifier, intermediate_type_inference.TypeAnnotationUnion
    ] = {
        Identifier("len"): intermediate_type_inference.BuiltinFunctionTypeAnnotation(
            func=intermediate_type_inference.BuiltinFunction(
                name=Identifier("len"),
                returns=intermediate_type_inference.PrimitiveTypeAnnotation(
                    intermediate_type_inference.PrimitiveType.LENGTH
                ),
            )
        )
    }

    for verification in symbol_table.verification_functions:
        assert verification.name not in environment
        environment[
            verification.name
        ] = intermediate_type_inference.VerificationTypeAnnotation(func=verification)

    assert "self" not in environment
    environment[Identifier("self")] = intermediate_type_inference.OurTypeAnnotation(
        symbol=something
    )

    for invariant in something.invariants:
        invariant_code, error = _transpile_invariant(
            invariant=invariant, symbol_table=symbol_table, environment=environment
        )
        if error is not None:
            errors.append(error)
            continue

        assert invariant_code is not None

        blocks.append(invariant_code)

    if len(errors) > 0:
        return None, Error(
            something.parsed.node,
            f"Failed to parse one or more invariants of the class {something.name!r}",
            errors,
        )

    if isinstance(something, intermediate.ConstrainedPrimitive):
        pass

    elif isinstance(something, intermediate.ConcreteClass):
        for prop in something.properties:
            enum_check_block = _unroll_enumeration_check(
                prop=prop, ref_association=symbol_table.ref_association
            )
            if enum_check_block != "":
                blocks.append(Stripped("if (errors.Full()) return;"))
                blocks.append(enum_check_block)

            constrained_primitive_check = _unroll_constrained_primitive_check(
                prop=prop, ref_association=symbol_table.ref_association
            )
            if constrained_primitive_check != "":
                blocks.append(Stripped("if (errors.Full()) return;"))
                blocks.append(constrained_primitive_check)
    else:
        assert_never(something)

    if len(blocks) == 0:
        blocks.append(Stripped("// There is no verification specified."))

    cls_name = csharp_naming.class_name(something.name)

    that_type = None  # type: Optional[str]
    if isinstance(something, intermediate.ConstrainedPrimitive):
        that_type = csharp_common.PRIMITIVE_TYPE_MAP[something.constrainee]
    elif isinstance(something, intermediate.ConcreteClass):
        that_type = f"Aas.{cls_name}"
    else:
        assert_never(something)

    assert that_type is not None

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            f"""\
        /// <summary>
        /// Verify <paramref name="that" /> and append any errors to
        /// <paramref name="Errors" />.
        ///
        /// The <paramref name="path" /> localizes <paramref name="that" />.
        /// </summary>
        public static void Verify{cls_name} (
        {I}{that_type} that,
        {I}string path,
        {I}Verification.Errors errors)
        {{
        """
        )
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    assert len(errors) == 0
    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation_class(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a private static class, ``Implementation``, with verification logic."""
    errors = []  # type: List[Error]
    blocks = [
        _generate_enum_value_sets(symbol_table=symbol_table)
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            implementation_verify, error = _generate_implementation_verify(
                something=symbol, symbol_table=symbol_table
            )
            if error is not None:
                errors.append(error)
                continue

            assert implementation_verify is not None

            if implementation_verify != "":
                blocks.append(implementation_verify)

        elif isinstance(symbol, intermediate.AbstractClass):
            # No verification of interfaces, and all abstract classes are modeled as
            # interfaces in C#.
            continue

        elif isinstance(symbol, intermediate.ConcreteClass):
            if symbol.is_implementation_specific:
                verify_key = specific_implementations.ImplementationKey(
                    f"Verification/Implementation/verify_{symbol.name}.cs"
                )
                if verify_key not in spec_impls:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The implementation snippet is missing for "
                            f"the ``Verify`` method "
                            f"of the ``Verification.Implementation`` class: {verify_key}",
                        )
                    )
                    continue

                blocks.append(spec_impls[verify_key])
            else:
                implementation_verify, error = _generate_implementation_verify(
                    something=symbol, symbol_table=symbol_table
                )
                if error is not None:
                    errors.append(error)
                    continue

                assert implementation_verify is not None

                if implementation_verify != "":
                    blocks.append(implementation_verify)
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            """\
            /// <summary>
            /// Verify the instances of the model classes non-recursively.
            /// </summary>
            /// <remarks>
            /// The methods provided by this class are re-used in the verification
            /// visitors.
            /// </remarks>
            private static class Implementation
            {{
            """
        )
    )
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // private static class Implementation")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_non_recursive_verifier(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the non-recursive verifier which visits the concrete classes."""
    blocks = [
        Stripped("public readonly Verification.Errors Errors;"),
        Stripped(
            textwrap.dedent(
                f"""\
            /// <summary>
            /// Initialize the visitor with the given <paramref name="errors" />.
            ///
            /// The errors observed during the visitation will be appended to
            /// the <paramref name="errors" />.
            /// </summary>
            NonRecursiveVerifier(Verification.Errors errors)
            {{
            {I}Errors = errors;
            }}"""
            )
        ),
        Stripped(
            textwrap.dedent(
                f"""\
            public void Visit(Aas.IClass that, string context)
            {{
            {I}that.Accept(this, context);
            }}"""
            )
        ),
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.ConcreteClass):
            continue

        cls_name = csharp_naming.class_name(symbol.name)

        blocks.append(
            Stripped(
                textwrap.dedent(
                    f"""\
            /// <summary>
            /// Verify <paramref name="that" /> instance and
            /// append any error to <see cref="Errors" />
            /// where <paramref name="context" /> is used to localize the error.
            /// </summary>
            public void Visit(Aas.{cls_name} that, string context)
            {{
            {I}Implementation.Verify{cls_name}(
            {II}that, context, Errors);
            }}"""
                )
            )
        )

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            f"""\
        /// <summary>
        /// Verify the instances of the model classes non-recursively.
        /// </summary>
        public class NonRecursiveVerifier :
        {I}Visitation.IVisitorWithContext<string>
        {{
        """
        )
    )
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public class NonRecursiveVerifier")

    return Stripped(writer.getvalue()), None


class _RecursionInRecursiveVerifyUnroller(csharp_unrolling.Unroller):
    """Generate the code that unrolls the recursive visits for the given property."""

    #: Symbol to be used to represent references within an AAS
    _ref_association: Final[intermediate.Symbol]

    def __init__(self, ref_association: intermediate.ClassUnion) -> None:
        """Initialize with the given values."""
        self._ref_association = ref_association

    def _unroll_primitive_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.PrimitiveTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        # We can not recurse visits into a primitive.
        return []

    # noinspection PyUnusedLocal
    def _unroll_our_type_or_ref_annotation(
        self,
        unrollee_expr: str,
        type_annotation: Union[
            intermediate.OurTypeAnnotation, intermediate.RefTypeAnnotation
        ],
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """
        Generate the code for both our atomic type annotations and references.

        We merged :py:method:`._unroll_our_type_annotation` and
        :py:method:`._unroll_ref_type_annotation` together since they differ in only
        which symbol is unrolled over.
        """
        symbol = None  # type: Optional[intermediate.Symbol]
        if isinstance(type_annotation, intermediate.OurTypeAnnotation):
            symbol = type_annotation.symbol
        elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
            symbol = self._ref_association
        else:
            assert_never(type_annotation)

        assert symbol is not None

        if isinstance(
            symbol, (intermediate.Enumeration, intermediate.ConstrainedPrimitive)
        ):
            return []

        assert isinstance(symbol, intermediate.Class), "Exhaustive matching"

        joined_pth = "/".join(path)
        return [
            csharp_unrolling.Node(
                text=textwrap.dedent(
                    f"""\
                if (Errors.Full()) return;
                Visit(
                    {unrollee_expr},
                    ${csharp_common.string_literal(joined_pth)});"""
                ),
                children=[],
            )
        ]

    def _unroll_our_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OurTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        return self._unroll_our_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )

    def _unroll_list_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.ListTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        # NOTE (mristin, 2021-12-19):
        # We need to iterate through the list with the index so that we can construct
        # meaningful paths.

        if item_level > 15:
            index_var = f"i{item_level}"
        else:
            # Use letters i, j, k *etc.* first before we resort to i16, i17 *etc.*
            index_var = chr(ord("i") + item_level)

        children = self.unroll(
            unrollee_expr=f"{unrollee_expr}[{index_var}]",
            type_annotation=type_annotation.items,
            path=path + [f"{{{index_var}}}"],
            item_level=item_level + 1,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        text = Stripped(
            f"for(var {index_var} = 0; "
            f"{index_var} < {unrollee_expr}.Count; "
            f"{index_var}++)"
        )

        # Break into lines if too long.
        # This is just a heuristics — we do not consider the actual prefix indention.
        if len(text) > 50:
            text = Stripped(
                textwrap.dedent(
                    f"""\
                    for(
                    {I}var {index_var} = 0;
                    {I}{index_var} < {unrollee_expr}.Count;
                    {I}{index_var}++)"""
                )
            )

        return [csharp_unrolling.Node(text=text, children=children)]

    def _unroll_optional_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OptionalTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        children = self.unroll(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation.value,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )
        if len(children) > 0:
            return [
                csharp_unrolling.Node(
                    text=f"if ({unrollee_expr} != null)", children=children
                )
            ]
        else:
            return []

    def _unroll_ref_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.RefTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        return self._unroll_our_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )


def _unroll_recursion_in_recursive_verify(
    prop: intermediate.Property, ref_association: intermediate.ClassUnion
) -> Stripped:
    """
    Generate the code for unrolling the recursive visits  for the given property.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """

    prop_name = csharp_naming.property_name(prop.name)

    unroller = _RecursionInRecursiveVerifyUnroller(ref_association=ref_association)
    roots = unroller.unroll(
        unrollee_expr=f"that.{prop_name}",
        type_annotation=prop.type_annotation,
        path=["{context}", prop_name],
        item_level=0,
        key_value_level=0,
    )

    if len(roots) == 0:
        return Stripped("")

    blocks = [csharp_unrolling.render(root) for root in roots]
    return Stripped("\n\n".join(blocks))


# fmt: on
@require(
    lambda cls: not cls.is_implementation_specific,
    "Implementation-specific classes are handled elsewhere",
)
# fmt: off
def _generate_recursive_verifier_visit(
        cls: intermediate.ConcreteClass,
        ref_association: intermediate.ClassUnion
) -> Stripped:
    """
    Generate the ``Visit`` method of the ``RecursiveVerifier`` for the ``cls``.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    cls_name = csharp_naming.class_name(cls.name)

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        /// <summary>
        /// Verify recursively <paramref name="that" /> instance and
        /// append any error to <see cref="Errors" />
        /// where <paramref name="context" /> is used to localize the error.
        /// </summary>
        public void Visit({cls_name} that, string context)
        {{
        '''))

    blocks = [
        Stripped(textwrap.dedent(f'''\
        Implementation.Verify{cls_name}(
        {I}that, context, Errors);'''))
    ]  # type: List[Stripped]

    # region Unroll

    recursion_ends_here = True
    for prop in cls.properties:
        unrolled_prop_verification = _unroll_recursion_in_recursive_verify(
            prop=prop,
            ref_association=ref_association
        )

        if unrolled_prop_verification != '':
            blocks.append(unrolled_prop_verification)
            recursion_ends_here = False

    if recursion_ends_here:
        blocks.append(Stripped("// The recursion ends here."))
    # endregion

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, I))

    writer.write('\n}')
    return Stripped(writer.getvalue())


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_recursive_verifier(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the ``Verifier`` class which visits the classes and verifies them."""
    blocks = [
        Stripped("public readonly Errors Errors;"),
        Stripped(
            textwrap.dedent(
                f"""\
            /// <summary>
            /// Initialize the visitor with the given <paramref name="errors" />.
            ///
            /// The errors observed during the visitation will be appended to
            /// the <paramref name="errors" />.
            /// </summary>
            RecursiveVerifier(Errors errors)
            {{
            {I}Errors = errors;
            }}"""
            )
        ),
        Stripped(
            textwrap.dedent(
                f"""\
            public void Visit(IClass that, string context)
            {{
            {I}that.Accept(this, context);
            }}"""
            )
        ),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.ConcreteClass):
            continue

        if symbol.is_implementation_specific:
            visit_key = specific_implementations.ImplementationKey(
                f"Verification/RecursiveVerifier/visit_{symbol.name}.cs"
            )

            implementation = spec_impls.get(visit_key, None)
            if implementation is None:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The implementation snippet is missing for "
                        f"the ``Visit`` method "
                        f"of the ``Verification.RecursiveVerifier`` class: "
                        f"{visit_key}",
                    )
                )
                continue

            blocks.append(implementation)
        else:
            blocks.append(
                _generate_recursive_verifier_visit(
                    cls=symbol, ref_association=symbol_table.ref_association
                )
            )

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            f"""\
        /// <summary>
        /// Verify the instances of the model classes recursively.
        /// </summary>
        public class RecursiveVerifier :
        {I}Visitation.IVisitorWithContext<string>
        {{
        """
        )
    )
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public class RecursiveVerifier")

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
        Stripped(
            textwrap.dedent(
                f"""\
            using Regex = System.Text.RegularExpressions.Regex;
            using System.Collections.Generic;  // can't alias
            using System.Collections.ObjectModel;  // can't alias
            using System.Linq;  // can't alias"

            using Aas = {namespace};
            using Visitation = {namespace}.Visitation;"""
            )
        ),
    ]  # type: List[Stripped]

    verification_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    for implementation_key in [
        specific_implementations.ImplementationKey("Verification/Error.cs"),
        specific_implementations.ImplementationKey("Verification/Errors.cs"),
    ] + [
        specific_implementations.ImplementationKey(f"Verification/{func.name}.cs")
        for func in symbol_table.verification_functions
        if isinstance(func, intermediate.ImplementationSpecificVerification)
    ]:
        implementation = spec_impls.get(implementation_key, None)
        if implementation is None:
            errors.append(Error(None, f"The snippet is missing: {implementation_key}"))
        else:
            verification_blocks.append(implementation)

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

    implementation_class, implementation_class_errors = _generate_implementation_class(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if implementation_class_errors:
        errors.extend(implementation_class_errors)
    else:
        assert implementation_class is not None

        verification_blocks.append(implementation_class)

    non_recursive, non_recursive_errors = _generate_non_recursive_verifier(
        symbol_table=symbol_table
    )

    if non_recursive_errors is not None:
        errors.extend(non_recursive_errors)
    else:
        assert non_recursive is not None

        verification_blocks.append(non_recursive)

    recursive, recursive_errors = _generate_recursive_verifier(
        symbol_table=symbol_table, spec_impls=spec_impls
    )

    if recursive_errors is not None:
        errors.extend(recursive_errors)
    else:
        assert recursive is not None

        verification_blocks.append(recursive)

    if len(errors) > 0:
        return None, errors

    verification_writer = io.StringIO()
    verification_writer.write(f"namespace {namespace}\n{{\n")
    verification_writer.write(f"{I}public static class Verification\n" f"{I}{{\n")

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
