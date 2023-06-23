"""Generate the Golang code for XML-ization based on the intermediate representation."""

import io
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
from aas_core_codegen.golang import (
    common as golang_common,
    naming as golang_naming,
    pointering as golang_pointering,
)
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
    INDENT6 as IIIIII,
)


# region De-serialization


def _generate_deserialization_error_and_its_methods() -> List[Stripped]:
    """Generate the code to represent the deserialization error."""
    return [
        Stripped(
            f"""\
// Represent an error during the de-serialization.
//
// Implements `error`.
type DeserializationError struct{{
{I}Path *aasreporting.Path
{I}Message string
}}"""
        ),
        Stripped(
            f"""\
func newDeserializationError(message string) *DeserializationError {{
{I}return &DeserializationError{{
{II}Path: &aasreporting.Path{{}},
{II}Message: message,
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func (de *DeserializationError) Error() string {{
{I}return fmt.Sprintf(
{II}"%s: %s",
{II}de.PathString(),
{II}de.Message,
{I})
}}"""
        ),
        Stripped(
            f"""\
// Render the path as a string.
func (de *DeserializationError) PathString() string {{
{I}return aasreporting.ToRelativeXPath(de.Path)
}}"""
        ),
    ]


def _generate_is_whitespace() -> Stripped:
    return Stripped(
        f"""\
// Check if the string `s` consists only of whitespace.
//
// An empty string causes panic — please cover that case before.
func isWhitespace(s string) bool {{
{I}if len(s) == 0 {{
{II}panic("Unexpected empty string")
{I}}}
{I}for _, c := range s {{
{II}if !unicode.IsSpace(c) {{
{III}return false
{II}}}
{I}}}
{I}return true
}}"""
    )


def _generate_read_next() -> Stripped:
    return Stripped(
        f"""\
// Read the next token from the `decoder` given the `current` token.
//
// If `current` token is [eof], return [eof].
func readNext(decoder *xml.Decoder, current xml.Token) (next xml.Token, err error) {{
{I}if _, isEOF := current.(eof); isEOF {{
{II}next = current
{II}return
{I}}}

{I}var tokenErr error
{I}next, tokenErr = decoder.Token()
{I}if tokenErr != nil {{
{II}if tokenErr == io.EOF {{
{III}next = &eof{{}}
{III}return
{II}}}

{II}err = tokenErr
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_skip_empty_text_whitespace_and_comments() -> Stripped:
    return Stripped(
        f"""\
// Read all the possible whitespace and comments.
//
// Return the `next` token which is neither empty text, nor whitespace nor comment,
// or [eof], if we reached the end-of-file.
//
// If we already reached the end-of-file, simply return [eof].
func skipEmptyTextWhitespaceAndComments(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (next xml.Token, err error) {{
{I}stop := false
{I}for !stop {{
{II}if _, isEOF := current.(eof); isEOF {{
{III}break
{II}}}

{II}switch et := current.(type) {{
{II}case xml.CharData:
{III}text := string(et)
{III}if len(text) != 0 && !isWhitespace(text) {{
{IIII}stop = true
{III}}} else {{
{IIII}// We should proceed to the next token.
{III}}}
{II}case xml.Comment:
{III}// We should proceed to the next token.
{II}default:
{III}stop = true
{II}}}

{II}if !stop {{
{III}current, err = readNext(decoder, current)
{III}if err != nil {{
{IIII}return
{III}}}
{II}}}
{I}}}

{I}next = current
{I}return
}}"""
    )


def _generate_read_text() -> Stripped:
    return Stripped(
        f"""\
// Consume the text tokens (char data).
//
// Any comment tokens are skipped.
//
// The resulting `next` token points to the first token which is neither text
// nor comment.
//
// If we reached the end-of-file, `next` is an [eof] sentinel token.
func readText(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (text string, next xml.Token, err error) {{
{I}b := &strings.Builder{{}}

{I}stop := false
{I}for {{
{II}if _, isEOF := current.(eof); isEOF {{
{III}err = newDeserializationError(
{IIII}"Expected to read text, but reached the end-of-file",
{III})
{III}return
{II}}}

{II}switch et := current.(type) {{
{II}case xml.CharData:
{III}b.WriteString(string(et))
{III}// Proceed to the next token.
{II}case xml.Comment:
{III}// Proceed to the next token.
{II}default:
{III}stop = true
{II}}}

{II}if !stop {{
{III}current, err = readNext(decoder, current)
{III}if err != nil {{
{IIII}return
{III}}}
{II}}} else {{
{III}break
{II}}}
{I}}}

{I}next = current
{I}text = b.String()
{I}return
}}"""
    )


def _generate_read_text_as_boolean() -> Stripped:
    return Stripped(
        f"""\
// Consume the text tokens (char data) as a representation of a `xs:boolean`.
//
// Any comment tokens are skipped.
//
// The resulting `next` token points to the first token which is neither text
// nor comment.
//
// If we reached the end-of-file, `next` is an [eof] sentinel token.
func readTextAsBoolean(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (value bool, next xml.Token, err error) {{
{I}var text string
{I}text, next, err = readText(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}switch text {{
{I}case "1":
{II}value = true
{I}case "true":
{II}value = true
{I}case "0":
{II}value = false
{I}case "false":
{II}value = false
{I}default:
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected a value as xs:boolean, but got: %s",
{IIII}text,
{III}),
{II})
{I}}}
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_read_text_as_long() -> Stripped:
    return Stripped(
        f"""\
// Consume the text tokens (char data) as a representation of a `xs:long`.
//
// Any comment tokens are skipped.
//
// The resulting `next` token points to the first token which is neither text
// nor comment.
//
// If we reached the end-of-file, `next` is an [eof] sentinel token.
func readTextAsLong(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (value int64, next xml.Token, err error) {{
{I}var text string
{I}text, next, err = readText(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}value, err = strconv.ParseInt(text, 10, 64)

{I}return
}}"""
    )


def _generate_read_text_as_double() -> Stripped:
    return Stripped(
        f"""\
// Consume the text tokens (char data) as a representation of a `xs:double`.
//
// Any comment tokens are skipped.
//
// The resulting `next` token points to the first token which is neither text
// nor comment.
//
// If we reached the end-of-file, `next` is an [eof] sentinel token.
func readTextAsDouble(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (value float64, next xml.Token, err error) {{
{I}var text string
{I}text, next, err = readText(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}// We need to check explicitly for the regular expression since
{I}// strconv.ParseFloat is too permissive. For example, it accepts "nan"
{I}// although only "NaN" is valid.
{I}// See: https://www.w3.org/TR/xmlschema-2/#double
{I}if !aasverification.MatchesXsDouble(text) {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected a value as xs:double, but got: %s",
{IIII}text,
{III}),
{II})
{II}return
{I}}}

{I}var parseErr error
{I}value, parseErr = strconv.ParseFloat(text, 64)
{I}if parseErr != nil {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected a value as xs:double, but it could not be parsed: %s: %s",
{IIII}parseErr.Error(), text,
{III}),
{II})
{II}return
{I}}}

{I}// NOTE (2023-06-14):
{I}// We explicitly do not check for loss of precision, as the majority of people will
{I}// use string representation of the floating point numbers ignoring the precision
{I}// issues. For example, the closest double-precision number to the number `359.9` is
{I}// `359.8999999999999772626324556767940521240234375`, but most people will simply
{I}// give `359.9` as the value.

{I}return
}}"""
    )


def _generate_read_text_as_base64_encoded_bytes() -> Stripped:
    return Stripped(
        f"""\
// Consume the text tokens (char data) as a base64-encoded bytes.
//
// Any comment tokens are skipped.
//
// The resulting `next` token points to the first token which is neither text
// nor comment.
//
// If we reached the end-of-file, `next` is an [eof] sentinel token.
func readTextAsBase64EncodedBytes(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (value []byte, next xml.Token, err error) {{
{I}var text string
{I}text, next, err = readText(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}var decodingErr error
{I}value, decodingErr = b64.StdEncoding.DecodeString(text)
{I}if decodingErr != nil {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Text could not be decoded as base64: %s",
{IIII}decodingErr.Error(),
{III}),
{II})
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_check_start_element() -> Stripped:
    return Stripped(
        f"""\
// Check that the `current` token is a valid start element, *i.e.*, lives in [Namespace]
// and contains no attributes.
func checkStartElement(
{I}current xml.StartElement,
) (err error) {{
{I}var unexpectedAttr []xml.Attr
{I}for _, attr := range current.Attr {{
{II}if attr.Name.Space == "" && attr.Name.Local == "xmlns" {{
{III}continue
{II}}}
{II}unexpectedAttr = append(unexpectedAttr, attr)
{I}}}
{I}if len(unexpectedAttr) != 0 {{
{II} err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected no attributes except 'xmlns' in the start element, "+
{IIII}"but got %d in the start element %s",
{IIII}len(unexpectedAttr), current.Name.Local,
{III}),
{II})
{II}return
{I}}}

{I}if current.Name.Space != Namespace {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected only start elements in the namespace %s, "+
{IIIII}"but got a start element %s in the namespace %s",
{IIII}Namespace, current.Name.Local, current.Name.Space,
{III}),
{II})
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_extract_local_name_from_start_element() -> Stripped:
    return Stripped(
        f"""\
// Expect a valid start element (as defined in [checkStartElement]) and extract its
// `local` name.
//
// This function is meant to be called whenever you know the runtime type of a token.
// If you do not know the runtime type, call [parseAsStartElementAndExtractLocalName]
// so that you can succinctly check the runtime type as well.
func extractLocalNameFromStartElement(
{I}current xml.StartElement,
) (local string, err error) {{
{I}err = checkStartElement(current)
{I}if err != nil {{
{II}return
{I}}}

{I}local = current.Name.Local
{I}return
}}"""
    )


def _generate_parse_as_start_element_and_extract_local_name() -> Stripped:
    return Stripped(
        f"""\
// Expect a valid start element (as defined in [checkStartElement]) and extract its
// local name.
//
// Valid means that we check that the start element lives in [Namespace] and contains
// no attributes.
//
// If you know the runtime type of `current` token, call
// [parseLocalNameFromStartElement] instead to save a cast.
func parseAsStartElementAndExtractLocalName(
{I}current xml.Token,
) (local string, err error) {{
{I}if _, isEOF := current.(eof); isEOF {{
{II}err = newDeserializationError(
{III}"Expected a start element, but reached the end-of-file",
{II})
{II}return
{I}}}

{I}et, ok := current.(xml.StartElement)
{I}if !ok {{
{II}switch v := current.(type) {{
{II}case xml.EndElement:
{III}err = newDeserializationError(
{IIII}fmt.Sprintf(
{IIIII}"Expected a start element, but got an end element %s in namespace %s",
{IIIII}v.Name.Local, v.Name.Space,
{IIII}),
{III})
{II}case xml.CharData:
{III}err = newDeserializationError(
{IIII}fmt.Sprintf(
{IIIII}"Expected a start element, but got text %s",
{IIIII}string(v),
{IIII}),
{III})
{II}default:
{III}err = newDeserializationError(
{IIII}fmt.Sprintf(
{IIIII}"Expected a start element, but got %T: %v",
{IIIII}current, current,
{IIII}),
{III})
{II}}}
{II}return
{I}}}

{I}local, err = extractLocalNameFromStartElement(et)
{I}return
}}"""
    )


def _generate_check_end_element() -> Stripped:
    return Stripped(
        f"""\
// Check that the `current` token is an end element, living in [Namespace], and
// having the `local` name.
func checkEndElement(current xml.Token, local string) (err error) {{
{I}if _, isEOF := current.(eof); isEOF {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected an end element %s, but reached the end-of-file",
{IIII}local,
{III}),
{II})
{II}return
{I}}}

{I}et, ok := current.(xml.EndElement)
{I}if !ok {{
{II}switch v := current.(type) {{
{II}case xml.StartElement:
{III}err = newDeserializationError(
{IIII}fmt.Sprintf(
{IIIII}"Expected an end element %s, but got a start element %s in namespace %s",
{IIIII}local, v.Name.Local, v.Name.Space,
{IIII}),
{III})
{II}case xml.CharData:
{III}err = newDeserializationError(
{IIII}fmt.Sprintf(
{IIIII}"Expected an end element %s, but got text %s",
{IIIII}local, string(v),
{IIII}),
{III})
{II}default:
{III}err = newDeserializationError(
{IIII}fmt.Sprintf(
{IIIII}"Expected an end element %s, but got %T: %v",
{IIIII}local, current, current,
{IIII}),
{III})
{II}}}
{II}return
{I}}}

{I}if et.Name.Space != Namespace {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected an end element %s in the namespace %s, "+
{IIIII}"but got an end element in the namespace %s",
{IIII}local, Namespace, et.Name.Space,
{III}),
{II})
{II}return
{I}}}

{I}if et.Name.Local != local {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected an end element %s, but got an end element %s",
{IIII}local, et.Name.Local,
{III}),
{II})
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_read_list() -> Stripped:
    return Stripped(
        f"""\
// Read a list of AAS instances as a sequence of XML elements.
//
// Every start element is considered to mark the start of an instance serialization. We
// stop the reading as soon as we encounter a non-start element.
//
// That last non-start element is returned as `next` element.
func readList[T aastypes.IClass](
{I}decoder *xml.Decoder,
{I}current xml.Token,
{I}readTWithLookahead func(
{II}aDecoder *xml.Decoder,
{II}aCurrent xml.Token,
{I}) (anInstance T, anErr error),
) (instances []T, next xml.Token, err error) {{
{I}i := 0
{I}for {{
{II}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{II}if err != nil {{
{III}return
{II}}}

{II}if _, ok := current.(xml.StartElement); !ok {{
{III}break
{II}}}

{II}var instance T
{II}var instanceErr error
{II}instance, instanceErr = readTWithLookahead(decoder, current)
{II}if instanceErr != nil {{
{III}if deseriaErr, ok := instanceErr.(*DeserializationError); ok {{
{IIII}deseriaErr.Path.PrependIndex(
{IIIII}&aasreporting.IndexSegment{{Index: i}},
{IIII})
{III}}}
{III}err = instanceErr
{III}return
{II}}}

{II}instances = append(instances, instance)

{II}i++

{II}current, err = readNext(decoder, nil)
{II}if err != nil {{
{III}return
{II}}}
{I}}}

{I}next = current
{I}return
}}"""
    )


def _generate_read_text_as_enumeration(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    enum_name = golang_naming.enum_name(enumeration.name)
    from_string_name = golang_naming.function_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    function_name = golang_naming.private_function_name(
        Identifier(f"read_text_as_{enumeration.name}")
    )

    return Stripped(
        f"""\
// Consume the text tokens (char data) as a string-encoded literal of
// [aastypes.{enum_name}].
//
// Any comment tokens are skipped.
//
// The resulting `next` token points to the first token which is neither text
// nor comment.
//
// If we reached the end-of-file, `next` is an [eof] sentinel token.
func {function_name}(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (value aastypes.{enum_name},
{I}next xml.Token,
{I}err error,
) {{
{I}var text string
{I}text, next, err = readText(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}var ok bool
{I}value, ok = aasstringification.{from_string_name}(text)
{I}if !ok {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Unexpected literal of {enum_name}: %v",
{IIII}text,
{III}),
{II})
{II}return
{I}}}

{I}return
}}"""
    )


_READ_FUNCTION_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: "readTextAsBoolean",
    intermediate.PrimitiveType.INT: "readTextAsLong",
    intermediate.PrimitiveType.FLOAT: "readTextAsDouble",
    intermediate.PrimitiveType.STR: "readText",
    intermediate.PrimitiveType.BYTEARRAY: "readTextAsBase64EncodedBytes",
}
assert all(
    literal in _READ_FUNCTION_BY_PRIMITIVE_TYPE
    for literal in intermediate.PrimitiveType
)


def _generate_snippet_to_switch_on_property_deserialization(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """
    Generate the switch block to dispatch how to read a property.

    The start element is expected to have been read. The variable ``local`` denotes
    the local name of the start element.

    The decoder points to the first token of the property content.

    The variables ``the*`` and ``found*`` will be set as well as ``valueErr``.
    """
    case_blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        prop_var = golang_naming.variable_name(Identifier(f"the_{prop.name}"))

        xml_prop_literal = golang_common.string_literal(naming.xml_property(prop.name))

        case_body_blocks = []  # type: List[Stripped]

        if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation) or (
            isinstance(type_anno, intermediate.OurTypeAnnotation)
            and isinstance(
                type_anno.our_type,
                (intermediate.ConstrainedPrimitive, intermediate.Enumeration),
            )
        ):
            primitive_type = intermediate.try_primitive_type(type_anno)

            if primitive_type is not None:
                read_function = _READ_FUNCTION_BY_PRIMITIVE_TYPE[primitive_type]
            else:
                assert isinstance(
                    type_anno, intermediate.OurTypeAnnotation
                ) and isinstance(type_anno.our_type, intermediate.Enumeration)

                read_function = golang_naming.private_function_name(
                    Identifier(f"read_text_as_{type_anno.our_type.name}")
                )

            pointer = golang_pointering.is_pointer_type(prop.type_annotation)

            if pointer:
                # NOTE (mristin, 2023-06-17):
                # We explicitly pass in ``type_anno`` to the type as the read function
                # will return a non-optional.
                value_type = golang_common.generate_type(
                    type_annotation=type_anno, types_package=Identifier("aastypes")
                )

                case_body_blocks.append(
                    Stripped(
                        f"""\
var value {value_type}
value, current, valueErr = {read_function}(
{I}decoder,
{I}current,
)
{prop_var} = &value"""
                    )
                )
            else:
                case_body_blocks.append(
                    Stripped(
                        f"""\
{prop_var}, current, valueErr = {read_function}(
{I}decoder,
{I}current,
)"""
                    )
                )

        elif isinstance(type_anno, intermediate.OurTypeAnnotation):
            our_type = type_anno.our_type

            if isinstance(our_type, intermediate.Enumeration):
                raise AssertionError("Must have been handled before")

            elif isinstance(our_type, intermediate.ConstrainedPrimitive):
                raise AssertionError("Must have been handled before")

            elif isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                if (
                    isinstance(our_type, intermediate.ConcreteClass)
                    and len(our_type.concrete_descendants) == 0
                ):
                    read_function = golang_naming.private_function_name(
                        Identifier(f"read_{type_anno.our_type.name}_as_sequence")
                    )

                    case_body_blocks.append(
                        Stripped(
                            f"""\
{prop_var}, current, valueErr =  {read_function}(
{I}decoder,
{I}current,
)"""
                        )
                    )

                else:
                    unmarshal_function = golang_naming.private_function_name(
                        Identifier(f"unmarshal_{type_anno.our_type.name}")
                    )

                    case_body_blocks.append(
                        Stripped(
                            f"""\
{prop_var}, valueErr =  {unmarshal_function}(
{I}decoder,
)
// {unmarshal_function} stops at the end element,
// so we look ahead to the next element.
if valueErr == nil {{
{I}current, valueErr = readNext(decoder, current)
}}"""
                        )
                    )

            else:
                assert_never(our_type)

        elif isinstance(type_anno, intermediate.ListTypeAnnotation):
            assert isinstance(
                type_anno.items, intermediate.OurTypeAnnotation
            ) and isinstance(
                type_anno.items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ), (
                f"NOTE (mristin, 2023-03-29): We expect only lists of classes "
                f"at the moment, but you specified {type_anno}. "
                f"Please contact the developers if you need this feature."
            )

            read_item_function = golang_naming.private_function_name(
                Identifier(f"read_{type_anno.items.our_type.name}_with_lookahead")
            )

            case_body_blocks.append(
                Stripped(
                    f"""\
{prop_var}, current, valueErr = readList(
{I}decoder,
{I}current,
{I}{read_item_function},
)"""
                )
            )
        else:
            assert_never(type_anno)

        assert len(case_body_blocks) > 0

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            found_var = golang_naming.variable_name(Identifier(f"found_{prop.name}"))
            case_body_blocks.append(Stripped(f"{found_var} = true"))

        case_body = "\n".join(case_body_blocks)
        case_blocks.append(
            Stripped(
                f"""\
case {xml_prop_literal}:
{I}{indent_but_first_line(case_body, I)}"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}valueErr = newDeserializationError(
{II}fmt.Sprintf(
{III}"Unexpected property",
{II}),
{I})"""
        )
    )

    case_blocks_joined = "\n\n".join(case_blocks)

    return Stripped(
        f"""\
var valueErr error
switch local {{
{case_blocks_joined}
}}"""
    )


def _generate_read_as_sequence(cls: intermediate.ConcreteClass) -> Stripped:
    interface_name = golang_naming.interface_name(cls.name)

    # region Initialize

    initialization_blocks = []  # type: List[Stripped]

    prop_var_initializations = []  # type: List[Stripped]
    for prop in cls.properties:
        prop_var = golang_naming.variable_name(Identifier(f"the_{prop.name}"))

        prop_var_type = golang_common.generate_type(
            type_annotation=prop.type_annotation, types_package=Identifier("aastypes")
        )

        prop_var_initializations.append(Stripped(f"var {prop_var} {prop_var_type}"))

    if len(prop_var_initializations) > 0:
        initialization_blocks.append(Stripped("\n".join(prop_var_initializations)))

    found_var_initializations = []  # type: List[Stripped]
    for prop in cls.properties:
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        found_var = golang_naming.variable_name(Identifier(f"found_{prop.name}"))

        found_var_initializations.append(Stripped(f"{found_var} := false"))

    if len(found_var_initializations) > 0:
        initialization_blocks.append(Stripped("\n".join(found_var_initializations)))

    if len(initialization_blocks) == 0:
        initialization_blocks.append(
            Stripped(
                f"""\
// No initialization as there are no properties
// in {interface_name}."""
            )
        )

    initialization = "\n\n".join(initialization_blocks)

    # endregion

    switch_snippet = _generate_snippet_to_switch_on_property_deserialization(cls=cls)

    # region Construct

    construct_blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        found_var = golang_naming.variable_name(Identifier(f"found_{prop.name}"))

        message_literal = golang_common.string_literal(
            f"The required property {naming.json_property(prop.name)!r} is missing"
        )

        construct_blocks.append(
            Stripped(
                f"""\
if !{found_var} {{
{I}err = newDeserializationError(
{II}{message_literal},
{I})
{I}return
}}"""
            )
        )

    constructing_statements = []  # type: List[Stripped]

    constructor_arguments = [
        golang_naming.variable_name(Identifier(f"the_{arg.name}"))
        for arg in cls.constructor.arguments
        if not isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation)
    ]  # type: List[Stripped]

    new_function = golang_naming.function_name(Identifier(f"new_{cls.name}"))

    if len(constructor_arguments) > 0:
        constructor_arguments_joined = "\n".join(
            f"{arg}," for arg in constructor_arguments
        )

        constructing_statements.append(
            Stripped(
                f"""\
instance = aastypes.{new_function}(
{I}{indent_but_first_line(constructor_arguments_joined, I)}
)"""
            )
        )
    else:
        constructing_statements.append(
            Stripped(f"instance = aastypes.{new_function}()")
        )

    for arg in cls.constructor.arguments:
        if not isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation):
            continue

        setter_name = golang_naming.setter_name(arg.name)
        prop_var = golang_naming.variable_name(Identifier(f"the_{arg.name}"))

        constructing_statements.append(
            Stripped(
                f"""\
instance.{setter_name}(
{I}{prop_var},
)"""
            )
        )

    construct_blocks.append(Stripped("\n".join(constructing_statements)))

    construct = "\n\n".join(construct_blocks)

    # endregion

    function_name = golang_naming.private_function_name(
        Identifier(f"read_{cls.name}_as_sequence")
    )

    return Stripped(
        f"""\
// De-serialize the instance of [aastypes.{interface_name}]
// as a sequence of XML elements, each representing a property
// of [aastypes.{interface_name}].
//
// The reading stops as soon as we encounter a non-start element, and we return
// that token as the `next` token.
func {function_name}(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (instance aastypes.{interface_name},
{I}next xml.Token,
{I}err error,
) {{
{I}{indent_but_first_line(initialization, I)}

{I}for {{
{II}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{II}if err != nil {{
{III}return
{II}}}

{II}if _, isEOF := current.(eof); isEOF {{
{III}break
{II}}}

{II}startElement, ok := current.(xml.StartElement)
{II}if !ok {{
{III}if charData, isCharData := current.(xml.CharData); isCharData {{
{IIII}err = newDeserializationError(
{IIIII}fmt.Sprintf(
{IIIIII}"Expected a sequence of XML elements representing properties "+
{IIIIII}"of {interface_name}, but got text: %s",
{IIIIII}string(charData),
{IIIII}),
{IIII})
{IIII}return
{III}}}

{III}break
{II}}}

{II}var local string
{II}local, err = extractLocalNameFromStartElement(startElement)
{II}if err != nil {{
{III}return
{II}}}

{II}// Move the current to the content of the XML element
{II}current, err = readNext(decoder, nil)
{II}if err != nil {{
{III}return
{II}}}

{II}{indent_but_first_line(switch_snippet, II)}

{II}if valueErr != nil {{
{III}if deseriaErr, ok := valueErr.(*DeserializationError); ok {{
{IIII}deseriaErr.Path.PrependName(
{IIIII}&aasreporting.NameSegment{{Name: local}},
{IIII})
{III}}}
{III}err = valueErr
{II}}}

{II}if err != nil {{
{III}return
{II}}}

{II}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{II}if err != nil {{
{III}return
{II}}}

{II}err = checkEndElement(current, local)
{II}if err != nil {{
{III}return
{II}}}

{II}current, err = readNext(decoder, current)
{II}if err != nil {{
{III}return
{II}}}
{I}}}

{I}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}next = current

{I}{indent_but_first_line(construct, I)}
{I}return
}}"""
    )


def _generate_read_with_lookahead_without_dispatch(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    interface_name = golang_naming.interface_name(cls.name)
    function_name = golang_naming.private_function_name(
        Identifier(f"read_{cls.name}_with_lookahead")
    )

    xml_class_name_literal = golang_common.string_literal(
        naming.xml_class_name(cls.name)
    )

    read_as_sequence_name = golang_naming.private_function_name(
        Identifier(f"read_{cls.name}_as_sequence")
    )

    return Stripped(
        f"""\
// De-serialize an instance of [aastypes.{interface_name}]
// as an XML element where the start element is expected to have been already
// read as `current` token.
//
// The de-serialization stops by consuming the final end element.
func {function_name}(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (instance aastypes.{interface_name},
{I}err error,
) {{
{I}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}var local string
{I}local, err = parseAsStartElementAndExtractLocalName(
{II}current,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}expectedLocal := {xml_class_name_literal}
{I}if local != expectedLocal {{
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Expected a start element with local name %s, "+
{IIIII}"but got a start element with local name %s",
{IIII}expectedLocal, local,
{III}),
{II})
{II}return
{I}}}

{I}current, err = readNext(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}instance, current, err = {read_as_sequence_name}(
{II}decoder,
{II}current,
)
{I}if err != nil {{
{II}return
{I}}}

{I}err = checkEndElement(current, local)
{I}return
}}"""
    )


@require(
    lambda cls: len(cls.concrete_descendants) > 0,
    "The class must have one or more concrete descendants; "
    "otherwise the dispatch makes no sense",
)
def _generate_read_with_lookahead_with_dispatch(
    cls: intermediate.ClassUnion,
) -> Stripped:
    interface_name = golang_naming.interface_name(cls.name)
    function_name = golang_naming.private_function_name(
        Identifier(f"read_{cls.name}_with_lookahead")
    )

    case_blocks = []  # type: List[Stripped]

    for descendant_cls in cls.concrete_descendants:
        xml_class_name_literal = golang_common.string_literal(
            naming.xml_class_name(descendant_cls.name)
        )
        read_as_sequence = golang_naming.private_function_name(
            Identifier(f"read_{descendant_cls.name}_as_sequence")
        )
        case_blocks.append(
            Stripped(
                f"""\
case {xml_class_name_literal}:
{I}instance, current, err = {read_as_sequence}(
{II}decoder, current,
{I})"""
            )
        )

    if isinstance(cls, intermediate.ConcreteClass):
        xml_class_name_literal = golang_common.string_literal(
            naming.xml_class_name(cls.name)
        )
        read_as_sequence = golang_naming.private_function_name(
            Identifier(f"read_{cls.name}_as_sequence")
        )
        case_blocks.append(
            Stripped(
                f"""\
case {xml_class_name_literal}:
{I}instance, current, err = {read_as_sequence}(
{II}decoder, current,
{I})"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}err = newDeserializationError(
{II}fmt.Sprintf(
{III}"Unexpected start element %s as discriminator "+
{IIII}"for {interface_name}",
{III}local,
{II}),
{I})"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    switch_stmt = Stripped(
        f"""\
switch local {{
{case_blocks_joined}
}}"""
    )

    return Stripped(
        f"""\
// De-serialize an instance of [aastypes.{interface_name}]
// as an XML element where the start element is expected to have been already read
// as `current` token.
//
// The de-serialization stops by consuming the final end element.
func {function_name}(
{I}decoder *xml.Decoder,
{I}current xml.Token,
) (instance aastypes.{interface_name},
{I}err error,
) {{
{I}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}var local string
{I}local, err = parseAsStartElementAndExtractLocalName(
{II}current,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}// Move the current to the properties of the instance
{I}current, err = readNext(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}{indent_but_first_line(switch_stmt, I)}
{I}if err != nil {{
{II}return
{I}}}

{I}err = checkEndElement(current, local)
{I}return
}}"""
    )


def _generate_unmarshal_for(cls: intermediate.ClassUnion) -> Stripped:
    interface_name = golang_naming.interface_name(cls.name)
    function_name = golang_naming.private_function_name(
        Identifier(f"unmarshal_{cls.name}")
    )

    read_with_lookahead = golang_naming.private_function_name(
        Identifier(f"read_{cls.name}_with_lookahead")
    )

    return Stripped(
        f"""\
// Unmarshal an instance of [aastypes.{interface_name}]
// serialized as an XML element.
//
// The XML element must live in the [Namespace] space.
func {function_name}(
{I}decoder *xml.Decoder,
) (instance aastypes.{interface_name},
{I}err error,
) {{
{I}var current xml.Token
{I}current, err = readNext(decoder, nil)
{I}if _, isEOF := current.(eof); isEOF {{
{II}err = newDeserializationError(
{III}"Expected an instance of {interface_name} "+
{IIII}"serialized as an XML element, but reached the end of file.",
{II})
{II}return
{I}}}

{I}instance, err = {read_with_lookahead}(
{II}decoder,
{II}current,
{I})
{I}return
}}"""
    )


def _generate_unmarshal(symbol_table: intermediate.SymbolTable) -> Stripped:
    case_blocks = []  # type: List[Stripped]
    for cls in symbol_table.concrete_classes:
        read_as_sequence = golang_naming.private_function_name(
            Identifier(f"read_{cls.name}_as_sequence")
        )

        xml_class_name_literal = golang_common.string_literal(
            naming.xml_class_name(cls.name)
        )

        case_blocks.append(
            Stripped(
                f"""\
case {xml_class_name_literal}:
{I}instance, current, err = {read_as_sequence}(
{II}decoder, current,
{I})"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default:
{II}err = newDeserializationError(
{III}fmt.Sprintf(
{IIII}"Unexpected XML element name %s as class discriminator",
{IIII}local,
{III}),
{II})"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    return Stripped(
        f"""\
// Unmarshal an instance of [aastypes.IClass] serialized as an XML element.
//
// The XML element must live in the [Namespace] space.
func Unmarshal(
{I}decoder *xml.Decoder,
) (instance aastypes.IClass, err error) {{
{I}var current xml.Token
{I}current, err = readNext(decoder, nil)
{I}if err != nil {{
{II}return
{I}}}

{I}current, err = skipEmptyTextWhitespaceAndComments(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}var local string
{I}local, err = parseAsStartElementAndExtractLocalName(
{II}current,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}// Move the current to the properties of the instance
{I}current, err = readNext(decoder, current)
{I}if err != nil {{
{II}return
{I}}}

{I}switch local {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
{I}if err != nil {{
{II}return
{I}}}

{I}err = checkEndElement(current, local)
{I}return
}}"""
    )


# endregion

# region Serialization


def _generate_serialization_error() -> List[Stripped]:
    return [
        Stripped(
            f"""\
// Represent an error during the serialization.
//
// Implements `error`.
type SerializationError struct {{
{I}Path    *aasreporting.Path
{I}Message string
}}"""
        ),
        Stripped(
            f"""\
func newSerializationError(message string) *SerializationError {{
{I}return &SerializationError{{
{II}Path:    &aasreporting.Path{{}},
{II}Message: message,
{I}}}
}}"""
        ),
        Stripped(
            f"""\
func (se *SerializationError) Error() string {{
{I}return fmt.Sprintf(
{II}"%s: %s",
{II}se.PathString(),
{II}se.Message,
{I})
}}"""
        ),
        Stripped(
            f"""\
// Render the path as a string.
func (se *SerializationError) PathString() string {{
{I}return aasreporting.ToGolangPath(se.Path)
}}"""
        ),
    ]


def _generate_write_start_element() -> Stripped:
    return Stripped(
        f"""\
// Write the start element with the given `local` name to the encoder.
//
// Do not flush.
//
// If the `withNamespace` is set, set the [xml.Name.Space] property in the element
// accordingly.
func writeStartElement(
{I}encoder *xml.Encoder,
{I}local string,
{I}withNamespace bool,
) (err error) {{
{I}startElement := xml.StartElement{{Name: xml.Name{{Local: local}}}}
{I}if withNamespace {{
{II}startElement.Name.Space = Namespace
{I}}}

{I}err = encoder.EncodeToken(startElement)
{I}return
}}"""
    )


def _generate_write_end_element() -> Stripped:
    return Stripped(
        f"""\
// Write the end element with the given `local` name to the encoder.
//
// Do not flush.
//
// If the `withNamespace` is set, set the [xml.Name.Space] property in the element
// accordingly.
func writeEndElement(
{I}encoder *xml.Encoder,
{I}local string,
{I}withNamespace bool,
) (err error) {{
{I}endElement := xml.EndElement{{Name: xml.Name{{Local: local}}}}
{I}if withNamespace {{
{II}endElement.Name.Space = Namespace
{I}}}

{I}err = encoder.EncodeToken(endElement)
{I}return
}}"""
    )


def _generate_write_text() -> Stripped:
    return Stripped(
        f"""\
// Write the `text` to the encoder.
//
// Do not flush.
//
// If `text` is empty, do nothing.
func writeText(
{I}encoder *xml.Encoder,
{I}text string,
) (err error) {{
{I}if len(text) > 0 {{
{II}err = encoder.EncodeToken(
{III}xml.CharData([]byte(text)),
{II})
{I}}}
{I}return
}}"""
    )


def _generate_write_boolean_property() -> Stripped:
    return Stripped(
        f"""\
// Write the `value` of a property as `xs:boolean` enclosed in an XML element.
//
// Do not flush.
//
// The XML namespace is expected to have been defined outside of the resulting XML
// element.
func writeBooleanProperty(
{I}encoder *xml.Encoder,
{I}local string,
{I}value bool,
) (err error) {{
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}text := "true"
{I}if !value {{
{II}text = "false"
{I}}}
{I}err = writeText(encoder, text)
{I}if err != nil {{
{II}return
{I}}}

{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_write_long_property() -> Stripped:
    return Stripped(
        f"""\
// Write the `value` of a property as `xs:long` enclosed in an XML element.
//
// Do not flush.
//
// The XML namespace is expected to have been defined outside of the resulting XML
// element.
func writeLongProperty(
{I}encoder *xml.Encoder,
{I}local string,
{I}value int64,
{I}withNamespace bool,
) (err error) {{
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}text := strconv.FormatInt(value, 10)
{I}err = writeText(encoder, text)
{I}if err != nil {{
{II}return
{I}}}

{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_write_double_property() -> Stripped:
    return Stripped(
        f"""\
// Write the `value` of a property as `xs:double` enclosed in an XML element.
//
// Do not flush.
//
// The XML namespace is expected to have been defined outside of the resulting XML
// element.
func writeDoubleProperty(
{I}encoder *xml.Encoder,
{I}local string,
{I}value float64,
) (err error) {{
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}var text string

{I}// See: https://www.w3.org/TR/xmlschema-2/#double
{I}// for the exact literals.
{I}if math.IsInf(value, 0) {{
{II}if value < 0 {{
{III}text = "-INF"
{II}}} else {{
{III}text = "INF"
{II}}}
{I}}} else if math.IsNaN(value) {{
{II}text = "NaN"
{I}}} else {{
{II}text = strconv.FormatFloat(value, 'g', -1, 64)
{I}}}

{I}err = writeText(encoder, text)
{I}if err != nil {{
{II}return
{I}}}

{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_write_string_property() -> Stripped:
    return Stripped(
        f"""\
// Write the `value` of a property as `xs:string` enclosed in an XML element.
//
// Do not flush.
//
// The XML namespace is expected to have been defined outside of the resulting XML
// element.
func writeStringProperty(
{I}encoder *xml.Encoder,
{I}local string,
{I}value string,
) (err error) {{
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}err = writeText(encoder, value)
{I}if err != nil {{
{II}return
{I}}}

{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_write_bytes_property() -> Stripped:
    return Stripped(
        f"""\
// Write the `value` of a property as base64-encoded bytes.
//
// Do not flush.
//
// The XML namespace is expected to have been defined outside of the resulting XML
// element.
func writeBytesProperty(
{I}encoder *xml.Encoder,
{I}local string,
{I}value []byte,
) (err error) {{
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}text := b64.StdEncoding.EncodeToString(
{II}value,
{I})

{I}err = writeText(encoder, text)
{I}if err != nil {{
{II}return
{I}}}

{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_write_list_as_sequence() -> Stripped:
    return Stripped(
        f"""\
// Serialize the list of instances as a sequence of XML elements enclosed in a parent
// XML element with the `local` name.
func writeListProperty[T aastypes.IClass](
{I}encoder *xml.Encoder,
{I}local string,
{I}list []T,
) (err error) {{
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}for i, item := range list {{
{II}err = Marshal(
{III}encoder,
{III}item,
{III}false,
{II})
{II}if err != nil {{
{III}if seriaErr, ok := err.(*SerializationError); ok {{
{IIII}seriaErr.Path.PrependIndex(
{IIIII}&aasreporting.IndexSegment{{
{IIIIII}Index: i,
{IIIII}}},
{IIII})
{III}}}
{III}return
{II}}}
{I}}}

{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}false,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}return
}}"""
    )


def _generate_write_enumeration_property(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    enum_name = golang_naming.enum_name(enumeration.name)
    function_name = golang_naming.private_function_name(
        Identifier(f"write_{enumeration.name}_property")
    )
    to_string_name = golang_naming.function_name(
        Identifier(f"{enumeration.name}_to_string")
    )

    return Stripped(
        f"""\
// Write the `value` of a property as string representation
// of [aastypes.{enum_name}]
// enclosed in an XML element.
//
// Do not flush.
func {function_name}(
{I}encoder *xml.Encoder,
{I}local string,
{I}value aastypes.{enum_name},
) (err error) {{
{I}text, ok := aasstringification.{to_string_name}(
{II}value,
{I})
{I}if !ok {{
{II}err = newSerializationError(
{III}fmt.Sprintf(
{IIII}"Unexpected literal of {enum_name}: %v",
{IIII}value,
{III}),
{II})
{II}return
{I}}}

{I}err = writeStringProperty(encoder, local, text)
{I}return
}}"""
    )


_WRITE_FUNCTION_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: "writeBooleanProperty",
    intermediate.PrimitiveType.INT: "writeLongProperty",
    intermediate.PrimitiveType.FLOAT: "writeDoubleProperty",
    intermediate.PrimitiveType.STR: "writeStringProperty",
    intermediate.PrimitiveType.BYTEARRAY: "writeBytesProperty",
}
assert all(
    literal in _WRITE_FUNCTION_BY_PRIMITIVE_TYPE
    for literal in intermediate.PrimitiveType
)


def _generate_snippet_to_serialize_property(prop: intermediate.Property) -> Stripped:
    blocks = []  # type: List[Stripped]

    local_literal = golang_common.string_literal(naming.xml_property(prop.name))

    segment_name_literal = golang_common.string_literal(
        f"{golang_naming.getter_name(prop.name)}()"
    )

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    getter_name = golang_naming.getter_name(prop.name)
    access_expr = f"that.{getter_name}()"
    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        prop_var = golang_naming.variable_name(Identifier(f"the_{prop.name}"))
        access_expr = prop_var

        blocks.append(
            Stripped(
                f"""\
{prop_var} := that.{getter_name}()"""
            )
        )

    write_block = None  # type: Optional[Stripped]

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation) or (
        isinstance(type_anno, intermediate.OurTypeAnnotation)
        and isinstance(
            type_anno.our_type,
            (intermediate.ConstrainedPrimitive, intermediate.Enumeration),
        )
    ):
        primitive_type = intermediate.try_primitive_type(type_anno)

        if primitive_type is not None:
            write_function = _WRITE_FUNCTION_BY_PRIMITIVE_TYPE[primitive_type]
        else:
            assert isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
                type_anno.our_type, intermediate.Enumeration
            )
            write_function = golang_naming.private_function_name(
                Identifier(f"write_{type_anno.our_type.name}_property")
            )

        pointer = golang_pointering.is_pointer_type(prop.type_annotation)

        if_err_nil_prepend_name_if_serialization_error = Stripped(
            f"""\
if err != nil {{
{I}if seriaErr, ok := err.(*SerializationError); ok {{
{II}seriaErr.Path.PrependName(
{III}&aasreporting.NameSegment{{
{IIII}Name: {segment_name_literal},
{III}}},
{II})
{I}}}
{I}return
}}"""
        )

        if pointer:
            write_block = Stripped(
                f"""\
err = {write_function}(
{I}encoder,
{I}{local_literal},
{I}*{access_expr},
)
{if_err_nil_prepend_name_if_serialization_error}"""
            )
        else:
            write_block = Stripped(
                f"""\
err = {write_function}(
{I}encoder,
{I}{local_literal},
{I}{access_expr},
)
{if_err_nil_prepend_name_if_serialization_error}"""
            )

    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        our_type = type_anno.our_type

        if isinstance(our_type, intermediate.Enumeration):
            raise AssertionError("Must have been handled before")

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            raise AssertionError("Must have been handled before")

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if (
                isinstance(our_type, intermediate.ConcreteClass)
                and len(our_type.concrete_descendants) == 0
            ):
                write_as_sequence_name = golang_naming.private_function_name(
                    Identifier(f"write_{our_type.name}_as_sequence")
                )
                write_block = Stripped(
                    f"""\
err = writeStartElement(
{I}encoder,
{I}{local_literal},
{I}false,
)
if err != nil {{
{I}return
}}
err = {write_as_sequence_name}(
{I}encoder,
{I}{access_expr},
)
if err != nil {{
{I}if seriaErr, ok := err.(*SerializationError); ok {{
{II}seriaErr.Path.PrependName(
{III}&aasreporting.NameSegment{{
{IIII}Name: {segment_name_literal},
{III}}},
{II})
{I}}}
{I}return
}}
err = writeEndElement(
{I}encoder,
{I}{local_literal},
{I}false,
)
if err != nil {{
{I}return
}}"""
                )
            else:
                write_block = Stripped(
                    f"""\
err = writeStartElement(
{I}encoder,
{I}{local_literal},
false,
)
if err != nil {{
{I}return
}}
err = Marshal(
{I}encoder,
{I}{access_expr},
{I}false,
)
if err != nil {{
{I}if seriaErr, ok := err.(*SerializationError); ok {{
{II}seriaErr.Path.PrependName(
{III}&aasreporting.NameSegment{{
{IIII}Name: {segment_name_literal},
{III}}},
{II})
{I}}}
{I}return
}}
err = writeEndElement(
{I}encoder,
{I}{local_literal},
false,
)
if err != nil {{
{I}return
}}"""
                )

        else:
            assert_never(our_type)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert isinstance(
            type_anno.items, intermediate.OurTypeAnnotation
        ) and isinstance(
            type_anno.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ), (
            f"NOTE (mristin, 2023-06-20): We expect only lists of classes "
            f"at the moment, but you specified {type_anno}. "
            f"Please contact the developers if you need this feature."
        )

        write_block = Stripped(
            f"""\
err = writeListProperty(
{I}encoder,
{I}{local_literal},
{I}{access_expr},
)
if err != nil {{
{I}if seriaErr, ok := err.(*SerializationError); ok {{
{II}seriaErr.Path.PrependName(
{III}&aasreporting.NameSegment{{
{IIII}Name: {segment_name_literal},
{III}}},
{II})
{I}}}
{I}return
}}"""
        )

    else:
        assert_never(type_anno)

    assert write_block is not None

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        blocks.append(
            Stripped(
                f"""\
if {access_expr} != nil {{
{I}{indent_but_first_line(write_block, I)}
}}"""
            )
        )
    else:
        blocks.append(write_block)

    blocks.append(
        Stripped(
            f"""\
err = encoder.Flush()
if err != nil {{
{I}return err
}}"""
        )
    )

    blocks.insert(0, Stripped(f"// region {getter_name}"))
    blocks.append(Stripped("// endregion"))

    return Stripped("\n\n".join(blocks))


def _generate_write_as_sequence(cls: intermediate.ConcreteClass) -> Stripped:
    function_name = golang_naming.private_function_name(
        Identifier(f"write_{cls.name}_as_sequence")
    )

    interface_name = golang_naming.interface_name(cls.name)

    prop_blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        prop_blocks.append(_generate_snippet_to_serialize_property(prop=prop))

    if len(prop_blocks) == 0:
        prop_blocks.append(Stripped("// Intentionally empty."))

    prop_blocks_joined = "\n\n".join(prop_blocks)

    return Stripped(
        f"""\
// Serialize the instance
// of [aastypes.{interface_name}]
// as a sequence of properties, each represented as an XML element.
//
// The XML namespace is expected to be set in the one of the parent elements
// enclosing the sequence.
//
// Flush at the end element of each property.
func {function_name}(
{I}encoder *xml.Encoder,
{I}that aastypes.{interface_name},
) (err error) {{
{I}{indent_but_first_line(prop_blocks_joined, I)}

{I}return
}}"""
    )


def _generate_write_for(cls: intermediate.ConcreteClass) -> Stripped:
    interface_name = golang_naming.interface_name(cls.name)

    if len(cls.concrete_descendants) == 0:
        function_name = golang_naming.private_function_name(
            Identifier(f"write_{cls.name}")
        )
        doc_comment = Stripped(
            f"""\
// Serialize the instance of [aastypes.{interface_name}]
// enclosed in an XML element which represents the model type.
//
// If `withNamespace` is set, the `xmlns` attribute is set in the outer XML element.
//
// Flush once the closing end element has been written."""
        )
    else:
        model_type_literal = golang_naming.enum_literal_name(
            enumeration_name=Identifier("Model_type"), literal_name=cls.name
        )

        doc_comment = Stripped(
            f"""\
// Serialize the instance of [aastypes.{interface_name}]
// enclosed in an XML element which represents the model type.
//
// Do not dispatch on the runtime model type, *i.e.*, assume that the runtime model type
// is exactly [aastypes.{model_type_literal}]. If you need dispatch,
// call [Marshal].
//
// If `withNamespace` is set, the `xmlns` attribute is set in the outer XML element.
//
// Flush once the closing end element has been written."""
        )

        function_name = golang_naming.private_function_name(
            Identifier(f"write_{cls.name}_without_dispatch")
        )

    xml_class_name_literal = golang_common.string_literal(
        naming.xml_class_name(cls.name)
    )

    write_as_sequence_name = golang_naming.private_function_name(
        Identifier(f"write_{cls.name}_as_sequence")
    )

    return Stripped(
        f"""\
{doc_comment}
func {function_name}(
{I}encoder *xml.Encoder,
{I}that aastypes.{interface_name},
{I}withNamespace bool,
) (err error) {{
{I}local := {xml_class_name_literal}
{I}
{I}err = writeStartElement(
{II}encoder,
{II}local,
{II}withNamespace,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}err = {write_as_sequence_name}(
{II}encoder,
{II}that,
{I})
{I}if err != nil {{
{II}return
{I}}}
{I}
{I}err = writeEndElement(
{II}encoder,
{II}local,
{II}withNamespace,
{I})
{I}if err != nil {{
{II}return
{I}}}

{I}err = encoder.Flush()
{I}return
}}"""
    )


def _generate_marshal(symbol_table: intermediate.SymbolTable) -> Stripped:
    case_blocks = []  # type: List[Stripped]
    for cls in symbol_table.concrete_classes:
        model_type_literal = golang_naming.enum_literal_name(
            enumeration_name=Identifier("Model_type"), literal_name=cls.name
        )

        interface_name = golang_naming.interface_name(cls.name)

        if len(cls.concrete_descendants) == 0:
            write_function = golang_naming.private_function_name(
                Identifier(f"write_{cls.name}")
            )
        else:
            write_function = golang_naming.private_function_name(
                Identifier(f"write_{cls.name}_without_dispatch")
            )

        case_blocks.append(
            Stripped(
                f"""\
case aastypes.{model_type_literal}:
{I}err = {write_function}(
{II}encoder,
{II}that.(aastypes.{interface_name}),
{II}withNamespace,
{I})"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}err = newSerializationError(
{II}fmt.Sprintf(
{III}"Unexpected model type: %v",
{III}that.ModelType(),
{II}),
{I})"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)
    model_type_getter = golang_naming.getter_name(Identifier("model_type"))

    return Stripped(
        f"""\
// Serialize `that` instance as an XML element.
//
// If `withNamespace` is set, the `xmlns` attribute is set in the XML element
// to [Namespace].
func Marshal(
{I}encoder *xml.Encoder,
{I}that aastypes.IClass,
{I}withNamespace bool,
) (err error) {{
{I}switch that.{model_type_getter}() {{
{I}{indent_but_first_line(case_blocks_joined, I)}
{I}}}
{I}return
}}"""
    )


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
    spec_impls: specific_implementations.SpecificImplementations,
    repo_url: Stripped,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the Golang code for the general de/serialization."""
    aastypes_url_literal = golang_common.string_literal(f"{repo_url}/types")

    aasreporting_url_literal = golang_common.string_literal(f"{repo_url}/reporting")

    aasstringification_url_literal = golang_common.string_literal(
        f"{repo_url}/stringification"
    )

    aasverification_url_literal = golang_common.string_literal(
        f"{repo_url}/verification"
    )

    namespace_literal = golang_common.string_literal(
        symbol_table.meta_model.xml_namespace
    )

    blocks = [
        Stripped(
            """\
// Package xmlization de/serializes model instances to and from XML.
//
// To de-serialize, call one of the `Unmarshal*` functions.
//
// To serialize, call the [Marshal] function.
package xmlization"""
        ),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}b64 "encoding/base64"
{I}"encoding/xml"
{I}"fmt"
{I}"io"
{I}"math"
{I}"strconv"
{I}"strings"
{I}"unicode"
{I}aasreporting {aasreporting_url_literal}
{I}aasstringification {aasstringification_url_literal}
{I}aastypes {aastypes_url_literal}
{I}aasverification {aasverification_url_literal}
)"""
        ),
        Stripped("// region De-serialization"),
    ]

    blocks.extend(_generate_deserialization_error_and_its_methods())

    blocks.extend(
        [
            Stripped(
                """\
// This is class for a sentinel token to signal the end-of-file.
type eof struct{}"""
            ),
            _generate_is_whitespace(),
            _generate_read_next(),
            _generate_skip_empty_text_whitespace_and_comments(),
            _generate_read_text(),
            _generate_read_text_as_boolean(),
            _generate_read_text_as_long(),
            _generate_read_text_as_double(),
            _generate_read_text_as_base64_encoded_bytes(),
            Stripped(
                f"""\
const Namespace = {namespace_literal}"""
            ),
            _generate_check_start_element(),
            _generate_extract_local_name_from_start_element(),
            _generate_parse_as_start_element_and_extract_local_name(),
            _generate_check_end_element(),
            _generate_read_list(),
        ]
    )

    errors = []  # type: List[Error]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            blocks.append(_generate_read_text_as_enumeration(enumeration=our_type))

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            pass
        elif isinstance(our_type, intermediate.AbstractClass):
            blocks.append(_generate_read_with_lookahead_with_dispatch(cls=our_type))

            blocks.append(_generate_unmarshal_for(cls=our_type))

        elif isinstance(our_type, intermediate.ConcreteClass):
            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"Xmlization/read_{our_type.name}_as_sequence.go"
                )

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The xmlization snippet is missing "
                            f"for the implementation-specific "
                            f"class {our_type.name}: {implementation_key}",
                        )
                    )
                    continue
            else:
                blocks.append(_generate_read_as_sequence(cls=our_type))

            if len(our_type.concrete_descendants) > 0:
                blocks.append(_generate_read_with_lookahead_with_dispatch(cls=our_type))
            else:
                blocks.append(
                    _generate_read_with_lookahead_without_dispatch(cls=our_type)
                )

            blocks.append(_generate_unmarshal_for(cls=our_type))
        else:
            assert_never(our_type)

    blocks.append(_generate_unmarshal(symbol_table=symbol_table))

    blocks.append(Stripped("// endregion"))

    blocks.append(Stripped("// region Serialization"))

    blocks.extend(_generate_serialization_error())

    blocks.extend(
        [
            _generate_write_start_element(),
            _generate_write_end_element(),
            _generate_write_text(),
            _generate_write_boolean_property(),
            _generate_write_long_property(),
            _generate_write_double_property(),
            _generate_write_string_property(),
            _generate_write_bytes_property(),
            _generate_write_list_as_sequence(),
        ]
    )

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            blocks.append(_generate_write_enumeration_property(enumeration=our_type))

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2023-06-18):
            # We will serialize constrained primitives as primitives.
            pass

        elif isinstance(our_type, intermediate.AbstractClass):
            # NOTE (mristin, 2023-06-18):
            # We will use general ``write`` function.
            pass

        elif isinstance(our_type, intermediate.ConcreteClass):
            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"Xmlization/write_{our_type.name}_as_sequence.go"
                )

                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The xmlization snippet is missing "
                            f"for the implementation-specific "
                            f"class {our_type.name}: {implementation_key}",
                        )
                    )
                    continue
            else:
                blocks.append(_generate_write_as_sequence(cls=our_type))

            blocks.append(_generate_write_for(cls=our_type))
        else:
            assert_never(our_type)

    blocks.append(_generate_marshal(symbol_table=symbol_table))

    blocks.append(Stripped("// endregion"))

    if len(errors) > 0:
        return None, errors

    blocks.append(golang_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None
