"""Generate C# code for XML-ization based on the intermediate representation."""

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


def _generate_skip_whitespace_and_comments() -> Stripped:
    """Generate the function to skip whitespace text and XML comments."""
    return Stripped(
        f"""\
internal static void SkipWhitespaceAndComments(
{I}Xml.XmlReader reader)
{{
{I}while (
{II}!reader.EOF
{II}&& reader.NodeType == Xml.XmlNodeType.Whitespace
{II}&& reader.NodeType == Xml.XmlNodeType.Comment)
{I}{{
{II}reader.Read();
{I}}}
}}"""
    )


def _generate_read_whole_content_as_base_64() -> Stripped:
    """Generate the function to skip whitespace text and XML comments."""
    return Stripped(
        f"""\
/// <summary>
/// Read the whole content of an element into memory.
/// </summary>
private static byte[] ReadWholeContentAsBase64(
{I}Xml.XmlReader reader)
{{
{I}// The capacity of 1024 bytes is an arbitrary,
{I}// but plausible default capacity.
{I}byte[] buffer = new byte[1024];
{I}using System.IO.MemoryStream stream = (
{II}new System.IO.MemoryStream(1024));
{I}int readBytes;
{I}while ((readBytes = reader.ReadContentAsBase64(buffer, 0, 1024)) > 0)
{I}{{
{II}stream.Write(buffer, 0, readBytes);
{I}}}
{I}return stream.ToArray();
}}"""
    )


def _generate_deserialize_primitive_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` of primitive type."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        a_type = type_anno.a_type
    elif isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.symbol, intermediate.ConstrainedPrimitive
    ):
        a_type = type_anno.symbol.constrainee
    else:
        raise AssertionError(f"Unexpected type annotation: {prop.type_annotation}")

    deserialization_expr = None  # type: Optional[str]
    if a_type is intermediate.PrimitiveType.BOOL:
        deserialization_expr = "reader.ReadContentAsBoolean()"
    elif a_type is intermediate.PrimitiveType.INT:
        deserialization_expr = "reader.ReadContentAsLong()"
    elif a_type is intermediate.PrimitiveType.FLOAT:
        deserialization_expr = "reader.ReadContentAsDouble()"
    elif a_type is intermediate.PrimitiveType.STR:
        deserialization_expr = "reader.ReadContentAsString()"
    elif a_type is intermediate.PrimitiveType.BYTEARRAY:
        deserialization_expr = f"""\
DeserializeImplementation.ReadWholeContentAsBase64(
{I}reader)"""
    else:
        assert_never(a_type)

    assert deserialization_expr is not None

    target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))

    prop_name = csharp_naming.property_name(prop.name)
    cls_name = csharp_naming.class_name(cls.name)
    xml_prop_name_literal = csharp_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
try
{{
{I}{target_var} = {indent_but_first_line(deserialization_expr, I)};
}}
catch (System.FormatException exception)
{{
{I}error = new Reporting.Error(
{II}"The property {prop_name} of an instance of class {cls_name} " +
{II}$"could not be de-serialized: {{exception}}");
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}"""
    )


def _generate_deserialize_enumeration_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as an enum."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    symbol = type_anno.symbol
    assert isinstance(symbol, intermediate.Enumeration)

    target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))
    text_var = csharp_naming.variable_name(Identifier(f"text_{prop.name}"))

    prop_name = csharp_naming.property_name(prop.name)
    cls_name = csharp_naming.class_name(cls.name)
    enum_name = csharp_naming.enum_name(symbol.name)
    xml_prop_name_literal = csharp_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
string {text_var};
try
{{
{I}{text_var} = reader.ReadContentAsString();
}}
catch (System.FormatException exception)
{{
{I}error = new Reporting.Error(
{II}"The property {prop_name} of an instance of class {cls_name} " +
{II}$"could not be de-serialized as a string: {{exception}}");
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}

{target_var} = Stringification.{enum_name}FromString(
{I}{text_var});

if ({target_var} == null)
{{
{I}error = new Reporting.Error(
{II}"The property {prop_name} of an instance of class {cls_name} " +
{II}"could not be de-serialized from an unexpected enumeration literal: " +
{II}{text_var});
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}"""
    )


def _generate_deserialize_interface_property(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as an interface."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    symbol = type_anno.symbol
    assert isinstance(symbol, (intermediate.AbstractClass, intermediate.ConcreteClass))
    assert symbol.interface is not None

    interface_name = csharp_naming.interface_name(symbol.interface.name)

    target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))
    xml_prop_name_literal = csharp_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
{target_var} = {interface_name}FromElement(
{I}reader,
{I}out error);

if (error != null)
{{
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}"""
    )


def _generate_deserialize_cls_property(prop: intermediate.Property) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as a concrete class."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    symbol = type_anno.symbol
    assert isinstance(symbol, intermediate.ConcreteClass)

    cls_name = csharp_naming.class_name(symbol.name)

    target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))
    xml_prop_name_literal = csharp_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
{target_var} = {cls_name}FromSequence(
{I}reader,
{I}out error);

if (error != null)
{{
{I}error._pathSegments.AddFirst(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}"""
    )


def _generate_deserialize_list_property(prop: intermediate.Property) -> Stripped:
    """Generate the code to de-serialize a property ``prop`` as a list."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # fmt: off
    assert (
        isinstance(type_anno, intermediate.ListTypeAnnotation)
        and isinstance(type_anno.items, intermediate.OurTypeAnnotation)
        and isinstance(
            type_anno.items.symbol,
            (intermediate.AbstractClass, intermediate.ConcreteClass)
        )
    ), "See intermediate._translate._verify_only_simple_type_patterns"
    # fmt: on

    target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))
    index_var = csharp_naming.variable_name(Identifier(f"index_{prop.name}"))

    item_symbol = type_anno.items.symbol
    if (
        isinstance(item_symbol, intermediate.AbstractClass)
        or len(item_symbol.concrete_descendants) > 0
    ):
        deserialize_method = (
            f"{csharp_naming.interface_name(type_anno.items.symbol.name)}FromElement"
        )
    else:
        deserialize_method = (
            f"{csharp_naming.class_name(type_anno.items.symbol.name)}FromElement"
        )

    item_type = csharp_common.generate_type(type_anno.items)

    return Stripped(
        f"""\
SkipWhitespaceAndComments(reader);
{target_var} = new List<{item_type}>();

int {index_var} = 0;
while (reader.NodeType == Xml.XmlNodeType.Element)
{{
{I}{item_type}? item = {deserialize_method}(
{II}reader,
{II}out error);

{I}if (error != null)
{I}{{
{II}error._pathSegments.AddFirst(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}return null;
{I}}}

{I}{target_var}.Add(
{II}item
{III}?? throw new System.InvalidOperationException(
{IIII}"Unexpected item null when error null"));

{I}{index_var}++;
{I}SkipWhitespaceAndComments(reader);
}}"""
    )


@require(lambda prop, cls: id(prop) in cls.property_id_set)
def _generate_deserialize_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the snippet to deserialize the property ``prop`` from the content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    prop_name = csharp_naming.property_name(prop.name)
    cls_name = csharp_naming.class_name(cls.name)

    blocks = [
        Stripped(
            f"""\
if (reader.EOF)
{{
{I}error = new Reporting.Error(
{II}"Expected an XML content representing " +
{II}"the property {prop_name} of an instance of class {cls_name}, " +
{II}"but reached the end-of-file");
{I}return null;
}}"""
        )
    ]  # type: List[Stripped]

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        blocks.append(_generate_deserialize_primitive_property(prop=prop, cls=cls))
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        symbol = type_anno.symbol
        if isinstance(symbol, intermediate.Enumeration):
            blocks.append(
                _generate_deserialize_enumeration_property(prop=prop, cls=cls)
            )
        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-04-13):
            # The constrained primitives are only verified, but not represented as
            # separate classes in the XSD.
            blocks.append(_generate_deserialize_primitive_property(prop=prop, cls=cls))
        elif isinstance(
            symbol, (intermediate.ConcreteClass, intermediate.AbstractClass)
        ):
            if (
                isinstance(symbol, intermediate.AbstractClass)
                or len(symbol.concrete_descendants) > 0
            ):
                blocks.append(_generate_deserialize_interface_property(prop=prop))
            else:
                blocks.append(_generate_deserialize_cls_property(prop=prop))
        else:
            assert_never(symbol)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        blocks.append(_generate_deserialize_list_property(prop=prop))

    else:
        assert_never(type_anno)

    return Stripped("\n\n".join(blocks)), None


def _generate_deserialize_impl_cls_from_sequence(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the function to de-serialize the ``cls`` from an XML sequence."""
    errors = []  # type: List[Error]

    name = csharp_naming.class_name(identifier=cls.name)

    blocks = [
        Stripped("error = null;"),
    ]  # type: List[Stripped]

    if len(cls.constructor.arguments) == 0:
        blocks.append(Stripped(f"return new Aas.{name}();"))
    else:
        init_target_var_stmts = []  # type: List[Stripped]
        for prop in cls.properties:
            target_type = csharp_common.generate_type(prop.type_annotation)
            target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))

            # NOTE (mristin, 2022-04-13):
            # This is a poor man's trick to make all temporary variables optional.
            # The required constructor arguments / properties will be checked just
            # before the constructor as we can not predict in advance which properties
            # were actually provided without any lookahead in XML reading.
            if not target_type.endswith("?"):
                target_type = Stripped(f"{target_type}?")

            init_target_var_stmts.append(
                Stripped(f"{target_type} {target_var} = null;")
            )
        blocks.append(Stripped("\n".join(init_target_var_stmts)))

        blocks.append(
            Stripped(
                f"""\
SkipWhitespaceAndComments(reader);
if (reader.EOF)
{{
{I}error = new Reporting.Error(
{II}"Expected an XML element representing " +
{II}"a property of an instance of class {name}, " +
{II}"but reached the end-of-file");
{I}return null;
}}"""
            )
        )

        case_blocks = []  # type: List[Stripped]
        for prop in cls.properties:
            case_body, error = _generate_deserialize_property(prop=prop, cls=cls)
            if error is not None:
                errors.append(error)
                continue

            assert case_body is not None

            xml_prop_name = naming.xml_property(prop.name)
            xml_prop_name_literal = csharp_common.string_literal(xml_prop_name)
            case_blocks.append(
                Stripped(
                    f"""\
case {xml_prop_name_literal}:
{{
{I}{indent_but_first_line(case_body, I)}
{I}break;
}}"""
                )
            )

        if len(errors) > 0:
            return None, errors

        case_blocks.append(
            Stripped(
                f"""\
default:
{I}error = new Reporting.Error(
{II}"We expected properties of the class {name}, " +
{II}"but got an unexpected element " +
{II}$"with the name {{reader.Name}}");
{I}return null;"""
            )
        )

        switch_body = "\n".join(case_blocks)

        blocks.append(
            Stripped(
                f"""\
while (reader.NodeType == Xml.XmlNodeType.Element)
{{
{I}string elementName = reader.Name;
{I}// Skip the expected start node
{I}reader.Read();
{I}switch (elementName)
{I}{{
{II}{indent_but_first_line(switch_body, II)}
{I}}}
{I}SkipWhitespaceAndComments(reader);
{I}if (reader.EOF)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected an XML end element to conclude a property of class {name} " +
{III}$"with the element name {{elementName}}, " +
{III}$"but got the end-of-file.");
{I}}}
{I}if (reader.NodeType != Xml.XmlNodeType.EndElement)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected an XML end element to conclude a property of class {name} " +
{III}$"with the element name {{elementName}}, " +
{III}$"but got the node of type {{reader.NodeType}} " +
{III}$"with the value {{reader.Value}}");
{I}}}
{I}if (reader.Name != elementName)
{I}{{
{II}error = new Reporting.Error(
{III}$"Expected an XML end element to conclude a property of class {name} " +
{III}$"with the element name {{elementName}}, " +
{III}$"but got the end element with the name {{reader.Name}}");
{I}}}
{I}// Skip the expected end element
{I}reader.Read();
{I}if (reader.EOF)
{I}{{
{II}break;
{I}}}
{I}SkipWhitespaceAndComments(reader);
}}"""
            )
        )

        # region Check that the mandatory properties have been set

        for prop in cls.properties:
            prop_csharp = csharp_naming.property_name(prop.name)
            target_var = csharp_naming.variable_name(Identifier(f"the_{prop.name}"))

            if not isinstance(
                prop.type_annotation, intermediate.OptionalTypeAnnotation
            ):
                blocks.append(
                    Stripped(
                        f"""\
if ({target_var} == null)
{{
{I}error = new Reporting.Error(
{II}"The required property {prop_csharp} has not been given " +
{II}"in the XML representation of an instance of class {name}");
{I}return null;
}}"""
                    )
                )

        # endregion

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

            # NOTE (mristin, 2022-04-13):
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
/// Deserialize an instance of class {name} from a sequence of XML elements.
/// </summary>
internal static Aas.{name}? {name}FromSequence(
{I}Xml.XmlReader reader,
{I}out Reporting.Error? error)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}  // internal static Aas.{name}? {name}FromSequence")

    return Stripped(writer.getvalue()), None


def _generate_deserialize_impl_concrete_cls_from_element(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Generate the function to de-serialize a concrete ``cls`` from an XML element."""
    name = csharp_naming.class_name(cls.name)
    xml_name = naming.xml_class_name(cls.name)
    xml_name_literal = csharp_common.string_literal(xml_name)

    body = Stripped(
        f"""\
error = null;

SkipWhitespaceAndComments(reader);

if (reader.EOF)
{{
{I}error = new Reporting.Error(
{II}"Expected an XML element representing an instance of class {name}, " +
{II}"but reached the end-of-file");
{I}return null;
}}

if (reader.NodeType != Xml.XmlNodeType.Element)
{{
{I}error = new Reporting.Error(
{II}$"Expected an XML element representing an instance of class {name}, " +
{II}$"but got a node of type {{reader.NodeType}} " +
{II}$"with value {{reader.Value}}");
{I}return null;
}}

if (reader.Name != {xml_name_literal})
{{
{I}error = new Reporting.Error(
{II}"Expected an element representing an instance of class {name} " +
{II}$"with element name {xml_name}, but got: {{reader.Name}}");
{I}return null;
}}

// Skip the element node and go to the content
reader.Read();

Aas.{name}? result = (
{I}{name}FromSequence(
{II}reader,
{II}out error));
if (error != null)
{{
    return null;
}}

SkipWhitespaceAndComments(reader);

if (reader.EOF)
{{
{I}error = new Reporting.Error(
{II}"Expected an XML end element concluding an instance of class {name}, " +
{II}"but reached the end-of-file");
{I}return null;
}}

if (reader.NodeType != Xml.XmlNodeType.EndElement)
{{
{I}error = new Reporting.Error(
{II}$"Expected an XML end element concluding an instance of class {name}, " +
{II}$"but got a node of type {{reader.NodeType}} " +
{II}$"with value {{reader.Value}}");
{I}return null;
}}

return result;"""
    )

    return Stripped(
        f"""\
/// <summary>
/// Deserialize an instance of class {name} from an XML element.
/// </summary>
internal static Aas.{name}? {name}FromElement(
{I}Xml.XmlReader reader,
{I}out Reporting.Error? error)
{{
{I}{indent_but_first_line(body, I)}
}}  // internal static Aas.{name}? {name}FromElement"""
    )


def _generate_deserialize_impl_interface_from_element(
    interface: intermediate.Interface,
) -> Stripped:
    """Generate the function to de-serialize an ``interface`` from an XML element."""
    name = csharp_naming.interface_name(interface.name)

    blocks = [
        Stripped(
            f"""\
error = null;

SkipWhitespaceAndComments(reader);

if (reader.EOF)
{{
{I}error = new Reporting.Error(
{II}"Expected an XML element, but reached end-of-file");
{I}return null;
}}

if (reader.NodeType != Xml.XmlNodeType.Element)
{{
{I}error = new Reporting.Error(
{II}$"Expected an XML element, " +
{II}$"but got a node of type {{reader.NodeType}} " +
{II}$"with value {{reader.Value}}");
{I}return null;
}}"""
        )
    ]  # type: List[Stripped]

    case_stmts = []  # type: List[Stripped]
    for implementer in interface.implementers:
        implementer_xml_name_literal = csharp_common.string_literal(
            naming.xml_class_name(implementer.name)
        )

        implementer_name = csharp_naming.class_name(implementer.name)

        case_stmts.append(
            Stripped(
                f"""\
case {implementer_xml_name_literal}:
{I}return {implementer_name}FromElement(
{II}reader,
{II}out error);"""
            )
        )

    case_stmts.append(
        Stripped(
            f"""\
default:
{I}error = new Reporting.Error(
{II}$"Unexpected element with the name {{reader.Name}}");
{I}return null;"""
        )
    )

    switch_writer = io.StringIO()
    switch_writer.write(
        """\
switch (reader.Name)
{
        """
    )
    for i, case_stmt in enumerate(case_stmts):
        if i > 0:
            switch_writer.write("\n")
        switch_writer.write(case_stmt)

    switch_writer.write("\n}")

    blocks.append(Stripped(switch_writer.getvalue()))

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Deserialize an instance of class {name} from an XML element.
/// </summary>
internal static Aas.{name}? {name}FromElement(
{I}Xml.XmlReader reader,
{I}out Reporting.Error? error)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}  // internal static Aas.{name}? {name}FromElement")

    return Stripped(writer.getvalue())


def _generate_deserialize_impl(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the implementation for deserialization functions."""
    blocks = [
        _generate_skip_whitespace_and_comments(),
        _generate_read_whole_content_as_base_64(),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            # NOTE (mristin, 2022-04-13):
            # Enumerations are going to be directly deserialized using
            # ``Stringification``.
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-04-13):
            # Constrained primitives are only verified, but do not represent a C# type.
            continue

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if symbol.is_implementation_specific:
                implementation_keys = [
                    specific_implementations.ImplementationKey(
                        f"Xmlization/DeserializeImplementation/"
                        f"{symbol.name}_from_element.cs"
                    ),
                    specific_implementations.ImplementationKey(
                        f"Xmlization/DeserializeImplementation/"
                        f"{symbol.name}_from_sequence.cs"
                    ),
                ]

                for implementation_key in implementation_keys:
                    implementation = spec_impls.get(implementation_key, None)
                    if implementation is None:
                        errors.append(
                            Error(
                                symbol.parsed.node,
                                f"The xmlization snippet is missing "
                                f"for the implementation-specific "
                                f"class {symbol.name}: {implementation_key}",
                            )
                        )
                        continue
                    else:
                        blocks.append(spec_impls[implementation_key])
            else:
                if isinstance(symbol, intermediate.ConcreteClass):
                    (
                        block,
                        generation_errors,
                    ) = _generate_deserialize_impl_cls_from_sequence(cls=symbol)
                    if generation_errors is not None:
                        errors.append(
                            Error(
                                symbol.parsed.node,
                                f"Failed to generate the XML deserialization code "
                                f"for the class {symbol.name}",
                                generation_errors,
                            )
                        )
                    else:
                        assert block is not None
                        blocks.append(block)

                if symbol.interface is not None:
                    blocks.append(
                        _generate_deserialize_impl_interface_from_element(
                            interface=symbol.interface
                        )
                    )

                if isinstance(symbol, intermediate.ConcreteClass):
                    blocks.append(
                        _generate_deserialize_impl_concrete_cls_from_element(cls=symbol)
                    )
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()

    writer.write(
        """\
/// <summary>
/// Implement the deserialization of meta-model classes from XML.
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

    writer.write("\n}  // internal static class DeserializeImplementation")

    return Stripped(writer.getvalue()), None


def _generate_deserialize_from(name: Identifier) -> Stripped:
    """Generate the facade method for deserialization of the class or interface."""
    return Stripped(
        f"""\
/// <summary>
/// Deserialize an instance of class {name} from <paramref name="reader" />.
/// </summary>
/// <param name="reader">Initialized XML reader with cursor set to the element</param>
/// <exception cref="Xmlization.Exception">
/// Thrown when <paramref name="node" /> is not a valid XML
/// representation of {name}.
/// </exception>
public static Aas.{name} {name}From(
{I}Xml.XmlReader reader)
{{
{I}Aas.{name}? result = (
{II}DeserializeImplementation.{name}FromElement(
{III}reader,
{III}out Reporting.Error? error));
{I}if (error != null)
{I}{{
{II}throw new Xmlization.Exception(
{III}Reporting.GenerateRelativeXPath(error.PathSegments),
{III}error.Cause);
{I}}}
{I}return result
{II}?? throw new System.InvalidOperationException(
{III}"Unexpected output null when error is null");
}}"""
    )


def _generate_deserialize(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the public class ``Deserialize``."""

    blocks = []  # type: List[Stripped]
    for symbol in symbol_table.symbols:
        if isinstance(symbol, intermediate.Enumeration):
            # NOTE (mristin, 2022-04-13):
            # We use stringification for de-serialization of enumerations.
            continue

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-04-13):
            # Constrained primitives are not handled as separate classes, but as
            # primitives, and only verified in the verification.
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
/// Deserialize instances of meta-model classes from XML.
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
/// Here is an example how to parse an instance of class {cls_name}:
/// <code>
/// var reader = new System.Xml.XmlReader(/* some arguments */);
/// Aas.{cls_name} {an_instance_variable} = Deserialize.{cls_name}From(
/// {I}reader);
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


def _generate_serialize_primitive_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of the primitive-type ``prop`` as XML content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        a_type = type_anno.a_type
    elif isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.symbol, intermediate.ConstrainedPrimitive
    ):
        a_type = type_anno.symbol.constrainee
    else:
        raise AssertionError(
            f"Unexpected primitive type " f"of the property {prop.name!r}: {type_anno}"
        )

    prop_name = csharp_naming.property_name(prop.name)
    write_value_block = Stripped(
        f"""\
writer.WriteValue(
{I}that.{prop_name});"""
    )

    if a_type is intermediate.PrimitiveType.BOOL:
        return write_value_block
    elif a_type is intermediate.PrimitiveType.INT:
        return write_value_block
    elif a_type is intermediate.PrimitiveType.FLOAT:
        return write_value_block
    elif a_type is intermediate.PrimitiveType.STR:
        return write_value_block
    elif a_type is intermediate.PrimitiveType.BYTEARRAY:
        stream_var = csharp_naming.variable_name(Identifier(f"stream_{prop_name}"))
        reader_var = csharp_naming.variable_name(Identifier(f"reader_{prop_name}"))

        return Stripped(
            f"""\
using var {stream_var} = new System.IO.MemoryStream(
{I}that.{prop_name});
using var {reader_var} = new System.IO.BinaryReader(
{I}{stream_var});
writer.WriteValue(
{I}{stream_var});"""
        )
    else:
        assert_never(a_type)


def _generate_serialize_enumeration_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of an enumeration ``prop`` as XML content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.symbol, intermediate.Enumeration
    ), "See intermediate._translate._verify_only_simple_type_patterns"

    enumeration = type_anno.symbol

    prop_name = csharp_naming.property_name(prop.name)
    enum_name = csharp_naming.enum_name(enumeration.name)

    text_var = csharp_naming.variable_name(Identifier(f"text_{prop.name}"))
    return Stripped(
        f"""\
string? {text_var} = Stringification.ToString(
{I}that.{prop_name});
writer.WriteValue(
{I}{text_var}
{II}?? throw new System.ArgumentException(
{III}"Invalid literal for the enumeration {enum_name}: " +
{III}that.{prop_name}.ToString()));"""
    )


def _generate_serialize_interface_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of an interface as XML content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # fmt: off
    assert (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and (
            isinstance(type_anno.symbol, intermediate.AbstractClass)
            or (
                isinstance(type_anno.symbol, intermediate.ConcreteClass)
                and len(type_anno.symbol.concrete_descendants) > 0
            )
        )
    ), "See intermediate._translate._verify_only_simple_type_patterns"
    # fmt: on

    prop_name = csharp_naming.property_name(prop.name)

    return Stripped(
        f"""\
this.Visit(
{I}that.{prop_name},
{I}writer);"""
    )


def _generate_serialize_concrete_class_property_as_sequence(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of the class ``prop`` as a sequence of properties."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation)
    assert isinstance(type_anno.symbol, intermediate.ConcreteClass)

    cls_to_sequence = csharp_naming.method_name(
        Identifier(f"{type_anno.symbol.name}_to_sequence")
    )

    prop_name = csharp_naming.property_name(prop.name)

    return Stripped(
        f"""\
this.{cls_to_sequence}(
{I}that.{prop_name},
{I}writer);"""
    )


def _generate_serialize_list_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of a list ``prop`` as a sequence of elements."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # fmt: off
    assert (
        isinstance(type_anno, intermediate.ListTypeAnnotation)
        and isinstance(type_anno.items, intermediate.OurTypeAnnotation)
        and isinstance(
            type_anno.items.symbol,
            (intermediate.AbstractClass, intermediate.ConcreteClass)
        )
    ), "See intermediate._translate._verify_only_simple_type_patterns"
    # fmt: on

    prop_name = csharp_naming.property_name(prop.name)
    return Stripped(
        f"""\
foreach (var item in that.{prop_name})
{{
{I}this.Visit(
{II}item,
{II}writer);
}}"""
    )


def _generate_serialize_property_as_content(prop: intermediate.Property) -> Stripped:
    """Generate the code to serialize the ``prop`` as content of an XML element."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    body = None  # type: Optional[Stripped]

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        body = _generate_serialize_primitive_property_as_content(prop=prop)
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        symbol = type_anno.symbol

        if isinstance(symbol, intermediate.Enumeration):
            body = _generate_serialize_enumeration_property_as_content(prop=prop)

        elif isinstance(symbol, intermediate.ConstrainedPrimitive):
            body = _generate_serialize_primitive_property_as_content(prop=prop)

        elif isinstance(
            symbol, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if (
                isinstance(symbol, intermediate.AbstractClass)
                or len(symbol.concrete_descendants) > 0
            ):
                body = _generate_serialize_interface_property_as_content(prop=prop)
            else:
                body = _generate_serialize_concrete_class_property_as_sequence(
                    prop=prop
                )

        else:
            assert_never(symbol)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        body = _generate_serialize_list_property_as_content(prop=prop)

    else:
        assert_never(type_anno)

    xml_prop_name_literal = csharp_common.string_literal(naming.xml_property(prop.name))
    return Stripped(
        f"""\
writer.WriteStartElement(
{I}{xml_prop_name_literal});
{body}
writer.WriteEndElement();"""
    )


def _generate_class_to_sequence(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the method to write ``cls`` as a sequence of properties as XML."""
    blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        body = _generate_serialize_property_as_content(prop=prop)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            prop_name = csharp_naming.property_name(prop.name)
            body = Stripped(
                f"""\
if (that.{prop_name} != null)
{{
{I}{indent_but_first_line(body, I)}
}}"""
            )
        else:
            pass

        blocks.append(body)

    cls_name = csharp_naming.class_name(cls.name)
    method_name = csharp_naming.method_name(Identifier(f"{cls.name}_to_sequence"))

    writer = io.StringIO()
    writer.write(
        f"""\
private void {method_name}(
{I}{cls_name} that,
{I}Xml.XmlWriter writer)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}  // private void {method_name}")

    return Stripped(writer.getvalue())


def _generate_visit_for_class(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the method to write the ``cls`` as an XML element."""
    cls_name = csharp_naming.class_name(cls.name)
    xml_cls_name_literal = csharp_common.string_literal(naming.xml_class_name(cls.name))

    return Stripped(
        f"""\
public override void Visit(
{I}Aas.{cls_name} that,
{I}Xml.XmlWriter writer)
{{
{I}writer.WriteStartElement(
{II}{xml_cls_name_literal});
{I}this.{cls_name}ToSequence(
{II}that,
{II}writer);
{I}writer.WriteEndElement();
}}"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_visitor(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a visitor which serializes instances of the meta-model to XML."""
    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

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
                implementation_keys = [
                    specific_implementations.ImplementationKey(
                        f"Xmlization/VisitorWithWriter/visit_{symbol.name}.cs"
                    ),
                    specific_implementations.ImplementationKey(
                        f"Xmlization/VisitorWithWriter/{symbol.name}_to_sequence.cs"
                    ),
                ]

                for implementation_key in implementation_keys:
                    implementation = spec_impls.get(implementation_key, None)
                    if implementation is None:
                        errors.append(
                            Error(
                                symbol.parsed.node,
                                f"The xmlization snippet is missing "
                                f"for the implementation-specific "
                                f"class {symbol.name}: {implementation_key}",
                            )
                        )
                        continue

                    blocks.append(spec_impls[implementation_key])
            else:
                blocks.append(_generate_class_to_sequence(cls=symbol))

                blocks.append(_generate_visit_for_class(cls=symbol))
        else:
            assert_never(symbol)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Serialize recursively the instances as XML elements.
/// </summary>
internal class VisitorWithWriter
{I}: Visitation.AbstractVisitorWithContext<Xml.XmlWriter>
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // internal class VisitorWithWriter")

    return Stripped(writer.getvalue()), None


def _generate_serialize(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the static serializer."""
    blocks = [
        Stripped(
            f"""\
private static VisitorWithWriter _visitorWithWriter = (
{I}new VisitorWithWriter());"""
        ),
        Stripped(
            f"""\
/// <summary>
/// Serialize an instance of the meta-model to XML.
/// </summary>
public static void To(
{I}Aas.IClass that,
{I}Xml.XmlWriter writer)
{{
{I}Serialize._visitorWithWriter.Visit(that, writer);
}}"""
        ),
    ]  # type: List[Stripped]

    writer = io.StringIO()
    writer.write(
        """\
/// <summary>
/// Serialize instances of meta-model classes to XML.
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
///     /* ... some constructor arguments ... */
/// );
/// var writer = new System.Xml.XmlWriter( /* some arguments */ );
/// Serialize.To(
/// {I}{an_instance_variable},
/// {I}writer);
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
    xmlization_blocks = []  # type: List[Stripped]

    errors = []  # type: List[Error]

    deserialize_impl_block, deserialize_impl_errors = _generate_deserialize_impl(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if deserialize_impl_errors is not None:
        errors.extend(deserialize_impl_errors)
    else:
        assert deserialize_impl_block is not None
        xmlization_blocks.append(deserialize_impl_block)

    xmlization_blocks.append(
        Stripped(
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
    )

    xmlization_blocks.append(_generate_deserialize(symbol_table=symbol_table))

    visitor_block, visitor_errors = _generate_visitor(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if visitor_errors is not None:
        errors.extend(visitor_errors)
    else:
        assert visitor_block is not None
        xmlization_blocks.append(visitor_block)

    if len(errors) > 0:
        return None, errors

    xmlization_blocks.append(_generate_serialize(symbol_table=symbol_table))

    xmlization_writer = io.StringIO()
    xmlization_writer.write(
        f"""\
namespace {namespace}
{{
{I}/// <summary>
{I}/// Provide de/serialization of meta-model classes to/from XML.
{I}/// </summary>
{I}public static class Xmlization
{I}{{
"""
    )

    for i, xmlization_block in enumerate(xmlization_blocks):
        if i > 0:
            xmlization_writer.write("\n\n")

        xmlization_writer.write(textwrap.indent(xmlization_block, II))

    xmlization_writer.write(f"\n{I}}}  // public static class Xmlization")
    xmlization_writer.write(f"\n}}  // namespace {namespace}")

    # pylint: disable=line-too-long
    blocks = [
        csharp_common.WARNING,
        Stripped(
            """\
using Xml = System.Xml;
using System.Collections.Generic;  // can't alias"""
        ),
        Stripped(f"using Aas = {namespace};"),
        Stripped(xmlization_writer.getvalue()),
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
