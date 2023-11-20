"""Generate the Java data structures from the intermediate representation."""
import io
import textwrap
from typing import (
    cast,
    Final,
    List,
    Mapping,
    Optional,
    Tuple,
)

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen import specific_implementations
from aas_core_codegen.common import (
    assert_never,
    Error,
    Identifier,
    Stripped,
)
from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
    unrolling as java_unrolling,
)
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
)
from aas_core_codegen.intermediate import (
    construction as intermediate_construction,
)
# region Checks


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
    """Verify that Java code can be generated from the ``symbol_table``."""

    return cast(VerifiedIntermediateSymbolTable, symbol_table), None


# endregion

# region Generation


class _DescendBodyUnroller(java_unrolling.AbstractUnroller):
    """Generate the code for the descend Stream generator."""

    # If set, generate code that descends recursively into the members.
    _recurse: Final[bool]

    #: Pre-computed descendability map. A type is descendable if we should unroll it
    #: further.
    _descendability: Final[Mapping[intermediate.TypeAnnotationUnion, bool]]

    @staticmethod
    def _get_item_var(item_level: int) -> Stripped:
        return Stripped(f"item{item_level}")


    @ensure(lambda item_level: item_level >= 0)
    @staticmethod
    def _get_parent_item_var(item_name: str, item_level: int) -> Stripped:
        if item_level == 0:
            return Stripped(f"{item_name}")

        parent_item_level = item_level - 1

        return _DescendBodyUnroller._get_item_var(parent_item_level)


    def __init__(
        self,
        recurse: bool,
        descendability: Mapping[intermediate.TypeAnnotationUnion, bool]
    ) -> None:
        self._recurse = recurse
        self._descendability = descendability

    def _unroll_primitive_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.PrimitiveTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[java_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        # We cannot descend into a primitive type.

        return []

    def _unroll_our_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OurTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[java_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        our_type = type_annotation.our_type

        if isinstance(our_type, intermediate.Enumeration):
            return []

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # We can not descend into a primitive type.
            return []

        assert isinstance(our_type, intermediate.Class)  # Exhaustively match

        parent_item_var = _DescendBodyUnroller._get_parent_item_var(f"self.{unrollee_expr}",
                                                                    item_level)

        if not self._recurse or not self._descendability[type_annotation]:
            return [
                java_unrolling.Node(
                    text=f"{parent_item_var}",
                    children=[],
                )
            ]
        else:
            return [
                java_unrolling.Node(
                    text=f"""\
Stream.<IClass>concat(Stream.<IClass>of({parent_item_var}),
{I * (item_level + 1)}StreamSupport.stream({parent_item_var}.descend().spliterator(), false))""",
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
    ) -> List[java_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""
        children = self.unroll(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation.items,
            path=[],
            item_level=item_level + 1,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        parent_item_var = _DescendBodyUnroller._get_parent_item_var(f"self.{unrollee_expr}",
                                                                    item_level)

        own_item_var = _DescendBodyUnroller._get_item_var(item_level)

        map_var = java_unrolling.Node(
            text=f"{own_item_var} ->",
            children=[],
        )

        map_args = [map_var] + children

        return [
            java_unrolling.Node(
                text=f"""\
StreamSupport.stream({parent_item_var}.spliterator(), false)
{I * (item_level + 1)}.flatMap""",
                children=map_args
            )
        ]


    def _unroll_optional_type_annotation(
        self,
        unrollee_expr: str,
        type_annotation: intermediate.OptionalTypeAnnotation,
        path: List[str],
        item_level: int,
        key_value_level: int,
    ) -> List[java_unrolling.Node]:
        """Generate code for the given specific ``type_annotation``."""

        # TODO account for initial level

        children = self.unroll(
            unrollee_expr=unrollee_expr,
            type_annotation=type_annotation.value,
            path=[],
            item_level=item_level + 1,
            key_value_level=key_value_level,
        )

        if len(children) == 0:
            return []

        parent_item_var = _DescendBodyUnroller._get_parent_item_var(f"self.{unrollee_expr}",
                                                                    item_level)

        own_item_var = _DescendBodyUnroller._get_item_var(item_level)

        map_var = java_unrolling.Node(
            text=f"{own_item_var} ->",
            children=[],
        )

        map_args = [map_var] + children

        return [
            java_unrolling.Node(
                text=f"""\
Stream.of({parent_item_var})
{I}.filter({own_item_var} -> {own_item_var}.isPresent())
{I}.map({own_item_var} -> {own_item_var}.get())
{I}.flatMap""",
                children=map_args
            )
        ]


def _generate_descend_body(cls: intermediate.ConcreteClass, recursive: bool) -> Stripped:
    """Generate the iterator function body for recursive and non-recursive descend methods.

    We leverage lazily evaluated streams to iterate over the object stream one by one.
    """
    blocks = []  # type: List[Stripped]

    blocks.append(
        Stripped("Stream<IClass> memberStream = Stream.empty();")
    )

    # region Streams

    for prop in cls.properties:
        prop_name = java_naming.property_name(prop.name)

        descendability = intermediate.map_descendability(
            type_annotation=prop.type_annotation
        )

        if not descendability[prop.type_annotation]:
            continue

        unroller = _DescendBodyUnroller(recurse=recursive, descendability=descendability)

        roots = unroller.unroll(
            unrollee_expr=prop_name,
            type_annotation=prop.type_annotation,
            path=[],
            item_level=0,
            key_value_level=0,
        )

        assert len(roots) == 1, (
            "The type annotation should have resulted in a single unrolled node."
        )

        prop_expr = java_unrolling.parentheses_render(roots[0])

        stream_stmt = Stripped(
f"""memberStream = Stream.<IClass>concat(memberStream,
{I}{prop_expr});"""
        )

        blocks.append(stream_stmt)

    # endregion

    blocks.append(
        Stripped("return memberStream;")
    )

    return Stripped("\n\n".join(blocks))


def _generate_descend_iterable_name(cls: intermediate.ConcreteClass, recursive: bool) -> Stripped:
    name = java_naming.class_name(cls.name)

    if recursive:
        return Stripped(f"{name}RecursiveIterable")
    else:
        return Stripped(f"{name}Iterable")


def _generate_descend_iterable(cls: intermediate.ConcreteClass, recursive: bool) -> Stripped:
    """Generate the iterator for the descend method."""

    name = java_naming.class_name(cls.name)

    iterable_name = _generate_descend_iterable_name(cls, recursive)

    iterable_body = _generate_descend_body(cls, recursive)

    indented_iterable_body = textwrap.indent(iterable_body, II)

    iterable = Stripped(f"""\
private static class {iterable_name} implements Iterable<IClass> {{
{I}private Extension self;

{I}public {iterable_name}({name} self) {{
{II}this.self = self;
{I}}}

{I}@Override
{I}public Iterator<IClass> iterator() {{
{II}Stream<IClass> stream = stream();

{II}return stream.iterator();
{I}}}

{I}@Override
{I}public void forEach(Consumer<? super IClass> action) {{
{II}Stream<IClass> stream = stream();

{II}stream.forEach(action);
{I}}}

{I}@Override
{I}public Spliterator<IClass> spliterator() {{
{II}Stream<IClass> stream = stream();

{II}return stream.spliterator();
{I}}}

{I}private Stream<IClass> stream() {{
{indented_iterable_body}
{I}}}
}}""")

    return iterable


def _generate_descend_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the recursive ``Descend`` method for the concrete class ``cls``."""

    iterable_name = _generate_descend_iterable_name(cls=cls, recursive=True)

    iterable_class = _generate_descend_iterable(cls=cls, recursive=True)

    return Stripped(
        f"""\
/**
 * Iterate recursively over all the class instances referenced from this instance.
 */
{iterable_class}

public Iterable<IClass> descend()
{{
{I}return new {iterable_name}(this);
}}"""
    )


def _generate_descend_once_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the recursive ``Descend`` method for the concrete class ``cls``."""

    iterable_name = _generate_descend_iterable_name(cls=cls, recursive=False)

    iterable_class = _generate_descend_iterable(cls=cls, recursive=False)

    return Stripped(
        f"""\
/**
 * Iterate over all the class instances referenced from this instance.
 */
{iterable_class}

public Iterable<IClass> descendOnce()
{{
{I}return new {iterable_name}(this);
}}"""
    )


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_interface(
    cls: intermediate.ClassUnion,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate C# interface for the given class ``cls``."""
    writer = io.StringIO()

    name = java_naming.interface_name(cls.name)

    inheritances = [inheritance.name for inheritance in cls.inheritances]
    if len(inheritances) == 0:
        inheritances = [Identifier("Class")]

    inheritance_names = list(map(java_naming.interface_name, inheritances))

    assert len(inheritances) > 0
    if len(inheritances) == 1:
        writer.write(f"public interface {name} extends {inheritance_names[0]}\n{{\n")
    else:
        writer.write(f"public interface {name} extends\n")
        for i, inheritance_name in enumerate(inheritance_names):
            if i > 0:
                writer.write(",\n")

            writer.write(textwrap.indent(inheritance_name, II))

        writer.write("\n{\n")

    # Code blocks separated by double newlines and indented once
    blocks = []  # type: List[Stripped]

    # region Getters and setters

    for prop in cls.properties:
        if prop.specified_for is not cls:
            continue

        prop_type = java_common.generate_type(type_annotation=prop.type_annotation)

        prop_name = java_naming.property_name(prop.name)

        getter_name = java_naming.getter_name(prop.name)
        setter_name = java_naming.setter_name(prop.name)

        blocks.append(Stripped(f"public {prop_type} {getter_name}();"))
        blocks.append(Stripped(f"public {prop_type} {setter_name}({prop_type} {prop_name});"))

    # endregion

    # region Signatures

    for method in cls.methods:
        if method.specified_for is not cls:
            continue

        signature_blocks = []  # type: List[Stripped]


        # fmt: off
        returns = (
            java_common.generate_type(type_annotation=method.returns)
            if method.returns is not None else "void"
        )
        # fmt: on

        arg_codes = []  # type: List[Stripped]
        for arg in method.arguments:
            arg_type = java_common.generate_type(type_annotation=arg.type_annotation)
            arg_name = java_naming.argument_name(arg.name)
            arg_codes.append(Stripped(f"{arg_type} {arg_name}"))

        signature_name = java_naming.method_name(method.name)
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

    for prop in cls.properties:
        if prop.specified_for is not cls:
            continue

        if isinstance(
            prop.type_annotation, intermediate.OptionalTypeAnnotation
        ) and isinstance(prop.type_annotation.value, intermediate.ListTypeAnnotation):
            prop_name = java_naming.property_name(prop.name)
            items_type = java_common.generate_type(prop.type_annotation.value.items)
            blocks.append(
                Stripped(
                    f"""\
/**
 * Iterate over {prop_name}, if set, and otherwise return an empty enumerable.
 */
public Iterable<{items_type}> over{prop_name}OrEmpty();"""
                )
            )

    # endregion

    if len(blocks) == 0:
        blocks = [Stripped("// Intentionally empty.")]

    for i, code in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(code, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_default_value(default: intermediate.Default) -> Stripped:
    """Generate the Java code representing the default value of an argument."""
    code = None  # type: Optional[str]

    if default is not None:
        if isinstance(default, intermediate.DefaultPrimitive):
            if default.value is None:
                code = "null"
            elif isinstance(default.value, bool):
                code = "true" if default.value else "false"
            elif isinstance(default.value, str):
                code = java_common.string_literal(default.value)
            elif isinstance(default.value, int):
                code = str(default.value)
            elif isinstance(default.value, float):
                code = f"{default}d"
            else:
                assert_never(default.value)
        elif isinstance(default, intermediate.DefaultEnumerationLiteral):
            code = ".".join(
                [
                    java_naming.enum_name(default.enumeration.name),
                    java_naming.enum_literal_name(default.literal.name),
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
    """
    Generate the constructor function for the given concrete class ``cls``.

    Return empty string if there is an empty constructor.
    """
    if (
        len(cls.constructor.arguments) == 0
        and len(cls.constructor.inlined_statements) == 0
    ):
        return Stripped(""), None

    cls_name = java_naming.class_name(cls.name)

    blocks = []  # type: List[str]

    arg_codes = []  # type: List[str]
    for arg in cls.constructor.arguments:
        arg_type = java_common.generate_type(type_annotation=arg.type_annotation)
        arg_name = java_naming.argument_name(arg.name)

        if arg.default is None:
            arg_codes.append(Stripped(f"{arg_type} {arg_name}"))
        else:
            arg_codes.append(
                Stripped(
                    f"{arg_type} {arg_name} = {_generate_default_value(arg.default)}"
                )
            )

    if len(arg_codes) == 0:
        blocks.append(f"public {cls_name}()\n{{")
    if len(arg_codes) == 1:
        blocks.append(f"public {cls_name}({arg_codes[0]})\n{{")
    else:
        arg_block = ",\n".join(arg_codes)
        arg_block_indented = textwrap.indent(arg_block, I)
        blocks.append(Stripped(f"public {cls_name}(\n{arg_block_indented})\n{{"))

    body = []  # type: List[str]

    for stmt in cls.constructor.inlined_statements:
        if isinstance(stmt, intermediate_construction.AssignArgument):
            if stmt.default is None:
                body.append(
                    f"this.{java_naming.property_name(stmt.name)} = "
                    f"{java_naming.argument_name(stmt.argument)};"
                )
            else:
                if isinstance(stmt.default, intermediate_construction.EmptyList):
                    prop = cls.properties_by_name[stmt.name]

                    type_anno = prop.type_annotation
                    while isinstance(type_anno, intermediate.OptionalTypeAnnotation):
                        type_anno = type_anno.value

                    prop_type = java_common.generate_type(type_annotation=type_anno)

                    arg_name = java_naming.argument_name(stmt.argument)

                    # Write the assignment as a ternary operator
                    writer = io.StringIO()
                    writer.write(f"this.{java_naming.property_name(stmt.name)} = ")
                    writer.write(f"({arg_name} != null)\n")
                    writer.write(textwrap.indent(f"? {arg_name}\n", I))
                    writer.write(textwrap.indent(f": new {prop_type}();", I))

                    body.append(writer.getvalue())
                elif isinstance(
                    stmt.default, intermediate_construction.DefaultEnumLiteral
                ):
                    literal_code = ".".join(
                        [
                            java_naming.enum_name(stmt.default.enum.name),
                            java_naming.enum_literal_name(stmt.default.literal.name),
                        ]
                    )

                    arg_name = java_naming.argument_name(stmt.argument)

                    body.append(
                        Stripped(
                            f"""\
this.{java_naming.property_name(stmt.name)} = ({arg_name} != null) {arg_name} ?? {literal_code};"""
                        )
                    )
                else:
                    assert_never(stmt.default)

        else:
            assert_never(stmt)

    blocks.append("\n".join(textwrap.indent(stmt_code, I) for stmt_code in body))

    blocks.append("}")

    return Stripped("\n".join(blocks)), None


# fmt: off
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
# fmt: on
def _generate_class(
    cls: intermediate.ConcreteClass,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate Java code for the class ``cls``."""
    # Code blocks to be later joined by double newlines and indented once
    blocks = []  # type: List[Stripped]

    # region Properties and matching getters and setters

    for prop in cls.properties:
        prop_type = java_common.generate_type(type_annotation=prop.type_annotation)

        prop_name = java_naming.property_name(prop.name)

        getter_name = java_naming.getter_name(prop.name)
        setter_name = java_naming.setter_name(prop.name)

        prop_blocks = []  # type: List[Stripped]

        prop_blocks.append(
            Stripped(
                f"""\
private {prop_type} {prop_name};"""
            )
        )

        prop_blocks.append(
            Stripped(
                f"""\
@Override
public {prop_type} {getter_name}() {{
{I}return {prop_name};
}}"""
            )
        )

        prop_blocks.append(
            Stripped(
                f"""\
@Override
public {prop_type} {setter_name}({prop_type} {prop_name}) {{
{I}this.{prop_name} = {prop_name};
}}"""
            )
        )

        blocks.append(Stripped("\n\n".join(prop_blocks)))

    # endregion

    # region OverXOrEmpty getter

    for prop in cls.properties:
        if isinstance(
                prop.type_annotation, intermediate.OptionalTypeAnnotation
        ) and isinstance(prop.type_annotation.value, intermediate.ListTypeAnnotation):
            prop_name = java_naming.property_name(prop.name)
            items_type = java_common.generate_type(prop.type_annotation.value.items)

            blocks.append(
                Stripped(
                    f"""\
/**
 * Iterate over {{@code {prop_name}}}, if set, and otherwise return an empty enumerable.
 */
public Iterable<{items_type}> over{prop_name}OrEmpty()
{{
{I}if ({prop_name} != null) {{
{II}return {prop_name};
{I}}} else {{
{II}return
}}
{I}return {prop_name}
}}"""
                )
            )

    # endregion

    # region Methods

    errors = []  # type: List[Error]

    for method in cls.methods:
        if isinstance(method, intermediate.ImplementationSpecificMethod):
            implementation_key = specific_implementations.ImplementationKey(
                f"Types/{method.specified_for.name}/{method.name}.java"
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
            errors.append(
                Error(
                    cls.parsed.node,
                    "At the moment, we do not transpile the method body and "
                    "its contracts. We want to finish the meta-model for the V3 and "
                    "fix de/serialization before taking on this rather hard task.",
                )
            )

    visit_name = java_naming.method_name(Identifier(f"visit_{cls.name}"))

    blocks.append(_generate_descend_method(cls=cls))
    blocks.append(
        Stripped(
            f"""\
/**
 * Accept the {{@code visitor}} to visit this instance for double dispatch.
 **/
@Override
public void accept(Visitation.IVisitor visitor)
{{
{I}visitor.{visit_name}(this);
}}"""
        )
    )

    blocks.append(
        Stripped(
            f"""\
/**
 * Accept the {{@code visitor}} to visit this instance for double dispatch
 * with the {{@code context}}.
 **/
@Override
public <TContext> void accept(
{I}Visitation.IVisitor visitor,
{I}TContext context)
{{
{I}visitor.{visit_name}(this, context);
}}"""
        )
    )

    transform_name = java_naming.method_name(Identifier(f"transform_{cls.name}"))

    blocks.append(
        Stripped(
            f"""\
/**
 * Accept the {{@code transformer}} to visit this instance for double dispatch.
 **/
@Override
public <T> T transform(Visitation.ITransformer<T> transformer)
{{
{I}return transformer.{transform_name}(this);
}}"""
        )
    )

    blocks.append(
        Stripped(
            f"""\
/**
 * Accept the {{@code transformer}} to visit this instance for double dispatch
 * with the {{@code context}}.
 **/
@Override
public <TContext, T> T transform(
{I}Visitation.ITransformerWithContext<TContext, T> transformer,
{I}TContext context)
{{
{I}return transformer.{transform_name}(this, context);
}}"""
        )
    )

    # endregion

    # region Constructor

    if cls.constructor.is_implementation_specific:
        implementation_key = specific_implementations.ImplementationKey(
            f"Types/{cls.name}/{cls.name}.java"
        )
        implementation = spec_impls.get(implementation_key, None)

        if implementation is None:
            errors.append(
                Error(
                    cls.parsed.node,
                    f"The implementation of the implementation-specific constructor "
                    f"is missign: {implementation_key}",
                )
            )
        else:
            blocks.append(implementation)
    else:
        constructor_block, error = _generate_constructor(cls=cls)

        if error is not None:
            errors.append(error)
        else:
            if constructor_block != "":
                assert constructor_block is not None
                blocks.append(constructor_block)

    # endregion

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node,
            f"Failed to generate the code for the class {cls.name}",
            errors,
        )

    interface_name = java_naming.interface_name(cls.name)

    name = java_naming.class_name(cls.name)

    writer = io.StringIO()

    writer.write(f"public class {name} implements {interface_name}\n{{\n")

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_enum(
    enum: intermediate.Enumeration
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate Java code for the enum."""
    writer = io.StringIO()

    name = java_naming.enum_name(enum.name)
    if len(enum.literals) == 0:
        writer.write(f"public enum {name}\n{{\n}}")
        return Stripped(writer.getvalue()), None

    writer.write(f"public enum {name}\n{{\n")
    for i, literal in enumerate(enum.literals):
        if i > 0:
            writer.write(",\n")

        writer.write(
            textwrap.indent(
                f"{java_naming.enum_literal_name(literal.name)}",
                I,
            )
        )

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


class JavaFile:
    """Representation of a Java source file."""

# fmt: off
    @require(lambda name, content: (len(name) > 0) and (len(content) > 0))
    @require(lambda content: content.endswith('\n'), "Trailing newline mandatory for valid end-of-files")
# fmt: on
    def __init__(
        self,
        name: str,
        content: str,
    ):
        self.name = name
        self.content = content


def _generate_java_files(
    structure_name: Stripped,
    code: Stripped,
    package: java_common.PackageIdentifier,
) -> JavaFile:
    file_name = Stripped(f"{structure_name}.java")
    file_content = f"""\
{java_common.WARNING}

package {package};

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.Optional;
import java.util.Spliterator;
import java.util.function.Consumer;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

{code}

// package {package}

{java_common.WARNING}\n"""

    return JavaFile(file_name, file_content)


def _generate_iclass(
    package: java_common.PackageIdentifier,
) -> JavaFile:
    structure_name = Stripped("IClass")
    file_name = Stripped(f"{structure_name}.java")
    file_content = f"""\
{java_common.WARNING}

package {package};

import java.lang.Iterable;

/**
 * Represent a general class of an AAS model.
 */
public interface IClass {{
{I}/**
{I} * Iterate over all the class instances referenced from this instance
{I} * without further recursion.
{I} */
{I}public Iterable<IClass> descendOnce();

{I}/**
{I} * Iterate recursively over all the class instances referenced from this instance.
{I} */
{I}public Iterable<IClass> descend();

{I}/**
{I} * Accept the {{@code visitor}} to visit this instance
{I} * for double dispatch.
{I} */
{I}public void accept(Visitation.IVisitor visitor);

{I}/**
{I} * Accept the visitor to visit this instance for double dispatch
{I} * with the {{@code context}}.
{I} */
{I}public <TContext> void accept(
{II}Visitation.IVisitorWithContext<TContext> visitor,
{II}TContext context);

{I}/**
{I} * Accept the {{@code transformer}} to transform this instance
{I} * for double dispatch.
{I} */
{I}public <T> T transform(Visitation.ITransformer<T> transformer);

{I}/**
{I} * Accept the {{@code transformer}} to visit this instance
{I} * for double dispatch with the {{@code context}}.
{I} */
{I}public <TContext, T> T transform(
{II}Visitation.ITransformerWithContext<TContext, T> transformer,
{II}TContext context);
}}
//package {package}

{java_common.WARNING}\n"""

    return JavaFile(file_name, file_content)


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _generate_structure(
    our_type: intermediate.OurType,
    package: java_common.PackageIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[List[JavaFile]], Optional[Error]]:
    """
    Generate the Java code for a single structure.
    """
    assert isinstance(our_type, (
        intermediate.Enumeration,
        intermediate.AbstractClass,
        intermediate.ConcreteClass,
    ))

    files = []  # List[JavaFile]

    if (
        isinstance(our_type, intermediate.Class)
        and our_type.is_implementation_specific
    ):
        implementation_key = specific_implementations.ImplementationKey(
            f"Types/{our_type.name}.java"
        )

        code = spec_impls.get(implementation_key, None)
        if code is None:
            return None, Error(
                    our_type.parsed.node,
                    f"The implementation is missing "
                    f"for the implementation-specific class: {implementation_key}",
            )

        structure_name = java_naming.class_name(our_type.name)

        java_source = _generate_java_files(structure_name, code, package)

        files.append(java_source)
    else:
        if isinstance(
                our_type, (
                    intermediate.AbstractClass,
                    intermediate.ConcreteClass
                )
        ):
            code, error = _generate_interface(cls=our_type)
            if error is not None:
                return None, Error(our_type.parsed.node,
                                   f"Failed to generate the interface code for "
                                   f"the class {our_type.name!r}",
                                   [error],
                )

            assert code is not None

            structure_name = java_naming.interface_name(our_type.name)

            java_source = _generate_java_files(structure_name, code, package)

            files.append(java_source)

            if isinstance(
                    our_type, intermediate.ConcreteClass
            ):
                code, error = _generate_class(cls=our_type, spec_impls=spec_impls)
                if error is not None:
                    return None, Error(our_type.parsed.node,
                                       f"Failed to generate the class code for "
                                       f"the class {our_type.name!r}",
                                       [error],
                    )

                assert code is not None

                structure_name = java_naming.class_name(our_type.name)

                java_source = _generate_java_files(structure_name, code, package)

                files.append(java_source)
        elif isinstance(
                our_type, intermediate.Enumeration
        ):
            code, error = _generate_enum(enum=our_type)
            if error is not None:
                return None, Error(our_type.parsed.node,
                                   f"Failed to generate the code for "
                                   f"the enumeration {our_type.name!r}",
                                   [error],
                )

            assert code is not None
            structure_name = java_naming.enum_name(our_type.name)

            java_source = _generate_java_files(structure_name, code, package)

            files.append(java_source)
        else:
            assert_never(our_type)


    return files, None

# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def generate(
    symbol_table: VerifiedIntermediateSymbolTable,
    package: java_common.PackageIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[List[JavaFile]], Optional[List[Error]]]:
    """
    Generate the Java code of the structures based on the symbol table.

    The ``package`` defines the AAS Java package.
    """

    files = []  # type: List[JavaFile]
    errors = []  # type: List[Error]

    files.append(_generate_iclass(package))

    for our_type in symbol_table.our_types:
        if not isinstance(
                our_type,
                (
                    intermediate.Enumeration,
                    intermediate.AbstractClass,
                    intermediate.ConcreteClass,
                ),
        ):
            continue

        new_files, error = _generate_structure(our_type,
                                               package,
                                               spec_impls)

        if new_files is not None:
            files.extend(new_files)
        elif error is not None:
            errors.append(error)

    if len(errors) > 0:
        return None, errors

    return files, None


# endregion
