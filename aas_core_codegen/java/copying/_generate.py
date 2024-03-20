"""Generate Java code for copying in memory based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import (
    Error,
    Stripped,
    Identifier,
    indent_but_first_line,
    assert_never,
)
from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
)


# region Generate


def _generate_shallow_copy_transform_method(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Generate the method in the transformer to make a shallow copy of ``cls''."""
    property_names = [prop.name for prop in cls.properties]
    constructor_argument_names = [arg.name for arg in cls.constructor.arguments]

    # fmt: off
    assert (
        set(prop.name for prop in cls.properties)
        == set(arg.name for arg in cls.constructor.arguments)
    ), (
        f"Expected the properties to coincide with constructor arguments, "
        f"but they do not for {cls.name!r}:"
        f"{property_names=}, {constructor_argument_names=}"
    )
    # fmt: on

    cls_name = java_naming.class_name(cls.name)

    if len(cls.constructor.arguments) == 0:
        return_statement = Stripped(f"return new {cls_name}();")
    else:
        constructor_arg_exprs = []  # type: List[str]
        for arg in cls.constructor.arguments:
            if isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation):
                getter_name = java_naming.getter_name(arg.name)
                constructor_arg_exprs.append(f"that.{getter_name}().orElse(null)")
            else:
                getter_name = java_naming.getter_name(arg.name)
                constructor_arg_exprs.append(f"that.{getter_name}()")

        args_joined = ", ".join(constructor_arg_exprs)
        return_statement = Stripped(f"return new {cls_name}({args_joined});")

        if len(return_statement) > 70:
            args_joined = ",\n".join(constructor_arg_exprs)
            return_statement = Stripped(
                f"""\
return new {cls_name}(
{I}{indent_but_first_line(args_joined, I)});"""
            )

    interface_name = java_naming.interface_name(cls.name)
    transform_name = java_naming.method_name(Identifier(f"transform_{cls.name}"))

    return Stripped(
        f"""\
@Override
public IClass {transform_name}(
{I}{interface_name} that
) {{
{I}{indent_but_first_line(return_statement, I)}
}}"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_shallow_copier(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the transformer which makes shallow copies."""
    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        if cls.is_implementation_specific:
            implementation_key = specific_implementations.ImplementationKey(
                f"Copying/ShallowCopier/transform_{cls.name}.java"
            )

            implementation = spec_impls.get(implementation_key, None)
            if implementation is None:
                errors.append(
                    Error(
                        cls.parsed.node,
                        f"The snippet for making shallow copies is missing "
                        f"for the implementation-specific "
                        f"class {cls.name}: {implementation_key}",
                    )
                )
                continue

            blocks.append(spec_impls[implementation_key])
        else:
            blocks.append(_generate_shallow_copy_transform_method(cls=cls))

    writer = io.StringIO()
    writer.write(
        """\
/**
 * Dispatch the making of shallow copies.
 */
private static class ShallowCopier extends AbstractTransformer<IClass> {
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_deep_copy_transform_method(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the method in the transformer to make a deep copy of ``cls''."""
    property_names = [prop.name for prop in cls.properties]
    constructor_argument_names = [arg.name for arg in cls.constructor.arguments]

    # fmt: off
    assert (
            set(prop.name for prop in cls.properties)
            == set(arg.name for arg in cls.constructor.arguments)
    ), (
        f"Expected the properties to coincide with constructor arguments, "
        f"but they do not for {cls.name!r}:"
        f"{property_names=}, {constructor_argument_names=}"
    )
    # fmt: on

    cls_name = java_naming.class_name(cls.name)

    body_blocks = []  # type: List[Stripped]

    if len(cls.constructor.arguments) == 0:
        body_blocks.append(Stripped(f"return new {cls_name}();"))
    else:
        for arg in cls.constructor.arguments:
            getter_name = java_naming.getter_name(arg.name)
            optional = isinstance(
                arg.type_annotation, intermediate.OptionalTypeAnnotation
            )

            type_anno = intermediate.beneath_optional(arg.type_annotation)

            if not isinstance(type_anno, intermediate.ListTypeAnnotation):
                continue

            assert isinstance(
                type_anno.items, intermediate.OurTypeAnnotation
            ) and isinstance(type_anno.items.our_type, intermediate.Class), (
                "We handle only lists of classes in the deep copies at the "
                "moment. The meta-model does not contain any other lists, so "
                "we wanted to keep the code as simple as possible, and avoid "
                "unrolling. Please contact the developers if you need this "
                "feature."
            )

            # We need to prefix to avoid any possible naming conflicts.
            variable_name = java_naming.variable_name(Identifier(f"the_{arg.name}"))

            variable_type = java_common.generate_type(type_anno)

            inner_type = java_naming.interface_name(type_anno.items.our_type.name)

            if not optional:
                body_blocks.append(
                    Stripped(
                        f"""\
{variable_type} {variable_name} = new ArrayList<>(
{I}that.{getter_name}().size());
for ({inner_type} item : that.{getter_name}()) {{
{I}{variable_name}.add(deep(item));
}}"""
                    )
                )
            else:
                other_property_name = java_naming.variable_name(
                    Identifier(f"that_{arg.name}")
                )

                body_blocks.append(
                    Stripped(
                        f"""\
{variable_type} {other_property_name} =
{I}that.{getter_name}().orElse(null);
{variable_type} {variable_name} = null;
if ({other_property_name} != null) {{
{I}{variable_name} = new ArrayList<>(
{II}{other_property_name}.size());
{I}for ({inner_type} item : {other_property_name})
{I}{{
{II}{variable_name}.add(deep(item));
{I}}}
}}"""
                    )
                )

        constructor_arg_exprs = []  # type: List[str]
        for arg in cls.constructor.arguments:
            getter_name = java_naming.getter_name(arg.name)

            type_anno = intermediate.beneath_optional(arg.type_annotation)

            optional = isinstance(
                arg.type_annotation, intermediate.OptionalTypeAnnotation
            )

            if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
                if optional:
                    constructor_arg_exprs.append(
                        f"""that.{getter_name}().orElse(null)"""
                    )
                else:
                    constructor_arg_exprs.append(f"""that.{getter_name}()""")

            elif isinstance(type_anno, intermediate.OurTypeAnnotation):
                if isinstance(type_anno.our_type, intermediate.Enumeration):
                    if optional:
                        constructor_arg_exprs.append(
                            f"""that.{getter_name}().orElse(null)"""
                        )
                    else:
                        constructor_arg_exprs.append(f"""that.{getter_name}()""")

                elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                    if optional:
                        constructor_arg_exprs.append(
                            f"""that.{getter_name}().orElse(null)"""
                        )
                    else:
                        constructor_arg_exprs.append(f"""that.{getter_name}()""")

                elif isinstance(
                    type_anno.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ):
                    if optional:
                        constructor_arg_exprs.append(
                            f"""that.{getter_name}().orElse(null)"""
                        )
                    else:
                        constructor_arg_exprs.append(f"deep(that.{getter_name}())")
                else:
                    assert_never(type_anno.our_type)

            elif isinstance(type_anno, intermediate.ListTypeAnnotation):
                # See how this variable is computed above in the generated code.
                constructor_arg_exprs.append(
                    java_naming.variable_name(Identifier(f"the_{arg.name}"))
                )
            else:
                assert_never(type_anno)

        return_statement_writer = io.StringIO()

        return_statement_writer.write(f"return new {cls_name}(\n")

        for i, arg_expr in enumerate(constructor_arg_exprs):
            return_statement_writer.write(textwrap.indent(arg_expr, I))

            if i < len(constructor_arg_exprs) - 1:
                return_statement_writer.write(",\n")
            else:
                return_statement_writer.write("\n")

        return_statement_writer.write(");")

        body_blocks.append(Stripped(return_statement_writer.getvalue()))

    body_writer = io.StringIO()
    for i, body_block in enumerate(body_blocks):
        if i > 0:
            body_writer.write("\n\n")

        body_writer.write(body_block)

    interface_name = java_naming.interface_name(cls.name)
    transform_name = java_naming.method_name(Identifier(f"transform_{cls.name}"))

    return Stripped(
        f"""\
@Override
public IClass {transform_name} (
{I}{interface_name} that
) {{
{I}{indent_but_first_line(body_writer.getvalue(), I)}
}}"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_deep_copier(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the transformer which makes deep copies."""
    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        if cls.is_implementation_specific:
            implementation_key = specific_implementations.ImplementationKey(
                f"Copying/DeepCopier/transform_{cls.name}.java"
            )

            implementation = spec_impls.get(implementation_key, None)
            if implementation is None:
                errors.append(
                    Error(
                        cls.parsed.node,
                        f"This snippet for making deep copies is missing "
                        f"for the implementation-specific "
                        f"class {cls.name}: {implementation_key}",
                    )
                )
                continue

            blocks.append(spec_impls[implementation_key])
        else:
            blocks.append(_generate_deep_copy_transform_method(cls=cls))

    writer = io.StringIO()
    writer.write(
        """\
/** Dispatch the making of deep copies. */
private static class DeepCopier extends AbstractTransformer<IClass> {
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

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
    symbol_table: intermediate.SymbolTable,
    package: java_common.PackageIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Java code for copying instances in memory.

    The ``namespace`` defines the AAS Java namespace.
    """
    errors = []  # type: List[Error]

    imports = [
        Stripped(f"import java.util.List;"),
        Stripped(f"import java.util.ArrayList;"),
        Stripped(f"import {package}.types.{java_common.INTERFACE_PKG}.IClass;"),
        Stripped(f"import {package}.visitation.AbstractTransformer;"),
        Stripped(f"import {package}.types.impl.*;"),
        Stripped(f"import {package}.types.model.*;"),
    ]  # type: List[Stripped]

    # NOTE (empwilli, 2023-12-14):
    # We wrap the shallow and deep copying in generic methods to allow for easier
    # enforcement of runtime type safety for the client. Otherwise, if we directly
    # provided the transformer, the client would always need to make the casts, which
    # is cumbersome.

    copy_blocks = [
        Stripped(
            f"""private static final ShallowCopier shallowCopierInstance = new ShallowCopier();"""
        ),
        Stripped(
            f"""private static final DeepCopier deepCopierInstance = new DeepCopier();"""
        ),
        Stripped(
            f"""\
/**
 * Make a shallow copy of {{@code that}}.
 *
 * <p>All the properties are copied by reference. This includes also the lists.
 * Hence, a list property is copied by reference, and not, as sometimes might be
 * expected, as a new list of underlying references.
 *
 * @param that to be copied in a shallow manner
 */
@SuppressWarnings("unchecked")
public static <T extends IClass> T shallow(T that) {{
{I}return (T) shallowCopierInstance.transform(that);
}}"""
        ),
        Stripped(
            f"""\
/**
 * Make a recursively a deep copy of {{@code that}}.
 *
 * @param that to be deeply copied in a recursive manner
 */
@SuppressWarnings("unchecked")
public static <T extends IClass> T deep(T that) {{
{I}return (T) deepCopierInstance.transform(that);
}}"""
        ),
    ]  # type: List[Stripped]

    shallow_copier_block, shallow_errors = _generate_shallow_copier(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if shallow_errors is not None:
        errors.extend(shallow_errors)
    else:
        assert shallow_copier_block is not None
        copy_blocks.append(shallow_copier_block)

    deep_copier_block, deep_errors = _generate_deep_copier(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if deep_errors is not None:
        errors.extend(deep_errors)
    else:
        assert deep_copier_block is not None
        copy_blocks.append(deep_copier_block)

    if len(errors) > 0:
        return None, errors

    copying_writer = io.StringIO()
    copying_writer.write(
        """\
/**
 * Allow for making shallow and deep copies of AAS model instances.
 */
public class Copying
{
"""
    )

    for i, copy_block in enumerate(copy_blocks):
        if i > 0:
            copying_writer.write("\n\n")

        copying_writer.write(textwrap.indent(copy_block, I))

    copying_writer.write("\n}")

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.copying;"),
        Stripped("\n".join(imports)),
        Stripped(f"{copying_writer.getvalue()}"),
        java_common.WARNING,
    ]  # type: List[Stripped]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None


# endregion
