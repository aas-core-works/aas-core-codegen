"""Generate the C# data structures from the intermediate representation."""
import io
import textwrap
from typing import (
    Optional,
    Dict,
    List,
    Tuple,
    cast,
    Union,
    Mapping,
    Final,
)

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen import specific_implementations
from aas_core_codegen.common import Error, Identifier, assert_never, Stripped, Rstripped
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    unrolling as csharp_unrolling,
    description as csharp_description,
)
from aas_core_codegen.csharp.common import INDENT as I, INDENT2 as II
from aas_core_codegen.intermediate import (
    construction as intermediate_construction,
)


# region Checks


def _human_readable_identifier(
    something: Union[
        intermediate.Enumeration, intermediate.ConcreteClass, intermediate.Interface
    ]
) -> str:
    """
    Represent ``something`` in a human-readable text.

    The reader should be able to trace ``something`` back to the meta-model.\
    """
    result = None  # type: Optional[str]

    if isinstance(something, intermediate.Enumeration):
        result = f"meta-model enumeration {something.name!r}"
    elif isinstance(something, intermediate.ConcreteClass):
        result = f"meta-model class {something.name!r}"
    elif isinstance(something, intermediate.Interface):
        result = f"interface based on the meta-model class {something.name!r}"
    else:
        assert_never(something)

    assert result is not None
    return result


def _verify_structure_name_collisions(
    symbol_table: intermediate.SymbolTable,
) -> List[Error]:
    """Verify that the C# names of the structures do not collide."""
    observed_structure_names: Dict[
        Identifier,
        Union[
            intermediate.Enumeration, intermediate.ConcreteClass, intermediate.Interface
        ],
    ] = dict()

    errors = []  # type: List[Error]

    # region Inter-structure collisions

    for something in csharp_common.over_enumerations_classes_and_interfaces(
        symbol_table
    ):
        name = csharp_naming.name_of(something)

        other = observed_structure_names.get(name, None)

        if other is not None:
            errors.append(
                Error(
                    something.parsed.node,
                    f"The C# name {name!r} "
                    f"of the {_human_readable_identifier(something)} "
                    f"collides with the C# name "
                    f"of the {_human_readable_identifier(other)}",
                )
            )
        else:
            observed_structure_names[name] = something

    # endregion

    # region Intra-structure collisions

    for symbol in symbol_table.symbols:
        collision_error = _verify_intra_structure_collisions(intermediate_symbol=symbol)

        if collision_error is not None:
            errors.append(collision_error)

    # endregion

    return errors


def _verify_intra_structure_collisions(
    intermediate_symbol: intermediate.Symbol,
) -> Optional[Error]:
    """Verify that no member names collide in the C# structure of the given symbol."""
    errors = []  # type: List[Error]

    if isinstance(intermediate_symbol, intermediate.Enumeration):
        pass

    elif isinstance(intermediate_symbol, intermediate.ConstrainedPrimitive):
        pass

    elif isinstance(intermediate_symbol, intermediate.Class):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in intermediate_symbol.properties:
            prop_name = csharp_naming.property_name(prop.name)
            if prop_name in observed_member_names:
                # BEFORE-RELEASE (mristin, 2021-12-13): test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# property {prop_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[prop_name]}",
                    )
                )
            else:
                observed_member_names[prop_name] = (
                    f"C# property {prop_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}"
                )

        for method in intermediate_symbol.methods:
            method_name = csharp_naming.method_name(method.name)

            if method_name in observed_member_names:
                # BEFORE-RELEASE (mristin, 2021-12-13): test
                errors.append(
                    Error(
                        method.parsed.node,
                        f"C# method {method_name!r} corresponding "
                        f"to the meta-model method {method.name!r} collides with "
                        f"the {observed_member_names[method_name]}",
                    )
                )
            else:
                observed_member_names[method_name] = (
                    f"C# method {method_name!r} corresponding to "
                    f"the meta-model method {method.name!r}"
                )

    else:
        assert_never(intermediate_symbol)

    if len(errors) > 0:
        errors.append(
            Error(
                intermediate_symbol.parsed.node,
                f"Naming collision(s) in C# code "
                f"for the symbol {intermediate_symbol.name!r}",
                underlying=errors,
            )
        )

    return None


class VerifiedIntermediateSymbolTable(intermediate.SymbolTable):
    """Represent a verified symbol table which can be used for code generation."""

    # noinspection PyInitNewSignature
    def __new__(
        cls, symbol_table: intermediate.SymbolTable
    ) -> "VerifiedIntermediateSymbolTable":
        raise AssertionError("Only for type annotation")


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def verify(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[VerifiedIntermediateSymbolTable], Optional[List[Error]]]:
    """Verify that C# code can be generated from the ``symbol_table``."""
    errors = []  # type: List[Error]

    structure_name_collisions = _verify_structure_name_collisions(
        symbol_table=symbol_table
    )

    errors.extend(structure_name_collisions)

    if len(errors) > 0:
        return None, errors

    return cast(VerifiedIntermediateSymbolTable, symbol_table), None


# endregion

# region Generation


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_enum(
    enum: intermediate.Enumeration,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the C# code for the enum."""
    writer = io.StringIO()

    if enum.description is not None:
        comment, comment_errors = csharp_description.generate_symbol_comment(
            enum.description
        )
        if comment_errors:
            return None, Error(
                enum.description.parsed.node,
                "Failed to generate the documentation comment",
                comment_errors,
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    name = csharp_naming.enum_name(enum.name)
    if len(enum.literals) == 0:
        writer.write(f"public enum {name}\n{{\n}}")
        return Stripped(writer.getvalue()), None

    writer.write(f"public enum {name}\n{{\n")
    for i, literal in enumerate(enum.literals):
        if i > 0:
            writer.write(",\n\n")

        if literal.description:
            (
                literal_comment,
                literal_comment_errors,
            ) = csharp_description.generate_enumeration_literal_comment(
                literal.description
            )

            if literal_comment_errors:
                return None, Error(
                    literal.description.parsed.node,
                    f"Failed to generate the comment "
                    f"for the enumeration literal {literal.name!r}",
                    literal_comment_errors,
                )

            assert literal_comment is not None

            writer.write(textwrap.indent(literal_comment, I))
            writer.write("\n")

        writer.write(
            textwrap.indent(
                f"[EnumMember(Value = {csharp_common.string_literal(literal.value)})]\n"
                f"{csharp_naming.enum_literal_name(literal.name)}",
                I,
            )
        )

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_interface(
    interface: intermediate.Interface,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate C# code for the given interface."""
    writer = io.StringIO()

    if interface.description is not None:
        comment, comment_errors = csharp_description.generate_symbol_comment(
            interface.description
        )

        if comment_errors is not None:
            return None, Error(
                interface.description.parsed.node,
                "Failed to generate the documentation comment",
                comment_errors,
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    name = csharp_naming.interface_name(interface.name)

    inheritances = [inheritance.name for inheritance in interface.inheritances] + [
        Identifier("Class")
    ]

    inheritance_names = list(map(csharp_naming.interface_name, inheritances))

    assert len(inheritances) > 0
    if len(inheritances) == 1:
        writer.write(f"public interface {name} : {inheritance_names[0]}\n{{\n")
    else:
        writer.write(f"public interface {name} :\n")
        for i, inheritance_name in enumerate(inheritance_names):
            if i > 0:
                writer.write(",\n")

            writer.write(textwrap.indent(inheritance_name, II))

        writer.write("\n{\n")

    # Code blocks separated by double newlines and indented once
    blocks = []  # type: List[Stripped]

    # region Getters and setters

    for prop in interface.properties:
        if prop.specified_for is interface.base:
            prop_type = csharp_common.generate_type(
                type_annotation=prop.type_annotation
            )
            prop_name = csharp_naming.property_name(prop.name)

            if prop.description is not None:
                (
                    prop_comment,
                    prop_comment_errors,
                ) = csharp_description.generate_property_comment(prop.description)

                if prop_comment_errors is not None:
                    return None, Error(
                        prop.description.parsed.node,
                        f"Failed to generate the documentation comment "
                        f"for the property {prop.name!r}",
                        prop_comment_errors,
                    )

                blocks.append(
                    Stripped(
                        f"{prop_comment}\n"
                        f"public {prop_type} {prop_name} {{ get; set; }}"
                    )
                )
            else:
                blocks.append(
                    Stripped(f"public {prop_type} {prop_name} {{ get; set; }}")
                )

    # endregion

    # region Signatures

    for signature in interface.signatures:
        signature_blocks = []  # type: List[Stripped]

        if signature.description is not None:
            (
                signature_comment,
                signature_comment_errors,
            ) = csharp_description.generate_signature_comment(signature.description)

            if signature_comment_errors is not None:
                return None, Error(
                    signature.description.parsed.node,
                    f"Failed to generate the documentation comment "
                    f"for signature {signature.name!r}",
                    signature_comment_errors,
                )

            assert signature_comment is not None

            signature_blocks.append(signature_comment)

        # fmt: off
        returns = (
            csharp_common.generate_type(type_annotation=signature.returns)
            if signature.returns is not None else "void"
        )
        # fmt: on

        arg_codes = []  # type: List[Stripped]
        for arg in signature.arguments:
            arg_type = csharp_common.generate_type(type_annotation=arg.type_annotation)
            arg_name = csharp_naming.argument_name(arg.name)
            arg_codes.append(Stripped(f"{arg_type} {arg_name}"))

        signature_name = csharp_naming.method_name(signature.name)
        if len(arg_codes) > 2:
            arg_block = ",\n".join(arg_codes)
            arg_block_indented = textwrap.indent(arg_block, I)
            signature_blocks.append(
                Stripped(f"public {returns} {signature_name}(\n{arg_block_indented});")
            )
        elif len(arg_codes) == 1:
            signature_blocks.append(
                Stripped(f"public {returns} {signature_name}({arg_codes[0]});")
            )
        else:
            assert len(arg_codes) == 0
            signature_blocks.append(Stripped(f"public {returns} {signature_name}();"))

        blocks.append(Stripped("\n".join(signature_blocks)))

    # endregion

    for i, code in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(code, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


class _DescendBodyUnroller(csharp_unrolling.Unroller):
    """Generate the code that unrolls descent into an element."""

    #: If set, generates the code with unrolled yields.
    #: Otherwise, we do not unroll recursively.
    _recurse: Final[bool]

    #: Pre-computed descendability map. A type is descendable if we should unroll it
    #: further.
    _descendability: Final[Mapping[intermediate.TypeAnnotationUnion, bool]]

    def __init__(
        self,
        recurse: bool,
        descendability: Mapping[intermediate.TypeAnnotationUnion, bool],
    ) -> None:
        """Initialize with the given values."""
        self._recurse = recurse
        self._descendability = descendability

    def _unroll_primitive_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.PrimitiveTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        # We can not descend into a primitive type.
        return []

    def _unroll_our_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OurTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        symbol = type_annotation.symbol

        if isinstance(symbol, intermediate.Enumeration):
            return []

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # We can not descend into a primitive type.
            return []

        assert isinstance(symbol, intermediate.Class)  # Exhaustively match

        result = [csharp_unrolling.Node(f"yield return {unrollee_expr};", children=[])]

        if self._recurse:
            if self._descendability[type_annotation]:
                recurse_var = csharp_unrolling.Unroller._loop_var_name(
                    level=item_level, suffix="Item"
                )

                result.append(
                    csharp_unrolling.Node(
                        text=textwrap.dedent(
                            f"""\
                        // Recurse
                        foreach (var {recurse_var} in {unrollee_expr}.Descend())
                        {{
                            yield return {recurse_var};
                        }}"""
                        ),
                        children=[],
                    )
                )
            else:
                result.append(
                    csharp_unrolling.Node(
                        text="// Recursive descent ends here.", children=[]
                    )
                )

        return result

    def _unroll_list_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.ListTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[csharp_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        item_var = csharp_unrolling.Unroller._loop_var_name(
            level=item_level, suffix="Item"
        )

        children = self.unroll(
            unrollee_expr=item_var,
            type_annotation=type_annotation.items,
            path=[],  # Path is unused in this context
            item_level=item_level + 1,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        node = csharp_unrolling.Node(
            text=f"foreach (var {item_var} in {unrollee_expr})",
            children=children,
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
        """Generate code for the given specific ``type_annotation``."""
        children = self.unroll(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation.value,
            path=path,
            item_level=item_level,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        return [
            csharp_unrolling.Node(
                text=f"if ({unrollee_expr} != null)", children=children
            )
        ]


def _generate_descend_body(cls: intermediate.ConcreteClass, recurse: bool) -> Stripped:
    """
    Generate the body of the ``Descend`` and ``DescendOnce`` methods.

    With this function, we can unroll the recursion as a simple optimization
    in the recursive case.
    """
    blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        descendability = intermediate.map_descendability(
            type_annotation=prop.type_annotation
        )

        if not descendability[prop.type_annotation]:
            continue

        # region Unroll

        unroller = _DescendBodyUnroller(recurse=recurse, descendability=descendability)

        roots = unroller.unroll(
            unrollee_expr=csharp_naming.property_name(prop.name),
            type_annotation=prop.type_annotation,
            path=[],  # We do not use path in this context
            item_level=0,
            key_value_level=0,
        )

        assert len(roots) > 0, (
            "Since the type annotation was descendable, we must have obtained "
            "at least one unrolling node"
        )

        blocks.extend(Stripped(csharp_unrolling.render(root)) for root in roots)

        # endregion

    if len(blocks) == 0:
        blocks.append(Stripped("// No descendable properties\nyield break;"))

    return Stripped("\n\n".join(blocks))


def _generate_descend_once_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the ``DescendOnce`` method for the concrete class ``cls``."""

    body = _generate_descend_body(cls=cls, recurse=False)

    indented_body = textwrap.indent(body, I)

    return Stripped(
        f"""\
/// <summary>
/// Iterate over all the class instances referenced from this instance
/// without further recursion.
/// </summary>
public IEnumerable<IClass> DescendOnce()
{{
{indented_body}
}}"""
    )


def _generate_descend_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the recursive ``Descend`` method for the concrete class ``cls``."""

    body = _generate_descend_body(cls=cls, recurse=True)

    indented_body = textwrap.indent(body, I)

    return Stripped(
        f"""\
/// <summary>
/// Iterate recursively over all the class instances referenced from this instance.
/// </summary>
public IEnumerable<IClass> Descend()
{{
{indented_body}
}}"""
    )


def _generate_default_value(default: intermediate.Default) -> Stripped:
    """Generate the C# code representing the default value of an argument."""
    code = None  # type: Optional[str]

    if default is not None:
        if isinstance(default, intermediate.DefaultConstant):
            if default.value is None:
                code = "null"
            elif isinstance(default.value, bool):
                code = "true" if default.value else "false"
            elif isinstance(default.value, str):
                code = csharp_common.string_literal(default.value)
            elif isinstance(default.value, int):
                code = str(default.value)
            elif isinstance(default.value, float):
                code = f"{default}d"
            else:
                assert_never(default.value)
        elif isinstance(default, intermediate.DefaultEnumerationLiteral):
            code = ".".join(
                [
                    csharp_naming.enum_name(default.enumeration.name),
                    csharp_naming.enum_literal_name(default.literal.name),
                ]
            )
        else:
            assert_never(default)

    assert code is not None
    return Stripped(code)


@require(lambda cls: not cls.is_implementation_specific)
@require(lambda cls: not cls.constructor.is_implementation_specific)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_constructor(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the constructor function for the given concrete class ``cls``."""
    cls_name = csharp_naming.class_name(cls.name)

    blocks = []  # type: List[str]

    arg_codes = []  # type: List[str]
    for arg in cls.constructor.arguments:
        arg_type = csharp_common.generate_type(type_annotation=arg.type_annotation)
        arg_name = csharp_naming.argument_name(arg.name)

        if arg.default is None:
            arg_codes.append(Stripped(f"{arg_type} {arg_name}"))
        else:
            arg_codes.append(
                Stripped(
                    f"{arg_type} {arg_name} = {_generate_default_value(arg.default)}"
                )
            )

    if len(arg_codes) == 0:
        return (
            None,
            Error(
                cls.parsed.node,
                "An empty constructor is automatically generated, "
                "which conflicts with the empty constructor "
                "specified in the meta-model",
            ),
        )

    elif len(arg_codes) == 1:
        blocks.append(f"public {cls_name}({arg_codes[0]})\n{{")
    else:
        arg_block = ",\n".join(arg_codes)
        arg_block_indented = textwrap.indent(arg_block, I)
        blocks.append(Stripped(f"public {cls_name}(\n{arg_block_indented})\n{{"))

    body = []  # type: List[str]
    for stmt in cls.constructor.statements:
        if isinstance(stmt, intermediate_construction.AssignArgument):
            if stmt.default is None:
                body.append(
                    f"{csharp_naming.property_name(stmt.name)} = "
                    f"{csharp_naming.argument_name(stmt.argument)};"
                )
            else:
                if isinstance(stmt.default, intermediate_construction.EmptyList):
                    prop = cls.properties_by_name[stmt.name]

                    type_anno = prop.type_annotation
                    while isinstance(type_anno, intermediate.OptionalTypeAnnotation):
                        type_anno = type_anno.value

                    prop_type = csharp_common.generate_type(type_annotation=type_anno)

                    arg_name = csharp_naming.argument_name(stmt.argument)

                    # Write the assignment as a ternary operator
                    writer = io.StringIO()
                    writer.write(f"{csharp_naming.property_name(stmt.name)} = ")
                    writer.write(f"({arg_name} != null)\n")
                    writer.write(textwrap.indent(f"? {arg_name}\n", I))
                    writer.write(textwrap.indent(f": new {prop_type}();", I))

                    body.append(writer.getvalue())
                elif isinstance(
                    stmt.default, intermediate_construction.DefaultEnumLiteral
                ):
                    literal_code = ".".join(
                        [
                            csharp_naming.enum_name(stmt.default.enum.name),
                            csharp_naming.enum_literal_name(stmt.default.literal.name),
                        ]
                    )

                    body.append(
                        f"{csharp_naming.property_name(stmt.name)} = "
                        f"{literal_code};"
                    )
                else:
                    assert_never(stmt.default)

        else:
            assert_never(stmt)

    blocks.append("\n".join(textwrap.indent(stmt_code, I) for stmt_code in body))

    blocks.append("}")

    return Stripped("\n".join(blocks)), None


@require(lambda cls: not cls.is_implementation_specific)
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_class(
    cls: intermediate.ConcreteClass,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate C# code for the given concrete class ``cls``."""
    writer = io.StringIO()

    if cls.description is not None:
        comment, comment_errors = csharp_description.generate_symbol_comment(
            cls.description
        )
        if comment_errors is not None:
            return None, Error(
                cls.description.parsed.node,
                "Failed to generate the comment description",
                comment_errors,
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    name = csharp_naming.class_name(cls.name)

    # NOTE (mristin, 2021-12-15):
    # Since C# does not support multiple inheritance, we model all the abstract classes
    # as interfaces. Hence a class only implements interfaces and does not extend
    # any abstract class.
    #
    # Moreover, if a concrete class has descendants (which we allow in the meta-model),
    # we will additionally generate an interface for that class and that class then also
    # implements the interface which was based on it.
    #
    # Finally, every class of the meta-model also implements the general
    # ``IClass`` interface.

    interface_names = []  # type: List[Identifier]
    for inheritance in cls.inheritances:
        assert inheritance.interface is not None, (
            f"Expected interface in the parent class {inheritance.name!r} "
            f"of class {cls.name!r}"
        )

        interface_names.append(csharp_naming.name_of(inheritance.interface))

    interface_names.append(csharp_naming.interface_name(Identifier("Class")))

    assert len(interface_names) > 0
    if len(interface_names) == 1:
        writer.write(f"public class {name} : {interface_names[0]}\n{{\n")
    else:
        writer.write(f"public class {name} :\n")
        for i, interface_name in enumerate(interface_names):
            if i > 0:
                writer.write(",\n")

            writer.write(textwrap.indent(interface_name, II))

        writer.write("\n{\n")

    # Code blocks separated by double newlines and indented once
    blocks = []  # type: List[Stripped]

    # region Getters and setters

    for prop in cls.properties:
        prop_type = csharp_common.generate_type(type_annotation=prop.type_annotation)

        prop_name = csharp_naming.property_name(prop.name)

        prop_blocks = []  # type: List[Stripped]

        if prop.description is not None:
            (
                prop_comment,
                prop_comment_errors,
            ) = csharp_description.generate_property_comment(prop.description)
            if prop_comment_errors:
                return None, Error(
                    prop.description.parsed.node,
                    f"Failed to generate the documentation comment "
                    f"for the property {prop.name!r}",
                    prop_comment_errors,
                )

            assert prop_comment is not None

            prop_blocks.append(prop_comment)

        prop_blocks.append(Stripped(f"public {prop_type} {prop_name} {{ get; set; }}"))

        blocks.append(Stripped("\n".join(prop_blocks)))

    # endregion

    # region Methods

    errors = []  # type: List[Error]

    for method in cls.methods:
        if isinstance(method, intermediate.ImplementationSpecificMethod):
            # NOTE (mristin, 2022-05-18):
            # We have to repeat the implementation of the method in all the descendants
            # since we share only interfaces between the classes, but not
            # the implementations.
            #
            # This makes the code a bit larger, but the class hierarchy is much simpler
            # and the individual classes are much easier to grasp.
            implementation_key = specific_implementations.ImplementationKey(
                f"Types/{method.specified_for.name}/{method.name}.cs"
            )

            implementation = spec_impls.get(implementation_key, None)

            if implementation is None:
                errors.append(
                    Error(
                        method.parsed.node,
                        f"The implementation is missing for "
                        f"the implementation-specific method: {implementation_key}",
                    )
                )
                continue

            blocks.append(implementation)
        else:
            # NOTE (mristin, 2021-09-16):
            # At the moment, we do not transpile the method body and its contracts.
            # We want to finish the meta-model for the V3 and fix de/serialization
            # before taking on this rather hard task.

            errors.append(
                Error(
                    cls.parsed.node,
                    "At the moment, we do not transpile the method body and "
                    "its contracts. We want to finish the meta-model for the V3 and "
                    "fix de/serialization before taking on this rather hard task.",
                )
            )

    blocks.append(_generate_descend_once_method(cls=cls))

    blocks.append(_generate_descend_method(cls=cls))

    blocks.append(
        Stripped(
            f"""\
/// <summary>
/// Accept the <paramref name="visitor" /> to visit this instance
/// for double dispatch.
/// </summary>
public void Accept(Visitation.IVisitor visitor)
{{
{I}visitor.Visit(this);
}}"""
        )
    )

    blocks.append(
        Stripped(
            f"""\
/// <summary>
/// Accept the visitor to visit this instance for double dispatch
/// with the <paramref name="context" />.
/// </summary>
public void Accept<C>(Visitation.IVisitorWithContext<C> visitor, C context)
{{
{I}visitor.Visit(this, context);
}}"""
        )
    )

    blocks.append(
        Stripped(
            f"""\
/// <summary>
/// Accept the <paramref name="transformer" /> to transform this instance
/// for double dispatch.
/// </summary>
public T Transform<T>(Visitation.ITransformer<T> transformer)
{{
{I}return transformer.Transform(this);
}}"""
        )
    )

    blocks.append(
        Stripped(
            f"""\
/// <summary>
/// Accept the <paramref name="transformer" /> to visit this instance
/// for double dispatch with the <paramref name="context" />.
/// </summary>
public T Transform<C, T>(
{I}Visitation.ITransformerWithContext<C, T> transformer, C context)
{{
{I}return transformer.Transform(this, context);
}}"""
        )
    )

    # endregion

    # region Constructor

    if cls.constructor.is_implementation_specific:
        implementation_key = specific_implementations.ImplementationKey(
            f"Types/{cls.name}/{cls.name}.cs"
        )
        implementation = spec_impls.get(implementation_key, None)

        if implementation is None:
            errors.append(
                Error(
                    cls.parsed.node,
                    f"The implementation of the implementation-specific constructor "
                    f"is missing: {implementation_key}",
                )
            )
        else:
            blocks.append(implementation)
    else:
        constructor_block, error = _generate_constructor(cls=cls)

        if error is not None:
            errors.append(error)
        else:
            assert constructor_block is not None
            blocks.append(constructor_block)

    # endregion

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node,
            f"Failed to generate the code for the class {cls.name}",
            errors,
        )

    for i, code in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(code, I))

    writer.write("\n}")

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
    symbol_table: VerifiedIntermediateSymbolTable,
    namespace: csharp_common.NamespaceIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the AAS C# namespace.
    """
    blocks = [csharp_common.WARNING]  # type: List[Rstripped]

    using_directives = [
        "using EnumMemberAttribute = System.Runtime.Serialization.EnumMemberAttribute;",
        "using System.Collections.Generic;  // can't alias",
    ]  # type: List[str]

    if len(using_directives) > 0:
        blocks.append(Stripped("\n".join(using_directives)))

    blocks.append(Stripped(f"namespace {namespace}\n{{"))

    blocks.append(
        Rstripped(
            textwrap.indent(
                f"""\
/// <summary>
/// Represent a general class of an AAS model.
/// </summary>
public interface IClass
{{
{I}/// <summary>
{I}/// Iterate over all the class instances referenced from this instance
{I}/// without further recursion.
{I}/// </summary>
{I}public IEnumerable<IClass> DescendOnce();

{I}/// <summary>
{I}/// Iterate recursively over all the class instances referenced from this instance.
{I}/// </summary>
{I}public IEnumerable<IClass> Descend();

{I}/// <summary>
{I}/// Accept the <paramref name="visitor" /> to visit this instance
{I}/// for double dispatch.
{I}/// </summary>
{I}public void Accept(Visitation.IVisitor visitor);

{I}/// <summary>
{I}/// Accept the visitor to visit this instance for double dispatch
{I}/// with the <paramref name="context" />.
{I}/// </summary>
{I}public void Accept<C>(Visitation.IVisitorWithContext<C> visitor, C context);

{I}/// <summary>
{I}/// Accept the <paramref name="transformer" /> to transform this instance
{I}/// for double dispatch.
{I}/// </summary>
{I}public T Transform<T>(Visitation.ITransformer<T> transformer);

{I}/// <summary>
{I}/// Accept the <paramref name="transformer" /> to visit this instance
{I}/// for double dispatch with the <paramref name="context" />.
{I}/// </summary>
{I}public T Transform<C, T>(
{II}Visitation.ITransformerWithContext<C, T> transformer, C context);
}}""",
                I,
            )
        )
    )

    errors = []  # type: List[Error]

    for something in csharp_common.over_enumerations_classes_and_interfaces(
        symbol_table
    ):
        code = None  # type: Optional[Stripped]
        error = None  # type: Optional[Error]

        if (
            isinstance(something, intermediate.Class)
            and something.is_implementation_specific
        ):
            implementation_key = specific_implementations.ImplementationKey(
                f"Types/{something.name}.cs"
            )

            code = spec_impls.get(implementation_key, None)
            if code is None:
                error = Error(
                    something.parsed.node,
                    f"The implementation is missing "
                    f"for the implementation-specific class: {implementation_key}",
                )
        else:
            if isinstance(something, intermediate.Enumeration):
                # BEFORE-RELEASE (mristin, 2021-12-13): test in isolation
                code, error = _generate_enum(enum=something)
            elif isinstance(something, intermediate.Interface):
                # BEFORE-RELEASE (mristin, 2021-12-13): test in isolation
                code, error = _generate_interface(interface=something)

            elif isinstance(something, intermediate.ConcreteClass):
                # BEFORE-RELEASE (mristin, 2021-12-13): test in isolation
                code, error = _generate_class(cls=something, spec_impls=spec_impls)
            else:
                assert_never(something)

        assert (code is None) ^ (error is None)
        if error is not None:
            errors.append(
                Error(
                    something.parsed.node,
                    f"Failed to generate the code for {something.name!r}",
                    [error],
                )
            )
        else:
            assert code is not None
            blocks.append(Rstripped(textwrap.indent(code, "    ")))

    if len(errors) > 0:
        return None, errors

    blocks.append(Rstripped(f"}}  // namespace {namespace}"))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None


# endregion
