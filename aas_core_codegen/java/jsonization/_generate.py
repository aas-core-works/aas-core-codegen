"""Generate Java code for JSON-ization based on the intermediate representation."""

import io
import textwrap
from typing import Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate, naming, specific_implementations
from aas_core_codegen.common import (
    Error,
    Stripped,
    Identifier,
    assert_never,
    indent_but_first_line,
)
from aas_core_codegen.java import (
    common as java_common,
    naming as java_naming,
)
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


def _generate_from_method_for_enumeration(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    """Generate the deserialization method for an enumeration."""
    name = java_naming.enum_name(identifier=enumeration.name)
    var_name = java_naming.variable_name(identifier=enumeration.name)
    method_name = java_naming.method_name(Identifier(f"{enumeration.name}_from_string"))

    message_literal = java_common.string_literal(
        f"Not a valid JSON representation of {name}"
    )

    return Stripped(
        f"""\
/**
 * Deserialize the enumeration {name} from the {{@code node}}.
 *
 * @param node JSON node to be parsed
 */
private static Result<{name}> try{name}From(JsonNode node) {{
{I}final Result<String> textResult = tryStringFrom(node);
{I}if (textResult.isError()) {{
{II}return textResult.castTo({name}.class);
{I}}}
{I}final Optional<{name}> {var_name} = Stringification.{method_name}(textResult.getResult());
{I}if (!{var_name}.isPresent()) {{
{II}final Reporting.Error error = new Reporting.Error({message_literal});
{II}return Result.failure(error);
{I}}}
{I}return Result.success({var_name}.get());
}}"""
    )


def _generate_from_method_for_interface(
    interface: intermediate.Interface,
) -> Stripped:
    """Generate the deserialization method for an interface."""
    name = java_naming.interface_name(interface.name)
    interface_name = java_naming.interface_name(interface.name)

    blocks = [
        Stripped(
            f"""\
if (node == null || !node.isObject()) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected a JsonObject, but got " + (node == null ? "null" : node.getNodeType()));
{I}return Result.failure(error);
}}

final JsonNode modelTypeNode = node.get("modelType");
if (modelTypeNode == null) {{
{I}final Reporting.Error error = new Reporting.Error(
{III}"Expected a model type, but none is present");
{I}return Result.failure(error);
}}
final Result<String> modelTypeResult = tryStringFrom(modelTypeNode);
if (modelTypeResult.isError()) {{
{I}return modelTypeResult.castTo({interface_name}.class);
}}"""
        ),
    ]  # type: List[Stripped]

    # region Write the switch block

    switch_writer = io.StringIO()
    switch_writer.write(
        """\
switch (modelTypeResult.getResult())
{
"""
    )

    for implementer in interface.implementers:
        model_type = naming.json_model_type(implementer.name)
        implementer_name = java_naming.class_name(implementer.name)
        switch_writer.write(
            f"""\
{I}case {java_common.string_literal(model_type)}: {{
{II}return try{implementer_name}From(node);
}}"""
        )

    switch_writer.write(
        f"""\
{I}default: {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Unexpected model type for {name}: " + modelTypeResult.getResult());
{II}return Result.failure(error);
{I}}}
}}"""
    )
    blocks.append(Stripped(switch_writer.getvalue()))

    # endregion

    writer = io.StringIO()

    writer.write(
        f"""\
/**
 * Deserialize an instance of {name} by dispatching
 * based on {{@code modelType}} property of the {{@code node}}.
 *
 * @param node JSON node to be parsed
 */
public static Result<? extends {name}> try{name}From(JsonNode node) {{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue())


_PARSE_METHOD_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: "tryBooleanFrom",
    intermediate.PrimitiveType.INT: "tryLongFrom",
    intermediate.PrimitiveType.FLOAT: "tryDoubleFrom",
    intermediate.PrimitiveType.STR: "tryStringFrom",
    intermediate.PrimitiveType.BYTEARRAY: "tryBytesFrom",
}
assert all(
    literal in _PARSE_METHOD_BY_PRIMITIVE_TYPE for literal in intermediate.PrimitiveType
)


def _parse_method_for_atomic_value(
    type_annotation: intermediate.AtomicTypeAnnotation,
) -> Stripped:
    """Determine the parse method for deserializing an atomic non-optional value."""
    parse_method = None  # type: Optional[str]

    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        parse_method = _PARSE_METHOD_BY_PRIMITIVE_TYPE[type_annotation.a_type]

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        our_type = type_annotation.our_type
        if isinstance(our_type, intermediate.Enumeration):
            enum_name = java_naming.enum_name(our_type.name)
            parse_method = f"try{enum_name}From"

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            parse_method = _PARSE_METHOD_BY_PRIMITIVE_TYPE[our_type.constrainee]

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if our_type.interface is not None:
                interface_name = java_naming.interface_name(our_type.interface.name)
                parse_method = f"try{interface_name}From"
            else:
                cls_name = java_naming.class_name(our_type.name)
                parse_method = f"try{cls_name}From"

        else:
            assert_never(our_type)
    else:
        assert_never(type_annotation)

    return Stripped(parse_method)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_deserialize_constructor_argument(
    arg: intermediate.Argument,
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the code snippet for de-serializing the constructor argument ``arg``."""
    type_anno = intermediate.beneath_optional(arg.type_annotation)

    # Prefix the variables to avoid naming conflicts
    target_var = java_naming.variable_name(Identifier(f"the_{arg.name}"))

    json_name = naming.json_property(arg.name)
    assert not java_common.needs_escaping(json_name)

    json_literal = java_common.string_literal(json_name)

    parse_block = None  # type: Optional[Stripped]
    if isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        parse_method = _parse_method_for_atomic_value(type_anno)

        value_type = java_common.generate_type(type_anno)

        cls_name = java_naming.class_name(cls.name)

        parse_block = Stripped(
            f"""\
final Result<? extends {value_type}> {target_var}Result = {parse_method}(currentNode.getValue());
if ({target_var}Result.isError()) {{
{I}{target_var}Result.getError()
{II}.prependSegment(new Reporting.NameSegment("{json_name}"));
{I}return {target_var}Result.castTo({cls_name}.class);
}}
{target_var} = {target_var}Result.getResult();"""
        )

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_anno.items,
            (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
        ), (
            "We chose to implement only a very limited pattern matching; "
            "see intermediate._translate_._verify_only_simple_type_patterns"
        )

        item_type = java_common.generate_type(type_anno.items)

        array_var = java_naming.variable_name(Identifier(f"array_{arg.name}"))
        index_var = java_naming.variable_name(Identifier(f"index_{arg.name}"))

        cls_name = java_naming.class_name(cls.name)

        parse_method = _parse_method_for_atomic_value(type_anno.items)

        parse_block = Stripped(
            f"""\
final JsonNode {array_var} = currentNode.getValue();
if (!{array_var}.isArray()) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected a JsonArray, but got " + {array_var}.getNodeType());
{I}error.prependSegment(
{II}new Reporting.NameSegment(
{III}{json_literal}));
{I}return Result.failure(error);
}}
{target_var} = new ArrayList<>(
{I}{array_var}.size());
int {index_var} = 0;
for (JsonNode item : {array_var}) {{
{I}if (item == null) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected a non-null item, but got a null");
{II}error.prependSegment(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}error.prependSegment(
{III}new Reporting.NameSegment(
{IIII}{json_literal}));
{II}return Result.failure(error);
{I}}}
{I}final Result<? extends {item_type}> parsedItemResult =
{II}{parse_method}(item);
{I}if (parsedItemResult.isError()) {{
{II}parsedItemResult
{III}.getError()
{III}.prependSegment(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}parsedItemResult
{III}.getError()
{III}.prependSegment(
{III}new Reporting.NameSegment(
{IIII}{json_literal}));
{II}return parsedItemResult.castTo({cls_name}.class);
{I}}}
{I}{target_var}.add(
{II}parsedItemResult.getResult());
{I}{index_var}++;
}}"""
        )
    else:
        assert_never(arg.type_annotation)

    return parse_block, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_from_method_for_class(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the deserialization method for a concrete class."""
    errors = []  # type: List[Error]

    name = java_naming.class_name(cls.name)

    blocks = [
        Stripped(
            f"""\
if (node == null || !node.isObject()) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected a JsonObject, but got " + (node == null ? "null" : node.getNodeType()));
{I}return Result.failure(error);
}}"""
        ),
    ]  # type: List[Stripped]

    # region Initialize argument variables to null

    args_init_writer = io.StringIO()
    for i, arg in enumerate(cls.constructor.arguments):
        arg_var = java_naming.variable_name(Identifier(f"the_{arg.name}"))
        type_anno = intermediate.beneath_optional(arg.type_annotation)
        arg_type = java_common.generate_type(type_anno)

        if i > 0:
            args_init_writer.write("\n")
        args_init_writer.write(f"{arg_type} {arg_var} = null;")

    blocks.append(Stripped(args_init_writer.getvalue()))

    # endregion

    # region Switch on property name

    cases = []  # type: List[Stripped]
    for arg in cls.constructor.arguments:
        case_body, error = _generate_deserialize_constructor_argument(arg=arg, cls=cls)
        if error is not None:
            errors.append(error)
        else:
            assert case_body is not None
            json_name = naming.json_property(arg.name)

            # NOTE (empwilli, 2024-01-18):
            # We put ``if (keyValue.Value != null)`` here instead of the outer loop
            # since we want to detect the unexpected additional properties even
            # though their value can be set to null.

            cases.append(
                Stripped(
                    f"""\
case {java_common.string_literal(json_name)}: {{
{I}if (currentNode.getValue() == null) {{
{II}continue;
{I}}}

{I}{indent_but_first_line(case_body, I)}
{I}break;
}}"""
                )
            )

    if len(errors) > 0:
        return None, errors

    if cls.serialization.with_model_type:
        cases.append(
            Stripped(
                """\
case "modelType": {
    continue;
}"""
            )
        )

    cases.append(
        Stripped(
            f"""\
default: {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Unexpected property: " + currentNode.getKey());
{I}return Result.failure(error);
}}"""
        )
    )

    foreach_writer = io.StringIO()
    foreach_writer.write(
        f"""\
for (Iterator<Map.Entry<String, JsonNode>> iterator = node.fields(); iterator.hasNext(); ) {{
{I}Map.Entry<String, JsonNode> currentNode = iterator.next();

{I}switch (currentNode.getKey()) {{"""
    )

    for case_block in cases:
        foreach_writer.write("\n")
        foreach_writer.write(textwrap.indent(case_block, II))

    foreach_writer.write(f"\n{I}}}\n}}")

    blocks.append(Stripped(foreach_writer.getvalue()))

    # endregion

    # region Check required

    required_check_writer = io.StringIO()
    for i, arg in enumerate(cls.constructor.arguments):
        if isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        arg_var = java_naming.variable_name(Identifier(f"the_{arg.name}"))
        json_name = naming.json_property(arg.name)
        assert not java_common.needs_escaping(json_name)

        if i > 0:
            required_check_writer.write("\n\n")

        required_check_writer.write(
            f"""\
if ({arg_var} == null) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Required property \\\"{json_name}\\\" is missing");
{I}return Result.failure(error);
}}"""
        )

    blocks.append(Stripped(required_check_writer.getvalue()))

    # endregion

    # region Pass in arguments to the constructor

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

    if len(cls.constructor.arguments) == 0:
        blocks.append(Stripped(f"return Result.success(new{name}());"))
    else:
        init_writer = io.StringIO()
        init_writer.write(f"return Result.success(new {name}(\n")

        for i, arg in enumerate(cls.constructor.arguments):
            prop = cls.properties_by_name[arg.name]

            # NOTE (empwilli, 2024-01-18):
            # The argument to the constructor may be optional while the property
            # might be required, since we can set the default value in the body of
            # the constructor. However, we can not have an optional property and a
            # required constructor argument as we then would not know how to create
            # the instance.

            if not (
                intermediate.type_annotations_equal(
                    arg.type_annotation, prop.type_annotation
                )
                or intermediate.type_annotations_equal(
                    intermediate.beneath_optional(arg.type_annotation),
                    prop.type_annotation,
                )
            ):
                errors.append(
                    Error(
                        arg.parsed.node,
                        f"Expected type annotation for property {prop.name!r} "
                        f"and constructor argument {arg.name!r} "
                        f"of the class {cls.name!r} to have matching types, "
                        f"but they do not: "
                        f"property type is {prop.type_annotation} "
                        f"and argument type is {arg.type_annotation}. "
                        f"Hence we do not know how to generate the call "
                        f"to the constructor in the JSON de-serialization.",
                    )
                )
                continue

            arg_var = java_naming.variable_name(Identifier(f"the_{arg.name}"))

            init_writer.write(f"{I}{arg_var}")

            if i < len(cls.constructor.arguments) - 1:
                init_writer.write(",\n")
            else:
                init_writer.write("));")

        if len(errors) > 0:
            return None, errors

        blocks.append(Stripped(init_writer.getvalue()))
    # endregion

    writer = io.StringIO()

    writer.write(
        f"""\
/**
 * Deserialize an instance of {name} from {{@param node}}.
 *
 * @param node JSON node to be parsed
 * @param elem Error, if any, during the deserialization
 */
private static Result<{name}> try{name}From(JsonNode node) {{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_deserialize_impl(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the implementation of the deserialization."""
    errors = []  # type: List[Error]
    blocks = [
        Stripped(
            f"""\
/** Convert {{@code value}} to a string.
 * @param node JSON node to be parsed
 */
private static Result<String> tryStringFrom(JsonNode value) {{
{I}if (!value.isTextual()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected a JsonValue of String, but got " + value.getNodeType());
{II}return Result.failure(error);
{I}}}
{I}return Result.success(value.asText());
}}"""
        ),
        Stripped(
            f"""\
/** Convert {{@code value}} to a boolean.
 * @param node JSON node to be parsed
 */
private static Result<Boolean> tryBooleanFrom(JsonNode value) {{
{I}if (!value.isBoolean()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected a JsonValue of Boolean, but got " + value.getNodeType());
{II}return Result.failure(error);
{I}}}
{I}return Result.success(value.asBoolean());
}}"""
        ),
        Stripped(
            f"""\
/** Convert {{@code value}} to a long 64-bit integer.
 * @param node JSON node to be parsed
 */
private static Result<Long> tryLongFrom(JsonNode value) {{
{I}if (!value.isLong()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected a JsonValue of Long, but got " + value.getNodeType());
{II}return Result.failure(error);
{I}}}
{I}return Result.success(value.asLong());
}}"""
        ),
        Stripped(
            f"""\
/** Convert {{@code value}} to a double-precision 64-bit float.
 * @param node JSON node to be parsed
 */
private static Result<Double> tryDoubleFrom(JsonNode value) {{
{I}if (!value.isDouble()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected a JsonValue of Double, but got " + value.getNodeType());
{II}return Result.failure(error);
{I}}}
{I}return Result.success(value.asDouble());
}}"""
        ),
        Stripped(
            f"""\
private static Result<byte[]> tryBytesFrom(JsonNode value) {{
{I}if (!value.isTextual()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected a JsonValue of String, but got " + value.getNodeType());
{II}return Result.failure(error);
{I}}}
{I}final byte[] decodedData;
{I}Base64.Decoder decoder = Base64.getDecoder();

{I}try {{
{II}decodedData = decoder.decode(value.textValue());
{I}}} catch (Exception exception) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected Base-64 encoded bytes, but the conversion failed " +
{IIII}"because: " + exception.getMessage());
{II}return Result.failure(error);
{I}}}

{I}return Result.success(decodedData);
}}"""
        ),
    ]  # type: List[Stripped]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            blocks.append(_generate_from_method_for_enumeration(enumeration=our_type))

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if our_type.interface is not None:
                blocks.append(
                    _generate_from_method_for_interface(interface=our_type.interface)
                )

            if isinstance(our_type, intermediate.ConcreteClass):
                if our_type.is_implementation_specific:
                    implementation_key = specific_implementations.ImplementationKey(
                        f"Jsonization/DeserializeImplementation/{our_type.name}_from.java"
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

                    blocks.append(spec_impls[implementation_key])
                else:
                    block, cls_errors = _generate_from_method_for_class(cls=our_type)
                    if cls_errors is not None:
                        errors.extend(cls_errors)
                        continue
                    else:
                        assert block is not None
                        blocks.append(block)
        else:
            assert_never(our_type)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()

    writer.write(
        """\
/**
 * Implement the deserialization of meta-model classes from JSON nodes.
 *
 * <p>The implementation propagates an {@link Reporting.Error} instead
 * of relying on exceptions. Under the assumption that incorrect data is much
 * less frequent than correct data, this makes the deserialization more
 * efficient.
 *
 * However, we do not want to force the client to deal with
 * the {@link Reporting.Error} class as this is not intuitive. Therefore
 * we distinguish the implementation, realized in
 * {@link DeserializeImplementation}, and the facade given in
 * {@link Deserialize} class.
 */
private static class DeserializeImplementation {
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_deserialize_from(name: str) -> Stripped:
    """Generate the facade deserialization method for the type with C# ``name``."""
    writer = io.StringIO()
    writer.write(
        f"""\
/**
 * Deserialize an instance of {name} from {{@code node}}.
 *
 * @param node JSON node to be parsed
 */
"""
    )

    writer.write(
        f"""\
public static {name} deserialize{name}(JsonNode node) {{
{I}final Result<? extends {name}> result =
{II}DeserializeImplementation.try{name}From(
{III}node);

{I}return result.onError(error -> {{
{II}throw new DeserializeException(
{III}Reporting.generateJsonPath(error.getPathSegments()),
{III}error.getCause());
{I}}});
}}"""
    )

    return Stripped(writer.getvalue())


def _generate_deserialize(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the deserializer with a deserialization method for each class."""
    blocks = []  # type: List[Stripped]
    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            blocks.append(
                _generate_deserialize_from(name=java_naming.enum_name(our_type.name))
            )

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if our_type.interface is not None:
                blocks.append(
                    _generate_deserialize_from(
                        name=java_naming.interface_name(our_type.interface.name)
                    )
                )

            if isinstance(our_type, intermediate.ConcreteClass):
                blocks.append(
                    _generate_deserialize_from(
                        name=java_naming.class_name(our_type.name)
                    )
                )
        else:
            assert_never(our_type)

    writer = io.StringIO()

    writer.write(
        """\
/**
 * Deserialize instances of meta-model classes from JSON nodes.
 *
"""
    )

    first_cls = (
        symbol_table.classes[0] if len(symbol_table.classes) > 0 else None
    )  # type: Optional[intermediate.ClassUnion]

    if first_cls is not None:
        cls_name = None  # type: Optional[str]
        if isinstance(first_cls, intermediate.AbstractClass):
            cls_name = java_naming.interface_name(first_cls.name)
        elif isinstance(first_cls, intermediate.ConcreteClass):
            cls_name = java_naming.class_name(first_cls.name)
        else:
            assert_never(first_cls)

        an_instance_variable = java_naming.variable_name(Identifier("an_instance"))

        writer.write(
            f"""\
 * <pre>
 * Here is an example how to parse an instance of {cls_name}:
 * {{@code
 * String someString = "... some JSON ...";
 * ObjectMapper objectMapper = new ObjectMapper();
 * JsonNode node = objectMapper.readTree(someString);
 * {cls_name} {an_instance_variable} = Deserialize.deserialize{cls_name}(
 * {I}node);
 * }}
 */
"""
        )

    writer.write(
        """\
public static class Deserialize
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue())


def _generate_serialize_primitive_value(
    primitive_type: intermediate.PrimitiveType, source_expr: Stripped
) -> Stripped:
    """
    Generate the snippet to serialize ``source_expr`` to JSON.

    Source expression is expected to be of ``primitive_type``.
    """
    if primitive_type is intermediate.PrimitiveType.BOOL:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
JsonNodeFactory.instance.booleanNode(
{I}{indent_but_first_line(source_expr, I)})"""
        )
    elif primitive_type is intermediate.PrimitiveType.FLOAT:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
JsonNodeFactory.instance.numberNode(
{I}{indent_but_first_line(source_expr, I)})"""
        )
    elif primitive_type is intermediate.PrimitiveType.STR:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
JsonNodeFactory.instance.textNode(
{I}{indent_but_first_line(source_expr, I)})"""
        )
    elif primitive_type is intermediate.PrimitiveType.INT:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
Transformer.toJsonValue(
{I}{indent_but_first_line(source_expr, I)})"""
        )
    elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
JsonNodeFactory.instance.textNode(
{II}Base64.getEncoder()
{III}.encodeToString({indent_but_first_line(source_expr, II)}))"""
        )
    else:
        assert_never(primitive_type)


def _generate_serialize_atomic_value(
    type_annotation: intermediate.AtomicTypeAnnotation, source_expr: Stripped
) -> Stripped:
    """Generate the snippet to serialize ``source_expr`` to JSON."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return _generate_serialize_primitive_value(
            primitive_type=type_annotation.a_type, source_expr=source_expr
        )
    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        our_type = type_annotation.our_type
        if isinstance(our_type, intermediate.Enumeration):
            method_name = java_naming.method_name(
                Identifier(f"{our_type.name}_to_json_value")
            )

            # We can not use textwrap due to indent_but_first_line.
            return Stripped(
                f"""\
Serialize.{method_name}(
{I}{indent_but_first_line(source_expr, I)})"""
            )
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            return _generate_serialize_primitive_value(
                primitive_type=our_type.constrainee, source_expr=source_expr
            )
        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # We can not use textwrap due to indent_but_first_line.
            return Stripped(
                f"""\
transform(
{I}{indent_but_first_line(source_expr, I)})"""
            )
        else:
            assert_never(our_type)
    else:
        assert_never(type_annotation)
        raise AssertionError("Unexpected execution path")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transform_property(
    prop: intermediate.Property,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the snippet to transform a property into a JSON node."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    stmts = []  # type: List[Stripped]

    getter_name = java_naming.getter_name(prop.name)
    prop_literal = java_common.string_literal(naming.json_property(prop.name))

    source_expr: Stripped

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        source_expr = Stripped(f"that.{getter_name}().get()")
    else:
        source_expr = Stripped(f"that.{getter_name}()")

    if isinstance(
        type_anno,
        intermediate.PrimitiveTypeAnnotation,
    ):
        conversion_expr = _generate_serialize_atomic_value(
            type_annotation=type_anno, source_expr=source_expr
        )

        # NOTE (empwilli, 2024-02-06):
        # We have to use ObjectNode.put for Strings but the function is deprecated for JsonObjects.
        if type_anno.a_type == intermediate.PrimitiveType.STR:
            stmts.append(Stripped(f"result.put({prop_literal}, {conversion_expr});"))
        else:
            stmts.append(Stripped(f"result.set({prop_literal}, {conversion_expr});"))
    elif isinstance(
        type_anno,
        intermediate.OurTypeAnnotation,
    ):
        conversion_expr = _generate_serialize_atomic_value(
            type_annotation=type_anno, source_expr=source_expr
        )
        stmts.append(Stripped(f"result.set({prop_literal}, {conversion_expr});"))
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_anno.items,
            (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
        ), (
            "We chose to implement only a very limited pattern matching; "
            "see intermediate._translate._verify_only_simple_type_patterns."
        )

        item_type = java_common.generate_type(type_anno.items)
        array_var = java_naming.variable_name(Identifier(f"array_{prop.name}"))

        item_conversion_expr = _generate_serialize_atomic_value(
            type_annotation=type_anno.items, source_expr=Stripped("item")
        )

        # We cannot use textwrap due to indent_but_first_line.
        stmts.append(
            Stripped(
                f"""\
final ArrayNode {array_var} = JsonNodeFactory.instance.arrayNode();
for ({item_type} item : {source_expr}) {{
{I}{array_var}.add(
{II}{indent_but_first_line(item_conversion_expr, II)});
}}
result.set({prop_literal}, {array_var});"""
            )
        )
    else:
        assert_never(type_anno)

    serialize_block = Stripped("\n".join(stmts))
    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        return (
            Stripped(
                f"""\
if (that.{getter_name}().isPresent()) {{
{I}{indent_but_first_line(serialize_block, I)}
}}"""
            ),
            None,
        )
    else:
        return serialize_block, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transform_for_class(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the transform method to a JSON object for the given concrete class."""
    errors = []  # type: List[Error]

    blocks = [
        Stripped("final ObjectNode result = JsonNodeFactory.instance.objectNode();"),
    ]  # type: List[Stripped]

    for prop in cls.properties:
        block, error = _generate_transform_property(prop=prop)
        if error is not None:
            errors.append(error)
        else:
            assert block is not None
            blocks.append(block)

    if len(errors) > 0:
        return None, errors

    if cls.serialization is not None and cls.serialization.with_model_type:
        model_type = java_common.string_literal(naming.json_model_type(cls.name))
        blocks.append(Stripped(f"""result.put("modelType", {model_type});"""))

    blocks.append(Stripped("return result;"))

    writer = io.StringIO()

    interface_name = java_naming.interface_name(cls.name)
    transform_name = java_naming.method_name(Identifier(f"transform_{cls.name}"))

    writer.write(
        f"""\
@Override
public JsonNode {transform_name}(
{I}{interface_name} that
) {{
"""
    )

    for i, stmt in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(stmt, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transformer(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a transformer which transforms instances of the meta-model to JSON."""
    errors = []  # type: List[Error]

    blocks = [
        Stripped(
            f"""\
/**
 * Convert {{@code that}} 64-bit long integer to a JSON value.
 *
 * @param that value to be converted
 */
private static JsonNode toJsonNode(Long that) {{
{I}// We need to check that we can perform a lossless conversion.
{I}long primitiveThat = that.longValue();
{I}if ((long)((double)primitiveThat) != primitiveThat) {{
{II}throw new IllegalArgumentException(
{III}"The number can not be losslessly represented in JSON: " + that);
{I}}}
{I}return JsonNodeFactory.instance.numberNode(that);
}}"""
        ),
    ]  # type: List[Stripped]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            continue

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(our_type, intermediate.AbstractClass):
            # The abstract classes are directly dispatched by the transformer,
            # so we do not need to handle them separately.
            pass

        elif isinstance(our_type, intermediate.ConcreteClass):
            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"Jsonization/Transformer/transform_{our_type.name}.java"
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

                blocks.append(spec_impls[implementation_key])
            else:
                block, cls_errors = _generate_transform_for_class(cls=our_type)
                if cls_errors is not None:
                    errors.extend(cls_errors)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(our_type)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        """\
private static class Transformer extends AbstractTransformer<JsonNode> {
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_serialize(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the static serializer."""
    blocks = [
        Stripped("private static final Transformer transformer = new Transformer();"),
        Stripped(
            f"""\
/**
 * Serialize an instance of the meta-model into a JSON object.
 */
public static JsonNode toJsonObject(IClass that) {{
{I}return transformer.transform(that);
}}"""
        ),
    ]  # type: List[Stripped]

    for enum in symbol_table.enumerations:
        name = java_naming.enum_name(enum.name)
        method_name = java_naming.method_name(Identifier(f"{enum.name}_to_json_value"))
        blocks.append(
            Stripped(
                f"""\
/**
 * Serialize a literal of {name} into a JSON string.
 */
public static JsonNode {method_name}({name} that) {{
{I}Optional<String> text = Stringification.toString(that);
{I}if (!text.isPresent()) {{
{II}throw new IllegalArgumentException("Invalid {name}: " + that);
{I}}}

{I}return JsonNodeFactory.instance.textNode(text.get());
}}"""
            )
        )

    writer = io.StringIO()

    writer.write(
        """\
/**
 * Serialize instances of meta-model classes to JSON elements.
 *
"""
    )

    first_cls = (
        symbol_table.classes[0] if len(symbol_table.classes) > 0 else None
    )  # type: Optional[intermediate.ClassUnion]

    if first_cls is not None:
        cls_name = None  # type: Optional[str]
        if isinstance(first_cls, intermediate.AbstractClass):
            cls_name = java_naming.interface_name(first_cls.name)
        elif isinstance(first_cls, intermediate.ConcreteClass):
            cls_name = java_naming.class_name(first_cls.name)
        else:
            assert_never(first_cls)

        an_instance_variable = java_naming.variable_name(Identifier("an_instance"))

        writer.write(
            f"""\
 * <pre>
 * Here is an example how to serialize an instance of {cls_name}:
 * {{@code
 * {cls_name} {an_instance_variable} = new {cls_name}(
 *     // ... some constructor arguments ...
 * );
 * JsonNode element = Jsonization.Serialize.toJsonObject(
 * {II}{an_instance_variable}));
 * }}
 */
"""
        )

    writer.write(
        """\
public static class Serialize
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue())


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
    Generate the Java code for the general serialization.

    The ``package`` defines the AAS Java package.
    """
    errors = []  # type: List[Error]

    imports = [
        Stripped("import aas_core.aas3_0.reporting.Reporting;"),
        Stripped("import aas_core.aas3_0.types.enums.*;"),
        Stripped("import aas_core.aas3_0.types.impl.*;"),
        Stripped("import aas_core.aas3_0.types.model.*;"),
        Stripped("import aas_core.aas3_0.stringification.Stringification;"),
        Stripped("import aas_core.aas3_0.visitation.AbstractTransformer;"),
        Stripped("import com.fasterxml.jackson.databind.JsonNode;"),
        Stripped("import com.fasterxml.jackson.databind.node.ArrayNode;"),
        Stripped("import com.fasterxml.jackson.databind.node.JsonNodeFactory;"),
        Stripped("import com.fasterxml.jackson.databind.node.ObjectNode;"),
        Stripped("import java.util.*;"),
        Stripped("import java.util.function.Function;"),
    ]  # type: List[Stripped]

    deserialize_impl_block, deserialize_impl_errors = _generate_deserialize_impl(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if deserialize_impl_errors is not None:
        errors.extend(deserialize_impl_errors)

    deserialize_block = _generate_deserialize(symbol_table=symbol_table)

    transformer_block, transformer_errors = _generate_transformer(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if transformer_errors is not None:
        errors.extend(transformer_errors)

    if len(errors) > 0:
        return None, errors

    assert deserialize_impl_block is not None
    assert deserialize_block is not None
    assert transformer_block is not None

    serialize_block = _generate_serialize(
        symbol_table=symbol_table,
    )

    exception_block = Stripped(
        f"""\
/**
* Represent a critical error during the deserialization.
*/
@SuppressWarnings("serial")
{I}public static class DeserializeException extends RuntimeException {{
{II}private final String path;
{II}private final String reason;

{II}public DeserializeException(String path, String reason) {{
{III}super(reason + " at: " + ("".equals(path) ? "the beginning" : path));
{III}this.path = path;
{III}this.reason = reason;
{II}}}

{II}public Optional<String> getPath() {{
{III}return Optional.ofNullable(path);
{II}}}

{II}public Optional<String> getReason() {{
{III}return Optional.ofNullable(reason);
{II}}}
{I}}}"""
    )

    result_block = Stripped(
        f"""\
private static class Result<T> {{
{I}private final T result;
{I}private final Reporting.Error error;
{I}private final boolean success;

{I}private Result(T result, Reporting.Error error, boolean success) {{
{II}this.result = result;
{II}this.error = error;
{II}this.success = success;
{I}}}

{I}public static <T> Result<T> success(T result) {{
{II}if (result == null) throw new IllegalArgumentException("Result must not be null.");
{II}return new Result<>(result, null, true);
{I}}}

{I}public static <T> Result<T> failure(Reporting.Error error) {{
{II}if (error == null) throw new IllegalArgumentException("Error must not be null.");
{II}return new Result<>(null, error, false);
{I}}}

{I}@SuppressWarnings("unchecked")
{I}public <I> Result<I> castTo(Class<I> type) {{
{II}if (isError() || type.isInstance(result)) return (Result<I>) this;
{II}throw new IllegalStateException("Result of type "
{III}+ result.getClass().getName()
{III}+ " is not an instance of "
{III}+ type.getName());
{I}}}

{I}public T getResult() {{
{II}if (!isSuccess()) throw new IllegalStateException("Result is not present.");
{II}return result;
{I}}}

{I}public boolean isSuccess() {{
{II}return success;
{I}}}

{I}public boolean isError() {{
        {II}return !success;
{I}}}

{I}public Reporting.Error getError() {{
{II}if (isSuccess()) throw new IllegalStateException("Result is present.");
{II}return error;
{I}}}

{I}public <R> R map(Function<T, R> successFunction, Function<Reporting.Error, R> errorFunction) {{
{II}return isSuccess() ? successFunction.apply(result) : errorFunction.apply(error);
{I}}}

{I}public T onError(Function<Reporting.Error, T> errorFunction) {{
{II}return map(Function.identity(), errorFunction);
{I}}}
}}"""
    )

    jsonization_blocks = [
        deserialize_impl_block,
        exception_block,
        result_block,
        deserialize_block,
        transformer_block,
        serialize_block,
    ]  # type: List[Stripped]

    jsonization_writer = io.StringIO()
    jsonization_writer.write(
        """\
/**
 * Provide de/serialization of meta-model classes to/from JSON.
 *
 * <p>We can not use one-pass deserialization for JSON since the object
 * properties do not have fixed order, and hence we can not read
 * {@code modelType} property ahead of the remaining properties.
 */
public class Jsonization {
"""
    )

    for i, deserialize_block in enumerate(jsonization_blocks):
        if i > 0:
            jsonization_writer.write("\n\n")

        jsonization_writer.write(textwrap.indent(deserialize_block, II))

    jsonization_writer.write("\n}")

    if len(errors) > 0:
        return None, errors

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.jsonization;"),
        Stripped("\n".join(imports)),
        Stripped(jsonization_writer.getvalue()),
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
