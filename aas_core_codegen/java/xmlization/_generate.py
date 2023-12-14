"""Generate Java code for XML-ization based on the intermediate representation."""
from typing import Tuple, Optional, List

from icontract import ensure, require

from aas_core_codegen import intermediate, naming, specific_implementations
from aas_core_codegen.common import (
    assert_never,
    Error,
    Identifier,
    indent_but_first_line,
    Stripped,
)
from aas_core_codegen import (
    intermediate,
    specific_implementations,
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
    INDENT5 as IIIII,
    INDENT6 as IIIIII,
)

# region Generate


def _generate_result() -> Stripped:
    """Generate the class to represent XML de/serialize results."""
    return Stripped(
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
{II}if(result == null) throw new IllegalArgumentException("Result must not be null.");
{II}return new Result<>(result, null, true);
{I}}}

{I}public static <T> Result<T> failure(Reporting.Error error) {{
{II}if(error == null) throw new IllegalArgumentException("Error must not be null.");
{II}return new Result<>(null, error, false);
{I}}}

{I}public T getResult() {{
{II}if (!isSuccess()) throw new IllegalStateException("Result is not present.");
{II}return result;
{I}}}

{I}public boolean isSuccess() {{
{II}return success;
{I}}}

{I}public boolean isError(){{return !success;}}

{I}public Reporting.Error getError() {{
{II}if (isSuccess()) throw new IllegalStateException("Result is present.");
{II}return error;
{I}}}

{I}public <R> R map(Function<T, R> successFunction, Function<Reporting.Error, R> errorFunction) {{
{II}return isSuccess() ? successFunction.apply(result) : errorFunction.apply(error);
{I}}}

{I}public T onError(Function<Reporting.Error, T>  errorFunction){{
{II}return map(Function.identity(),errorFunction);
{I}}}
}}"""
    )


def _generate_current_event() -> Stripped:
    """Generate the function to a single XML event."""

    return Stripped(
        f"""\
private static XMLEvent currentEvent(XMLEventReader reader) {{
{I}try {{
{II}return reader.peek();
{I}}} catch (XMLStreamException xmlStreamException) {{
{II}throw new DeserializeException("", "Failed in method peek because of: " + xmlStreamException.getMessage());
{I}}}
}}"""
    )


def _generate_try_content() -> Stripped:
    """Generate the function to read textual content."""

    return Stripped(
        f"""\
private static Result<String> tryContent(XMLEventReader reader) {{
{I}final Reporting.Error error;
{I}final StringBuilder content = new StringBuilder();
{I}try {{
{II}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{III}if (reader.peek().isCharacters()) {{
{IIII}content.append(reader.peek().asCharacters().getData());
{III}}}
{III}reader.nextEvent();
{II}}}
{I}}} catch (XMLStreamException exception) {{
{II}error = new Reporting.Error(exception.getMessage());
{II}return Result.failure(error);
{I}}}
{I}return Result.success(content.toString());
}}"""
    )


def _generate_skip_whitespace_and_comments() -> Stripped:
    """Generate the function to skip whitespace text and XML comments."""
    return Stripped(
        f"""\
private static void skipWhitespaceAndComments(XMLEventReader reader){{
{I}while (whiteSpaceOrComment(reader)) {{
{II}reader.next();
{I}}}
}}

private static boolean whiteSpaceOrComment(XMLEventReader reader){{
{I}final XMLEvent currentEvent = currentEvent(reader);
{I}final boolean isComment = (currentEvent != null &&
{II}currentEvent.getEventType() == XMLStreamConstants.COMMENT);
{I}final boolean isWhiteSpace = (currentEvent != null &&
{II}currentEvent.getEventType() == XMLStreamConstants.CHARACTERS &&
{II}currentEvent.asCharacters().isWhiteSpace());
{I}return isComment || isWhiteSpace;
}}"""
    )


def _generate_read_whole_content_as_base_64() -> Stripped:
    """Generate the function to read the whole of element's content as bytes."""
    return Stripped(
        f"""\
/**
 * Read the whole content of an element into memory.
 */
private static Result<byte[]> readWholeContentAsBase64(
{I}XMLEventReader reader) {{
{I}final StringBuilder content = new StringBuilder();
{I}try {{
{II}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{III}if (reader.peek().isCharacters()) {{
{IIII}content.append(reader.peek().asCharacters().getData());
{III}}}
{III}reader.nextEvent();
{II}}}
{I}}} catch (XMLStreamException exception) {{
{II}return Result.failure(
{III}new Reporting.Error(exception.getMessage()));
{I}}}

{I}String encodedData = content.toString();
{I}final byte[] decodedData;
{I}Base64.Decoder decoder = Base64.getDecoder();
{I}try {{
{II}decodedData = decoder.decode(encodedData);
{I}}} catch (IllegalArgumentException exception) {{
{II}return Result.failure(
{III}new Reporting.Error(exception.getMessage()));
{I}}}
{I}return Result.success(decodedData);
}}"""
    )


def _generate_get_event_type_as_string() -> Stripped:
    """Generate the function to map XML event types to their string representations."""

    return Stripped(
        f"""\
private static String getEventTypeAsString(XMLEvent event) {{
{I}switch (event.getEventType()) {{
{II}case XMLStreamConstants.START_ELEMENT:
{III}return "Start-Element";
{II}case XMLStreamConstants.END_ELEMENT:
{III}return "End-Element";
{II}case XMLStreamConstants.PROCESSING_INSTRUCTION:
{III}return "Processing-Instruction";
{II}case XMLStreamConstants.CHARACTERS:
{III}return "Characters";
{II}case XMLStreamConstants.COMMENT:
{III}return "Comment";
{II}case XMLStreamConstants.SPACE:
{III}return "Space";
{II}case XMLStreamConstants.START_DOCUMENT:
{III}return "Start-Document";
{II}case XMLStreamConstants.END_DOCUMENT:
{III}return "End-Document";
{II}case XMLStreamConstants.ENTITY_REFERENCE:
{III}return "Entity-Reference";
{II}case XMLStreamConstants.ATTRIBUTE:
{III}return "Attribute";
{II}case XMLStreamConstants.NOTATION_DECLARATION:
{III}return "Notation-Declaration";
{II}default:
{III}return "Unknown-Type";
{I}}}
}}"""
    )


def _generate_try_element_name() -> Stripped:
    """Generate the function to strip the prefix and check the namespace."""
    return Stripped(
        f"""\
private static boolean invalidNameSpace(XMLEvent event) {{
{I}if (event.isStartElement()) {{
{II}return !AAS_NAME_SPACE.equals(event.asStartElement().getName().getNamespaceURI());
{I}}} else {{
{II}return !AAS_NAME_SPACE.equals(event.asEndElement().getName().getNamespaceURI());
{I}}}
}}


/**
 * Check the namespace and extract the element's name.
 */
private static Result<String> tryElementName(XMLEventReader reader){{
{I}final XMLEvent currentEvent = currentEvent(reader);
{I}final boolean precondition = currentEvent.isStartElement() || currentEvent.isEndElement();
{I}if (!precondition) {{
{II}throw new IllegalStateException("Expected to be at a start or an end element "
{IIII}+ "but got: " + getEventTypeAsString(currentEvent));
{I}}}

{I}if (invalidNameSpace(currentEvent)) {{
{II}String namespace = currentEvent.isStartElement()
{IIII}? currentEvent.asStartElement().getName().getNamespaceURI()
{IIII}: currentEvent.asEndElement().getName().getNamespaceURI();
{II}final Reporting.Error error = new Reporting.Error("Expected an element within a namespace " + AAS_NAME_SPACE + ", "
{IIII}+ "but got: " + namespace);
{II}return Result.failure(error);
{I}}}
{I}return Result.success(currentEvent.isStartElement()
{III}? currentEvent.asStartElement().getName().getLocalPart()
{III}: currentEvent.asEndElement().getName().getLocalPart());
}}"""
    )


def _generate_verify_closing_tag_for_class() -> Stripped:
    return Stripped(
        f"""\
private static boolean isWrongClosingTag(
{I}Result<String> tryElementName,
{I}Result<String> tryEndElementName) {{
{I}return !tryElementName.getResult().equals(tryEndElementName.getResult());
}}

private static Result<XMLEvent> verifyClosingTagForClass(
{I}String className,
{I}XMLEventReader reader,
{I}Result<String> tryElementName) {{
{I}final Reporting.Error error;
{I}final XMLEvent currentEvent = currentEvent(reader);
{I}if (currentEvent.isEndDocument()) {{
{II}error = new Reporting.Error(
{IIII}"Expected an XML end element to conclude a property of class " + className
{IIIIII}+ " with the element name " + tryElementName.getResult() + ", "
{IIIIII}+ "but got the end-of-file.");
{II}return Result.failure(error);
{I}}}

{I}if (!currentEvent.isEndElement()) {{
{II}error = new Reporting.Error(
{IIII}"Expected an XML end element to conclude a property of class " + className
{IIIIII}+ " with the element name " + tryElementName.getResult() + ", "
{IIIIII}+ "but got the node of type " + getEventTypeAsString(currentEvent)
{IIIIII}+ " with the value " + currentEvent);
{II}return Result.failure(error);
{I}}}
{I}final Result<String> tryEndElementName = tryElementName(reader);
{I}if (tryEndElementName.isError()) {{
{II}return Result.failure(tryEndElementName.getError());
{I}}}
{I}if (isWrongClosingTag(tryElementName, tryEndElementName)) {{
{II}error = new Reporting.Error(
{IIII}"Expected an XML end element to conclude a property of class ConceptDescription " + className
{IIIIII}+ " with the element name " + tryElementName.getResult() + ", "
{IIIIII}+ "but got the end element with the name " + tryEndElementName.getResult());
{II}return Result.failure(error);
{I}}}
{I}try {{
{II}return Result.success(reader.nextEvent());
{I}}} catch (XMLStreamException xmlStreamException) {{
{II}throw new DeserializeException("",
{III}"Failed in method verifyClosingTagForClass because of: " +
{III}xmlStreamException.getMessage());
{I}}}
}}"""
    )


def _generate_deserialize_primitive_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` of primitive type."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    a_type = intermediate.try_primitive_type(type_anno)
    assert a_type is not None, f"Unexpected type annotation: {prop.type_annotation}"

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

    target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))

    prop_name = java_naming.property_name(prop.name)
    cls_name = java_naming.class_name(cls.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    if a_type is intermediate.PrimitiveType.STR:
        empty_handling_body = Stripped(f'{target_var} = "";')
    else:
        empty_handling_body = Stripped(
            f"""\
error = new Reporting.Error(
{I}"The property {prop_name} of an instance of class {cls_name} " +
{I}"can not be de-serialized from a self-closing element " +
{I}"since it needs content");
error.PrependSegment(
{I}new Reporting.NameSegment(
{II}{xml_prop_name_literal}));
return null;"""
        )

    return Stripped(
        f"""\
if (isEmptyProperty)
{{
{I}{indent_but_first_line(empty_handling_body, I)}
}}
else
{{
{I}if (reader.EOF)
{I}{{
{II}error = new Reporting.Error(
{III}"Expected an XML content representing " +
{III}"the property {prop_name} of an instance of class {cls_name}, " +
{III}"but reached the end-of-file");
{II}return null;
{I}}}

{I}try
{I}{{
{II}{target_var} = {indent_but_first_line(deserialization_expr, I)};
{I}}}
{I}catch (System.Exception exception)
{I}{{
{II}if (exception is System.FormatException
{III}|| exception is System.Xml.XmlException)
{II}{{
{III}error = new Reporting.Error(
{IIII}"The property {prop_name} of an instance of class {cls_name} " +
{IIII}$"could not be de-serialized: {{exception.Message}}");
{III}error.PrependSegment(
{IIII}new Reporting.NameSegment(
{IIIII}{xml_prop_name_literal}));
{III}return null;
{II}}}

{II}throw;
{I}}}
}}"""
    )


def _generate_deserialize_enumeration_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as an enum."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    our_type = type_anno.our_type
    assert isinstance(our_type, intermediate.Enumeration)

    target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))
    text_var = java_naming.variable_name(Identifier(f"text_{prop.name}"))

    prop_name = java_naming.property_name(prop.name)
    cls_name = java_naming.class_name(cls.name)
    enum_name = java_naming.enum_name(our_type.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
if (isEmptyProperty)
{{
{I}error = new Reporting.Error(
{II}"The property {prop_name} of an instance of class {cls_name} " +
{II}"can not be de-serialized from a self-closing element " +
{II}"since it needs content");
{I}error.PrependSegment(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}

{I}if (reader.EOF)
{{
{II}error = new Reporting.Error(
{III}"Expected an XML content representing " +
{III}"the property {prop_name} of an instance of class {cls_name}, " +
{III}"but reached the end-of-file");
{II}return null;
}}

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
{I}error.PrependSegment(
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
{I}error.PrependSegment(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}"""
    )


def _generate_deserialize_interface_property(
    prop: intermediate.Property,
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as an interface."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    our_type = type_anno.our_type
    assert isinstance(
        our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
    )
    assert our_type.interface is not None

    prop_name = java_naming.property_name(prop.name)
    cls_name = java_naming.class_name(cls.name)

    interface_name = java_naming.interface_name(our_type.interface.name)

    target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
if (isEmptyProperty)
{{
{I}error = new Reporting.Error(
{II}$"Expected an XML element within the element {{elementName}} representing " +
{II}"the property {prop_name} of an instance of class {cls_name}, " +
{II}"but encountered a self-closing element {{elementName}}");
{I}return null;
}}

// We need to skip the whitespace here in order to be able to look ahead
// the discriminator element shortly.
SkipNoneWhitespaceAndComments(reader);

if (reader.EOF)
{{
{I}error = new Reporting.Error(
{II}$"Expected an XML element within the element {{elementName}} representing " +
{II}"the property {prop_name} of an instance of class {cls_name}, " +
{II}"but reached the end-of-file");
{I}return null;
}}

// Try to look ahead the discriminator name;
// we need this name only for the error reporting below.
// {interface_name}FromElement will perform more sophisticated
// checks.
string? discriminatorElementName = null;
if (reader.NodeType == Xml.XmlNodeType.Element)
{{
{I}discriminatorElementName = reader.LocalName;
}}

{target_var} = {interface_name}FromElement(
{I}reader, out error);

if (error != null)
{{
{I}if (discriminatorElementName != null)
{I}{{
{II}error.PrependSegment(
{III}new Reporting.NameSegment(
{IIII}discriminatorElementName));
{I}}}

{I}error.PrependSegment(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return null;
}}"""
    )


def _generate_deserialize_cls_property(prop: intermediate.Property) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as a concrete class."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    our_type = type_anno.our_type
    assert isinstance(our_type, intermediate.ConcreteClass)

    target_cls_name = java_naming.class_name(our_type.name)

    target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
{target_var} = {target_cls_name}FromSequence(
{I}reader, isEmptyProperty, out error);

if (error != null)
{{
{I}error.PrependSegment(
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
            type_anno.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass)
        )
    ), "See intermediate._translate._verify_only_simple_type_patterns"
    # fmt: on

    target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))
    index_var = java_naming.variable_name(Identifier(f"index_{prop.name}"))

    item_our_type = type_anno.items.our_type
    if (
        isinstance(item_our_type, intermediate.AbstractClass)
        or len(item_our_type.concrete_descendants) > 0
    ):
        deserialize_method = (
            f"{java_naming.interface_name(type_anno.items.our_type.name)}FromElement"
        )
    else:
        deserialize_method = (
            f"{java_naming.class_name(type_anno.items.our_type.name)}FromElement"
        )

    item_type = java_common.generate_type(type_anno.items)

    xml_prop_name = naming.xml_property(prop.name)
    xml_prop_name_literal = java_common.string_literal(xml_prop_name)

    body_for_non_empty_property = Stripped(
        f"""\
SkipNoneWhitespaceAndComments(reader);

int {index_var} = 0;
while (reader.NodeType == Xml.XmlNodeType.Element)
{{
{I}{item_type}? item = {deserialize_method}(
{II}reader, out error);

{I}if (error != null)
{I}{{
{II}error.PrependSegment(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
error.PrependSegment(
{I}new Reporting.NameSegment(
{II}{xml_prop_name_literal}));
{II}return null;
{I}}}

{I}{target_var}.Add(
{II}item
{III}?? throw new System.InvalidOperationException(
{IIII}"Unexpected item null when error null"));

{I}{index_var}++;
{I}SkipNoneWhitespaceAndComments(reader);
}}"""
    )

    return Stripped(
        f"""\
{target_var} = new List<{item_type}>();

if (!isEmptyProperty)
{{
{I}{indent_but_first_line(body_for_non_empty_property, I)}
}}"""
    )


@require(lambda prop, cls: id(prop) in cls.property_id_set)
def _generate_deserialize_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the snippet to deserialize the property ``prop`` from the content."""
    blocks = []  # type: List[Stripped]

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        blocks.append(_generate_deserialize_primitive_property(prop=prop, cls=cls))
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        our_type = type_anno.our_type
        if isinstance(our_type, intermediate.Enumeration):
            blocks.append(
                _generate_deserialize_enumeration_property(prop=prop, cls=cls)
            )
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-04-13):
            # The constrained primitives are only verified, but not represented as
            # separate classes in the XSD.
            blocks.append(_generate_deserialize_primitive_property(prop=prop, cls=cls))
        elif isinstance(
            our_type, (intermediate.ConcreteClass, intermediate.AbstractClass)
        ):
            if (
                isinstance(our_type, intermediate.AbstractClass)
                or len(our_type.concrete_descendants) > 0
            ):
                blocks.append(
                    _generate_deserialize_interface_property(prop=prop, cls=cls)
                )
            else:
                blocks.append(_generate_deserialize_cls_property(prop=prop))
        else:
            assert_never(our_type)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        blocks.append(_generate_deserialize_list_property(prop=prop))

    else:
        assert_never(type_anno)

    return Stripped("\n\n".join(blocks)), None


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

    The ``package`` defines the root Java package.
    """
    errors = []  # type: List[Error]

    imports = [
        Stripped("import java.util.Base64;"),
        Stripped("import java.util.function.Function;"),
        Stripped("import java.util.Optional;"),
        Stripped("import javax.xml.stream.events.XMLEvent;"),
        Stripped("import javax.xml.stream.XMLEventReader;"),
        Stripped("import javax.xml.stream.XMLStreamConstants;"),
        Stripped("import javax.xml.stream.XMLStreamException;"),
        Stripped(f"import {package}.reporting.Reporting;"),
    ]  # type: List[Stripped]

    xml_result_class = _generate_result()

    xml_current_event = _generate_current_event()

    xml_try_content = _generate_try_content()

    xml_skip_whitespace_and_comments = _generate_skip_whitespace_and_comments()

    xml_read_whole_content_as_base64 = _generate_read_whole_content_as_base_64()

    xml_get_event_type_as_string = _generate_get_event_type_as_string()

    xml_try_element_name = _generate_try_element_name()

    xml_verify_closing_tag_for_class = _generate_verify_closing_tag_for_class()

    xml_namespace_literal = java_common.string_literal(
        symbol_table.meta_model.xml_namespace
    )

    xmlization_blocks = [
        Stripped(
            f"""\
/**
 * Represent a critical error during the deserialization.
 */
class DeserializeException extends RuntimeException{{
{I}private final String path;
{I}private final String reason;

{I}public DeserializeException(String path, String reason) {{
{II}super(reason + " at: " + ("".equals(path) ? "the beginning" : path));
{II}this.path = path;
{II}this.reason = reason;
{I}}}

{I}public Optional<String> getPath() {{
{II}return Optional.ofNullable(path);
{I}}}

{I}public Optional<String> getReason() {{
{II}return Optional.ofNullable(reason);
{I}}}
}}"""
        ),
        Stripped(
            f"""\
/**
 * Provide de/serialization of meta-model classes to/from XML.
 */
public class Xmlization
{{
{I}/**
{I} * The XML namespace of the meta-model
{I} */
{I}public static final String AAS_NAME_SPACE =
{II}{xml_namespace_literal};

{I}{indent_but_first_line(xml_result_class, I)}

{I}{indent_but_first_line(xml_current_event, I)}

{I}{indent_but_first_line(xml_try_content, I)}

{I}{indent_but_first_line(xml_skip_whitespace_and_comments, I)}

{I}{indent_but_first_line(xml_read_whole_content_as_base64, I)}

{I}{indent_but_first_line(xml_get_event_type_as_string, I)}

{I}{indent_but_first_line(xml_try_element_name, I)}

{I}{indent_but_first_line(xml_verify_closing_tag_for_class, I)}
}}"""
        ),
    ]  # type: List[Stripped]

    if len(errors) > 0:
        return None, errors

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.xmlization;"),
        Stripped("\n".join(imports)),
        Stripped("\n\n".join(xmlization_blocks)),
        java_common.WARNING,
    ]  # type: List[Stripped]

    code = "\n\n".join(blocks)

    return f"{code}\n", None


# endregion
