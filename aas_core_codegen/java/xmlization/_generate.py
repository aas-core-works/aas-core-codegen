"""Generate Java code for XML-ization based on the intermediate representation."""
import io
import textwrap

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

{I}public static <T, I> Result<T> failure(Result<I> other) {{
{II}if(other.error == null) throw new IllegalArgumentException("Error must not be null.");
{II}return new Result<>(null, other.error, false);
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
{II}return map(Function.identity(), errorFunction);
{I}}}

{I}public static <I> Result<I> convert(Result<? extends I> result) {{
{II}return new Result<I>(result.result, result.error, result.success);
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
{II}throw new Xmlization.DeserializeException("",
{III}"Failed in method peek because of: " +
{III}xmlStreamException.getMessage());
{I}}}
}}"""
    )


def _generate_try_content_for_primitives() -> Stripped:
    """Generate the function to read textual content."""

    return Stripped(
        f"""\
private static String tryContentAsString(XMLEventReader reader) throws XMLStreamException {{
{I}final StringBuilder content = new StringBuilder();

{I}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{II}if (reader.peek().isCharacters()) {{
{III}content.append(reader.peek().asCharacters().getData());
{II}}}
{II}reader.nextEvent();
{I}}}

{I}return content.toString();
}}

private static Boolean tryContentAsBool(XMLEventReader reader) throws XMLStreamException {{
{I}final StringBuilder content = new StringBuilder();

{I}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{II}if (reader.peek().isCharacters()) {{
{III}content.append(reader.peek().asCharacters().getData());
{II}}}
{II}reader.nextEvent();
{I}}}

{I}return Boolean.valueOf(content.toString());
}}

private static Long tryContentAsLong(XMLEventReader reader) throws XMLStreamException {{
{I}final StringBuilder content = new StringBuilder();

{I}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{II}if (reader.peek().isCharacters()) {{
{III}content.append(reader.peek().asCharacters().getData());
{II}}}
{II}reader.nextEvent();
{I}}}

{I}return Long.valueOf(content.toString());
}}

private static Double tryContentAsDouble(XMLEventReader reader) throws XMLStreamException {{
{I}final StringBuilder content = new StringBuilder();

{I}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{II}if (reader.peek().isCharacters()) {{
{III}content.append(reader.peek().asCharacters().getData());
{II}}}
{II}reader.nextEvent();
{I}}}

{I}return Double.valueOf(content.toString());
}}

/**
 * Read the whole content of an element into memory.
 */
private static byte[] tryContentAsBase64(
{I}XMLEventReader reader) throws XMLStreamException {{
{I}final StringBuilder content = new StringBuilder();
{I}while (reader.peek().isCharacters() || reader.peek().getEventType() == XMLStreamConstants.COMMENT) {{
{II}if (reader.peek().isCharacters()) {{
{III}content.append(reader.peek().asCharacters().getData());
{II}}}
{II}reader.nextEvent();
{I}}}

{I}String encodedData = content.toString();
{I}final byte[] decodedData;
{I}Base64.Decoder decoder = Base64.getDecoder();

{I}try {{
{II}decodedData = decoder.decode(encodedData);
{I}}} catch (IllegalArgumentException exception) {{
{II}throw new XMLStreamException(
{III}"Failed to read base64 encoded data: " +
{III}exception.getMessage());
{I}}}

{I}return decodedData;
}}"""
    )


def _generate_skip_whitespace_and_comments() -> Stripped:
    """Generate the function to skip whitespace text and XML comments."""
    return Stripped(
        f"""\
private static void skipWhitespaceAndComments(XMLEventReader reader) {{
{I}while (whiteSpaceOrComment(reader)) {{
{II}reader.next();
{I}}}
}}

private static boolean whiteSpaceOrComment(XMLEventReader reader) {{
{I}final XMLEvent currentEvent = currentEvent(reader);
{I}final boolean isComment = (currentEvent != null &&
{II}currentEvent.getEventType() == XMLStreamConstants.COMMENT);
{I}final boolean isWhiteSpace = (currentEvent != null &&
{II}currentEvent.getEventType() == XMLStreamConstants.CHARACTERS &&
{II}currentEvent.asCharacters().isWhiteSpace());
{I}return isComment || isWhiteSpace;
}}"""
    )


def _generate_is_empty_element() -> Stripped:
    """Generate the function to check if an element is empty."""
    return Stripped(
        f"""\
private static boolean isEmptyElement(XMLEventReader reader) {{
{I}// Skip the element node and go to the content
{I}try {{
{II}reader.nextEvent();
{I}}} catch (XMLStreamException xmlStreamException) {{
{II}throw new Xmlization.DeserializeException("",
{III}"Failed in method isEmptyElement because of: " +
{III}xmlStreamException.getMessage());
{I}}}
{I}return currentEvent(reader).isEndElement();
}}"""
    )


def _generate_deserialize_primitive_property(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` of primitive type."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    a_type = intermediate.try_primitive_type(type_anno)
    assert a_type is not None, f"Unexpected type annotation: {prop.type_annotation}"

    primitive_name = java_common.generate_type(type_anno)

    deserialization_expr = None  # type: Optional[str]
    if a_type is intermediate.PrimitiveType.BOOL:
        deserialization_expr = "tryContentAsBool(reader)"
    elif a_type is intermediate.PrimitiveType.INT:
        deserialization_expr = "tryContentAsInt(reader)"
    elif a_type is intermediate.PrimitiveType.FLOAT:
        deserialization_expr = "tryContentAsFloat(reader)"
    elif a_type is intermediate.PrimitiveType.STR:
        deserialization_expr = "tryContentAsString(reader)"
    elif a_type is intermediate.PrimitiveType.BYTEARRAY:
        deserialization_expr = "tryContentAsBase64(reader)"
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
final Reporting.Error error = new Reporting.Error(
{I}"The property {prop_name} of an instance of class {cls_name} " +
{I}"can not be de-serialized from a self-closing element " +
{I}"since it needs content");
error.prependSegment(
{I}new Reporting.NameSegment(
{II}{xml_prop_name_literal}));
return Result.failure(error);"""
        )

    return Stripped(
        f"""\
if (isEmptyProperty) {{
{I}{indent_but_first_line(empty_handling_body, I)}
}}
else {{
{I}if (currentEvent(reader).isEndDocument()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected an XML content representing " +
{III}"the property {prop_name} of an instance of class {cls_name}, " +
{III}"but reached the end-of-file");
{II}return Result.failure(error);
{I}}}

{I}try {{
{II}{target_var} = {deserialization_expr};
{I}}} catch (XMLStreamException e) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"The property {target_var} of an instance of class {cls_name} "
{IIII}+ " could not be de-serialized: " + e.getMessage());
{II}error.prependSegment(
{III}new Reporting.NameSegment(
{IIII}"{target_var}"));
{II}return Result.failure(error);
{I}}}
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
private static Result<String> tryElementName(XMLEventReader reader) {{
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
{II}final Reporting.Error error = new Reporting.Error(
{IIII}"Expected an element within a namespace " +
{IIII}AAS_NAME_SPACE + ", " + "but got: " + namespace);
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
{I}final XMLEvent currentEvent = currentEvent(reader);
{I}if (currentEvent.isEndDocument()) {{
{II}final Reporting.Error error = new Reporting.Error(
{IIII}"Expected an XML end element to conclude a property of class " + className
{IIIIII}+ " with the element name " + tryElementName.getResult() + ", "
{IIIIII}+ "but got the end-of-file.");
{II}return Result.failure(error);
{I}}}

{I}if (!currentEvent.isEndElement()) {{
{II}final Reporting.Error error = new Reporting.Error(
{IIII}"Expected an XML end element to conclude a property of class " + className
{IIIIII}+ " with the element name " + tryElementName.getResult() + ", "
{IIIIII}+ "but got the node of type " + getEventTypeAsString(currentEvent)
{IIIIII}+ " with the value " + currentEvent);
{II}return Result.failure(error);
{I}}}
{I}final Result<String> tryEndElementName = tryElementName(reader);
{I}if (tryEndElementName.isError()) {{
{II}return Result.failure(tryEndElementName);
{I}}}
{I}if (isWrongClosingTag(tryElementName, tryEndElementName)) {{
{II}final Reporting.Error error = new Reporting.Error(
{IIII}"Expected an XML end element to conclude a property of class ConceptDescription " + className
{IIIIII}+ " with the element name " + tryElementName.getResult() + ", "
{IIIIII}+ "but got the end element with the name " + tryEndElementName.getResult());
{II}return Result.failure(error);
{I}}}
{I}try {{
{II}return Result.success(reader.nextEvent());
{I}}} catch (XMLStreamException xmlStreamException) {{
{II}throw new Xmlization.DeserializeException("",
{III}"Failed in method verifyClosingTagForClass because of: " +
{III}xmlStreamException.getMessage());
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
    text_target_var = java_naming.variable_name(Identifier(f"text_{prop.name}"))
    optional_target_var = java_naming.variable_name(Identifier(f"optional_{prop.name}"))

    prop_name = java_naming.property_name(prop.name)
    prop_type_name = java_naming.enum_name(our_type.name)
    from_str_name = java_naming.private_property_name(
        Identifier(f"{our_type.name}_from_string")
    )
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
if (isEmptyProperty) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"The property {prop_name} of an instance of class {prop_type_name} " +
{II}"can not be de-serialized from a self-closing element " +
{II}"since it needs content");
{I}error.prependSegment(
{II}new Reporting.NameSegment(
{III}{xml_prop_name_literal}));
{I}return Result.failure(error);
}}

if (currentEvent(reader).isEndDocument()) {{
{I}final Reporting.Error error = new Reporting.Error(
{III}"Expected an XML content representing "
{IIIII}+ "the property {prop_name} of an instance of class {prop_type_name}, "
{IIIII}+ "but reached the end-of-file");
{I}return Result.failure(error);
}}

String {text_target_var};
try {{
{I}{text_target_var} = tryContentAsString(reader);
}} catch (XMLStreamException e) {{
{I}final Reporting.Error error = new Reporting.Error(
{III}"The property {prop_name} of an instance of class {prop_type_name} "
{IIIII}+ " could not be de-serialized: " + e.getMessage());
{I}error.prependSegment(
{III}new Reporting.NameSegment(
{IIIII}"{target_var}"));
{I}return Result.failure(error);
}}

final Optional<{prop_type_name}> {optional_target_var} =
{I}Stringification.{from_str_name}(
{II}{text_target_var});

if ({optional_target_var}.isPresent()) {{
{I}{target_var} = {optional_target_var}.get();
}} else {{
{I}final Reporting.Error error = new Reporting.Error(
{III}"The property {prop_name} of an instance of class {prop_type_name} " +
{IIIII}"could not be de-serialized from an unexpected enumeration literal: " +
{IIIII}{target_var});
{I}error.prependSegment(
{III}new Reporting.NameSegment(
{IIIII}"{target_var}"));
{I}return Result.failure(error);
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
    try_target_var = java_naming.variable_name(Identifier(f"try_{prop.name}"))
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
if (isEmptyProperty) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element within the element " + tryElementName.getResult() + " representing " +
{II}"the property {prop_name} of an instance of class {cls_name}, " +
{II}"but encountered a self-closing element.");
{I}return Result.failure(error);
}}

// We need to skip the whitespace here in order to be able to look ahead
// the discriminator element shortly.
skipWhitespaceAndComments(reader);

if (currentEvent(reader).isEndDocument()) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element within the element " + tryElementName.getResult() + " representing " +
{II}"the property {prop_name} of an instance of class {cls_name}, " +
{II}"but reached the end-of-file");
{I}return Result.failure(error);
}}

// Try to look ahead the discriminator name;
// we need this name only for the error reporting below.
// {interface_name}FromElement will perform more sophisticated
// checks.
String discriminatorElementName = null;
if (currentEvent(reader).isStartElement()) {{
{I}Result<String> tryDiscriminatorElementName = tryElementName(reader);
{I}assert(!tryDiscriminatorElementName.isError());
{I}discriminatorElementName = tryDiscriminatorElementName.getResult();
}}

Result<{interface_name}> {try_target_var} = try{interface_name}FromElement(reader);

if ({try_target_var}.isError()) {{
{I}if (discriminatorElementName != null) {{
{II}{try_target_var}.getError().
{III}prependSegment(
{IIII}new Reporting.NameSegment(
{IIIII}discriminatorElementName));
{I}}}

{I}{try_target_var}.getError()
{II}.prependSegment(
{III}new Reporting.NameSegment(
{IIII}{xml_prop_name_literal}));
{I}return Result.failure({try_target_var});
}}

{target_var} = {try_target_var}.getResult();"""
    )


def _generate_deserialize_cls_property(prop: intermediate.Property) -> Stripped:
    """Generate the snippet to deserialize a property ``prop`` as a concrete class."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    assert isinstance(type_anno, intermediate.OurTypeAnnotation)

    our_type = type_anno.our_type
    assert isinstance(our_type, intermediate.ConcreteClass)

    target_cls_name = java_naming.class_name(our_type.name)

    target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))

    try_target_var = java_naming.variable_name(Identifier(f"try_{prop.name}"))

    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    return Stripped(
        f"""\
Result<{target_cls_name}> {try_target_var} = {target_cls_name}FromSequence(
{I}reader, isEmptyProperty);

if ({try_target_var}.isError()) {{
{I}{try_target_var}.getError()
{II}.prependSegment(
{III}new Reporting.NameSegment(
{IIII}{xml_prop_name_literal}));
{I}return Result.failure({try_target_var});
}}

{target_var} = {try_target_var}.getResult();"""
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

    item_our_type = type_anno.items.our_type
    item_type_name = java_common.generate_type(type_anno.items)
    if (
        isinstance(item_our_type, intermediate.AbstractClass)
        or len(item_our_type.concrete_descendants) > 0
    ):
        interface_name = java_naming.interface_name(type_anno.items.our_type.name)
        deserialize_method = f"{interface_name}FromElement"
    else:
        class_name = java_naming.class_name(type_anno.items.our_type.name)
        deserialize_method = f"{class_name}FromElement"

    item_type = java_common.generate_type(type_anno.items)

    return Stripped(
        f"""\
{target_var} = new ArrayList<{item_type_name}>();
if (!isEmptyProperty) {{
{I}skipWhitespaceAndComments(reader);
{I}int index = 0;
{I}while (currentEvent(reader).isStartElement()) {{

{II}Result<? extends {item_type}> itemResult = try{deserialize_method}(reader);

{II}if (itemResult.isError()) {{
{III}itemResult.getError()
{IIII}.prependSegment(
{IIIII}new Reporting.IndexSegment(index));
{III}itemResult.getError()
{IIII}.prependSegment(
{IIIII}new Reporting.NameSegment("{target_var}"));
{III}return Result.failure(itemResult);
{II}}}

{II}{target_var}.add(itemResult.getResult());
{II}index++;
{II}skipWhitespaceAndComments(reader);
{I}}}
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
            # NOTE (empwilli, 2023-12-18):
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


def _generate_deserialize_impl_cls_from_sequence(
    cls: intermediate.ConcreteClass,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the function to de-serialize the ``cls`` from an XML sequence."""
    name = java_naming.class_name(identifier=cls.name)

    description = Stripped(
        f"""\
/**
 * Deserialize an instance of class {name} from a sequence of XML elements.
 *
 * <p>If {{@code isEmptySequence}} is set, we should try to deserialize
 * the instance from an empty sequence. That is, the parent element
 * was a self-closing element.
 */"""
    )

    # NOTE (empwilli, 2023-12-18):
    # Hard-wire for the case when no sequence is read
    if len(cls.constructor.arguments) == 0:
        return (
            Stripped(
                f"""\
{description}
private static Result<{name}> {name}FromSequence(
{I}XMLEventReader reader,
{I}boolean isEmptySequence) {{
{I}return Result.success(new {name}());
}}"""
            ),
            None,
        )

    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

    assert len(cls.constructor.arguments) > 0, "Otherwise expected hard-wiring above"
    init_target_var_stmts = []  # type: List[Stripped]
    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        assert isinstance(
            type_anno,
            (
                intermediate.PrimitiveTypeAnnotation,
                intermediate.OurTypeAnnotation,
                intermediate.ListTypeAnnotation,
            ),
        )

        target_type = java_common.generate_type(type_anno)
        target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))

        init_target_var_stmts.append(Stripped(f"{target_type} {target_var} = null;"))
    blocks.append(Stripped("\n".join(init_target_var_stmts)))

    # noinspection PyListCreation
    blocks_for_non_empty = []  # type: List[Stripped]

    blocks_for_non_empty.append(
        Stripped(
            f"""\
skipWhitespaceAndComments(reader);
if (currentEvent(reader).isEndDocument()) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element representing " +
{II}"a property of an instance of class {name}, " +
{II}"but reached the end-of-file");
{I}return Result.failure(error);
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
        xml_prop_name_literal = java_common.string_literal(xml_prop_name)
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
{I}final Reporting.Error error = new Reporting.Error(
{II}"We expected properties of the class {name}, " +
{II}"but got an unexpected element " +
{II}"with the name " + elementName);
{I}return Result.failure(error);"""
        )
    )

    switch_body = "\n".join(case_blocks)

    blocks_for_non_empty.append(
        Stripped(
            f"""\
while (true) {{
{I}skipWhitespaceAndComments(reader);

{I}if (currentEvent(reader).isEndElement() || currentEvent(reader).isEndDocument()) {{
{II}break;
{I}}}

{I}if (!currentEvent(reader).isStartElement()) {{
{II}final Reporting.Error error = new Reporting.Error(
{III}"Expected an XML start element representing " +
{III}"a property of an instance of class {name}, " +
{III}"but got the node of type " + getEventTypeAsString(currentEvent(reader)) +
{III}"with the value " + currentEvent(reader));
{II}return Result.failure(error);
{I}}}

{I}final Result<String> tryElementName = tryElementName(reader);
{I}if (tryElementName.isError()) {{
{II}return Result.failure(tryElementName);
{I}}}

{I}final boolean isEmptyProperty = isEmptyElement(reader);
{I}final String elementName = tryElementName.getResult();

{I}switch (tryElementName.getResult()) {{
{II}{indent_but_first_line(switch_body, II)}
{I}}}

{I}skipWhitespaceAndComments(reader);

{I}if (!isEmptyProperty) {{
{II}final Result<XMLEvent> checkEndElement = verifyClosingTagForClass(
{III}"{name}",
{III}reader,
{III}tryElementName);
{II}if (checkEndElement.isError()) return Result.failure(checkEndElement);
{I}}}
}}"""
        )
    )

    body_for_non_empty_sequence = "\n".join(blocks_for_non_empty)
    blocks.append(
        Stripped(
            f"""\
if (!isEmptySequence) {{
{I}{indent_but_first_line(body_for_non_empty_sequence, I)}
}}"""
        )
    )

    # region Check that the mandatory properties have been set

    for prop in cls.properties:
        prop_java = java_naming.property_name(prop.name)
        target_var = java_naming.variable_name(Identifier(f"the_{prop.name}"))

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            blocks.append(
                Stripped(
                    f"""\
if ({target_var} == null) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"The required property {prop_java} has not been given " +
{II}"in the XML representation of an instance of class {name}");
{I}return Result.failure(error);
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
    init_writer.write(f"return Result.success(new {name}(\n")

    for i, arg in enumerate(cls.constructor.arguments):
        prop = cls.properties_by_name[arg.name]

        # NOTE (empwilli, 2023-12-18):
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
                    f"to the constructor in the XML de-serialization.",
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

    # endregion

    blocks.append(Stripped(init_writer.getvalue()))

    writer = io.StringIO()
    writer.write(
        f"""\
{description}
private static Result<{name}> {name}FromSequence(
{I}XMLEventReader reader,
{I}boolean isEmptySequence) {{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}")

    return Stripped(writer.getvalue()), None


def _generate_deserialize_impl_concrete_cls_from_element(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Generate the function to de-serialize a concrete ``cls`` from an XML element."""
    name = java_naming.class_name(cls.name)
    xml_name = naming.xml_class_name(cls.name)
    xml_name_literal = java_common.string_literal(xml_name)

    body = Stripped(
        f"""\
skipWhitespaceAndComments(reader);

final XMLEvent currentEvent = currentEvent(reader);
if (currentEvent.getEventType() == XMLStreamConstants.END_DOCUMENT) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element representing an instance of class {name}, " +
{II}"but reached the end-of-file");
{I}return Result.failure(error);
}}

if (currentEvent.getEventType() != XMLStreamConstants.START_ELEMENT) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element representing an instance of class {name}, " +
{II}"but got a node of type " + getEventTypeAsString(currentEvent) +
{II}"with value " + currentEvent);
{I}return Result.failure(error);
}}

final Result<String> tryElementName = tryElementName(reader);
if (tryElementName.isError()) {{
{I}return Result.failure(tryElementName);
}}

final String elementName = tryElementName.getResult();
if (!{xml_name_literal}.equals(tryElementName.getResult())) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an element representing an instance of class {name} " +
{II}"with element name {xml_name}, but got: " + elementName);
{I}return Result.failure(error);
}}

final boolean isEmptyElement = isEmptyElement(reader);

Result<{name}> result = {name}FromSequence(
{I}reader,
{I}isEmptyElement);

if (!isEmptyElement) {{
{I}final Result<XMLEvent> checkEndElement = verifyClosingTagForClass(
{II}"{name}",
{II}reader,
{II}tryElementName);
{I}if (checkEndElement.isError()) return Result.failure(checkEndElement);
}}

return result;"""
    )

    return Stripped(
        f"""\
/**
 * Deserialize an instance of class {name} from an XML element.
 */
private static Result<{name}> try{name}FromElement(
{I}XMLEventReader reader) {{
{I}{indent_but_first_line(body, I)}
}}"""
    )


def _generate_deserialize_impl_interface_from_element(
    interface: intermediate.Interface,
) -> Stripped:
    """Generate the function to de-serialize an ``interface`` from an XML element."""
    name = java_naming.interface_name(interface.name)

    blocks = [
        Stripped(
            f"""\
skipWhitespaceAndComments(reader);

final XMLEvent currentEvent = currentEvent(reader);
if (currentEvent.getEventType() == XMLStreamConstants.END_DOCUMENT) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element, but reached end-of-file");
{I}return Result.failure(error);
}}

if (currentEvent.getEventType() != XMLStreamConstants.START_ELEMENT) {{
{I}final Reporting.Error error = new Reporting.Error(
{II}"Expected an XML element representing an instance of class {name}, " +
{II}"but got a node of type " + getEventTypeAsString(currentEvent) +
{II}"with value " + currentEvent);
{I}return Result.failure(error);
}}"""
        )
    ]  # type: List[Stripped]

    case_stmts = []  # type: List[Stripped]
    for implementer in interface.implementers:
        implementer_xml_name_literal = java_common.string_literal(
            naming.xml_class_name(implementer.name)
        )

        implementer_name = java_naming.class_name(implementer.name)

        case_stmts.append(
            Stripped(
                f"""\
case {implementer_xml_name_literal}:
{I}return Result.convert(try{implementer_name}FromElement(reader));"""
            )
        )

    case_stmts.append(
        Stripped(
            f"""\
default:
{I}final Reporting.Error error = new Reporting.Error(
{II}"Unexpected element with the name " + getEventTypeAsString(currentEvent));
{I}return Result.failure(error);"""
        )
    )

    switch_writer = io.StringIO()
    switch_writer.write(
        f"""\
Result<String> tryElementName = tryElementName(
{I}reader);
if (tryElementName.isError()) {{
{I}return Result.failure(tryElementName);
}}

final String elementName = tryElementName.getResult();
switch (elementName) {{
"""
    )
    for i, case_stmt in enumerate(case_stmts):
        if i > 0:
            switch_writer.write("\n")
        switch_writer.write(textwrap.indent(case_stmt, I))

    switch_writer.write("\n}")

    blocks.append(Stripped(switch_writer.getvalue()))

    writer = io.StringIO()
    writer.write(
        f"""\
/**
 * Deserialize an instance of {name} from an XML element.
 */
private static Result<{name}> try{name}FromElement(
{I}XMLEventReader reader) {{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}")

    return Stripped(writer.getvalue())


def _generate_deserialize_impl(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the implementation for deserialization functions."""
    blocks = [
        _generate_current_event(),
        _generate_get_event_type_as_string(),
        _generate_is_empty_element(),
        _generate_verify_closing_tag_for_class(),
        _generate_skip_whitespace_and_comments(),
        _generate_try_element_name(),
        _generate_try_content_for_primitives(),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    # NOTE (empwilli, 2023-12-18):
    # Enumerations are going to be directly deserialized using
    # ``Stringification``.

    # NOTE (empwilli, 2023-12-18):
    # Constrained primitives are only verified, but do not represent a C# type.

    for cls in symbol_table.classes:
        if cls.is_implementation_specific:
            implementation_keys = [
                specific_implementations.ImplementationKey(
                    f"Xmlization/DeserializeImplementation/"
                    f"{cls.name}_from_element.java"
                ),
                specific_implementations.ImplementationKey(
                    f"Xmlization/DeserializeImplementation/"
                    f"{cls.name}_from_sequence.java"
                ),
            ]

            for implementation_key in implementation_keys:
                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            cls.parsed.node,
                            f"The xmlization snippet is missing "
                            f"for the implementation-specific "
                            f"class {cls.name}: {implementation_key}",
                        )
                    )
                    continue
                else:
                    blocks.append(spec_impls[implementation_key])
        else:
            if isinstance(cls, intermediate.ConcreteClass):
                (
                    block,
                    generation_errors,
                ) = _generate_deserialize_impl_cls_from_sequence(cls=cls)
                if generation_errors is not None:
                    errors.append(
                        Error(
                            cls.parsed.node,
                            f"Failed to generate the XML deserialization code "
                            f"for the class {cls.name}",
                            generation_errors,
                        )
                    )
                else:
                    assert block is not None
                    blocks.append(block)

            if cls.interface is not None:
                blocks.append(
                    _generate_deserialize_impl_interface_from_element(
                        interface=cls.interface
                    )
                )

            if isinstance(cls, intermediate.ConcreteClass):
                blocks.append(
                    _generate_deserialize_impl_concrete_cls_from_element(cls=cls)
                )

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()

    writer.write(
        """\
/**
 * Implement the deserialization of meta-model classes from XML.
 *
 * <p>The implementation propagates an {@link Reporting#Error} instead of
 * relying on exceptions. Under the assumption that incorrect data is much less
 * frequent than correct data, this makes the deserialization more
 * efficient.
 *
 * <p>However, we do not want to force the client to deal with
 * the {@link Reporting#Error} class as this is not intuitive.
 * Therefore we distinguish the implementation, realized in
 * {@link DeserializeImplementation}, and the facade given in
 * {@link Deserialize} class.
 */
private static class DeserializeImplementation
{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_deserialize_from(name: Identifier) -> Stripped:
    """Generate the facade method for deserialization of the class or interface."""
    writer = io.StringIO()

    writer.write(
        f"""\
/**
 * Deserialize an instance of {name} from {{@code reader}}.
 *
 * @param reader Initialized XML reader with cursor set to the element
 */
"""
    )

    type_name = java_naming.class_name(Identifier(f"{name}"))

    writer.write(
        f"""\
public static {name} deserialize{type_name}(
{I}XMLEventReader reader) {{

{I}DeserializeImplementation.skipWhitespaceAndComments(reader);

{I}if (DeserializeImplementation.currentEvent(reader).getEventType() == XMLStreamConstants.START_DOCUMENT) {{
{II}String reason = "Unexpected XML declaration when reading an instance "
{III}+ "of class {name}, as we expect the reader "
{III}+ "to be set at content.";
{II}throw new DeserializeException("", reason);
{I}}}

{I}Result<{name}> result =
{II}DeserializeImplementation.try{name}FromElement(
{III}reader);

{I}return result.onError(error -> {{
{II}throw new DeserializeException(
{III}Reporting.generateRelativeXPath(error.getPathSegments()),
{III}error.getCause());
{I}}});
}}"""
    )

    return Stripped(writer.getvalue())


def _generate_deserialize(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the public class ``Deserialize``."""
    blocks = []  # type: List[Stripped]

    # NOTE (empwilli, 2023-12-18):
    # We use stringification for de-serialization of enumerations.

    # NOTE (empwilli, 2023-12-18):
    # Constrained primitives are not handled as separate classes, but as
    # primitives, and only verified in the verification.

    for cls in symbol_table.classes:
        if cls.interface is not None:
            blocks.append(
                _generate_deserialize_from(
                    name=java_naming.interface_name(cls.interface.name)
                )
            )

        if isinstance(cls, intermediate.ConcreteClass):
            blocks.append(
                _generate_deserialize_from(name=java_naming.class_name(cls.name))
            )

    writer = io.StringIO()
    writer.write(
        """\
/**
 * Deserialize instances of meta-model classes from XML.
 */
"""
    )

    first_cls = symbol_table.classes[0] if len(symbol_table.classes) > 0 else None

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
/** <pre>
 * Here is an example how to parse an instance of class {cls_name}:
 * {{@code
 * XMLEventReader reader = xmlFactory.createXMLEventReader(...some arguments...);
 * {cls_name} {an_instance_variable} = Deserialize.{cls_name}From(
 * {I}reader);
 * }}
 * </pre>
 *
 * <pre>
 * If the elements live in a namespace, you have to supply it. For example:
 * {{@code
 * XMLEventReader reader = xmlFactory.createXMLEventReader(...some arguments...);
 * {cls_name} {an_instance_variable} = Deserialize.{cls_name}From(
 * {I}reader,
 * {I}"http://www.example.com/5/12");
 * }}
 * </pre>
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


def _generate_serialize_primitive_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of the primitive-type ``prop`` as XML content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    a_type = intermediate.try_primitive_type(type_anno)
    assert (
        a_type is not None
    ), f"Unexpected non-primitive type of the property {prop.name!r}: {type_anno}"

    prop_name = java_naming.property_name(prop.name)
    getter_name = java_naming.getter_name(prop.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    write_value_block: Stripped

    if (
        a_type is intermediate.PrimitiveType.BOOL
        or a_type is intermediate.PrimitiveType.INT
        or a_type is intermediate.PrimitiveType.FLOAT
        or a_type is intermediate.PrimitiveType.STR
    ):
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            write_value_block = Stripped(
                f"""\
if (that.{getter_name}().isPresent()) {{
{I}writer.writeStartElement(
{II}{xml_prop_name_literal});
{I}writer.writeNamespace(
{II}"xmlns",
{II}AAS_NAME_SPACE);

{I}writer.writeCharacters(
{II}that.{getter_name}().get().toString());

{I}writer.writeEndElement();
}}"""
            )
        else:
            write_value_block = Stripped(
                f"""\
writer.writeCharacters(
{I}that.{getter_name}().toString());"""
            )
    elif a_type is intermediate.PrimitiveType.BYTEARRAY:
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            base64_prop_name = java_naming.property_name(
                Identifier(f"the_b64_{prop_name}")
            )
            write_value_block = Stripped(
                f"""\
if (that.{getter_name}().isPresent()) {{
{I}String {base64_prop_name} = Base64.getEncoder().encodeToString(
{II}that.{getter_name}().get());
{I}writer.writeCharacters({base64_prop_name});
}}"""
            )
        else:
            base64_prop_name = java_naming.property_name(
                Identifier(f"the_b64_{prop_name}")
            )
            write_value_block = Stripped(
                f"""\
String {base64_prop_name} = Base64.getEncoder().encodeToString(
{I}that.{getter_name}());
writer.writeCharacters({base64_prop_name});"""
            )
    else:
        assert_never(a_type)

    assert write_value_block is not None

    write_value_block = Stripped(
        f"""\
try {{
{I}{indent_but_first_line(write_value_block, I)}
}} catch (XMLStreamException exception) {{
{I}error = new Reporting.Error(exception.getMessage());
}}"""
    )

    return write_value_block


def _generate_serialize_enumeration_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of an enumeration ``prop`` as XML content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
        type_anno.our_type, intermediate.Enumeration
    ), "See intermediate._translate._verify_only_simple_type_patterns"

    enumeration = type_anno.our_type

    getter_name = java_naming.getter_name(prop.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    enum_name = java_naming.enum_name(enumeration.name)

    text_var = java_naming.variable_name(Identifier(f"text_{prop.name}"))

    write_value_block: Stripped

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        write_value_block = Stripped(
            f"""\
if (that.{getter_name}().isPresent()) {{
{I}writer.writeStartElement(
{II}{xml_prop_name_literal});
{I}writer.writeNamespace(
{II}"xmlns",
{II}AAS_NAME_SPACE);

{I}Optional<String> {text_var} = Stringification.toString(
{II}that.{getter_name}().get());

{I}if (!{text_var}.isPresent()) {{
{II}throw new IllegalArgumentException(
{III}"Invalid literal for the enumeration {enum_name}: " +
{III}that.{getter_name}().get().toString());
{I}}}

{I}writer.writeCharacters({text_var}.get());

{I}writer.writeEndElement();
}}"""
        )
    else:
        write_value_block = Stripped(
            f"""\
writer.writeStartElement(
{I}{xml_prop_name_literal});
writer.writeNamespace(
{I}"xmlns",
{I}AAS_NAME_SPACE);

Optional<String> {text_var} = Stringification.toString(
{I}that.{getter_name}());

if (!{text_var}.isPresent()) {{
{I}throw new IllegalArgumentException(
{II}"Invalid literal for the enumeration {enum_name}: " +
{II}that.{getter_name}().toString());
}}

writer.writeCharacters({text_var}.get());

writer.writeEndElement();"""
        )

    write_value_block = Stripped(
        f"""\
try {{
{I}{indent_but_first_line(write_value_block, I)}
}} catch (XMLStreamException exception) {{
{I}error = new Reporting.Error(exception.getMessage());
}}"""
    )

    return write_value_block


def _generate_serialize_interface_property_as_content(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of an interface as XML content."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    # fmt: off
    assert (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and (
            isinstance(type_anno.our_type, intermediate.AbstractClass)
            or (
                isinstance(type_anno.our_type, intermediate.ConcreteClass)
                and len(type_anno.our_type.concrete_descendants) > 0
            )
        )
    ), "See intermediate._translate._verify_only_simple_type_patterns"
    # fmt: on

    getter_name = java_naming.getter_name(prop.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    result: Stripped

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        result = Stripped(
            f"""\
if (that.{getter_name}().isPresent()) {{
{I}writer.writeStartElement(
{II}{xml_prop_name_literal});
{I}writer.writeNamespace(
{II}"xmlns",
{II}AAS_NAME_SPACE);

{I}this.visit(
{II}that.{getter_name}().get(),
{II}writer);

{I}writer.writeEndElement();
}}"""
        )
    else:
        result = Stripped(
            f"""\
writer.writeStartElement(
{I}{xml_prop_name_literal});
writer.writeNamespace(
{I}"xmlns",
{I}AAS_NAME_SPACE);

this.visit(
{I}that.{getter_name}(),
{I}writer);

writer.writeEndElement();"""
        )

    result = Stripped(
        f"""\
try {{
{I}{indent_but_first_line(result, I)}
}} catch (XMLStreamException exception) {{
{I}error = new Reporting.Error(exception.getMessage());
}}"""
    )

    return result


def _generate_serialize_concrete_class_property_as_sequence(
    prop: intermediate.Property,
) -> Stripped:
    """Generate the serialization of the class ``prop`` as a sequence of properties."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)
    assert isinstance(type_anno, intermediate.OurTypeAnnotation)
    assert isinstance(type_anno.our_type, intermediate.ConcreteClass)

    cls_to_sequence = java_naming.method_name(
        Identifier(f"{type_anno.our_type.name}_to_sequence")
    )

    getter_name = java_naming.getter_name(prop.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    result: Stripped

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        result = Stripped(
            f"""\
if (that.{getter_name}().isPresent()) {{
{I}writer.writeStartElement(
{II}{xml_prop_name_literal});
{I}writer.writeNamespace(
{II}"xmlns",
{II}AAS_NAME_SPACE);

{I}this.{cls_to_sequence}(
{II}that.{getter_name}().get(),
{II}writer);

{I}writer.writeEndElement();
}}"""
        )
    else:
        result = Stripped(
            f"""\
writer.writeStartElement(
{I}{xml_prop_name_literal});
writer.writeNamespace(
{I}"xmlns",
{I}AAS_NAME_SPACE);

this.{cls_to_sequence}(
{I}that.{getter_name}(),
{I}writer);

writer.writeEndElement();"""
        )

    result = Stripped(
        f"""\
try {{
{I}{indent_but_first_line(result, I)}
}} catch (XMLStreamException exception) {{
{I}error = new Reporting.Error(exception.getMessage());
}}"""
    )

    return result


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
            type_anno.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass)
        )
    ), "See intermediate._translate._verify_only_simple_type_patterns"
    # fmt: on

    getter_name = java_naming.getter_name(prop.name)
    xml_prop_name_literal = java_common.string_literal(naming.xml_property(prop.name))

    result: Stripped

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        result = Stripped(
            f"""\
writer.writeStartElement(
{I}{xml_prop_name_literal});
writer.writeNamespace(
{I}"xmlns",
{I}AAS_NAME_SPACE);

if (that.{getter_name}().isPresent()) {{
{I}for (IClass item : that.{getter_name}().get()) {{
{II}this.visit(
{III}item,
{III}writer);
{I}}}
}}

writer.writeEndElement();"""
        )
    else:
        result = Stripped(
            f"""\
writer.writeStartElement(
{I}{xml_prop_name_literal});
writer.writeNamespace(
{I}"xmlns",
{I}AAS_NAME_SPACE);

for (IClass item : that.{getter_name}()) {{
{I}this.visit(
{II}item,
{II}writer);
}}

writer.writeEndElement();"""
        )

    result = Stripped(
        f"""\
try {{
{I}{indent_but_first_line(result, I)}
}} catch (XMLStreamException exception) {{
{I}error = new Reporting.Error(exception.getMessage());
}}"""
    )

    return result


def _generate_serialize_property_as_content(prop: intermediate.Property) -> Stripped:
    """Generate the code to serialize the ``prop`` as content of an XML element."""
    type_anno = intermediate.beneath_optional(prop.type_annotation)

    body = None  # type: Optional[Stripped]

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        body = _generate_serialize_primitive_property_as_content(prop=prop)
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        our_type = type_anno.our_type

        if isinstance(our_type, intermediate.Enumeration):
            body = _generate_serialize_enumeration_property_as_content(prop=prop)

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            body = _generate_serialize_primitive_property_as_content(prop=prop)

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if (
                isinstance(our_type, intermediate.AbstractClass)
                or len(our_type.concrete_descendants) > 0
            ):
                body = _generate_serialize_interface_property_as_content(prop=prop)
            else:
                body = _generate_serialize_concrete_class_property_as_sequence(
                    prop=prop
                )

        else:
            assert_never(our_type)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        body = _generate_serialize_list_property_as_content(prop=prop)

    else:
        assert_never(type_anno)

    return body


def _generate_class_to_sequence(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the method to write ``cls`` as a sequence of properties as XML."""
    blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        body = _generate_serialize_property_as_content(prop=prop)
        blocks.append(body)

    interface_name = java_naming.interface_name(cls.name)
    method_name = java_naming.method_name(Identifier(f"{cls.name}_to_sequence"))

    writer = io.StringIO()

    if len(cls.properties) == 0:
        blocks.append(Stripped("// Intentionally empty."))

    writer.write(
        f"""\
private void {method_name}(
{I}{interface_name} that,
{I}XMLStreamWriter writer) {{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write(f"\n}}")

    return Stripped(writer.getvalue())


def _generate_visit_for_class(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the method to write the ``cls`` as an XML element."""
    interface_name = java_naming.interface_name(cls.name)
    visit_name = java_naming.method_name(Identifier(f"visit_{cls.name}"))

    cls_to_sequence_name = java_naming.method_name(
        Identifier(f"{cls.name}_to_sequence")
    )

    xml_cls_name_literal = java_common.string_literal(naming.xml_class_name(cls.name))

    return Stripped(
        f"""\
@Override
public void {visit_name}(
{I}{interface_name} that,
{I}XMLStreamWriter writer) {{
{I}try {{
{II}writer.writeStartElement(
{III}{xml_cls_name_literal});
{II}writer.writeNamespace(
{III}"xmlns",
{III}AAS_NAME_SPACE);
{II}this.{cls_to_sequence_name}(
{III}that,
{III}writer);
{II}writer.writeEndElement();
}} catch (XMLStreamException exception) {{
{I}error = new Reporting.Error(exception.getMessage());
}}
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

    # The abstract classes are directly dispatched by the transformer,
    # so we do not need to handle them separately.

    for cls in symbol_table.concrete_classes:
        if cls.is_implementation_specific:
            implementation_keys = [
                specific_implementations.ImplementationKey(
                    f"Xmlization/VisitorWithWriter/visit_{cls.name}.java"
                ),
                specific_implementations.ImplementationKey(
                    f"Xmlization/VisitorWithWriter/{cls.name}_to_sequence.java"
                ),
            ]

            for implementation_key in implementation_keys:
                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            cls.parsed.node,
                            f"The xmlization snippet is missing "
                            f"for the implementation-specific "
                            f"class {cls.name}: {implementation_key}",
                        )
                    )
                    continue

                blocks.append(spec_impls[implementation_key])
        else:
            blocks.append(_generate_class_to_sequence(cls=cls))

            blocks.append(_generate_visit_for_class(cls=cls))

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        f"""\
/**
 * Serialize recursively the instances as XML elements.
 */
static class VisitorWithWriter
{I}extends AbstractVisitorWithContext<XMLStreamWriter> {{

Reporting.Error error = null;

public boolean isError() {{
{I}return error != null;
}}

public Reporting.Error getError() {{
{I}return error;
}}
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
        Stripped(
            f"""\
private static final VisitorWithWriter _visitorWithWriter =
{I}new VisitorWithWriter();"""
        ),
        Stripped(
            f"""\
/**
 * Serialize an instance of the meta-model to XML.
 */
public static void to(
{I}IClass that,
{I}XMLStreamWriter writer) throws SerializeException {{
{I}Serialize._visitorWithWriter.visit(
{II}that, writer);
{I}if (Serialize._visitorWithWriter.isError()) {{
{II}Reporting.Error error = Serialize._visitorWithWriter.getError();
{II}throw new SerializeException("",
{II}"Failed to serialize object graph: " +
{II}error.getCause());
{I}}}
}}"""
        ),
    ]  # type: List[Stripped]

    writer = io.StringIO()
    writer.write(
        """\
/**
 * Serialize instances of meta-model classes to XML.
 */
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
/**
 * <pre>
 * Here is an example how to serialize an instance of {cls_name}:
 * {{@code
 * IClass {an_instance_variable} = new {cls_name}(
 *     ... some constructor arguments ...
 * );
 * XMLStreamWriter writer = xmlWriterFactory.createXMLStreamWriter(...some arguments...);
 * Serialize.to(
 * {I}{an_instance_variable},
 * {I}writer);
 * }}
 * </pre>
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

    The ``package`` defines the root Java package.
    """
    errors = []  # type: List[Error]

    imports = [
        Stripped("import javax.xml.stream.events.XMLEvent;"),
        Stripped("import javax.xml.stream.XMLEventReader;"),
        Stripped("import javax.xml.stream.XMLStreamConstants;"),
        Stripped("import javax.xml.stream.XMLStreamException;"),
        Stripped("import javax.xml.stream.XMLStreamWriter;"),
        Stripped("import java.util.ArrayList;"),
        Stripped("import java.util.Base64;"),
        Stripped("import java.util.function.Function;"),
        Stripped("import java.util.List;"),
        Stripped("import java.util.Optional;"),
        Stripped(f"import {package}.reporting.Reporting;"),
        Stripped(f"import {package}.reporting.Reporting.Error;"),
        Stripped(f"import {package}.stringification.Stringification;"),
        Stripped(f"import {package}.types.enums.*;"),
        Stripped(f"import {package}.types.impl.*;"),
        Stripped(f"import {package}.types.model.*;"),
        Stripped(f"import {package}.visitation.*;"),
    ]  # type: List[Stripped]

    # region Deserialization helpers

    xml_result_class = _generate_result()

    xml_namespace_literal = java_common.string_literal(
        symbol_table.meta_model.xml_namespace
    )

    # endregion

    # region Deserialization Implementation

    deserialize_impl_block, deserialize_impl_errors = _generate_deserialize_impl(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if deserialize_impl_errors is not None:
        errors.extend(deserialize_impl_errors)

    assert deserialize_impl_block is not None

    # endregion

    # region Deserialization

    deserialize_block = _generate_deserialize(symbol_table=symbol_table)

    # endregion

    # region Visitor

    visitor_block, visitor_errors = _generate_visitor(
        symbol_table=symbol_table, spec_impls=spec_impls
    )
    if visitor_errors is not None:
        errors.extend(visitor_errors)

    assert visitor_block is not None

    # endregion

    # region Serialization

    serialization_block = _generate_serialize(symbol_table=symbol_table)

    # endregion

    xmlization_blocks = [
        Stripped(
            f"""\
/**
 * Provide de/serialization of meta-model classes to/from XML.
 */
public class Xmlization
{{

{I}/**
{I} * Represent a critical error during the deserialization.
{I} */
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
{I}}}

{I}/**
{I} * Represent a critical error during the serialization.
{I} */
{I}public static class SerializeException extends RuntimeException {{
{II}private final String path;
{II}private final String reason;

{II}public SerializeException(String path, String reason) {{
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
{I}}}

{I}/**
{I} * The XML namespace of the meta-model
{I} */
{I}public static final String AAS_NAME_SPACE =
{II}{xml_namespace_literal};

{I}{indent_but_first_line(xml_result_class, I)}

{I}{indent_but_first_line(deserialize_impl_block, I)}

{I}{indent_but_first_line(deserialize_block, I)}

{I}{indent_but_first_line(visitor_block, I)}

{I}{indent_but_first_line(serialization_block, I)}
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
