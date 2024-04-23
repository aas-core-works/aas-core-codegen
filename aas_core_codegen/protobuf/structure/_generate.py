"""Generate the ProtoBuf data structures from the intermediate representation."""

import io
import textwrap
from typing import (
    Optional,
    Dict,
    List,
    Tuple,
    cast,
    Union,
    Set,
)

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen import specific_implementations
from aas_core_codegen.common import (
    Error,
    Identifier,
    assert_never,
    Stripped,
    indent_but_first_line,
)
from aas_core_codegen.protobuf import (
    common as proto_common,
    naming as proto_naming,
    description as proto_description,
)
from aas_core_codegen.protobuf.common import INDENT as I, INDENT2 as II


# region Checks


def _human_readable_identifier(
    something: Union[
        intermediate.Enumeration, intermediate.AbstractClass, intermediate.ConcreteClass
    ]
) -> str:
    """
    Represent ``something`` in a human-readable text.

    The reader should be able to trace ``something`` back to the meta-model.
    """
    result: str

    if isinstance(something, intermediate.Enumeration):
        result = f"meta-model enumeration {something.name!r}"
    elif isinstance(something, intermediate.AbstractClass):
        result = f"meta-model abstract class {something.name!r}"
    elif isinstance(something, intermediate.ConcreteClass):
        result = f"meta-model concrete class {something.name!r}"
    else:
        assert_never(something)

    return result


def _verify_intra_structure_collisions(
    our_type: intermediate.OurType,
) -> Optional[Error]:
    """Verify that no member names collide in the ProtoBuf structure of our type."""
    errors = []  # type: List[Error]

    if isinstance(our_type, intermediate.Enumeration):
        pass

    elif isinstance(our_type, intermediate.ConstrainedPrimitive):
        pass

    elif isinstance(our_type, intermediate.Class):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in our_type.properties:
            prop_name = proto_naming.property_name(prop.name)
            if prop_name in observed_member_names:
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"ProtoBuf property {prop_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[prop_name]}",
                    )
                )
            else:
                observed_member_names[prop_name] = (
                    f"ProtoBuf property {prop_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}"
                )

    else:
        assert_never(our_type)

    if len(errors) > 0:
        errors.append(
            Error(
                our_type.parsed.node,
                f"Naming collision(s) in ProtoBuf code for our type {our_type.name!r}",
                underlying=errors,
            )
        )

    return None


def _verify_structure_name_collisions(
    symbol_table: intermediate.SymbolTable,
) -> List[Error]:
    """Verify that the ProtoBuf names of the structures do not collide."""
    observed_structure_names: Dict[
        Identifier,
        Union[
            intermediate.Enumeration,
            intermediate.AbstractClass,
            intermediate.ConcreteClass,
        ],
    ] = dict()

    errors = []  # type: List[Error]

    # region Inter-structure collisions

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type,
            (
                intermediate.Enumeration,
                intermediate.Class,
            ),
        ):
            continue

        if isinstance(our_type, intermediate.Enumeration):
            name = proto_naming.enum_name(our_type.name)
            other = observed_structure_names.get(name, None)

            if other is not None:
                errors.append(
                    Error(
                        our_type.parsed.node,
                        f"The ProtoBuf name {name!r} for the enumeration"
                        f" {our_type.name!r} "
                        f"collides with the same ProtoBuf name "
                        f"coming from the {_human_readable_identifier(other)}",
                    )
                )
            else:
                observed_structure_names[name] = our_type

        elif isinstance(our_type, intermediate.Class):
            interface_name = proto_naming.class_name(our_type.name)

            other = observed_structure_names.get(interface_name, None)

            if other is not None:
                errors.append(
                    Error(
                        our_type.parsed.node,
                        f"The ProtoBuf name {interface_name!r} of the interface "
                        f"for the class {our_type.name!r} "
                        f"collides with the same ProtoBuf name "
                        f"coming from the {_human_readable_identifier(other)}",
                    )
                )
            else:
                observed_structure_names[interface_name] = our_type

        else:
            assert_never(our_type)

    # endregion

    # region Intra-structure collisions

    for our_type in symbol_table.our_types:
        collision_error = _verify_intra_structure_collisions(our_type=our_type)

        if collision_error is not None:
            errors.append(collision_error)

    # endregion

    return errors


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
    """Verify that ProtoBuf code can be generated from the ``symbol_table``."""
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
    """Generate the ProtoBuf code for the enum."""
    writer = io.StringIO()

    if enum.description is not None:
        comment, comment_errors = proto_description.generate_comment_for_our_type(
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

    name = proto_naming.enum_name(enum.name)

    # write enum and its name
    writer.write(f"enum {name} {{\n")
    # write at least the unspecified enum entry
    writer.write(textwrap.indent(f"{proto_naming.enum_name(name)}_UNSPECIFIED = 0;", I))

    if len(enum.literals) == 0:
        writer.write("\n}")
        return Stripped(writer.getvalue()), None

    for i, literal in enumerate(enum.literals):
        writer.write("\n\n")

        if literal.description:
            (
                literal_comment,
                literal_comment_errors,
            ) = proto_description.generate_comment_for_enumeration_literal(
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

        # Enums cannot have string-values assigned to them in proto3. Instead, they each get assigned
        # an ID that is used for (de-)serialization.
        # If that ID is re-assigned to another literal in the same enum in a later version, a system using the
        # old version will (de-)serialize that literal differently. Hence, hope that the order of writing the literals
        # stays the same in each build so that one literal always gets the same ID. Otherwise, don't mix versions.
        # With each version, compare to the previous one and assign same ID.
        # With each version, add a `reserved`-statement for deleted literals and their IDs.
        writer.write(
            textwrap.indent(
                f"""\
{proto_naming.enum_name(name)}_{proto_naming.enum_literal_name(literal.name)}\
 = {i + 1};""",
                I,
            )
        )

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@require(lambda cls: not cls.is_implementation_specific)
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_class(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[Error], List[intermediate.AbstractClass],]:
    """Generate ProtoBuf code for the given concrete class ``cls``."""
    # Code blocks to be later joined by double newlines and indented once
    blocks = []  # type: List[Stripped]

    required_choice_object = []  # type: List[intermediate.AbstractClass]

    # region Getters and setters
    for i, prop in enumerate(
        set(cls.properties).union(
            set(cls.interface.properties if cls.interface is not None else [])
        )
    ):
        prop_type = proto_common.generate_type(type_annotation=prop.type_annotation)

        prop_name = proto_naming.property_name(prop.name)

        prop_blocks = []  # type: List[Stripped]

        if prop.description is not None:
            (
                prop_comment,
                prop_comment_errors,
            ) = proto_description.generate_comment_for_property(prop.description)
            if prop_comment_errors:
                return (
                    None,
                    Error(
                        prop.description.parsed.node,
                        f"Failed to generate the documentation comment "
                        f"for the property {prop.name!r}",
                        prop_comment_errors,
                    ),
                    [],
                )

            assert prop_comment is not None

            prop_blocks.append(prop_comment)

        # lists of our types where our types are abstract/interfaces
        if (
            isinstance(prop.type_annotation, intermediate.ListTypeAnnotation)
            and isinstance(prop.type_annotation.items, intermediate.OurTypeAnnotation)
            and isinstance(
                prop.type_annotation.items.our_type,
                (intermediate.Interface, intermediate.AbstractClass),
            )
        ):
            # -> must create a new message (choice object) since "oneof"
            # and "repeated" do not go together
            prop_blocks.append(Stripped(f"{prop_type} {prop_name} = {i + 2};"))
            required_choice_object.append(prop.type_annotation.items.our_type)

        # optional lists of our types where our types are abstract/interfaces
        elif (
            isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
            and isinstance(prop.type_annotation.value, intermediate.ListTypeAnnotation)
            and isinstance(
                prop.type_annotation.value.items, intermediate.OurTypeAnnotation
            )
            and isinstance(
                prop.type_annotation.value.items.our_type,
                (intermediate.Interface, intermediate.AbstractClass),
            )
        ):
            # -> same as the case before
            prop_blocks.append(Stripped(f"{prop_type} {prop_name} = {i + 2};"))
            required_choice_object.append(prop.type_annotation.value.items.our_type)

        # our types where our types are abstract/interfaces
        elif isinstance(
            prop.type_annotation, intermediate.OurTypeAnnotation
        ) and isinstance(
            prop.type_annotation.our_type,
            (intermediate.Interface, intermediate.AbstractClass),
        ):
            # -> must use "oneof"
            prop_blocks.append(Stripped(f"{prop_type} {prop_name} = {i + 2};"))
            required_choice_object.append(prop.type_annotation.our_type)

        else:
            # just a normal property with type
            prop_blocks.append(Stripped(f"{prop_type} {prop_name} = {i + 2};"))

        blocks.append(Stripped("\n".join(prop_blocks)))

    # one additional property indicating the concrete class type (in case multiple
    # inherit from the same interface) when instantiating a class of this proto,
    # the field must be set (ideally in the constructor)
    blocks.append(Stripped("MessageType message_type = 1;"))

    # endregion

    name = proto_naming.class_name(cls.name)

    writer = io.StringIO()

    if cls.description is not None:
        comment, comment_errors = proto_description.generate_comment_for_our_type(
            cls.description
        )
        if comment_errors is not None:
            return (
                None,
                Error(
                    cls.description.parsed.node,
                    "Failed to generate the comment description",
                    comment_errors,
                ),
                [],
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    writer.write(f"message {name} {{\n")

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None, required_choice_object


def _generate_message_type_enum(
    symbol_table: VerifiedIntermediateSymbolTable,
) -> Tuple[Stripped, Optional[Error]]:
    writer = io.StringIO()

    name = "MessageType"

    # write enum and its name
    writer.write(f"enum {name} {{\n")
    # write at least the unspecified enum entry
    writer.write(textwrap.indent(f"{name}_UNSPECIFIED = 0;", I))

    # generate one enum entry for each concrete class
    for i, cls in enumerate(symbol_table.concrete_classes):
        writer.write("\n\n")

        writer.write(
            textwrap.indent(
                f"{name}_{proto_naming.enum_literal_name(cls.name)} = {i + 1};",
                I,
            )
        )

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_choice_class(cls: intermediate.AbstractClass) -> str:
    msg_header = f"message {proto_naming.class_name(cls.name)} {{\n"
    msg_body = f"{I}oneof value {{\n"

    for j, subtype in enumerate(cls.concrete_descendants):
        subtype_type = proto_naming.class_name(subtype.name)
        subtype_name = proto_naming.property_name(subtype.name)
        msg_body += f"{II}{subtype_type} {subtype_name} = {j + 1};\n"

    return msg_header + msg_body + f"{I}}}\n}}"


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result: not (result[0] is not None) or result[0].endswith("\n"),
    "Trailing newline mandatory for valid end-of-files",
)
# fmt: on
def generate(
    symbol_table: VerifiedIntermediateSymbolTable,
    namespace: proto_common.NamespaceIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the ProtoBuf code of the structures based on the symbol table.

    The ``namespace`` defines the AAS ProtoBuf package.
    """
    code_blocks = []  # type: List[Stripped]

    errors = []  # type: List[Error]

    required_choice_objects = set([])  # type: Set[intermediate.AbstractClass]

    for our_type in symbol_table.our_types:
        if not isinstance(
            our_type,
            (
                intermediate.Enumeration,
                intermediate.ConcreteClass,
            ),
        ):
            continue

        if isinstance(our_type, intermediate.ConcreteClass):
            code, error, choice_obj = _generate_class(cls=our_type)
            if error is not None:
                errors.append(
                    Error(
                        our_type.parsed.node,
                        f"Failed to generate the class code for "
                        f"the class {our_type.name!r}",
                        [error],
                    )
                )
                continue

            assert code is not None
            code_blocks.append(code)
            required_choice_objects = required_choice_objects.union(set(choice_obj))

        elif isinstance(our_type, intermediate.Enumeration):
            code, error = _generate_enum(enum=our_type)
            if error is not None:
                errors.append(
                    Error(
                        our_type.parsed.node,
                        f"Failed to generate the code for "
                        f"the enumeration {our_type.name!r}",
                        [error],
                    )
                )
                continue

            assert code is not None
            code_blocks.append(code)

        else:
            assert_never(our_type)

    # generate the necessary classes for choice (i.e. a class for every property that
    # was like "repeated <interface>")
    for cls in required_choice_objects:
        code_blocks.append(Stripped(_generate_choice_class(cls)))

    code, error = _generate_message_type_enum(symbol_table)
    if error is None:
        code_blocks.append(code)

    if len(errors) > 0:
        return None, errors

    code_blocks_joined = "\n\n".join(code_blocks)

    blocks = [
        proto_common.WARNING,
        Stripped(
            f"""\
syntax = "proto3";

package {namespace};


{I}{indent_but_first_line(code_blocks_joined, I)}"""
        ),
        proto_common.WARNING,
    ]  # type: List[Stripped]

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None
