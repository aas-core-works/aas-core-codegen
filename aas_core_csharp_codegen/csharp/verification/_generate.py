"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
from typing import Tuple, Optional, List, Mapping

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen.common import Error, Stripped, Rstripped, assert_never, \
    Identifier
from aas_core_csharp_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    unrolling as csharp_unrolling
)
from aas_core_csharp_codegen.csharp import specific_implementations
from aas_core_csharp_codegen.parse import (tree as parse_tree)
from aas_core_csharp_codegen.specific_implementations import ImplementationKey


# region Verify

def verify(
        spec_impls: specific_implementations.SpecificImplementations
) -> Optional[List[str]]:
    """Verify all the implementation snippets related to verification."""
    errors = []  # type: List[str]

    expected_keys = [
        'Verification/is_IRI', 'Verification/is_IRDI', 'Verification/is_ID_short',
        'Verification/Error', 'Verification/Errors'
    ]
    for key in expected_keys:
        if ImplementationKey(key) not in spec_impls:
            errors.append(f"The implementation snippet is missing for: {key}")

    if len(errors) == 0:
        return None

    return errors


# endregion

# region Generate


def _generate_pattern_class(
        spec_impls: specific_implementations.SpecificImplementations
) -> Stripped:
    """Generate the Pattern class used for verifying different patterns."""
    blocks = [
        spec_impls[ImplementationKey('Verification/is_IRI')],
        spec_impls[ImplementationKey('Verification/is_IRDI')],
        spec_impls[ImplementationKey('Verification/is_ID_short')]
    ]  # type: List[str]

    writer = io.StringIO()
    writer.write('public static class Pattern\n{\n')
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block.strip(), csharp_common.INDENT))

    writer.write('\n}')
    return Stripped(writer.getvalue())


def _generate_enum_value_sets(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate a class that pre-computes the sets of allowed enumeration literals."""
    blocks = []  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Enumeration):
            continue

        enum_name = csharp_naming.enum_name(symbol.name)
        blocks.append(Stripped(
            f"public static HashSet<int> For{enum_name} = new HashSet<int>(\n"
            f"{csharp_common.INDENT}System.Enum.GetValues(typeof({enum_name})).Cast<int>());"))

    writer = io.StringIO()
    writer.write(textwrap.dedent('''\
        /// <summary>
        /// Hash allowed enum values for efficient validation of enums.
        /// </summary> 
        private static class EnumValueSet
        {
        '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}  // private static class EnumValueSet')

    return Stripped(writer.getvalue())


def _unroll_enumeration_check(prop: intermediate.Property) -> Stripped:
    """Generate the code for unrolling the enumeration checks for the given property."""

    @require(lambda var_index: var_index >= 0)
    @require(lambda suffix: suffix in ("Item", "KeyValue"))
    def var_name(var_index: int, suffix: str) -> Identifier:
        """Generate the name of the loop variable."""
        if var_index == 0:
            if suffix == 'Item':
                return Identifier(f"an{suffix}")
            else:
                assert suffix == 'KeyValue'
                return Identifier(f"a{suffix}")

        elif var_index == 1:
            return Identifier(f"another{suffix}")
        else:
            return Identifier("yet" + "Yet" * (var_index - 1) + f"another{suffix}")

    prop_name = csharp_naming.property_name(prop.name)

    def unroll(
            current_var_name: str,
            item_count: int,
            key_value_count: int,
            path: List[str],
            type_anno: intermediate.TypeAnnotation
    ) -> List[csharp_unrolling.Node]:
        """Generate the node corresponding to the ``type_anno`` and recurse."""
        if isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
            return []

        elif isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
            if not isinstance(type_anno.symbol, intermediate.Enumeration):
                return []

            enum_name = csharp_naming.enum_name(type_anno.symbol.name)
            joined_pth = '/'.join(path)

            return [
                csharp_unrolling.Node(
                    text=textwrap.dedent(f'''\
                    if (!EnumValueSet.For{enum_name}.Contains(
                    {csharp_common.INDENT2}(int){current_var_name}))
                    {{
                    {csharp_common.INDENT}errors.Add(
                    {csharp_common.INDENT2}new Error(
                    {csharp_common.INDENT3}$"{{path}}/{joined_pth}",
                    {csharp_common.INDENT3}$"Invalid {{nameof({enum_name})}}: {{{current_var_name}}}"));
                    }}'''),
                    children=[])]

        elif isinstance(type_anno, (
                intermediate.ListTypeAnnotation, intermediate.SequenceTypeAnnotation,
                intermediate.SetTypeAnnotation)):
            item_var = var_name(item_count, "Item")

            children = unroll(
                current_var_name=item_var,
                item_count=item_count + 1,
                key_value_count=key_value_count,
                path=path + [f'{{{item_var}}}'],
                type_anno=type_anno.items)

            if len(children) == 0:
                return []

            node = csharp_unrolling.Node(
                text=f"foreach (var {item_var} in {current_var_name}",
                children=children)

            return [node]

        elif isinstance(type_anno, (
                intermediate.MappingTypeAnnotation,
                intermediate.MutableMappingTypeAnnotation
        )):
            key_value_var = var_name(key_value_count + 1, "KeyValue")

            key_children = unroll(
                current_var_name=f'{key_value_var}.Key',
                item_count=item_count,
                key_value_count=key_value_count + 1,
                path=path + [f'{{{key_value_var}.Key}}'],
                type_anno=type_anno.keys)

            value_children = unroll(
                current_var_name=f'{key_value_var}.Value',
                item_count=item_count,
                key_value_count=key_value_count + 1,
                path=path + [f'{{{key_value_var}.Key}}'],
                type_anno=type_anno.values)

            children = key_children + value_children

            if len(children) > 0:
                return [csharp_unrolling.Node(
                    text=f'foreach (var {key_value_var} in {current_var_name})',
                    children=children)]
            else:
                return []

        elif isinstance(type_anno, intermediate.OptionalTypeAnnotation):
            children = unroll(
                current_var_name=current_var_name,
                item_count=item_count,
                key_value_count=key_value_count,
                path=path,
                type_anno=type_anno.value)
            if len(children) > 0:
                return [csharp_unrolling.Node(
                    text=f"if ({current_var_name} != null)", children=children)]
            else:
                return []
        else:
            assert_never(type_anno)

    roots = unroll(
        current_var_name=f'that.{prop_name}',
        item_count=0,
        key_value_count=0,
        path=[prop_name],
        type_anno=prop.type_annotation)

    if len(roots) == 0:
        return Stripped('')

    blocks = [csharp_unrolling.render(root) for root in roots]
    return Stripped('\n\n'.join(blocks))


def _transpile_expression(
        expr: parse_tree.Expression,
        environment: Mapping[str, Stripped]
) -> Stripped:
    """
    Transpile the given expression ``expr``.

    The ``environment`` defines how names should be mapped to outer scope
    in the C# code.
    """
    # TODO: refactor this into a visitor once finished

    # TODO: watch out! This is only a minimal implementation for our presentation in
    #  November 2021. The real implementation needs to go to a separate module!
    if isinstance(expr, parse_tree.Name):
        environment_var = environment.get(expr.identifier, None)
        if environment_var is not None:
            return environment_var

        return Stripped(expr.identifier)

    elif isinstance(expr, parse_tree.Member):
        instance = _transpile_expression(expr=expr.instance, environment=environment)
        member_name = csharp_naming.property_name(expr.name)

        if isinstance(expr.instance, (parse_tree.Member, parse_tree.Name)):
            return Stripped(f"{instance}.{member_name}")
        else:
            return Stripped(f"({instance}).{member_name}")


class _InvariantTranspiler(
    parse_tree.Transformer[Tuple[Optional[Stripped], Optional[Error]]]):
    """Transpile an invariant expression into a code, or an error."""

    def __init__(self, symbol_table: intermediate.SymbolTable) -> None:
        """Initialize with the given values."""
        self.symbol_table = symbol_table

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform(
            self,
            node: parse_tree.Node
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        """Dispatch to the appropriate transformation method."""
        return node.transform(self)

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_member(
            self,
            node: parse_tree.Member
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
        parse_tree.Comparator.NE: "!="
    }

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_comparison(
            self,
            node: parse_tree.Comparison
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
                node.original_node, "Failed to transpile the comparison", errors)

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name,
            parse_tree.Constant
        )

        if (
                isinstance(node.left, no_parentheses_types)
                and isinstance(node.right, no_parentheses_types)
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
                node.original_node, "Failed to transpile the implication", errors)

        assert antecedent is not None
        assert consequent is not None

        no_parentheses_types = (
            parse_tree.Member,
            parse_tree.FunctionCall,
            parse_tree.MethodCall,
            parse_tree.Name
        )

        if isinstance(node.antecedent, no_parentheses_types):
            not_antecedent = f"!{antecedent}"
        else:
            not_antecedent = f"!({antecedent})"

        if not isinstance(node.consequent, no_parentheses_types):
            consequent = f"({consequent})"

        return Stripped(
                f"{not_antecedent}\n"
                f"|| {consequent}"), None

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
                node.original_node, "Failed to transpile the method call", errors)

        assert instance is not None

        if not isinstance(node.member.instance, (parse_tree.Name, parse_tree.Member)):
            instance = f"({instance})"

        method_name = csharp_naming.method_name(node.member.name)

        # TODO: add heuristic for breaking the lines
        joined_args = ", ".join(args)

        return Stripped(f"{instance}.{method_name}({joined_args})"), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_function_call(
            self,
            node: parse_tree.FunctionCall
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
                node.original_node, "Failed to transpile the function call", errors)

        # TODO: add heuristic for breaking the lines
        joined_args = ", ".join(args)

        if node.name == "is_IRDI":
            if len(args) != 1:
                return None, Error(node.original_node, "Expected exactly one argument")

            return Stripped(f"Pattern.IsIrdi({joined_args})"), None
        elif node.name == "is_IRI":
            if len(args) != 1:
                return None, Error(node.original_node, "Expected exactly one argument")

            return Stripped(f"Pattern.IsIri({joined_args})"), None
        elif node.name == "is_ID_short":
            if len(args) != 1:
                return None, Error(node.original_node, "Expected exactly one argument")

            return Stripped(f"Pattern.IsIdShort({joined_args})"), None
        elif node.name == "len":
            if len(args) != 1:
                return None, Error(node.original_node, "Expected exactly one argument")

            collection_node = node.args[0]
            if not isinstance(
                    collection_node,
                    (parse_tree.Name, parse_tree.Member, parse_tree.MethodCall)
            ):
                collection = f"({args[0]})"
            else:
                collection = args[0]

            return Stripped(f"{collection}.Count"), None
        else:
            return None, Error(
                node.original_node,
                f"The handling of the function is not implemented: {node.name}")

    def transform_constant(
            self,
            node: parse_tree.Constant
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
            parse_tree.FunctionCall
        )
        if isinstance(node.value, no_parentheses_types):
            return Stripped(f"{value} == null"), None
        else:
            return Stripped(f"({value}) == null"), None

    def transform_is_not_none(
            self,
            node: parse_tree.IsNotNone
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        value, error = self.transform(node.value)
        if error is not None:
            return None, error

        no_parentheses_types = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall
        )
        if isinstance(node.value, no_parentheses_types):
            return Stripped(f"{value} != null"), None
        else:
            return Stripped(f"({value}) != null"), None

    def transform_name(
            self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier == 'self':
            # The ``that`` refers to the argument of the verification function.
            return Stripped("that"), None

        return Stripped(csharp_naming.variable_name(node.identifier)), None

    def transform_and(
            self,
            node: parse_tree.And) -> Tuple[Optional[Stripped], Optional[Error]]:
        errors = []  # type: List[Error]
        values = []  # type: List[Stripped]

        for value_node in node.values:
            value, error = self.transform(value_node)
            if error is not None:
                errors.append(error)
                continue

            if not isinstance(value_node, (
                    parse_tree.Member,
                    parse_tree.MethodCall,
                    parse_tree.FunctionCall,
                    parse_tree.Comparison,
                    parse_tree.Name
            )):
                value = f"({value})"

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors)

        # TODO: add heuristic for breaking the lines
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

            if not isinstance(value_node, (
                    parse_tree.Member,
                    parse_tree.MethodCall,
                    parse_tree.FunctionCall,
                    parse_tree.Comparison,
                    parse_tree.Name
            )):
                value = f"({value})"

            values.append(value)

        if len(errors) > 0:
            return None, Error(
                node.original_node, "Failed to transpile the conjunction", errors)

        # TODO: add heuristic for breaking the lines
        return Stripped(" || ".join(values)), None

    def transform_declaration(
            self,
            node: parse_tree.Declaration
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        # TODO: implement once we got to end-to-end with serialization
        raise NotImplementedError()

    def transform_expression_with_declarations(
            self,
            node: parse_tree.ExpressionWithDeclarations
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        # TODO: implement once we got to end-to-end with serialization
        raise NotImplementedError()


# noinspection PyProtectedMember,PyProtectedMember
assert all(
    op in _InvariantTranspiler._CSHARP_COMPARISON_MAP
    for op in parse_tree.Comparator
)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_invariant(
        invariant: intermediate.Invariant,
        symbol_table: intermediate.SymbolTable
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Translate the invariant from the meta-model into C# code."""
    # NOTE (mristin, 2021-10-24):
    # We manually transpile the invariant from our custom syntax without additional
    # semantic analysis in the :py:mod:`aas_core_csharp_codegen.intermediate` layer.
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
    if len(expr) > 50 or '\n' in expr:
        writer.write("if (!(\n")
        writer.write(textwrap.indent(expr, csharp_common.INDENT))
        writer.write("))\n{\n")
    else:
        if isinstance(
                invariant.parsed.body,
                (parse_tree.Name, parse_tree.Member, parse_tree.MethodCall,
                 parse_tree.FunctionCall)
        ):
            not_expr = f"!{expr}"
        else:
            not_expr = f"!({expr})"

        writer.write(f"if ({not_expr})\n{{\n")

    writer.write(textwrap.dedent(f'''\
        {csharp_common.INDENT}errors.Add(
        {csharp_common.INDENT2}new Error(
        {csharp_common.INDENT3}path,
        {csharp_common.INDENT3}"Invariant violated:\\n" +
        '''))

    lines = []  # type: List[str]
    if invariant.description is not None:
        lines = invariant.description.splitlines()

    lines = lines + expr.splitlines()

    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            line_literal = csharp_common.string_literal(line + "\n")
            writer.write(
                f'{csharp_common.INDENT3}{line_literal} +\n')
        else:
            writer.write(
                f'{csharp_common.INDENT3}{csharp_common.string_literal(line)}));')

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation_verify(
        cls: intermediate.Class,
        symbol_table: intermediate.SymbolTable
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verify function in the ``Implementation`` class."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    cls_name = csharp_naming.class_name(cls.name)

    if len(cls.invariants) == 0:
        blocks.append(Stripped(f'// There are no invariants defined for {cls_name}.'))
    else:
        for invariant in cls.invariants:
            invariant_code, error = _transpile_invariant(
                invariant=invariant, symbol_table=symbol_table)
            if error is not None:
                errors.append(error)
                continue

            blocks.append(invariant_code)

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node,
            f"Failed to parse one or more invariants of the class {cls}",
            underlying=errors)

    for prop in cls.properties:
        enum_check_block = _unroll_enumeration_check(prop=prop)
        if enum_check_block != '':
            blocks.append(Stripped("if (errors.Full()) return;"))
            blocks.append(enum_check_block)

    if len(blocks) == 0:
        blocks.append(Stripped(
            f'// There is no verification specified for {cls_name}.'))

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        /// <summary>
        /// Verify <paramref name="that" /> instance and 
        /// append any errors to <paramref name="Errors" />.
        /// 
        /// The <paramref name="path" /> localizes <paramref name="that" /> instance.
        /// </summary>
        public static void Verify{cls_name} (
        {csharp_common.INDENT}{cls_name} that,
        {csharp_common.INDENT}string path,
        {csharp_common.INDENT}Errors errors)
        {{
        '''))

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')
        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}')

    assert len(errors) == 0
    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a private static class, ``Implementation``, with verification logic."""
    errors = []  # type: List[Error]
    blocks = [
        _generate_enum_value_sets(symbol_table=symbol_table)
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, (intermediate.Enumeration, intermediate.Interface)):
            continue

        if symbol.implementation_key is not None:
            verify_key = ImplementationKey(
                f'Verification/Implementation/verify_{symbol.name}')
            if verify_key not in spec_impls:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The implementation snippet is missing for "
                        f"the ``Verify`` method "
                        f"of the ``Verification.Implementation`` class: {verify_key}"))
                continue

            blocks.append(spec_impls[verify_key])
        else:
            implementation_verify, error = _generate_implementation_verify(
                cls=symbol, symbol_table=symbol_table)
            if error is not None:
                errors.append(error)
                continue

            if implementation_verify != '':
                blocks.append(implementation_verify)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
            /// <summary>
            /// Verify the instances of the model entities non-recursively.
            /// </summary>
            /// <remarks>
            /// The methods provided by this class are re-used in the verification
            /// visitors.
            /// </remarks>
            private static class Implementation
            {{
            '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}  // private static class Implementation')

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_non_recursive_verifier(
        symbol_table: intermediate.SymbolTable
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the non-recursive verifier which visits the entities."""
    blocks = [
        Stripped("public readonly Errors Errors;"),
        Stripped(textwrap.dedent(f'''\
            /// <summary>
            /// Initialize the visitor with the given <paramref name="errors" />.
            ///
            /// The errors observed during the visitation will be appended to
            /// the <paramref name="errors" />.
            /// </summary>
            NonRecursiveVerifier(Errors errors)
            {{
            {csharp_common.INDENT}Errors = errors;
            }}''')),
        Stripped(textwrap.dedent(f'''\
            public void Visit(IEntity that, string context)
            {{
            {csharp_common.INDENT}that.Accept(this, context);
            }}'''))
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Class):
            continue

        cls_name = csharp_naming.class_name(symbol.name)

        blocks.append(Stripped(textwrap.dedent(f'''\
            /// <summary>
            /// Verify <paramref name="that" /> instance and
            /// append any error to <see cref="Errors" /> 
            /// where <paramref name="context" /> is used to localize the error.
            /// </summary>
            public void Visit({cls_name} that, string context)
            {{
            {csharp_common.INDENT}Implementation.Verify{cls_name}(
            {csharp_common.INDENT2}that, context, Errors);
            }}''')))

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        /// <summary>
        /// Verify the instances of the model entities non-recursively.
        /// </summary>
        public class NonRecursiveVerifier : 
        {csharp_common.INDENT}Visitation.IVisitorWithContext<string>
        {{
        '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}  // public class NonRecursiveVerifier')

    return Stripped(writer.getvalue()), None


def _unroll_recursion_in_recursive_verify(
        prop: intermediate.Property) -> Stripped:
    """Generate the code for unrolling the recursive visits  for the given property."""

    @require(lambda var_index: var_index >= 0)
    @require(lambda suffix: suffix in ("Item", "KeyValue"))
    def var_name(var_index: int, suffix: str) -> Identifier:
        """Generate the name of the loop variable."""
        if var_index == 0:
            if suffix == 'Item':
                return Identifier(f"an{suffix}")
            else:
                return Identifier(f"a{suffix}")

        elif var_index == 1:
            return Identifier(f"another{suffix}")
        else:
            return Identifier("yet" + "Yet" * (var_index - 1) + f"another{suffix}")

    def unroll(
            current_var_name: str,
            item_count: int,
            key_value_count: int,
            path: List[str],
            type_anno: intermediate.TypeAnnotation
    ) -> List[csharp_unrolling.Node]:
        """Generate the node corresponding to the ``type_anno`` and recurse."""
        if isinstance(type_anno, intermediate.BuiltinAtomicTypeAnnotation):
            return []

        elif isinstance(type_anno, intermediate.OurAtomicTypeAnnotation):
            if isinstance(type_anno.symbol, intermediate.Enumeration):
                return []

            joined_pth = '/'.join(path)
            return [csharp_unrolling.Node(
                text=textwrap.dedent(f'''\
                    if (Errors.Full()) return;
                    Visit(
                        {current_var_name},
                        ${csharp_common.string_literal(joined_pth)});'''),
                children=[])]

        elif isinstance(type_anno, (
                intermediate.ListTypeAnnotation, intermediate.SequenceTypeAnnotation,
                intermediate.SetTypeAnnotation)):

            if item_count > 15:
                index_var = f'i{item_count}'
            else:
                index_var = chr(ord('i') + item_count)

            children = unroll(
                current_var_name=f'{current_var_name}[{index_var}]',
                item_count=item_count + 1,
                key_value_count=key_value_count,
                path=path + [f'{{{index_var}}}'],
                type_anno=type_anno.items)

            if len(children) == 0:
                return []

            text = Stripped(
                f'for(var {index_var} = 0; '
                f'{index_var} < {current_var_name}.Count; '
                f'{index_var}++)')

            # Break into lines if too long.
            # This is just a heuristics — we do not consider the actual indention.
            if len(text) > 50:
                text = Stripped(textwrap.dedent(f'''\
                    for(
                    {csharp_common.INDENT}var {index_var} = 0;
                    {csharp_common.INDENT}{index_var} < {current_var_name}.Count;
                    {csharp_common.INDENT}{index_var}++)'''))

            return [csharp_unrolling.Node(text=text, children=children)]

        elif isinstance(type_anno, (
                intermediate.MappingTypeAnnotation,
                intermediate.MutableMappingTypeAnnotation
        )):
            key_value_var = var_name(key_value_count + 1, "KeyValue")

            children = unroll(
                current_var_name=f'{key_value_var}.Value',
                item_count=item_count,
                key_value_count=key_value_count + 1,
                path=path + [f'{{{key_value_var}.Key}}'],
                type_anno=type_anno.values)

            if len(children) > 0:
                return [csharp_unrolling.Node(
                    text=f'foreach (var {key_value_var} in {current_var_name})',
                    children=children)]
            else:
                return []

        elif isinstance(type_anno, intermediate.OptionalTypeAnnotation):
            children = unroll(
                current_var_name=current_var_name,
                item_count=item_count,
                key_value_count=key_value_count,
                path=path,
                type_anno=type_anno.value)
            if len(children) > 0:
                return [csharp_unrolling.Node(
                    text=f"if ({current_var_name} != null)", children=children)]
            else:
                return []
        else:
            assert_never(type_anno)

    prop_name = csharp_naming.property_name(prop.name)

    roots = unroll(
        current_var_name=f'that.{prop_name}',
        item_count=0,
        key_value_count=0,
        path=['{context}', prop_name],
        type_anno=prop.type_annotation)

    if len(roots) == 0:
        return Stripped('')

    blocks = [csharp_unrolling.render(root) for root in roots]
    return Stripped('\n\n'.join(blocks))


# fmt: on
@require(
    lambda cls:
    cls.implementation_key is None,
    "Implementation-specific classes are handled elsewhere"
)
# fmt: off
def _generate_recursive_verifier_visit(
        cls: intermediate.Class
) -> Stripped:
    """Generate the ``Visit`` method of the ``RecursiveVerifier`` for the ``cls``."""
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
        {csharp_common.INDENT}that, context, Errors);'''))
    ]  # type: List[Stripped]

    # region Unroll

    recursion_ends_here = True
    for prop in cls.properties:
        unrolled_prop_verification = _unroll_recursion_in_recursive_verify(prop=prop)

        if unrolled_prop_verification != '':
            blocks.append(unrolled_prop_verification)
            recursion_ends_here = False

    if recursion_ends_here:
        blocks.append(Stripped("// The recursion ends here."))
    # endregion

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}')
    return Stripped(writer.getvalue())


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_recursive_verifier(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the ``Verifier`` class which visits the entities and verifies them."""
    blocks = [
        Stripped("public readonly Errors Errors;"),
        Stripped(textwrap.dedent(f'''\
            /// <summary>
            /// Initialize the visitor with the given <paramref name="errors" />.
            ///
            /// The errors observed during the visitation will be appended to
            /// the <paramref name="errors" />.
            /// </summary>
            RecursiveVerifier(Errors errors)
            {{
            {csharp_common.INDENT}Errors = errors;
            }}''')),
        Stripped(textwrap.dedent(f'''\
            public void Visit(IEntity that, string context)
            {{
            {csharp_common.INDENT}that.Accept(this, context);
            }}'''))
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, intermediate.Class):
            continue

        if symbol.implementation_key is not None:
            visit_key = ImplementationKey(
                f'Verification/RecursiveVerifier/visit_{symbol.name}')
            if visit_key not in spec_impls:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The implementation snippet is missing for "
                        f"the ``Visit`` method "
                        f"of the ``Verification.RecursiveVerifier`` class: "
                        f"{visit_key}"))
                continue

            blocks.append(spec_impls[visit_key])
        else:
            blocks.append(_generate_recursive_verifier_visit(cls=symbol))

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(textwrap.dedent(f'''\
        /// <summary>
        /// Verify the instances of the model entities recursively.
        /// </summary>
        public class RecursiveVerifier : 
        {csharp_common.INDENT}Visitation.IVisitorWithContext<string>
        {{
        '''))
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write('\n\n')

        writer.write(textwrap.indent(block, csharp_common.INDENT))

    writer.write('\n}  // public class RecursiveVerifier')

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
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the AAS C# namespace.
    """
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    using_directives = [
        "using ArgumentException = System.ArgumentException;\n"
        "using InvalidOperationException = System.InvalidOperationException;\n"
        "using NotImplementedException = System.NotImplementedException;\n"
        "using Regex = System.Text.RegularExpressions.Regex;\n"
        "using System.Collections.Generic;  // can't alias\n"
        "using System.Collections.ObjectModel;  // can't alias\n"
        "using System.Linq;  // can't alias"
    ]  # type: List[str]

    blocks.append(Stripped("\n".join(using_directives)))

    verification_blocks = [
        _generate_pattern_class(spec_impls=spec_impls),
        spec_impls[ImplementationKey('Verification/Error')],
        spec_impls[ImplementationKey('Verification/Errors')]
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    implementation, implementation_errors = _generate_implementation(
        symbol_table=symbol_table, spec_impls=spec_impls)
    if implementation_errors:
        errors.extend(implementation_errors)
    else:
        verification_blocks.append(implementation)

    non_recursive, non_recursive_errors = _generate_non_recursive_verifier(
        symbol_table=symbol_table)

    if non_recursive_errors is not None:
        errors.extend(non_recursive_errors)
    else:
        verification_blocks.append(non_recursive)

    recursive, recursive_errors = _generate_recursive_verifier(
        symbol_table=symbol_table,
        spec_impls=spec_impls)

    if recursive_errors is not None:
        errors.extend(recursive_errors)
    else:
        verification_blocks.append(recursive)

    if len(errors) > 0:
        return None, errors

    verification_writer = io.StringIO()
    verification_writer.write(f"namespace {namespace}\n{{\n")
    verification_writer.write(
        f"{csharp_common.INDENT}public static class Verification\n"
        f"{csharp_common.INDENT}{{\n")

    for i, verification_block in enumerate(verification_blocks):
        if i > 0:
            verification_writer.write('\n\n')

        verification_writer.write(
            textwrap.indent(verification_block, 2 * csharp_common.INDENT))

    verification_writer.write(
        f"\n{csharp_common.INDENT}}}  // public static class Verification")
    verification_writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(verification_writer.getvalue()))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write('\n\n')

        assert not block.startswith('\n')
        assert not block.endswith('\n')
        out.write(block)

    out.write('\n')

    return out.getvalue(), None

# endregion
