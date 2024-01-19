"""Generate Python code for JSON-ization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure, require

from aas_core_codegen import intermediate, naming, specific_implementations
from aas_core_codegen.common import (
    Error,
    Stripped,
    Identifier,
    assert_never,
    indent_but_first_line,
)
from aas_core_codegen.python import (
    common as python_common,
    naming as python_naming,
)
from aas_core_codegen.python.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


# region De-serialization


def _generate_bool_from_jsonable() -> Stripped:
    """Generate the function to decode a ``bool`` from a JSON-able."""
    return Stripped(
        f"""\
def _bool_from_jsonable(
{I}jsonable: Jsonable
) -> bool:
{I}\"\"\"
{I}Parse :paramref:`jsonable` as a boolean.

{I}:param jsonable: JSON-able structure to be parsed
{I}:return: parsed boolean
{I}:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, bool):
{II}raise DeserializationException(
{III}f"Expected a bool, but got: {{type(jsonable)}}"
{II})
{I}return jsonable"""
    )


def _generate_int_from_jsonable() -> Stripped:
    """Generate the function to decode an ``int`` from a JSON-able."""
    return Stripped(
        f"""\
def _int_from_jsonable(
{I}jsonable: Jsonable
) -> int:
{I}\"\"\"
{I}Parse :paramref:`jsonable` as an integer.

{I}:param jsonable: JSON-able structure to be parsed
{I}:return: parsed integer
{I}:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, int):
{II}raise DeserializationException(
{III}f"Expected an int, but got: {{type(jsonable)}}"
{II})
{I}return jsonable"""
    )


def _generate_float_from_jsonable() -> Stripped:
    """Generate the function to decode a ``float`` from a JSON-able."""
    return Stripped(
        f"""\
def _float_from_jsonable(
{I}jsonable: Jsonable
) -> float:
{I}\"\"\"
{I}Parse :paramref:`jsonable` as a floating-point number.

{I}:param jsonable: JSON-able structure to be parsed
{I}:return: parsed floating-point number
{I}:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, float):
{II}raise DeserializationException(
{III}f"Expected a float, but got: {{type(jsonable)}}"
{II})
{I}return jsonable"""
    )


def _generate_str_from_jsonable() -> Stripped:
    """Generate the function to decode a ``str`` from a JSON-able."""
    return Stripped(
        f"""\
def _str_from_jsonable(
{I}jsonable: Jsonable
) -> str:
{I}\"\"\"
{I}Parse :paramref:`jsonable` as a string.

{I}:param jsonable: JSON-able structure to be parsed
{I}:return: parsed string
{I}:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, str):
{II}raise DeserializationException(
{III}f"Expected a str, but got: {{type(jsonable)}}"
{II})
{I}return jsonable"""
    )


def _generate_bytes_from_jsonable() -> Stripped:
    """Generate the function to decode ``bytes`` from a JSON-able."""
    return Stripped(
        f"""\
def _bytes_from_jsonable(
{I}jsonable: Jsonable
) -> bytes:
{I}\"\"\"
{I}Decode :paramref:`jsonable` as base64 string to a ``bytearray``.

{I}:param jsonable: JSON-able structure to be decoded
{I}:return: decoded bytearray
{I}:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, str):
{II}raise DeserializationException(
{III}f"Expected a str, but got: {{type(jsonable)}}"
{II})

{I}return base64.b64decode(
{II}jsonable.encode('ascii')
{I})"""
    )


def _generate_enumeration_from_jsonable(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    """Generate the deserialization method for an enumeration."""
    enum_name = python_naming.enum_name(identifier=enumeration.name)

    function_name = python_naming.function_name(
        Identifier(f"{enumeration.name}_from_jsonable")
    )

    enum_from_str = python_naming.function_name(
        Identifier(f"{enumeration.name}_from_str")
    )

    return Stripped(
        f"""\
def {function_name}(
{I}jsonable: Jsonable
) -> aas_types.{enum_name}:
{I}\"\"\"
{I}Convert the JSON-able structure :paramref:`jsonable` to a literal of
{I}:py:class:`.types.{enum_name}`.

{I}:param jsonable: JSON-able structure to be parsed
{I}:return: parsed literal
{I}:raise: :py:class:`.DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, str):
{II}raise DeserializationException(
{III}"Expected a str, but got: {{type(jsonable)}}"
{II})

{I}literal = aas_stringification.{enum_from_str}(jsonable)
{I}if literal is None:
{II}raise DeserializationException(
{III}f"Not a valid string representation of "
{III}f"a literal of {enum_name}: {{jsonable}}"
{II})

{I}return literal"""
    )


def _generate_dispatch_map_for_abstract_class(
    cls: intermediate.AbstractClass,
) -> Stripped:
    """Generate a mapping model type 🠒 de-serialization function."""
    assert len(cls.concrete_descendants) > 0, (
        "Expected an abstract class to have concrete descendants. "
        "Otherwise we do not know how to de-serialize it."
    )

    mapping_name = python_naming.private_constant_name(
        Identifier(f"{cls.name}_from_jsonable_dispatch")
    )

    cls_name = python_naming.class_name(cls.name)

    mapping_writer = io.StringIO()
    mapping_writer.write(
        f"""\
{mapping_name}: Mapping[
{I}str,
{I}Callable[[Jsonable], aas_types.{cls_name}]
] = {{
"""
    )

    for descendant in cls.concrete_descendants:
        function_name_for_descendant = python_naming.function_name(
            Identifier(f"{descendant.name}_from_jsonable")
        )

        descendant_literal = python_common.string_literal(
            naming.json_model_type(descendant.name)
        )

        mapping_writer.write(
            f"""\
{I}{descendant_literal}: {function_name_for_descendant},
"""
        )

    mapping_writer.write("}")

    return Stripped(mapping_writer.getvalue())


@require(lambda cls: len(cls.concrete_descendants) > 0)
def _generate_dispatch_map_for_concrete_class(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """
    Generate a mapping model type 🠒 de-serialization function.

    The ``jsonable`` can not be parsed straight-away as we don't know which class
    (the actual one or one of the descendants) needs to be parsed.
    """
    mapping_name = python_naming.private_constant_name(
        Identifier(f"{cls.name}_from_jsonable_dispatch")
    )

    cls_name = python_naming.class_name(cls.name)

    mapping_writer = io.StringIO()
    mapping_writer.write(
        f"""\
{mapping_name}: Mapping[
{I}str,
{I}Callable[[Jsonable], aas_types.{cls_name}]
] = {{
"""
    )

    function_name_for_cls = python_naming.function_name(
        Identifier(f"_{cls.name}_from_jsonable_without_dispatch")
    )

    cls_literal = python_common.string_literal(naming.json_model_type(cls.name))

    mapping_writer.write(
        f"""\
{I}{cls_literal}: {function_name_for_cls},
"""
    )

    for descendant in cls.concrete_descendants:
        function_name_for_descendant = python_naming.function_name(
            Identifier(f"{descendant.name}_from_jsonable")
        )

        descendant_literal = python_common.string_literal(
            naming.json_model_type(descendant.name)
        )

        mapping_writer.write(
            f"""\
{I}{descendant_literal}: {function_name_for_descendant},
"""
        )

    mapping_writer.write("}")

    return Stripped(mapping_writer.getvalue())


# fmt: off
@require(
    lambda cls: len(cls.concrete_descendants) > 0,
    "Dispatch is only possible if there are one or more concrete descendants"
)
# fmt: on
def _generate_dispatch_from_jsonable(cls: intermediate.ClassUnion) -> Stripped:
    """Generate the de-serialization dispatch for an abstract class."""
    function_name = python_naming.function_name(Identifier(f"{cls.name}_from_jsonable"))

    cls_name = python_naming.class_name(cls.name)

    mapping_name = python_naming.private_constant_name(
        Identifier(f"{cls.name}_from_jsonable_dispatch")
    )

    return Stripped(
        f"""\
def {function_name}(
{II}jsonable: Jsonable
) -> aas_types.{cls_name}:
{I}\"\"\"
{I}Parse an instance of :py:class:`.types.{cls_name}` from the JSON-able
{I}structure :paramref:`jsonable`.

{I}:param jsonable: structure to be parsed
{I}:return: Concrete instance of :py:class:`.types.{cls_name}`
{I}:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`
{I}\"\"\"
{I}if not isinstance(jsonable, collections.abc.Mapping):
{II}raise DeserializationException(
{III}f"Expected a mapping, but got: {{type(jsonable)}}"
{II})

{I}model_type = jsonable.get("modelType", None)
{I}if model_type is None:
{II}raise DeserializationException(
{III}"Expected the property modelType, but found none"
{II})

{I}if not isinstance(model_type, str):
{II}raise DeserializationException(
{III}"Expected the property modelType to be a str, but got: {{type(model_type)}}"
{II})

{I}dispatch = {mapping_name}.get(model_type, None)
{I}if dispatch is None:
{II}raise DeserializationException(
{III}f"Unexpected model type for {cls_name}: {{model_type}}"
{II})

{I}return dispatch(jsonable)"""
    )


_PARSE_FUNCTION_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: "_bool_from_jsonable",
    intermediate.PrimitiveType.INT: "_int_from_jsonable",
    intermediate.PrimitiveType.FLOAT: "_float_from_jsonable",
    intermediate.PrimitiveType.STR: "_str_from_jsonable",
    intermediate.PrimitiveType.BYTEARRAY: "_bytes_from_jsonable",
}
assert all(
    literal in _PARSE_FUNCTION_BY_PRIMITIVE_TYPE
    for literal in intermediate.PrimitiveType
)


def _parse_function_for_atomic_value(
    type_annotation: intermediate.AtomicTypeAnnotation,
) -> Stripped:
    """Determine the parse function for deserializing an atomic non-optional value."""
    function_name: str

    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        function_name = _PARSE_FUNCTION_BY_PRIMITIVE_TYPE[type_annotation.a_type]

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        our_type = type_annotation.our_type

        if isinstance(
            our_type,
            (
                intermediate.Enumeration,
                intermediate.AbstractClass,
                intermediate.ConcreteClass,
            ),
        ):
            function_name = python_naming.function_name(
                Identifier(f"{our_type.name}_from_jsonable")
            )

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            function_name = _PARSE_FUNCTION_BY_PRIMITIVE_TYPE[our_type.constrainee]

        else:
            assert_never(our_type)
    else:
        assert_never(type_annotation)

    return Stripped(function_name)


def _generate_setter(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate a class which allows us to dispatch de-serialization for properties."""
    methods = []  # type: List[Stripped]

    init_writer = io.StringIO()
    for i, prop in enumerate(cls.properties):
        prop_name = python_naming.property_name(prop.name)
        prop_type = python_common.generate_type(
            prop.type_annotation, types_module=Identifier("aas_types")
        )

        # NOTE (mristin, 2022-07-22):
        # We make all the properties optional since we switch over the properties
        # during the de-serialization.
        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            prop_type = Stripped(f"Optional[{prop_type}]")

        if i > 0:
            init_writer.write("\n")
        init_writer.write(f"self.{prop_name}: {prop_type} = None")

    methods.append(
        Stripped(
            f"""\
def __init__(self) -> None:
{I}\"\"\"Initialize with all the properties unset.\"\"\"
{I}{indent_but_first_line(init_writer.getvalue(), I)}"""
        )
    )

    methods.append(
        Stripped(
            f"""\
def ignore(self, jsonable: Jsonable) -> None:
{I}\"\"\"Ignore :paramref:`jsonable` and do not set anything.\"\"\"
{I}pass"""
        )
    )

    for i, prop in enumerate(cls.properties):
        prop_name = python_naming.property_name(prop.name)

        method_name = python_naming.method_name(
            Identifier(f"set_{prop.name}_from_jsonable")
        )

        type_anno = intermediate.beneath_optional(prop.type_annotation)
        if isinstance(
            type_anno,
            (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
        ):
            function_name = _parse_function_for_atomic_value(type_anno)
            body = Stripped(
                f"""\
self.{prop_name} = {function_name}(
{I}jsonable
)"""
            )

        elif isinstance(type_anno, intermediate.ListTypeAnnotation):
            assert not isinstance(
                type_anno.items,
                (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
            ), (
                "We chose to implement only a very limited pattern matching; "
                "see intermediate._translate_._verify_only_simple_type_patterns"
            )

            items_type = python_common.generate_type(
                type_anno.items, types_module=Identifier("aas_types")
            )
            parse_function = _parse_function_for_atomic_value(type_anno.items)

            body = Stripped(
                f"""\
if not isinstance(jsonable, collections.abc.Iterable):
{I}raise DeserializationException(
{II}f"Expected an iterable, but got: {{type(jsonable)}}"
{I})

items: List[
{I}{items_type}
] = []
for i, jsonable_item in enumerate(jsonable):
{I}try:
{II}item = {parse_function}(
{III}jsonable_item
{II})
{I}except DeserializationException as exception:
{II}exception.path._prepend(
{III}IndexSegment(
{IIII}jsonable,
{IIII}i
{III})
{II})
{II}raise

{I}items.append(item)

self.{prop_name} = items"""
            )

        else:
            assert_never(type_anno)
            raise AssertionError("Unexpected execution path")

        method_writer = io.StringIO()
        method_writer.write(
            f"""\
def {method_name}(
{II}self,
{II}jsonable: Jsonable
) -> None:
{I}\"\"\"
{I}Parse :paramref:`jsonable` as the value of :py:attr:`~{prop_name}`.

{I}:param jsonable: input to be parsed
{I}\"\"\"
{I}{indent_but_first_line(body, I)}"""
        )

        methods.append(Stripped(method_writer.getvalue()))

    cls_name = python_naming.private_class_name(Identifier(f"Setter_for_{cls.name}"))

    writer = io.StringIO()
    writer.write(
        f"""\
class {cls_name}:
{I}\"\"\"Provide de-serialization-setters for properties.\"\"\"

"""
    )

    assert len(methods) > 0, (
        "Expected at least one method, otherwise the newlines are invalid and "
        "have to be fixed"
    )

    for i, method in enumerate(methods):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(method, I))

    return Stripped(writer.getvalue())


def _generate_setter_map(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate a mapping ``JSON property name`` -> deserialization on a setter."""
    # fmt: off
    assert (
            sorted(
                (arg.name, str(arg.type_annotation))
                for arg in cls.constructor.arguments
            ) == sorted(
                (prop.name, str(prop.type_annotation))
                for prop in cls.properties
            )
    ), (
        "(mristin, 2022-10-03) We assume that the properties and constructor arguments "
        "are identical at this point. If this is not the case, we have to re-write the "
        "logic substantially! Please contact the developers if you see this."
    )
    # fmt: on

    identifiers_expressions = []  # type: List[Tuple[Identifier, Stripped]]

    setter_cls_name = python_naming.private_class_name(
        Identifier(f"Setter_for_{cls.name}")
    )

    for prop in cls.properties:
        json_identifier = naming.json_property(prop.name)
        method_name = python_naming.method_name(
            Identifier(f"set_{prop.name}_from_jsonable")
        )

        identifiers_expressions.append(
            (json_identifier, Stripped(f"{setter_cls_name}.{method_name}"))
        )

    map_name = python_naming.private_constant_name(
        Identifier(f"setter_map_for_{cls.name}")
    )

    writer = io.StringIO()
    writer.write(
        f"""\
{map_name}: Mapping[
{I}str,
{I}Callable[
{II}[{setter_cls_name}, Jsonable],
{II}None
{I}]
] = {{
"""
    )
    for identifier, expression in identifiers_expressions:
        writer.write(
            f"""\
{I}{python_common.string_literal(identifier)}:
{II}{indent_but_first_line(expression, II)},
"""
        )

    writer.write(
        f"""\
{I}'modelType':
{II}{setter_cls_name}.ignore
"""
    )

    writer.write("}")
    return Stripped(writer.getvalue())


def _generate_concrete_class_from_jsonable(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """
    Generate the deserialization function for a concrete class.

    This function performs no dispatch. If it de-serializes a concrete class with
    concrete descendants, we have to provide a different name. Otherwise, it would
    shadow the name for the dispatch function.
    """
    # fmt: off
    assert (
            sorted(
                (arg.name, str(arg.type_annotation))
                for arg in cls.constructor.arguments
            ) == sorted(
                (prop.name, str(prop.type_annotation))
                for prop in cls.properties
            )
    ), (
        "(mristin, 2022-10-03) We assume that the properties and constructor arguments "
        "are identical at this point. If this is not the case, we have to re-write the "
        "logic substantially! Please contact the developers if you see this."
    )
    # fmt: on

    setter_cls_name = python_naming.private_class_name(
        Identifier(f"Setter_for_{cls.name}")
    )

    blocks = [
        Stripped(
            f"""\
if not isinstance(jsonable, collections.abc.Mapping):
{I}raise DeserializationException(
{II}f"Expected a mapping, but got: {{type(jsonable)}}"
{I})"""
        ),
        Stripped(f"setter = {setter_cls_name}()"),
    ]  # type: List[Stripped]

    # region Switch on property name

    map_name = python_naming.private_constant_name(
        Identifier(f"setter_map_for_{cls.name}")
    )

    blocks.append(
        Stripped(
            f"""\
for key, jsonable_value in jsonable.items():
{I}setter_method = (
{II}{map_name}.get(key)
{I})
{I}if setter_method is None:
{II}raise DeserializationException(
{III}f"Unexpected property: {{key}}"
{II})

{I}try:
{II}setter_method(setter, jsonable_value)
{I}except DeserializationException as exception:
{II}exception.path._prepend(
{III}PropertySegment(
{IIII}jsonable_value,
{IIII}key
{III})
{II})
{II}raise exception"""
        )
    )

    # region Check required properties

    required_checks = []  # type: List[Stripped]
    for i, prop in enumerate(cls.properties):
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        prop_name = python_naming.property_name(prop.name)

        cause_literal = python_common.string_literal(
            f"The required property {naming.json_property(prop.name)!r} is missing"
        )
        required_checks.append(
            Stripped(
                f"""\
if setter.{prop_name} is None:
{I}raise DeserializationException(
{II}{cause_literal}
{I})"""
            )
        )

    if len(required_checks) > 0:
        blocks.append(Stripped("\n\n".join(required_checks)))

    # endregion

    # region Pass in arguments to the constructor

    cls_name = python_naming.class_name(cls.name)

    if len(cls.constructor.arguments) == 0:
        blocks.append(Stripped(f"return aas_types.{cls_name}()"))
    else:
        init_writer = io.StringIO()
        init_writer.write(f"return aas_types.{cls_name}(\n")

        for i, arg in enumerate(cls.constructor.arguments):
            prop = cls.properties_by_name[arg.name]

            prop_name = python_naming.property_name(prop.name)

            init_writer.write(f"{I}setter.{prop_name}")

            if i < len(cls.constructor.arguments) - 1:
                init_writer.write(",\n")
            else:
                init_writer.write("\n")

        init_writer.write(")")

        blocks.append(Stripped(init_writer.getvalue()))
    # endregion

    writer = io.StringIO()

    if len(cls._concrete_descendants) == 0:
        function_name = python_naming.function_name(
            Identifier(f"{cls.name}_from_jsonable")
        )
    else:
        function_name = python_naming.function_name(
            Identifier(f"_{cls.name}_from_jsonable_without_dispatch")
        )

    docstring_blocks = [
        Stripped(
            f"""\
Parse an instance of :py:class:`.types.{cls_name}` from the JSON-able
structure :paramref:`jsonable`."""
        )
    ]  # type: List[Stripped]

    if len(cls.concrete_descendants) > 0:
        function_name_with_dispatch = python_naming.function_name(
            Identifier(f"{cls.name}_from_jsonable")
        )

        docstring_blocks.append(
            Stripped(
                f"""\
This function performs no dispatch! It is used to parse the properties
as-are, and already assumes the exact model type. Usually, this function
is called from within a dispatching function, and you never call it
directly. If you want to de-serialize an instance of
:py:class:`.types.{cls_name}`, call
:py:func:`{function_name_with_dispatch}`."""
            )
        )

    docstring_blocks.append(
        Stripped(
            f"""\
:param jsonable: structure to be parsed
:return: Parsed instance of :py:class:`.types.{cls_name}`
:raise: :py:class:`DeserializationException` if unexpected :paramref:`jsonable`"""
        )
    )

    docstring = "\n\n".join(docstring_blocks)

    writer.write(
        f"""\
def {function_name}(
{II}jsonable: Jsonable
) -> aas_types.{cls_name}:
{I}\"\"\"
{I}{indent_but_first_line(docstring, I)}
{I}\"\"\"
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    return Stripped(writer.getvalue())


# endregion

# region Serialization


def _generate_bytes_to_base64_str() -> Stripped:
    """Generate the function to encode bytes as base64-encoded string."""
    return Stripped(
        f"""\
def _bytes_to_base64_str(
{I}value: bytes
) -> str:
{I}\"\"\"
{I}Encode :paramref:`value` as a base64 string.

{I}:param value: to be encoded
{I}:return: encoded :paramref:`value` in base64
{I}\"\"\"
{I}# We need to decode as ascii as ``base64.b64encode`` returns bytes,
{I}# not a string!
{I}return base64.b64encode(value).decode('ascii')"""
    )


def _generate_transform_atomic_value(
    access_expression: str, type_anno: intermediate.AtomicTypeAnnotation
) -> Stripped:
    """
    Generate the snippet to transform the ``access_expression``.

    The ``access_expression`` should either be a name or a member access.
    """
    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation) or (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive)
    ):
        a_type = intermediate.try_primitive_type(type_anno)
        assert a_type is not None

        if (
            a_type is intermediate.PrimitiveType.BOOL
            or a_type is intermediate.PrimitiveType.INT
            or a_type is intermediate.PrimitiveType.FLOAT
            or a_type is intermediate.PrimitiveType.STR
        ):
            return Stripped(f"{access_expression}")

        elif a_type is intermediate.PrimitiveType.BYTEARRAY:
            return Stripped(f"_bytes_to_base64_str({access_expression})")

        else:
            assert_never(a_type)

    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        if isinstance(type_anno.our_type, intermediate.Enumeration):
            return Stripped(f"{access_expression}.value")

        elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
            raise AssertionError("This case should have been handled before.")

        elif isinstance(
            type_anno.our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            return Stripped(f"self.transform({access_expression})")

        else:
            assert_never(type_anno.our_type)

    else:
        assert_never(type_anno.our_type)


def _generate_transform(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the ``transform_X`` method to serialize an instance into a JSON-able."""
    blocks = [
        Stripped("jsonable: MutableMapping[str, MutableJsonable] = dict()")
    ]  # type: List[Stripped]

    for prop in cls.properties:
        key_literal = python_common.string_literal(naming.json_property(prop.name))
        prop_name = python_naming.property_name(prop.name)

        type_anno = intermediate.beneath_optional(prop.type_annotation)

        block: Stripped

        if isinstance(
            type_anno,
            (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
        ):
            transformation_expression = _generate_transform_atomic_value(
                access_expression=Stripped(f"that.{prop_name}"), type_anno=type_anno
            )

            block = Stripped(f"jsonable[{key_literal}] = {transformation_expression}")

            # Rudimentary formatting heuristics
            if len(block) > 70:
                block = Stripped(
                    f"""\
jsonable[{key_literal}] = (
{I}{transformation_expression}
)"""
                )

        elif isinstance(type_anno, intermediate.ListTypeAnnotation):
            assert isinstance(
                type_anno.items,
                (intermediate.PrimitiveType, intermediate.OurTypeAnnotation),
            ), (
                "We expect only lists of primitive and our types. Lists of optionals "
                "and nested lists are not handled yet. Please contact the developers."
            )

            transformation_expression = _generate_transform_atomic_value(
                access_expression=Stripped("item"), type_anno=type_anno.items
            )

            block = Stripped(
                f"""\
jsonable[{key_literal}] = [
{I}{transformation_expression}
{I}for item in that.{prop_name}
]"""
            )

        else:
            assert_never(type_anno)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            block = Stripped(
                f"""\
if that.{prop_name} is not None:
{I}{indent_but_first_line(block, I)}"""
            )

        blocks.append(block)

    if cls.serialization.with_model_type:
        model_type_literal = python_common.string_literal(
            naming.json_model_type(cls.name)
        )
        blocks.append(Stripped(f"""jsonable["modelType"] = {model_type_literal}"""))

    blocks.append(Stripped("return jsonable"))

    method_name = python_naming.method_name(Identifier(f"transform_{cls.name}"))

    cls_name = python_naming.class_name(cls.name)

    writer = io.StringIO()

    no_self_use = all(
        (
            some_type_anno := intermediate.beneath_optional(prop.type_annotation),
            intermediate.try_primitive_type(some_type_anno) is not None
            or (
                isinstance(some_type_anno, intermediate.OurTypeAnnotation)
                and isinstance(some_type_anno.our_type, intermediate.Enumeration)
            ),
        )[1]
        for prop in cls.properties
    )

    if no_self_use:
        writer.write("# noinspection PyMethodMayBeStatic\n")

    writer.write(
        f"""\
def {method_name}(
{I}self,
{I}that: aas_types.{cls_name}
) -> MutableJsonable:
{I}\"\"\"Serialize :paramref:`that` to a JSON-able representation.\"\"\""""
    )

    if len(blocks) > 0:
        writer.write("\n")

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    return Stripped(writer.getvalue())


def _generate_transformer(symbol_table: intermediate.SymbolTable) -> Stripped:
    methods = []  # type: List[Stripped]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.ConcreteClass):
            methods.append(_generate_transform(our_type))

    writer = io.StringIO()
    writer.write(
        f"""\
class _Serializer(
{II}aas_types.AbstractTransformer[MutableJsonable]
):
{I}\"\"\"Transform the instance to its JSON-able representation.\"\"\""""
    )

    for method in methods:
        writer.write("\n\n")
        writer.write(textwrap.indent(method, I))

    return Stripped(writer.getvalue())


# endregion

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
    aas_module: python_common.QualifiedModuleName,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Python code for the general serialization.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped(
            """\
\"\"\"
Provide de/serialization of AAS classes to/from JSON.

We can not use one-pass deserialization for JSON since the object
properties do not have fixed order, and hence we can not read
``modelType`` property ahead of the remaining properties.
\"\"\""""
        ),
        python_common.WARNING,
        Stripped(
            f"""\
import base64
import collections.abc
import sys
from typing import (
{I}Any,
{I}Callable,
{I}Iterable,
{I}List,
{I}Mapping,
{I}MutableMapping,
{I}Optional,
{I}Sequence,
{I}Union,
)

if sys.version_info >= (3, 8):
{I}from typing import Final
else:
{I}from typing_extensions import Final

import {aas_module}.common as aas_common
import {aas_module}.stringification as aas_stringification
import {aas_module}.types as aas_types"""
        ),
        Stripped(
            f"""\
class PropertySegment:
{I}\"\"\"Represent a property on a path to the erroneous value.\"\"\"

{I}#: Instance that contains the property
{I}instance: Final[Mapping[str, Any]]

{I}#: Name of the property
{I}name: Final[str]

{I}def __init__(
{III}self,
{III}instance: Mapping[str, Any],
{III}name: str
{I}) -> None:
{II}\"\"\"Initialize with the given values.\"\"\"
{II}self.instance = instance
{II}self.name = name"""
        ),
        Stripped(
            f"""\
class IndexSegment:
{I}\"\"\"Represent an index access on a path to the erroneous value.\"\"\"

{I}#: Container that contains the item
{I}container: Final[Iterable[Any]]

{I}#: Index of the item
{I}index: Final[int]

{I}def __init__(
{III}self,
{III}container: Iterable[Any],
{III}index: int
{I}) -> None:
{II}\"\"\"Initialize with the given values.\"\"\"
{II}self.container = container
{II}self.index = index"""
        ),
        Stripped(
            """\
Segment = Union[PropertySegment, IndexSegment]"""
        ),
        Stripped(
            f"""\
class Path:
{I}\"\"\"Represent the relative path to the erroneous value.\"\"\"

{I}def __init__(self) -> None:
{II}\"\"\"Initialize as an empty path.\"\"\"
{II}self._segments = []  # type: List[Segment]

{I}@property
{I}def segments(self) -> Sequence[Segment]:
{II}\"\"\"Get the segments of the path.\"\"\"
{II}return self._segments

{I}def _prepend(self, segment: Segment) -> None:
{II}\"\"\"Insert the :paramref:`segment` in front of other segments.\"\"\"
{II}self._segments.insert(0, segment)

{I}def __str__(self) -> str:
{II}if len(self._segments) == 0:
{III}return ""

{II}parts = []  # type: List[str]

{II}iterator = iter(self._segments)
{II}first = next(iterator)
{II}if isinstance(first, PropertySegment):
{III}parts.append(f"{{first.name}}")
{II}elif isinstance(first, IndexSegment):
{III}parts.append(f"[{{first.index}}]")
{II}else:
{III}aas_common.assert_never(first)

{II}for segment in iterator:
{III}if isinstance(segment, PropertySegment):
{IIII}parts.append(f".{{segment.name}}")
{III}elif isinstance(segment, IndexSegment):
{IIII}parts.append(f"[{{segment.index}}]")
{III}else:
{IIII}aas_common.assert_never(segment)

{II}return "".join(parts)"""
        ),
        Stripped(
            f"""\
class DeserializationException(Exception):
{I}\"\"\"Signal that the JSON de-serialization could not be performed.\"\"\"

{I}#: Human-readable explanation of the exception's cause
{I}cause: Final[str]

{I}#: Relative path to the erroneous value
{I}path: Final[Path]

{I}def __init__(
{III}self,
{III}cause: str
{I}) -> None:
{II}\"\"\"Initialize with the given :paramref:`cause` and an empty path.\"\"\"
{II}self.cause = cause
{II}self.path = Path()"""
        ),
        Stripped(
            f"""\
# NOTE (mristin, 2022-10-03):
# Recursive definitions are not yet available in mypy
# (see https://github.com/python/mypy/issues/731). We have to use ``Any``
# here, instead of recursive type annotations.
Jsonable = Union[
{I}bool,
{I}int,
{I}float,
{I}str,
{I}Sequence[Any],
{I}Mapping[str, Any]
]"""
        ),
        Stripped(
            f"""\
MutableJsonable = Union[
{I}bool,
{I}int,
{I}float,
{I}str,
{I}List[Any],
{I}MutableMapping[str, Any]
]"""
        ),
        Stripped("# region De-serialization"),
        _generate_bool_from_jsonable(),
        _generate_int_from_jsonable(),
        _generate_float_from_jsonable(),
        _generate_str_from_jsonable(),
        _generate_bytes_from_jsonable(),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            blocks.append(_generate_enumeration_from_jsonable(enumeration=our_type))
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            pass
        elif isinstance(our_type, intermediate.AbstractClass):
            blocks.append(_generate_dispatch_from_jsonable(cls=our_type))
        elif isinstance(our_type, intermediate.ConcreteClass):
            if len(our_type.concrete_descendants) > 0:
                blocks.append(_generate_dispatch_from_jsonable(cls=our_type))

            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"Jsonization/{our_type.name}_from_jsonable.py"
                )

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The jsonization snippet is missing "
                            f"for the implementation-specific "
                            f"class {our_type.name}: {implementation_key}",
                        )
                    )
                    continue
            else:
                blocks.append(_generate_setter(cls=our_type))

                blocks.append(_generate_concrete_class_from_jsonable(cls=our_type))
        else:
            assert_never(our_type)

    # NOTE (mristin, 2022-10-03):
    # We add all the dispatch mappings at the end as the functions might not have been
    # defined yet otherwise.
    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.AbstractClass):
            blocks.append(_generate_dispatch_map_for_abstract_class(cls=our_type))
        elif isinstance(our_type, intermediate.ConcreteClass):
            if len(our_type.concrete_descendants) > 0:
                blocks.append(_generate_dispatch_map_for_concrete_class(cls=our_type))

            if not our_type.is_implementation_specific:
                blocks.append(_generate_setter_map(cls=our_type))

        else:
            pass

    blocks.append(Stripped("# endregion"))

    blocks.append(Stripped("# region Serialization"))

    blocks.append(_generate_bytes_to_base64_str())

    blocks.append(_generate_transformer(symbol_table=symbol_table))

    blocks.append(Stripped("_SERIALIZER = _Serializer()"))

    blocks.append(
        Stripped(
            f"""\
def to_jsonable(that: aas_types.Class) -> MutableJsonable:
{I}\"\"\"
{I}Convert :paramref:`that` to a JSON-able structure.

{I}:param that:
{II}AAS data to be recursively converted to a JSON-able structure
{I}:return:
{II}JSON-able structure which can be further encoded with, *e.g.*, :py:mod:`json`
{I}\"\"\"
{I}return _SERIALIZER.transform(that)"""
        )
    )

    blocks.append(Stripped("# endregion"))

    if len(errors) > 0:
        return None, errors

    blocks.append(python_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None
