"""Generate C# code for JSON-ization based on the intermediate representation."""

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
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


def _generate_from_method_for_enumeration(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    """Generate the deserialization method for an enumeration."""
    name = csharp_naming.enum_name(identifier=enumeration.name)

    message_literal = csharp_common.string_literal(
        f"Not a valid JSON representation of {name} "
    )

    return Stripped(
        f"""\
/// <summary>
/// Deserialize the enumeration {name} from the <paramref name="node" />.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static Aas.{name}? {name}From(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
{I}error = null;
{I}string? text = DeserializeImplementation.StringFrom(
{II}node, out error);
{I}if (error != null)
{I}{{
{II}return null;
{I}}}
{I}if (text == null)
{I}{{
{II}throw new System.InvalidOperationException(
{III}"Unexpected text null if error null");
{I}}}
{I}Aas.{name}? result = Stringification.{name}FromString(text);
{I}if (result == null)
{I}{{
{II}error = new Reporting.Error(
{III}{message_literal});
{I}}}
{I}return result;
}}  // internal static {name}From"""
    )


def _generate_from_method_for_interface(
    interface: intermediate.Interface,
) -> Stripped:
    """Generate the deserialization method for an interface."""
    name = csharp_naming.interface_name(interface.name)

    blocks = [
        Stripped("error = null;"),
        Stripped(
            f"""\
var obj = node as Nodes.JsonObject;
if (obj == null)
{{
{I}error = new Reporting.Error(
{II}"Expected Nodes.JsonObject, but got {{node.GetType()}}");
{I}return null;
}}"""
        ),
        Stripped(
            f"""\
Nodes.JsonNode? modelTypeNode = obj["modelType"];
if (modelTypeNode == null)
{{
{I}error = new Reporting.Error(
{II}"Expected a model type, but none is present");
{I}return null;
}}
Nodes.JsonValue? modelTypeValue = modelTypeNode as Nodes.JsonValue;
if (modelTypeValue == null)
{{
{I}error = new Reporting.Error(
{II}"Expected JsonValue, " +
{II}$"but got {{modelTypeNode.GetType()}}");
{I}return null;
}}
modelTypeValue.TryGetValue<string>(out string? modelType);
if (modelType == null)
{{
{I}error = new Reporting.Error(
{II}"Expected a string, " +
{II}$"but the conversion failed from {{modelTypeValue}}");
{I}return null;
}}"""
        ),
    ]  # type: List[Stripped]

    # region Write the switch block

    switch_writer = io.StringIO()
    switch_writer.write(
        """\
switch (modelType)
{
"""
    )

    for implementer in interface.implementers:
        model_type = naming.json_model_type(implementer.name)
        implementer_name = csharp_naming.class_name(implementer.name)
        switch_writer.write(
            f"""\
{I}case {csharp_common.string_literal(model_type)}:
{II}return {implementer_name}From(
{III}node, out error);
"""
        )

    switch_writer.write(
        f"""\
{I}default:
{II}error = new Reporting.Error(
{III}$"Unexpected model type for {name}: {{modelType}}");
{II}return null;
}}"""
    )
    blocks.append(Stripped(switch_writer.getvalue()))

    # endregion

    writer = io.StringIO()

    writer.write(
        f"""\
/// <summary>
/// Deserialize an instance of {name} by dispatching
/// based on <c>modelType</c> property of the <paramref name="node" />.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
public static Aas.{name}? {name}From(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}  // public static Aas.{name} {name}From")

    return Stripped(writer.getvalue())


_PARSE_METHOD_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: "DeserializeImplementation.BoolFrom",
    intermediate.PrimitiveType.INT: "DeserializeImplementation.LongFrom",
    intermediate.PrimitiveType.FLOAT: "DeserializeImplementation.DoubleFrom",
    intermediate.PrimitiveType.STR: "DeserializeImplementation.StringFrom",
    intermediate.PrimitiveType.BYTEARRAY: "DeserializeImplementation.BytesFrom",
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
        symbol = type_annotation.symbol
        if isinstance(symbol, intermediate.Enumeration):
            enum_name = csharp_naming.enum_name(symbol.name)
            parse_method = f"DeserializeImplementation.{enum_name}From"

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            parse_method = _PARSE_METHOD_BY_PRIMITIVE_TYPE[symbol.constrainee]

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if symbol.interface is not None:
                interface_name = csharp_naming.interface_name(symbol.interface.name)
                parse_method = f"DeserializeImplementation.{interface_name}From"
            else:
                cls_name = csharp_naming.class_name(symbol.name)
                parse_method = f"DeserializeImplementation.{cls_name}From"

        else:
            assert_never(symbol)
    else:
        assert_never(type_annotation)

    return Stripped(parse_method)


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_deserialize_property(
    prop: intermediate.Property,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the code snippet for de-serializing the property ``prop``."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # Prefix the variables to avoid naming conflicts
    target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))
    node_var = csharp_naming.variable_name(Identifier(f"node_{prop.name}"))

    json_name = naming.json_property(prop.name)
    assert not csharp_common.needs_escaping(json_name)

    json_literal = csharp_common.string_literal(json_name)

    stmts = [
        Stripped(f"Nodes.JsonNode? {node_var} = obj[{json_literal}];")
    ]  # type: List[Stripped]

    required = not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
    target_type = csharp_common.generate_type(type_anno)
    if isinstance(type_anno, intermediate.OurTypeAnnotation):
        if isinstance(
            type_anno.symbol,
            (
                intermediate.Enumeration,
                intermediate.AbstractClass,
                intermediate.ConcreteClass,
            ),
        ):
            target_type = Stripped(f"Aas.{target_type}")
        elif isinstance(type_anno.symbol, intermediate.ConstrainedPrimitive):
            # We do not have to prefix the type as it will be a primitive.
            pass
        else:
            assert_never(type_anno.symbol)

    parse_block = None  # type: Optional[Stripped]
    if isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        parse_method = _parse_method_for_atomic_value(type_anno)

        # When the property is optional, we already define the ``target_var`` and
        # set it to null by default.
        define_target_var_prefix = f"{target_type}? " if required else ""

        parse_block = Stripped(
            f"""\
{define_target_var_prefix}{target_var} = {parse_method}(
{I}{node_var},
{I}out error);
if (error != null)
{{
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{json_literal}));
{I}return null;
}}
if ({target_var} == null)
{{
{I}throw new System.InvalidOperationException(
{II}"Unexpected {target_var} null when error is also null");
}}"""
        )

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_anno.items,
            (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
        ), (
            "We chose to implement only a very limited pattern matching; "
            "see intermediate._translate_._verify_only_simple_type_patterns"
        )

        item_type = csharp_common.generate_type(type_anno.items)

        array_var = csharp_naming.variable_name(Identifier(f"array_{prop.name}"))
        index_var = csharp_naming.variable_name(Identifier(f"index_{prop.name}"))

        parse_method = _parse_method_for_atomic_value(type_anno.items)

        # If the property is required, the target_var will be defined before.
        target_var_prefix = "var " if required else ""

        parse_block = Stripped(
            f"""\
Nodes.JsonArray? {array_var} = {node_var} as Nodes.JsonArray;
if ({array_var} == null)
{{
{I}error = new Reporting.Error(
{II}$"Expected a JsonArray, but got {{{node_var}.GetType()}}");
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{json_literal}));
{I}return null;
}}
{target_var_prefix}{target_var} = new List<{item_type}>(
{I}{array_var}.Count);
int {index_var} = 0;
foreach (Nodes.JsonNode? item in {array_var})
{{
{I}if (item == null)
{I}{{
{II}error = new Reporting.Error(
{III}"Expected a non-null item, but got a null");
{II}error._pathSegments.AddFirst(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}error._pathSegments.AddFirst(
{III}new Reporting.NameSegment(
{IIII}{json_literal}));
{I}}}
{I}{item_type}? parsedItem = {parse_method}(
{II}item ?? throw new System.InvalidOperationException(),
{II}out error);
{I}if (error != null)
{I}{{
{II}error._pathSegments.AddFirst(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}error._pathSegments.AddFirst(
{III}new Reporting.NameSegment(
{IIII}{json_literal}));
{II}return null;
{I}}}
{I}{target_var}.Add(
{II}parsedItem
{III}?? throw new System.InvalidOperationException(
{IIII}"Unexpected result null when error is null"));
{I}{index_var}++;
}}"""
        )
    else:
        assert_never(prop.type_annotation)

    if required:
        message_literal = csharp_common.string_literal(
            f"Required property {json_literal} is missing "
        )

        stmts.append(
            Stripped(
                f"""\
if ({node_var} == null)
{{
{I}error = new Reporting.Error(
{II}{message_literal});
{I}return null;
}}"""
            )
        )
        stmts.append(parse_block)
    else:
        assert not target_type.endswith(
            "?"
        ), "Expected the type of the target not to consider the outer Optional"

        # NOTE (mristin, 2022-03-11):
        # We can not use textwrap.dedent since we need to indent the parse_block.
        stmts.append(
            Stripped(
                f"""\
{target_type}? {target_var} = null;
if ({node_var} != null)
{{
{I}{indent_but_first_line(parse_block, I)}
}}"""
            )
        )

    return Stripped("\n".join(stmts)), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_from_method_for_class(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the deserialization method for a concrete class."""
    errors = []  # type: List[Error]

    name = csharp_naming.class_name(cls.name)

    blocks = [
        Stripped("error = null;"),
        Stripped(
            f"""\
Nodes.JsonObject? obj = node as Nodes.JsonObject;
if (obj == null)
{{
{I}error = new Reporting.Error(
{II}$"Expected a JsonObject, but got {{node.GetType()}}");
{I}return null;
}}"""
        ),
    ]  # type: List[Stripped]

    if len(cls.constructor.arguments) == 0:
        blocks.append(Stripped(f"return new Aas.{name}();"))
    else:
        for prop in cls.properties:
            block, error = _generate_deserialize_property(prop=prop)
            if error is not None:
                errors.append(error)
            else:
                assert block is not None
                blocks.append(block)

        if len(errors) > 0:
            return None, errors

        # region Pass in properties as arguments to the constructor

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

        init_writer = io.StringIO()
        init_writer.write(f"return new Aas.{name}(\n")

        for i, arg in enumerate(cls.constructor.arguments):
            prop = cls.properties_by_name[arg.name]

            # NOTE (mristin, 2022-03-11):
            # The argument to the constructor may be optional while the property might
            # be required, since we can set the default value in the body of the
            # constructor. However, we can not have an optional property and a required
            # constructor argument as we then would not know how to create the instance.

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

            arg_var = csharp_naming.variable_name(Identifier(f"the_{arg.name}"))

            init_writer.write(f"{I}{arg_var}")
            if not isinstance(
                prop.type_annotation, intermediate.OptionalTypeAnnotation
            ):
                init_writer.write("\n")

                # Dedention could not work here due to prefix indention at the very
                # beginning.
                init_writer.write(
                    f"""\
{II} ?? throw new System.InvalidOperationException(
{III}"Unexpected null, had to be handled before")"""
                )

            if i < len(cls.constructor.arguments) - 1:
                init_writer.write(",\n")
            else:
                init_writer.write(");")

        if len(errors) > 0:
            return None, errors

        # endregion

        blocks.append(Stripped(init_writer.getvalue()))

    writer = io.StringIO()

    writer.write(
        f"""\
/// <summary>
/// Deserialize an instance of {name} from <paramref name="node" />.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static Aas.{name}? {name}From(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}  // internal static {name}From")

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
/// <summary>Convert <paramref name="node" /> to a boolean.</summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static bool? BoolFrom(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
{I}error = null;
{I}Nodes.JsonValue? value = node as Nodes.JsonValue;
{I}if (value == null)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a JsonValue, but got {{node.GetType()}}");
{II}return null;
{I}}}
{I}bool ok = value.TryGetValue<bool>(out bool result);
{I}if (!ok)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a boolean, but the conversion failed " +
{III}$"from {{value.ToJsonString()}}");
{II}return null;
{I}}}
{I}return result;
}}"""
        ),
        Stripped(
            f"""\
/// <summary>
/// Convert the <paramref name="node" /> to a long 64-bit integer.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static long? LongFrom(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
{I}error = null;
{I}Nodes.JsonValue? value = node as Nodes.JsonValue;
{I}if (value == null)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a JsonValue, but got {{node.GetType()}}");
{II}return null;
{I}}}
{I}bool ok = value.TryGetValue<long>(out long result);
{I}if (!ok)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a 64-bit long integer, but the conversion failed " +
{III}$"from {{value.ToJsonString()}}");
{II}return null;
{I}}}
{I}return result;
}}"""
        ),
        Stripped(
            f"""\
/// <summary>
/// Convert the <paramref name="node" /> to a double-precision 64-bit float.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static double? DoubleFrom(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
{I}error = null;
{I}Nodes.JsonValue? value = node as Nodes.JsonValue;
{I}if (value == null)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a JsonValue, but got {{node.GetType()}}");
{II}return null;
{I}}}
{I}bool ok = value.TryGetValue<double>(out double result);
{I}if (!ok)
{I}{{
{II}error = new Reporting.Error(
{III}"Expected a 64-bit double-precision float, " +
{III}"but the conversion failed " +
{III}$"from {{value.ToJsonString()}}");
{II}return null;
{I}}}
{I}return result;
}}"""
        ),
        Stripped(
            f"""\
/// <summary>
/// Convert the <paramref name="node" /> to a string.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static string? StringFrom(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
{I}error = null;
{I}Nodes.JsonValue? value = node as Nodes.JsonValue;
{I}if (value == null)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a JsonValue, but got {{node.GetType()}}");
{II}return null;
{I}}}
{I}bool ok = value.TryGetValue<string>(out string? result);
{I}if (!ok)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a string, but the conversion failed " +
{III}$"from {{value.ToJsonString()}}");
{II}return null;
{I}}}
{I}if (result == null)
{I}{{
{II}error = new Reporting.Error(
{III}"Expected a string, but got a null");
{II}return null;
{I}}}
{I}return result;
}}"""
        ),
        Stripped(
            f"""\
/// <summary>
/// Convert the <paramref name="node" /> to bytes.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <param name="error">Error, if any, during the deserialization</param>
internal static byte[]? BytesFrom(
{I}Nodes.JsonNode node,
{I}out Reporting.Error? error)
{{
{I}error = null;
{I}Nodes.JsonValue? value = node as Nodes.JsonValue;
{I}if (value == null)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a JsonValue, but got {{node.GetType()}}");
{II}return null;
{I}}}
{I}bool ok = value.TryGetValue<string>(out string? text);
{I}if (!ok)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected a string, but the conversion failed " +
{III}$"from {{value.ToJsonString()}}");
{II}return null;
{I}}}
{I}if (text == null)
{I}{{
{II}error = new Reporting.Error(
{III}"Expected a string, but got a null");
{II}return null;
{I}}}
{I}try
{I}{{
{II}return System.Convert.FromBase64String(text);
{I}}}
{I}catch (System.FormatException exception)
{I}{{
{II}error = new Reporting.Error(
{III}"Expected Base-64 encoded bytes, but the conversion failed " +
{III}$"because: {{exception}}");
{II}return null;
{I}}}
}}"""
        ),
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            blocks.append(_generate_from_method_for_enumeration(enumeration=symbol))

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if symbol.interface is not None:
                blocks.append(
                    _generate_from_method_for_interface(interface=symbol.interface)
                )

            if isinstance(symbol, intermediate.ConcreteClass):
                if symbol.is_implementation_specific:
                    implementation_key = specific_implementations.ImplementationKey(
                        f"Jsonization/DeserializeImplementation/{symbol.name}_from.cs"
                    )

                    implementation = spec_impls.get(implementation_key, None)
                    if implementation is None:
                        errors.append(
                            Error(
                                symbol.parsed.node,
                                f"The jsonization snippet is missing "
                                f"for the implementation-specific "
                                f"class {symbol.name}: {implementation_key}",
                            )
                        )
                        continue

                    blocks.append(spec_impls[implementation_key])
                else:
                    block, cls_errors = _generate_from_method_for_class(cls=symbol)
                    if cls_errors is not None:
                        errors.extend(cls_errors)
                        continue
                    else:
                        assert block is not None
                        blocks.append(block)
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()

    writer.write(
        """\
/// <summary>
/// Implement the deserialization of meta-model classes from JSON nodes.
/// </summary>
/// <remarks>
/// The implementation propagates an <see cref="Error" /> instead of relying
/// on exceptions. Under the assumption that incorrect data is much less
/// frequent than correct data, this makes the deserialization more
/// efficient.
///
/// However, we do not want to force the client to deal with
/// the <see cref="Error" /> class as this is not intuitive. Therefore
/// we distinguish the implementation, realized in
/// <see cref="DeserializeImplementation" />, and the facade given in
/// <see cref="Deserialize" /> class.
internal static class DeserializeImplementation
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // public static class DeserializeImplementation")

    return Stripped(writer.getvalue()), None


def _generate_deserialize_from(name: str) -> Stripped:
    """Generate the facade deserialization method for the symbol with C# ``name``."""
    return Stripped(
        f"""\
/// <summary>
/// Deserialize an instance of {name} from <paramref name="node" />.
/// </summary>
/// <param name="node">JSON node to be parsed</param>
/// <exception cref="Jsonization.Exception">
/// Thrown when <paramref name="node" /> is not a valid JSON
/// representation of {name}.
/// </exception>
public static Aas.{name} {name}From(
{I}Nodes.JsonNode node)
{{
{I}Aas.{name}? result = DeserializeImplementation.{name}From(
{II}node,
{II}out Reporting.Error? error);
{I}if (error != null)
{I}{{
{II}throw new Jsonization.Exception(
{III}Reporting.GenerateJsonPath(error.PathSegments),
{III}error.Cause);
{I}}}
{I}return result
{II}?? throw new System.InvalidOperationException(
{III}"Unexpected output null when error is null");
}}"""
    )


def _generate_deserialize(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the deserializer with a deserialization method for each class."""
    blocks = []  # type: List[Stripped]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            blocks.append(
                _generate_deserialize_from(name=csharp_naming.enum_name(symbol.name))
            )

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if symbol.interface is not None:
                blocks.append(
                    _generate_deserialize_from(
                        name=csharp_naming.interface_name(symbol.interface.name)
                    )
                )

            if isinstance(symbol, intermediate.ConcreteClass):
                blocks.append(
                    _generate_deserialize_from(
                        name=csharp_naming.class_name(symbol.name)
                    )
                )
        else:
            assert_never(symbol)

    writer = io.StringIO()

    writer.write(
        """\
/// <summary>
/// Deserialize instances of meta-model classes from JSON nodes.
/// </summary>
"""
    )

    first_cls = None  # type: Optional[intermediate.ClassUnion]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)):
            first_cls = symbol
            break

    if first_cls is not None:
        cls_name = None  # type: Optional[str]
        if isinstance(first_cls, intermediate.AbstractClass):
            cls_name = csharp_naming.interface_name(first_cls.name)
        elif isinstance(first_cls, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(first_cls.name)
        else:
            assert_never(first_cls)

        an_instance_variable = csharp_naming.variable_name(Identifier("an_instance"))

        writer.write(
            f"""\
/// <example>
/// Here is an example how to parse an instance of {cls_name}:
/// <code>
/// string someString = "... some JSON ...";
/// var node = System.Text.Json.Nodes.JsonNode.Parse(someString);
/// Aas.{cls_name} {an_instance_variable} = Deserialize.{cls_name}From(
/// {I}node);
/// </code>
/// </example>
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

    writer.write("\n}  // public static class Deserialize")

    return Stripped(writer.getvalue())


def _generate_serialize_primitive_value(
    primitive_type: intermediate.PrimitiveType, source_expr: Stripped
) -> Stripped:
    """
    Generate the snippet to serialize ``source_expr`` to JSON.

    Source expression is expected to be of ``primitive_type``.
    """
    if (
        primitive_type is intermediate.PrimitiveType.BOOL
        or primitive_type is intermediate.PrimitiveType.FLOAT
        or primitive_type is intermediate.PrimitiveType.STR
    ):
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
Nodes.JsonValue.Create(
{I}{indent_but_first_line(source_expr, I)})"""
        )
    elif primitive_type is intermediate.PrimitiveType.INT:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
Transformer.ToJsonValue(
{I}{indent_but_first_line(source_expr, I)})"""
        )
    elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        # We can not use textwrap due to indent_but_first_line.
        return Stripped(
            f"""\
Nodes.JsonValue.Create(
{I}System.Convert.ToBase64String(
{II}{indent_but_first_line(source_expr, II)}))"""
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
        symbol = type_annotation.symbol
        if isinstance(symbol, intermediate.Enumeration):
            name = csharp_naming.enum_name(symbol.name)

            # We can not use textwrap due to indent_but_first_line.
            return Stripped(
                f"""\
Serialize.{name}ToJsonValue(
{I}{indent_but_first_line(source_expr, I)})"""
            )
        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            return _generate_serialize_primitive_value(
                primitive_type=symbol.constrainee, source_expr=source_expr
            )
        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # We can not use textwrap due to indent_but_first_line.
            return Stripped(
                f"""\
Transform(
{I}{indent_but_first_line(source_expr, I)})"""
            )
        else:
            assert_never(symbol)
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

    name = csharp_naming.property_name(prop.name)
    prop_literal = csharp_common.string_literal(naming.json_property(prop.name))

    # NOTE (mristin, 2022-03-12):
    # For some unexplainable reason, C# compiler can not infer that properties which
    # are enumerations are not null after an ``if (that.someProperty != null)``.
    # Hence we need to add a null-coalescing for these particular cases.
    # Otherwise, we can just stick to ``that.someProperty``.

    needs_null_coalescing = (
        isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
        and isinstance(prop.type_annotation.value, intermediate.OurTypeAnnotation)
        and isinstance(prop.type_annotation.value.symbol, intermediate.Enumeration)
    )
    if needs_null_coalescing:
        source_expr = Stripped("value")
    else:
        source_expr = Stripped(f"that.{name}")

    if isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        conversion_expr = _generate_serialize_atomic_value(
            type_annotation=type_anno, source_expr=source_expr
        )
        stmts.append(Stripped(f"result[{prop_literal}] = {conversion_expr};"))
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_anno.items,
            (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
        ), (
            "We chose to implement only a very limited pattern matching; "
            "see intermediate._translate._verify_only_simple_type_patterns."
        )

        item_type = csharp_common.generate_type(type_anno.items)
        array_var = csharp_naming.variable_name(Identifier(f"array_{prop.name}"))

        item_conversion_expr = _generate_serialize_atomic_value(
            type_annotation=type_anno.items, source_expr=Stripped("item")
        )

        # We can not use textwrap due to indent_but_first_line.
        stmts.append(
            Stripped(
                f"""\
var {array_var} = new Nodes.JsonArray();
foreach ({item_type} item in {source_expr})
{{
{I}{array_var}.Add(
{II}{indent_but_first_line(item_conversion_expr, II)});
}}
result[{prop_literal}] = {array_var};"""
            )
        )
    else:
        assert_never(type_anno)

    serialize_block = Stripped("\n".join(stmts))
    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        if needs_null_coalescing:
            value_type = csharp_common.generate_type(prop.type_annotation.value)
            if isinstance(prop.type_annotation.value, intermediate.OurTypeAnnotation):
                symbol = prop.type_annotation.value.symbol
                if isinstance(
                    symbol,
                    (
                        intermediate.Enumeration,
                        intermediate.AbstractClass,
                        intermediate.ConcreteClass,
                    ),
                ):
                    value_type = Stripped(f"Aas.{value_type}")

            return (
                Stripped(
                    f"""\
if (that.{name} != null)
{{
{I}// We need to help the static analyzer with a null coalescing.
{I}{value_type} value = that.{name}
{II}?? throw new System.InvalidOperationException();
{I}{indent_but_first_line(serialize_block, I)}
}}"""
                ),
                None,
            )

        else:
            return (
                Stripped(
                    f"""\
if (that.{name} != null)
{{
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
    name = csharp_naming.class_name(cls.name)

    blocks = [Stripped("var result = new Nodes.JsonObject();")]  # type: List[Stripped]

    for prop in cls.properties:
        block, error = _generate_transform_property(prop=prop)
        if error is not None:
            errors.append(error)
        else:
            assert block is not None
            blocks.append(block)

    if len(errors) > 0:
        return None, errors

    blocks.append(Stripped("return result;"))

    writer = io.StringIO()
    writer.write(
        f"""\
public override Nodes.JsonObject Transform(Aas.{name} that)
{{
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
/// <summary>
/// Convert <paramref name="that" /> 64-bit long integer to a JSON value.
/// </summary>
/// <param name="that">value to be converted</param>
/// <exception name="System.ArgumentException>
/// Thrown if <paramref name="that"> is not within the range where it
/// can be losslessly converted to a double floating number.
/// </exception>
private static Nodes.JsonValue ToJsonValue(long that)
{{
{I}// We need to check that we can perform a lossless conversion.
{I}if ((long)((double)that) != that)
{I}{{
{II}throw new System.ArgumentException(
{III}$"The number can not be losslessly represented in JSON: {{that}}");
{I}}}
{I}return Nodes.JsonValue.Create(that);
}}"""
        ),
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(symbol, intermediate.AbstractClass):
            # The abstract classes are directly dispatched by the transformer,
            # so we do not need to handle them separately.
            pass

        elif isinstance(symbol, intermediate.ConcreteClass):
            if symbol.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"Jsonization/Transformer/transform_{symbol.name}.cs"
                )

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            symbol.parsed.node,
                            f"The jsonization snippet is missing "
                            f"for the implementation-specific "
                            f"class {symbol.name}: {implementation_key}",
                        )
                    )
                    continue

                blocks.append(spec_impls[implementation_key])
            else:
                block, cls_errors = _generate_transform_for_class(cls=symbol)
                if cls_errors is not None:
                    errors.extend(cls_errors)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        f"""\
internal class Transformer
{I}: Visitation.AbstractTransformer<Nodes.JsonObject>
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // internal class Transformer")

    return Stripped(writer.getvalue()), None


def _generate_serialize(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the static serializer."""
    blocks = [
        Stripped("private static Transformer _transformer = new Transformer();"),
        Stripped(
            f"""\
/// <summary>
/// Serialize an instance of the meta-model into a JSON object.
/// </summary>
public static Nodes.JsonObject ToJsonObject(Aas.IClass that)
{{
{I}return Serialize._transformer.Transform(that);
}}"""
        ),
    ]  # type: List[Stripped]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            name = csharp_naming.enum_name(symbol.name)
            blocks.append(
                Stripped(
                    f"""\
/// <summary>
/// Serialize a literal of {name} into a JSON string.
/// </summary>
public static Nodes.JsonValue {name}ToJsonValue(Aas.{name} that)
{{
{I}string? text = Stringification.ToString(that);
{I}return Nodes.JsonValue.Create(text)
{II}?? throw new System.ArgumentException(
{III}$"Invalid {name}: {{that}}");
}}"""
                )
            )

    writer = io.StringIO()

    writer.write(
        """\
/// <summary>
/// Serialize instances of meta-model classes to JSON elements.
/// </summary>
"""
    )

    first_cls = None  # type: Optional[intermediate.ClassUnion]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)):
            first_cls = symbol
            break

    if first_cls is not None:
        cls_name = None  # type: Optional[str]
        if isinstance(first_cls, intermediate.AbstractClass):
            cls_name = csharp_naming.interface_name(first_cls.name)
        elif isinstance(first_cls, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(first_cls.name)
        else:
            assert_never(first_cls)

        an_instance_variable = csharp_naming.variable_name(Identifier("an_instance"))

        writer.write(
            f"""\
/// <example>
/// Here is an example how to serialize an instance of {cls_name}:
/// <code>
/// var {an_instance_variable} = new Aas.{cls_name}(
///     // ... some constructor arguments ...
/// );
/// System.Text.Json.Nodes.JsonObject element = (
/// {I}Serialize.ToJsonObject(
/// {II}{an_instance_variable}));
/// </code>
/// </example>
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

    writer.write("\n}  // public static class Serialize")

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
    namespace: csharp_common.NamespaceIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code for the general serialization.

    The ``namespace`` defines the AAS C# namespace.
    """
    errors = []  # type: List[Error]

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
/// <summary>
/// Represent a critical error during the deserialization.
/// </summary>
public class Exception : System.Exception
{{
{I}public readonly string Path;
{I}public readonly string Cause;
{I}public Exception(string path, string cause)
{II}: base($"{{cause}} at: {{path}}")
{I}{{
{II}Path = path;
{II}Cause = cause;
{I}}}
}}"""
    )

    jsonization_blocks = [
        deserialize_impl_block,
        exception_block,
        deserialize_block,
        transformer_block,
        serialize_block,
    ]  # type: List[Stripped]

    jsonization_writer = io.StringIO()
    jsonization_writer.write(
        f"""\
namespace {namespace}
{{
{I}/// <summary>
{I}/// Provide de/serialization of meta-model classes to/from JSON.
{I}/// </summary>
{I}/// <remarks>
{I}/// We can not use one-pass deserialization for JSON since the object
{I}/// properties do not have fixed order, and hence we can not read
{I}/// <c>modelType</c> property ahead of the remaining properties.
{I}/// </remarks>
{I}public static class Jsonization
{I}{{
"""
    )

    for i, deserialize_block in enumerate(jsonization_blocks):
        if i > 0:
            jsonization_writer.write("\n\n")

        jsonization_writer.write(textwrap.indent(deserialize_block, II))

    jsonization_writer.write(f"\n{I}}}  // public static class Jsonization")
    jsonization_writer.write(f"\n}}  // namespace {namespace}")

    # pylint: disable=line-too-long
    blocks = [
        csharp_common.WARNING,
        Stripped(
            """\
using Nodes = System.Text.Json.Nodes;
using System.Collections.Generic;  // can't alias"""
        ),
        Stripped(f"using Aas = {namespace};"),
        Stripped(jsonization_writer.getvalue()),
        csharp_common.WARNING,
    ]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None
