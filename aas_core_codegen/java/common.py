"""Provide common functions shared among different Java code generation modules."""
import re
from typing import List, cast, Optional

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen.common import Stripped, assert_never
from aas_core_codegen.java import naming as java_naming


@ensure(lambda result: result.startswith('"'))
@ensure(lambda result: result.endswith('"'))
def string_literal(text: str) -> Stripped:
    """Generate a Java string literal from the ``text``."""
    escaped = []  # type: List[str]

    for character in text:
        if character == "\t":
            escaped.append("\\t")
        elif character == "\b":
            escaped.append("\\b")
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\f":
            escaped.append("\\f")
        elif character == "'":
            escaped.append("\\'")
        elif character == '"':
            escaped.append('\\"')
        elif character == "\\":
            escaped.append("\\\\")
        else:
            escaped.append(character)

    return Stripped('"{}"'.format("".join(escaped)))


def needs_escaping(text: str) -> bool:
    """Check whether the ``text`` contains a character that needs escaping."""
    for character in text:
        if character == "\t":
            return True
        elif character == "\b":
            return True
        elif character == "\n":
            return True
        elif character == "\r":
            return True
        elif character == "\f":
            return True
        elif character == "'":
            return True
        elif character == '"':
            return True
        elif character == "\\":
            return True
        else:
            pass

    return False


PRIMITIVE_TYPE_MAP = {
    intermediate.PrimitiveType.BOOL: Stripped("Boolean"),
    intermediate.PrimitiveType.INT: Stripped("Long"),
    intermediate.PrimitiveType.FLOAT: Stripped("Float"),
    intermediate.PrimitiveType.STR: Stripped("String"),
    intermediate.PrimitiveType.BYTEARRAY: Stripped("byte[]"),
}


# fmt: off
@require(
    lambda our_type_qualifier:
    not (our_type_qualifier is not None)
    or not our_type_qualifier.endswith('.')
)
# fmt: on
def generate_type(
    type_annotation: intermediate.TypeAnnotationUnion,
    our_type_qualifier: Optional[Stripped] = None,
) -> Stripped:
    """
    Generate the Java type for the given type annotation.

    ``our_type_prefix`` is appended to all our types, if specified.
    """
    our_type_prefix = "" if our_type_qualifier is None else f"{our_type_qualifier}."
    # BEFORE-RELEASE (empwilli, 2023-12-14): test in isolation
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return PRIMITIVE_TYPE_MAP[type_annotation.a_type]

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        our_type = type_annotation.our_type

        if isinstance(our_type, intermediate.Enumeration):
            return Stripped(
                our_type_prefix + java_naming.enum_name(type_annotation.our_type.name)
            )

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            return PRIMITIVE_TYPE_MAP[our_type.constrainee]

        elif isinstance(our_type, intermediate.Class):
            # NOTE (empwilli, 2023-12-14):
            # We want to allow custom enhancements and wrappings around
            # our model classes. Therefore, we always operate over Java interfaces
            # instead of concrete classes, even if the class is a concrete one and
            # has no concrete descendants.

            return Stripped(our_type_prefix + java_naming.interface_name(our_type.name))

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        item_type = generate_type(
            type_annotation=type_annotation.items, our_type_qualifier=our_type_qualifier
        )

        return Stripped(f"List<{item_type}>")

    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        value = generate_type(
            type_annotation=type_annotation.value, our_type_qualifier=our_type_qualifier
        )
        return Stripped(f"Optional<{value}>")

    else:
        assert_never(type_annotation)

    raise AssertionError("Should not have gotten here")


INDENT = "  "
INDENT2 = INDENT * 2
INDENT3 = INDENT * 3
INDENT4 = INDENT * 4
INDENT5 = INDENT * 5
INDENT6 = INDENT * 6


INTERFACE_PKG = "model"
CLASS_PKG = "impl"
ENUM_PKG = "enums"


def interface_package_path(name: Stripped) -> Stripped:
    """Create the package path for an interface file."""
    return Stripped(f"{INTERFACE_PKG}/{name}.java")


def class_package_path(name: Stripped) -> Stripped:
    """Create the package path for an interface file."""
    return Stripped(f"{CLASS_PKG}/{name}.java")


def enum_package_path(name: Stripped) -> Stripped:
    """Create the package path for an interface file."""
    return Stripped(f"{ENUM_PKG}/{name}.java")


# noinspection RegExpSimplifiable
PACKAGE_IDENTIFIER_RE = re.compile(r"[a-z][a-z_0-9]*(\.[a-z][a-z_0-9]*)*")


class PackageIdentifier(str):
    """Capture a package identifier."""

    @require(lambda identifier: PACKAGE_IDENTIFIER_RE.fullmatch(identifier))
    def __new__(cls, identifier: str) -> "PackageIdentifier":
        return cast(PackageIdentifier, identifier)


WARNING = Stripped(
    """\
/*
 * This code has been automatically generated by aas-core-codegen.
 * Do NOT edit or append.
 */"""
)


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
