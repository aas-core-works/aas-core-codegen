"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
from typing import Tuple, Optional, List, Sequence, Union, Final

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import Error, Stripped, assert_never
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    unrolling as csharp_unrolling,
)
from aas_core_codegen.csharp.common import INDENT as I, INDENT2 as II, INDENT3 as III
from aas_core_codegen.parse import tree as parse_tree


# region Verify


def verify(
        spec_impls: specific_implementations.SpecificImplementations,
        verification_functions: Sequence[intermediate.Method]
) -> Optional[List[str]]:
    """Verify all the implementation snippets related to verification."""
    errors = []  # type: List[str]

    expected_keys = [
        specific_implementations.ImplementationKey("Verification/Error.cs"),
        specific_implementations.ImplementationKey("Verification/Errors.cs"),
    ]

    for func in verification_functions:
        expected_keys.append(
            specific_implementations.ImplementationKey(f"Verification/{func.name}.cs"),
        )

    for key in expected_keys:
        if key not in spec_impls:
            errors.append(f"The implementation snippet is missing for: {key}")

    if len(errors) == 0:
        return None

    return errors


# endregion

# region Generate


def _generate_enum_value_sets(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate a class that pre-computes the sets of allowed enumeration literals."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Enumeration):
            continue

        enum_name = csharp_naming.enum_name(symbol.name)
        blocks.append(
            Stripped(
                f"public static HashSet<int> For{enum_name} = new HashSet<int>(\n"
                f"{I}System.Enum.GetValues(typeof(Aas.{enum_name})).Cast<int>());"
            )
        )

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
    _ref_association: Final[intermediate.Symbol]

    def __init__(
            self,
            ref_association: intermediate.Symbol
    ) -> None:
        """Initialize with the given values."""
        self._ref_association = ref_association

    def _unroll_builtin_atomic_type_annotation(
            self,
            unrollee_expr: str,
            type_annotation: intermediate.BuiltinAtomicTypeAnnotation,
            path: List[str],
            item_level: int,
            key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        # Built-ins are not enumerations, so nothing to check here.
        return []

    # noinspection PyUnusedLocal
    def _unroll_our_atomic_type_or_ref_annotation(
            self,
            unrollee_expr: str,
            type_annotation: Union[
                intermediate.OurAtomicTypeAnnotation,
                intermediate.RefTypeAnnotation
            ],
            path: List[str],
            item_level: int,
            key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """
        Generate the code for both our atomic type annotations and references.

        We merged :py:method:`._unroll_our_atomic_type_annotation` and
        :py:method:`._unroll_ref_type_annotation` together since they differ in only
        which symbol is unrolled over.
        """
        symbol = None  # type: Optional[intermediate.Symbol]
        if isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
            symbol = type_annotation.symbol
        elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
            symbol = self._ref_association
        else:
            assert_never(type_annotation)

        assert symbol is not None

        if not isinstance(symbol, intermediate.Enumeration):
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

    def _unroll_our_atomic_type_annotation(
            self,
            unrollee_expr: str,
            type_annotation: intermediate.OurAtomicTypeAnnotation,
            path: List[str],
            item_level: int,
            key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        return self._unroll_our_atomic_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level
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
            level=item_level, suffix="Item")

        children = self.unroll(
            unrollee_expr=item_var,
            type_annotation=type_annotation.items,
            path=path + [f"{{item_var}}"],
            item_level=item_level + 1,
            key_value_level=key_value_level
        )

        if len(children) == 0:
            return []

        node = csharp_unrolling.Node(
            text=f"foreach (var {item_var} in {unrollee_expr}", children=children
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
            key_value_level=key_value_level
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
        return self._unroll_our_atomic_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level
        )


def _unroll_enumeration_check(
        prop: intermediate.Property,
        ref_association: intermediate.Symbol
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
        key_value_level=0
    )

    if len(roots) == 0:
        return Stripped("")

    blocks = [csharp_unrolling.render(root) for root in roots]
    return Stripped("\n\n".join(blocks))


class _InvariantTranspiler(
    parse_tree.Transformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile an invariant expression into a code, or an error."""

    def __init__(self, symbol_table: intermediate.SymbolTable) -> None:
        """Initialize with the given values."""
        self.symbol_table = symbol_table

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform(
            self, node: parse_tree.Node
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        """Dispatch to the appropriate transformation method."""
        return node.transform(self)

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_member(
            self, node: parse_tree.Member
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        instance, error = self.transform(node.instance)
        if error is not None:
            return None, error

        # Special case: enumeration literal
        if isinstance(node.instance, parse_tree.Name):
            symbol = self.symbol_table.find(name=node.instance.identifier)
            if symbol is not None and isinstance(symbol, intermediate.Enumeration):
                enumeration_name = csharp_naming.enum_name(symbol.name)
                enum_literal_name = csharp_naming.enum_literal_name(node.name)

                return Stripped(f"{enumeration_name}.{enum_literal_name}"), None

        prop_name = csharp_naming.property_name(node.name)

        if isinstance(node.instance, (parse_tree.Name, parse_tree.Member)):
            return Stripped(f"{instance}.{prop_name}"), None

        return Stripped(f"({instance}).{prop_name}"), None

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

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
        )

        if isinstance(node.antecedent, no_parentheses_types):
            not_antecedent = f"!{antecedent}"
        else:
            not_antecedent = f"!({antecedent})"

        if not isinstance(node.consequent, no_parentheses_types):
            consequent = f"({consequent})"

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

            args.append(arg)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the method call", errors
            )

        assert instance is not None

        if not isinstance(node.member.instance, (parse_tree.Name, parse_tree.Member)):
            instance = f"({instance})"

        method_name = csharp_naming.method_name(node.member.name)

        # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
        #  add heuristic for breaking the lines
        joined_args = ", ".join(args)

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

            args.append(arg)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the function call", errors
            )

        # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
        #  add heuristic for breaking the lines
        joined_args = ", ".join(args)

        verification_function = self.symbol_table.verification_functions_by_name.get(
            node.name, None)

        # NOTE (mristin, 2021-12-16):
        # The validity of the arguments is checked in
        # :py:func:`aas_core_codegen.intermediate._translate.translate`, so we do not
        # have to test for argument arity here.

        if verification_function is not None:
            method_name = csharp_naming.method_name(verification_function.name)
            return Stripped(f"Verification.{method_name}({joined_args})"), None

        elif node.name == "len":
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

            return Stripped(f"{collection}.Count"), None
        else:
            return None, Error(
                node.original_node,
                f"The handling of the function is not implemented: {node.name}",
            )

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

        no_parentheses_types = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
        )
        if isinstance(node.value, no_parentheses_types):
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

            if not isinstance(
                    value_node,
                    (
                            parse_tree.Member,
                            parse_tree.MethodCall,
                            parse_tree.FunctionCall,
                            parse_tree.Comparison,
                            parse_tree.Name,
                    ),
            ):
                value = f"({value})"

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors
            )

        # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
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

            if not isinstance(
                    value_node,
                    (
                            parse_tree.Member,
                            parse_tree.MethodCall,
                            parse_tree.FunctionCall,
                            parse_tree.Comparison,
                            parse_tree.Name,
                    ),
            ):
                value = f"({value})"

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors
            )

        # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
        #  add heuristic for breaking the lines
        return Stripped(" || ".join(values)), None

    def transform_declaration(
            self, node: parse_tree.Declaration
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
        #  implement once we got to end-to-end with serialization
        raise NotImplementedError()

    def transform_expression_with_declarations(
            self, node: parse_tree.ExpressionWithDeclarations
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        # TODO-BEFORE-RELEASE (mristin, 2021-12-13):
        #  implement once we got to end-to-end with serialization
        raise NotImplementedError()


# noinspection PyProtectedMember,PyProtectedMember
assert all(
    op in _InvariantTranspiler._CSHARP_COMPARISON_MAP for op in parse_tree.Comparator
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_invariant(
        invariant: intermediate.Invariant, symbol_table: intermediate.SymbolTable
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

    transformer = _InvariantTranspiler(symbol_table=symbol_table)
    expr, error = transformer.transform(invariant.parsed.body)
    if error is not None:
        return None, error

    writer = io.StringIO()
    if len(expr) > 50 or "\n" in expr:
        writer.write("if (!(\n")
        writer.write(textwrap.indent(expr, I))
        writer.write("))\n{\n")
    else:
        if isinstance(
                invariant.parsed.body,
                (
                        parse_tree.Name,
                        parse_tree.Member,
                        parse_tree.MethodCall,
                        parse_tree.FunctionCall,
                ),
        ):
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
        cls: intermediate.Class, symbol_table: intermediate.SymbolTable
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verify function in the ``Implementation`` class."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    cls_name = csharp_naming.class_name(cls.name)

    if len(cls.invariants) == 0:
        blocks.append(Stripped(f"// There are no invariants defined for {cls_name}."))
    else:
        for invariant in cls.invariants:
            invariant_code, error = _transpile_invariant(
                invariant=invariant, symbol_table=symbol_table
            )
            if error is not None:
                errors.append(error)
                continue

            blocks.append(invariant_code)

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node,
            f"Failed to parse one or more invariants of the class {cls}",
            errors,
        )

    for prop in cls.properties:
        enum_check_block = _unroll_enumeration_check(
            prop=prop, ref_association=symbol_table.ref_association)
        if enum_check_block != "":
            blocks.append(Stripped("if (errors.Full()) return;"))
            blocks.append(enum_check_block)

    if len(blocks) == 0:
        blocks.append(
            Stripped(f"// There is no verification specified for {cls_name}.")
        )

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            f"""\
        /// <summary>
        /// Verify <paramref name="that" /> instance and 
        /// append any errors to <paramref name="Errors" />.
        /// 
        /// The <paramref name="path" /> localizes <paramref name="that" /> instance.
        /// </summary>
        public static void Verify{cls_name} (
        {I}Aas.{cls_name} that,
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
        if isinstance(symbol, (intermediate.Enumeration, intermediate.Interface)):
            continue

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
                cls=symbol, symbol_table=symbol_table
            )
            if error is not None:
                errors.append(error)
                continue

            if implementation_verify != "":
                blocks.append(implementation_verify)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        textwrap.dedent(
            f"""\
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
    """Generate the non-recursive verifier which visits the classes."""
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
        if not isinstance(symbol, intermediate.Class):
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

    def __init__(
            self,
            ref_association: intermediate.Symbol
    ) -> None:
        """Initialize with the given values."""
        self._ref_association = ref_association

    def _unroll_builtin_atomic_type_annotation(
            self,
            unrollee_expr: str,
            type_annotation: intermediate.BuiltinAtomicTypeAnnotation,
            path: List[str],
            item_level: int,
            key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        # We can not recurse visits into an atomic built-in.
        return []

    # noinspection PyUnusedLocal
    def _unroll_our_atomic_type_or_ref_annotation(
            self,
            unrollee_expr: str,
            type_annotation: Union[
                intermediate.OurAtomicTypeAnnotation,
                intermediate.RefTypeAnnotation
            ],
            path: List[str],
            item_level: int,
            key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """
        Generate the code for both our atomic type annotations and references.

        We merged :py:method:`._unroll_our_atomic_type_annotation` and
        :py:method:`._unroll_ref_type_annotation` together since they differ in only
        which symbol is unrolled over.
        """
        symbol = None  # type: Optional[intermediate.Symbol]
        if isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
            symbol = type_annotation.symbol
        elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
            symbol = self._ref_association
        else:
            assert_never(type_annotation)

        assert symbol is not None

        if isinstance(symbol, intermediate.Enumeration):
            return []

        assert isinstance(symbol, (intermediate.Class, intermediate.Interface))

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

    def _unroll_our_atomic_type_annotation(
            self,
            unrollee_expr: str,
            type_annotation: intermediate.OurAtomicTypeAnnotation,
            path: List[str],
            item_level: int,
            key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        return self._unroll_our_atomic_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level
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
            item_level=item_level+1,
            key_value_level=key_value_level
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
            key_value_level=key_value_level
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
        return self._unroll_our_atomic_type_or_ref_annotation(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level
        )


def _unroll_recursion_in_recursive_verify(
        prop: intermediate.Property,
        ref_association: intermediate.Symbol
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
        key_value_level=0
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
        cls: intermediate.Class,
        ref_association: intermediate.Symbol
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
        if not isinstance(symbol, intermediate.Class):
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
                    cls=symbol,
                    ref_association=symbol_table.ref_association))

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
                                  specific_implementations.ImplementationKey(
                                      "Verification/Error.cs"),
                                  specific_implementations.ImplementationKey(
                                      "Verification/Errors.cs"),
                              ] + [
                                  specific_implementations.ImplementationKey(
                                      f"Verification/{func.name}.cs")
                                  for func in symbol_table.verification_functions
                              ]:
        implementation = spec_impls.get(implementation_key, None)
        if implementation is None:
            errors.append(Error(None, f"The snippet is missing: {implementation_key}"))
        else:
            verification_blocks.append(implementation)

    implementation_class, implementation_class_errors = _generate_implementation_class(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if implementation_class_errors:
        errors.extend(implementation_class_errors)
    else:
        verification_blocks.append(implementation_class)

    non_recursive, non_recursive_errors = _generate_non_recursive_verifier(
        symbol_table=symbol_table
    )

    if non_recursive_errors is not None:
        errors.extend(non_recursive_errors)
    else:
        verification_blocks.append(non_recursive)

    recursive, recursive_errors = _generate_recursive_verifier(
        symbol_table=symbol_table, spec_impls=spec_impls
    )

    if recursive_errors is not None:
        errors.extend(recursive_errors)
    else:
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
