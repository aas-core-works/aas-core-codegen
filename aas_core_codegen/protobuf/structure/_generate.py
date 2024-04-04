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
    Mapping,
    Final,
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
    unrolling as proto_unrolling,
    description as proto_description,
)
from aas_core_codegen.protobuf.common import (
    INDENT as I,
    INDENT2 as II,
)
from aas_core_codegen.intermediate import (
    construction as intermediate_construction,
)


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

        for method in our_type.methods:
            method_name = proto_naming.method_name(method.name)

            if method_name in observed_member_names:
                errors.append(
                    Error(
                        method.parsed.node,
                        f"ProtoBuf method {method_name!r} corresponding "
                        f"to the meta-model method {method.name!r} collides with "
                        f"the {observed_member_names[method_name]}",
                    )
                )
            else:
                observed_member_names[method_name] = (
                    f"ProtoBuf method {method_name!r} corresponding to "
                    f"the meta-model method {method.name!r}"
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
                intermediate.AbstractClass,
                intermediate.ConcreteClass,
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
                        f"The ProtoBuf name {name!r} for the enumeration {our_type.name!r} "
                        f"collides with the same ProtoBuf name "
                        f"coming from the {_human_readable_identifier(other)}",
                    )
                )
            else:
                observed_structure_names[name] = our_type

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            interface_name = proto_naming.interface_name(our_type.name)

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

            if isinstance(our_type, intermediate.ConcreteClass):
                class_name = proto_naming.class_name(our_type.name)

                other = observed_structure_names.get(class_name, None)

                if other is not None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The ProtoBuf name {class_name!r} "
                            f"for the class {our_type.name!r} "
                            f"collides with the same ProtoBuf name "
                            f"coming from the {_human_readable_identifier(other)}",
                        )
                    )
                else:
                    observed_structure_names[class_name] = our_type
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
    writer.write(textwrap.indent(f"{proto_naming.enum_literal_name(enum.name)}_UNSPECIFIED = 0", I))

    if len(enum.literals) == 0:
        writer.write(f"\n}}")
        return Stripped(writer.getvalue()), None

    for i, literal in enumerate(enum.literals):
        writer.write(",\n\n")

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
        # an ID that is necessary for (de-)serialization.
        # If that ID is re-assigned to another literal in the same enum in a later version, conflicts will arise.
        # TODO: With each build, add IDs of the previous build to a `reserved`-statement and add an offset to new IDs.
        writer.write(
            textwrap.indent(
                f"{proto_naming.enum_literal_name(literal.name)} = {i + 1}",
                I,
            )
        )

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_interface(
    cls: intermediate.ClassUnion,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate ProtoBuf interface for the given class ``cls``."""
    raise NotImplementedError("Interfaces are not supported by proto3. Treat as class instead.")

