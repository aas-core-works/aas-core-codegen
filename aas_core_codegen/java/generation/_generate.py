"""Generate builders for the AAS data structures."""

import io
import textwrap
from typing import (
    List,
    Optional,
    Tuple,
)

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    Error,
    Identifier,
    Stripped,
    indent_but_first_line,
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


# fmt: off
@require(
    lambda cls: any(
        isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation)
        for arg in cls.constructor.arguments
    )
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _generate_builder(
    cls: intermediate.ConcreteClass,
    package: java_common.PackageIdentifier,
) -> Tuple[Optional[java_common.JavaFile], Optional[Error]]:

    class_name = java_naming.class_name(cls.name)

    builder_name = java_naming.class_name(Identifier(f"{class_name}_builder"))

    file_name = f"{builder_name}.java"

    package_name = java_common.PackageIdentifier(f"{package}.generation")

    builder_blocks = []  # type: List[Stripped]

    # region Properties

    properties_blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        prop_type = java_common.generate_type(type_annotation=type_anno)

        prop_name = java_naming.property_name(prop.name)

        blocks = []  # type: List[Stripped]

        if prop.description is not None:
            (
                prop_comment,
                prop_comment_errors,
            ) = java_description.generate_comment_for_property(prop.description)

            if prop_comment_errors:
                return None, Error(
                    prop.description.parsed.node,
                    f"Failed to generate the documentation comment "
                    f"for the property {prop.name!r}",
                    prop_comment_errors,
                )

            assert prop_comment is not None

            blocks.append(prop_comment)

        blocks.append(
            Stripped(
                f"""\
private {prop_type} {prop_name};"""
            )
        )

        properties_blocks.append(Stripped("\n".join(blocks)))

    builder_blocks.append(Stripped("\n\n".join(properties_blocks)))

    # endregion

    # region Constructor

    arg_codes = []  # type: List[Stripped]

    for arg in cls.constructor.arguments:
        if isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        arg_type = java_common.generate_type(type_annotation=arg.type_annotation)

        arg_name = java_naming.argument_name(arg.name)

        arg_codes.append(Stripped(f"{arg_type} {arg_name}"))

    if len(arg_codes) > 0:

        constructor_writer = io.StringIO()

        if len(arg_codes) == 1:
            constructor_writer.write(f"public {builder_name}({arg_codes[0]}) {{\n")
        else:
            arg_block = ",\n".join(arg_codes)
            arg_block_indented = textwrap.indent(arg_block, I)
            constructor_writer.write(
                f"public {builder_name}(\n{arg_block_indented}) {{\n"
            )

        for arg in cls.constructor.arguments:
            if isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation):
                continue

            arg_name = java_naming.argument_name(arg.name)

            constructor_writer.write(
                f"""\
{I}this.{arg_name} = Objects.requireNonNull(
{II}{arg_name},
{II}"Argument \\"{arg_name}\\" must be non-null.");
"""
            )

        constructor_writer.write("}")

        constructor = constructor_writer.getvalue()

        builder_blocks.append(Stripped(constructor))

    # endregion

    # region Setters

    setter_blocks = []  # type: List[Stripped]

    for arg in cls.constructor.arguments:
        if not isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        type_anno = intermediate.beneath_optional(arg.type_annotation)

        arg_type = java_common.generate_type(type_annotation=type_anno)

        arg_name = java_naming.argument_name(arg.name)

        setter_name = java_naming.setter_name(arg_name)

        setter_blocks.append(
            Stripped(
                f"""\
public {builder_name} {setter_name}({arg_type} {arg_name}) {{
{I}this.{arg_name} = {arg_name};
{I}return this;
}}"""
            )
        )

    builder_blocks.append(Stripped("\n\n".join(setter_blocks)))

    # endregion

    # region Build method

    build_method_writer = io.StringIO()

    build_method_writer.write(f"public {class_name} build() {{\n")

    build_method_writer.write(f"{I}return new {class_name}(")

    if len(cls.constructor.arguments) == 1:
        arg_name = java_naming.argument_name(cls.constructor.arguments[0].name)

        build_method_writer.write(f"this.{arg_name}")
    else:
        for idx, arg in enumerate(cls.constructor.arguments):
            arg_name = java_naming.argument_name(arg.name)

            if idx >= 1:
                build_method_writer.write(f",")

            build_method_writer.write(f"\n{II}this.{arg_name}")

    build_method_writer.write(f");")

    build_method_writer.write("\n}")

    builder_blocks.append(Stripped(build_method_writer.getvalue()))

    # endregion

    builder = Stripped("\n\n".join(builder_blocks))

    return (
        java_common.JavaFile(
            name=file_name,
            content=f"""\
package {package_name};

import {package}.types.enums.*;
import {package}.types.impl.*;
import {package}.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import javax.annotation.Generated;

/**
 * Builder for the {class_name} type.
 */
@Generated("generated by aas-core-codegen")
public class {builder_name} {{
{I}{indent_but_first_line(builder, I)}
}}
""",
        ),
        None,
    )


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    package: java_common.PackageIdentifier,
) -> Tuple[Optional[List[java_common.JavaFile]], Optional[List[Error]]]:
    """
    Generate the Java code of the structures based on the symbol table.

    The ``package`` defines the root Java package.
    """

    files = []  # type: List[java_common.JavaFile]
    errors = []  # type: List[Error]

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type,
            intermediate.ConcreteClass,
        ):
            continue

        if not any(
            isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation)
            for arg in our_type.constructor.arguments
        ):
            continue

        new_file, error = _generate_builder(our_type, package)

        if error is not None:
            errors.append(error)
            continue

        assert new_file is not None

        files.append(new_file)

    if len(errors) > 0:
        return None, errors

    return files, None
