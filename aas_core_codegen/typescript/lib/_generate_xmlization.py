"""Generate code for XML de/serialization."""

import io
from typing import Tuple, Optional, List, Dict

from icontract import ensure

from aas_core_codegen import intermediate, naming, specific_implementations
from aas_core_codegen.common import (
    Error,
    Stripped,
    Identifier,
    assert_never,
    indent_but_first_line,
)
from aas_core_codegen.typescript import (
    common as typescript_common,
    naming as typescript_naming,
)
from aas_core_codegen.typescript.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)


_PARSE_FUNCTION_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: Identifier("parseBooleanText"),
    intermediate.PrimitiveType.INT: Identifier("parseIntegerText"),
    intermediate.PrimitiveType.FLOAT: Identifier("parseFloatText"),
    intermediate.PrimitiveType.STR: Identifier("parseStringText"),
    intermediate.PrimitiveType.BYTEARRAY: Identifier("parseBase64EncodedBytesText"),
}


_SERIALIZE_FUNCTION_BY_PRIMITIVE_TYPE = {
    intermediate.PrimitiveType.BOOL: Identifier("serializeBooleanText"),
    intermediate.PrimitiveType.INT: Identifier("serializeIntegerText"),
    intermediate.PrimitiveType.FLOAT: Identifier("serializeFloatText"),
    intermediate.PrimitiveType.STR: Identifier("serializeStringText"),
    intermediate.PrimitiveType.BYTEARRAY: Identifier("serializeBase64EncodedBytesText"),
}


def _parse_function_for_atomic_type(
    type_annotation: intermediate.AtomicTypeAnnotation,
) -> Identifier:
    """Resolve the generated parse helper for an atomic XML text value."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return _PARSE_FUNCTION_BY_PRIMITIVE_TYPE[type_annotation.a_type]

    if isinstance(type_annotation, intermediate.OurTypeAnnotation):
        if isinstance(type_annotation.our_type, intermediate.Enumeration):
            return typescript_naming.function_name(
                Identifier(f"parse_{type_annotation.our_type.name}_text")
            )

        if isinstance(type_annotation.our_type, intermediate.ConstrainedPrimitive):
            return _PARSE_FUNCTION_BY_PRIMITIVE_TYPE[
                type_annotation.our_type.constrainee
            ]

        raise AssertionError(
            f"Unexpected atomic XML text type: {type_annotation.our_type}"
        )

    assert_never(type_annotation)


def _parse_function_name_for_concrete_class(
    cls: intermediate.ConcreteClass,
) -> Identifier:
    """Generate the name of the parse function for the concrete class."""
    return typescript_naming.function_name(
        Identifier(f"parse_{cls.name}_from_open_tag")
    )


def _serialize_function_for_atomic_type(
    type_annotation: intermediate.AtomicTypeAnnotation,
) -> Identifier:
    """Resolve the generated serializer helper for an atomic XML text value."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return _SERIALIZE_FUNCTION_BY_PRIMITIVE_TYPE[type_annotation.a_type]

    if isinstance(type_annotation, intermediate.OurTypeAnnotation):
        if isinstance(type_annotation.our_type, intermediate.Enumeration):
            return typescript_naming.function_name(
                Identifier(f"serialize_{type_annotation.our_type.name}_text")
            )

        if isinstance(type_annotation.our_type, intermediate.ConstrainedPrimitive):
            return _SERIALIZE_FUNCTION_BY_PRIMITIVE_TYPE[
                type_annotation.our_type.constrainee
            ]

        raise AssertionError(
            f"Unexpected atomic XML text type: {type_annotation.our_type}"
        )

    assert_never(type_annotation)


def _generate_parse_text_as_enumeration(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    """Generate parser for text representation of an enumeration literal."""
    enum_name = typescript_naming.enum_name(enumeration.name)
    parse_function_name = typescript_naming.function_name(
        Identifier(f"parse_{enumeration.name}_text")
    )
    from_string_function = typescript_naming.function_name(
        Identifier(f"{enumeration.name}_from_string")
    )

    return Stripped(
        f"""\
function {parse_function_name}(
{I}text: string
): AasCommon.Either<AasTypes.{enum_name}, DeserializationError> {{
{I}const literal = AasStringification.{from_string_function}(text);
{I}if (literal === null) {{
{II}return newDeserializationError<AasTypes.{enum_name}>(
{III}`Unexpected literal of {enum_name}: ${{text}}`
{II});
{I}}}

{I}return new AasCommon.Either<AasTypes.{enum_name}, DeserializationError>(
{II}literal,
{II}null
{I});
}}"""
    )


def _generate_parse_case_for_property(
    cls: intermediate.ConcreteClass,
    prop: intermediate.Property,
    var_name: Identifier,
) -> Stripped:
    """Generate a switch case to parse a property from XML element content."""
    xml_name_literal = typescript_common.string_literal(naming.xml_property(prop.name))

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    duplicate_check = Stripped(
        f"""\
if ({var_name} !== null) {{
{I}propertyError = new DeserializationError(
{II}"Property " +
{III}{xml_name_literal} +
{III}" occurred more than once"
{I});
{I}break;
}}"""
    )

    if isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        if isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            as_function_name = typescript_naming.function_name(
                Identifier(f"as_{type_anno.our_type.name}")
            )

            expected_name = typescript_naming.interface_name(type_anno.our_type.name)

            parse_body = Stripped(
                f"""\
const classOrError = parseClassValueInProperty(cursor, propertyStartTag);
if (classOrError.error !== null) {{
{I}propertyError = classOrError.error;
{I}break;
}}

const casted = AasTypes.{as_function_name}(classOrError.mustValue());
if (casted === null) {{
{I}propertyError = new DeserializationError(
{II}"Expected property " +
{III}{xml_name_literal} +
{III}" to contain an instance of {expected_name}"
{I});
{I}break;
}}

{var_name} = casted;"""
            )
        else:
            parse_function = _parse_function_for_atomic_type(type_anno)
            parse_body = Stripped(
                f"""\
const textOrError = readTextContentAndConsumeEndTag(cursor, propertyStartTag);
if (textOrError.error !== null) {{
{I}propertyError = textOrError.error;
{I}break;
}}

const parsedOrError = {parse_function}(textOrError.mustValue());
if (parsedOrError.error !== null) {{
{I}propertyError = parsedOrError.error;
{I}break;
}}

{var_name} = parsedOrError.mustValue();"""
            )

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        list_items_type = typescript_common.generate_type(
            type_anno.items,
            types_module=Identifier("AasTypes"),
        )

        if isinstance(
            type_anno.items,
            (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
        ) and not (
            isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and isinstance(
                type_anno.items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            )
        ):
            parse_item_function = _parse_function_for_atomic_type(type_anno.items)

            parse_body = Stripped(
                f"""\
const parsedItems = new Array<{list_items_type}>();
let itemIndex = 0;

cursor.skipIgnorable();
while (true) {{
{I}const itemOrClose = cursor.current();
{I}if (itemOrClose === null) {{
{II}propertyError = new DeserializationError(
{III}"Expected an XML element corresponding to a list item " +
{IIII}"or property closing element, but got end of token stream"
{II});
{II}break;
{I}}}

{I}if (itemOrClose instanceof CloseTagToken) {{
{II}const propertyCloseError = checkExpectedCloseTag(
{III}itemOrClose,
{III}localNameOfTag(propertyStartTag.tag)
{II});
{II}if (propertyCloseError !== null) {{
{III}propertyError = propertyCloseError;
{III}break;
{II}}}

{II}cursor.advance();
{II}break;
{I}}}

{I}if (!(itemOrClose instanceof OpenTagToken)) {{
{II}propertyError = new DeserializationError(
{III}"Expected an XML element corresponding to a list item " +
{IIII}`or property closing element, but got token kind: ${{itemOrClose.kind}}`
{II});
{II}break;
{I}}}

{I}const itemStartTag = itemOrClose;
{I}const itemNamespaceError = checkExpectedOpenTagNamespace(itemStartTag);
{I}if (itemNamespaceError !== null) {{
{II}propertyError = itemNamespaceError;
{II}break;
{I}}}

{I}const itemLocalName = localNameOfTag(itemStartTag.tag);
{I}if (itemLocalName !== "v") {{
{II}propertyError = new DeserializationError(
{III}`Expected list item element 'v', but got: ${{itemLocalName}}`
{II});
{II}break;
{I}}}

{I}cursor.advance();

{I}const itemTextOrError = readTextContentAndConsumeEndTag(cursor, itemStartTag);
{I}if (itemTextOrError.error !== null) {{
{II}propertyError = itemTextOrError.error;
{II}propertyError.path.prepend(new IndexSegment(itemIndex));
{II}break;
{I}}}

{I}const itemParsedOrError = {parse_item_function}(itemTextOrError.mustValue());
{I}if (itemParsedOrError.error !== null) {{
{II}propertyError = itemParsedOrError.error;
{II}propertyError.path.prepend(new IndexSegment(itemIndex));
{II}break;
{I}}}

{I}parsedItems.push(itemParsedOrError.mustValue());
{I}itemIndex++;
{I}cursor.skipIgnorable();
}}

if (propertyError === null) {{
{I}{var_name} = parsedItems;
}}"""
            )

        elif isinstance(type_anno.items, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            as_function_name = typescript_naming.function_name(
                Identifier(f"as_{type_anno.items.our_type.name}")
            )
            expected_name = typescript_naming.interface_name(type_anno.items.our_type.name)

            parse_body = Stripped(
                f"""\
const parsedItems = new Array<{list_items_type}>();
let itemIndex = 0;

cursor.skipIgnorable();
while (true) {{
{I}const itemOrClose = cursor.current();
{I}if (itemOrClose === null) {{
{II}propertyError = new DeserializationError(
{III}"Expected an XML element corresponding to a list item " +
{IIII}"or property closing element, but got end of token stream"
{II});
{II}break;
{I}}}

{I}if (itemOrClose instanceof CloseTagToken) {{
{II}const propertyCloseError = checkExpectedCloseTag(
{III}itemOrClose,
{III}localNameOfTag(propertyStartTag.tag)
{II});
{II}if (propertyCloseError !== null) {{
{III}propertyError = propertyCloseError;
{III}break;
{II}}}

{II}cursor.advance();
{II}break;
{I}}}

{I}if (!(itemOrClose instanceof OpenTagToken)) {{
{II}propertyError = new DeserializationError(
{III}"Expected an XML element corresponding to a list item " +
{IIII}`or property closing element, but got token kind: ${{itemOrClose.kind}}`
{II});
{II}break;
{I}}}

{I}const itemStartTag = itemOrClose;
{I}const itemNamespaceError = checkExpectedOpenTagNamespace(itemStartTag);
{I}if (itemNamespaceError !== null) {{
{II}propertyError = itemNamespaceError;
{II}break;
{I}}}

{I}const dispatch = ROOT_DISPATCH_BY_LOCAL_NAME.get(localNameOfTag(itemStartTag.tag));
{I}if (dispatch === undefined) {{
{II}propertyError = new DeserializationError(
{III}`Unexpected XML element in list property: ${{localNameOfTag(itemStartTag.tag)}}`
{II});
{II}break;
{I}}}

{I}cursor.advance();

{I}const itemOrError = dispatch(cursor, itemStartTag);
{I}if (itemOrError.error !== null) {{
{II}propertyError = itemOrError.error;
{II}propertyError.path.prepend(new IndexSegment(itemIndex));
{II}break;
{I}}}

{I}const casted = AasTypes.{as_function_name}(itemOrError.mustValue());
{I}if (casted === null) {{
{II}propertyError = new DeserializationError(
{III}"Expected a list item instance of {expected_name}"
{II});
{II}propertyError.path.prepend(new IndexSegment(itemIndex));
{II}break;
{I}}}

{I}parsedItems.push(casted);
{I}itemIndex++;
{I}cursor.skipIgnorable();
}}

if (propertyError === null) {{
{I}{var_name} = parsedItems;
}}"""
            )
        else:
            parse_body = Stripped(
                f"""\
propertyError = new DeserializationError(
{I}"XML de-serialization of the list property " +
{II}{xml_name_literal} +
{II}" in {typescript_naming.class_name(cls.name)} can not handle list items " +
{II}"of this kind"
);"""
            )
    else:
        assert_never(type_anno)

    return Stripped(
        f"""\
case {xml_name_literal}: {{
{I}{indent_but_first_line(duplicate_check, I)}

{I}{indent_but_first_line(parse_body, I)}
{I}break;
}}"""
    )


def _generate_parse_concrete_class(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate parser for a concrete class from a start XML tag."""
    function_name = _parse_function_name_for_concrete_class(cls=cls)
    cls_name = typescript_naming.class_name(cls.name)
    local_name_literal = typescript_common.string_literal(naming.xml_class_name(cls.name))

    var_declarations = []  # type: List[Stripped]
    required_checks = []  # type: List[Stripped]
    parse_cases = []  # type: List[Stripped]

    var_name_by_property = {}  # type: Dict[Identifier, Identifier]

    for prop in cls.properties:
        var_name = typescript_naming.variable_name(Identifier(f"the_{prop.name}"))
        var_name_by_property[prop.name] = var_name

        var_type = typescript_common.generate_type(
            prop.type_annotation,
            types_module=Identifier("AasTypes"),
        )
        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            var_type = Stripped(f"{var_type} | null")

        var_declarations.append(Stripped(f"let {var_name}: {var_type} = null;"))

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            message_literal = typescript_common.string_literal(
                f"The required property {naming.xml_property(prop.name)!r} is missing"
            )
            required_checks.append(
                Stripped(
                    f"""\
if ({var_name} === null) {{
{I}return newDeserializationError<AasTypes.Class>(
{II}{message_literal}
{I});
}}"""
                )
            )

        parse_cases.append(_generate_parse_case_for_property(cls=cls, prop=prop, var_name=var_name))

    parse_cases.append(
        Stripped(
            """\
default: {
  propertyError = new DeserializationError(
    `Unexpected XML property: ${propertyLocalName}`
  );
  break;
}"""
        )
    )

    parse_cases_joined = "\n\n".join(parse_cases)

    if len(cls.constructor.arguments) == 0:
        construct = Stripped(
            f"""\
const instance = new AasTypes.{cls_name}();
return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{I}instance,
{I}null
);"""
        )
    else:
        writer = io.StringIO()
        writer.write(f"const instance = new AasTypes.{cls_name}(\n")
        for i, arg in enumerate(cls.constructor.arguments):
            var_name = var_name_by_property[arg.name]
            writer.write(f"{I}{var_name}")
            if i < len(cls.constructor.arguments) - 1:
                writer.write(",\n")
            else:
                writer.write("\n")
        writer.write(
            f"""\
);
return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{I}instance,
{I}null
);"""
        )
        construct = Stripped(writer.getvalue())

    declarations = Stripped("\n".join(var_declarations)) if len(var_declarations) > 0 else Stripped("// No properties")
    required_checks_block = Stripped("\n\n".join(required_checks)) if len(required_checks) > 0 else Stripped("// No required properties")

    return Stripped(
        f"""\
function {function_name}(
{I}cursor: XmlCursor,
{I}startTag: OpenTagToken
): AasCommon.Either<AasTypes.Class, DeserializationError> {{
{I}const observedLocalName = localNameOfTag(startTag.tag);
{I}if (observedLocalName !== {local_name_literal}) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}`Expected root XML element {local_name_literal}, ` +
{III}`but got: ${{observedLocalName}}`
{II});
{I}}}

{I}{indent_but_first_line(declarations, I)}

{I}cursor.skipIgnorable();
{I}while (true) {{
{II}const token = cursor.current();
{II}if (token === null) {{
{III}return newDeserializationError<AasTypes.Class>(
{IIII}`Unexpected end of token stream while parsing {cls_name}`
{III});
{II}}}

{II}if (token instanceof CloseTagToken) {{
{III}break;
{II}}}

{II}if (!(token instanceof OpenTagToken)) {{
{III}return newDeserializationError<AasTypes.Class>(
{IIII}"Expected an XML property start element or the closing element of " +
{IIII}`{cls_name}, but got token kind: ${{token.kind}}`
{III});
{II}}}

{II}const namespaceError = checkExpectedOpenTagNamespace(token);
{II}if (namespaceError !== null) {{
{III}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{IIII}null,
{IIII}namespaceError
{III});
{II}}}

{II}const propertyStartTag = token;
{II}const propertyLocalName = localNameOfTag(propertyStartTag.tag);
{II}cursor.advance();

{II}let propertyError: DeserializationError | null = null;
{II}switch (propertyLocalName) {{
{III}{indent_but_first_line(parse_cases_joined, III)}
{II}}}

{II}if (propertyError !== null) {{
{III}propertyError.path.prepend(new NameSegment(propertyLocalName));
{III}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{IIII}null,
{IIII}propertyError
{III});
{II}}}

{II}cursor.skipIgnorable();
{I}}}

{I}const closeTag = cursor.current();
{I}if (!(closeTag instanceof CloseTagToken)) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}"Expected closing element of " +
{IIII}`{cls_name}, but got token kind: ${{currentTokenKind(cursor)}}`
{II});
{I}}}

{I}const closeError = checkExpectedCloseTag(closeTag, observedLocalName);
{I}if (closeError !== null) {{
{II}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{III}null,
{III}closeError
{II});
{I}}}

{I}cursor.advance();

{I}{indent_but_first_line(required_checks_block, I)}

{I}{indent_but_first_line(construct, I)}
}}"""
    )


def _generate_serialize_text_as_enumeration(
    enumeration: intermediate.Enumeration,
) -> Stripped:
    """Generate serializer for text representation of an enumeration literal."""
    enum_name = typescript_naming.enum_name(enumeration.name)
    serialize_function_name = typescript_naming.function_name(
        Identifier(f"serialize_{enumeration.name}_text")
    )
    to_string_function = typescript_naming.function_name(
        Identifier(f"must_{enumeration.name}_to_string")
    )

    return Stripped(
        f"""\
function {serialize_function_name}(
{I}value: AasTypes.{enum_name}
): string {{
{I}return escapeXmlText(AasStringification.{to_string_function}(value));
}}"""
    )


def _generate_serialize_block_for_property(
    cls: intermediate.ConcreteClass,
    prop: intermediate.Property,
) -> Stripped:
    """Generate serialization statements for a property."""
    xml_name_literal = typescript_common.string_literal(naming.xml_property(prop.name))
    prop_name = typescript_naming.property_name(prop.name)
    access_expr = Stripped(f"that.{prop_name}")

    type_anno = intermediate.beneath_optional(prop.type_annotation)

    if isinstance(
        type_anno,
        (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
    ):
        if isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            serialized_var = typescript_naming.variable_name(
                Identifier(f"serialized_{prop.name}")
            )
            body = Stripped(
                f"""\
const {serialized_var} = this.transform({access_expr});
parts.push(openTag({xml_name_literal}));
parts.push(openTag({serialized_var}.localName));
parts.push({serialized_var}.innerXml);
parts.push(closeTag({serialized_var}.localName));
parts.push(closeTag({xml_name_literal}));"""
            )
        else:
            serialize_function = _serialize_function_for_atomic_type(type_anno)
            body = Stripped(
                f"""\
parts.push(openTag({xml_name_literal}));
parts.push({serialize_function}({access_expr}));
parts.push(closeTag({xml_name_literal}));"""
            )

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        if isinstance(
            type_anno.items,
            (intermediate.PrimitiveTypeAnnotation, intermediate.OurTypeAnnotation),
        ) and not (
            isinstance(type_anno.items, intermediate.OurTypeAnnotation)
            and isinstance(
                type_anno.items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            )
        ):
            serialize_item_function = _serialize_function_for_atomic_type(type_anno.items)
            item_var = typescript_naming.variable_name(Identifier(f"item_{prop.name}"))

            body = Stripped(
                f"""\
parts.push(openTag({xml_name_literal}));
for (const {item_var} of {access_expr}) {{
{I}parts.push(openTag("v"));
{I}parts.push({serialize_item_function}({item_var}));
{I}parts.push(closeTag("v"));
}}
parts.push(closeTag({xml_name_literal}));"""
            )

        elif isinstance(type_anno.items, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.items.our_type,
            (intermediate.AbstractClass, intermediate.ConcreteClass),
        ):
            item_var = typescript_naming.variable_name(Identifier(f"item_{prop.name}"))
            serialized_item_var = typescript_naming.variable_name(
                Identifier(f"serialized_{prop.name}_item")
            )

            body = Stripped(
                f"""\
parts.push(openTag({xml_name_literal}));
for (const {item_var} of {access_expr}) {{
{I}const {serialized_item_var} = this.transform({item_var});
{I}parts.push(openTag({serialized_item_var}.localName));
{I}parts.push({serialized_item_var}.innerXml);
{I}parts.push(closeTag({serialized_item_var}.localName));
}}
parts.push(closeTag({xml_name_literal}));"""
            )

        else:
            body = Stripped(
                f"""\
throw new Error(
{I}"XML serialization of the list property " +
{II}{xml_name_literal} +
{II}" in {typescript_naming.class_name(cls.name)} can not handle list items " +
{II}"of this kind"
);"""
            )
    else:
        assert_never(type_anno)

    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        return Stripped(
            f"""\
if ({access_expr} !== null) {{
{I}{indent_but_first_line(body, I)}
}}"""
        )

    return body


def _generate_transform_of_concrete_class(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate ``transformX`` to serialize a concrete class to XML parts."""
    method_name = typescript_naming.method_name(Identifier(f"transform_{cls.name}"))
    cls_name = typescript_naming.class_name(cls.name)
    local_name_literal = typescript_common.string_literal(naming.xml_class_name(cls.name))

    blocks = [Stripped("const parts = new Array<string>();")]  # type: List[Stripped]

    for prop in cls.properties:
        blocks.append(_generate_serialize_block_for_property(cls=cls, prop=prop))

    blocks.append(
        Stripped(
            f"""\
return {{
{I}localName: {local_name_literal},
{I}innerXml: parts.join("")
}};"""
        )
    )

    writer = io.StringIO()
    writer.write(
        f"""\
/**
 * Serialize `that` to an XML element representation.
 *
 * @param that - instance to be serialized
 * @returns serialized XML element representation
 */
{method_name}(
{I}that: AasTypes.{cls_name}
): SerializedElement {{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(indent_but_first_line(block, I))

    writer.write("\n}")
    return Stripped(writer.getvalue())


def _generate_serializer(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the serializer transformer over all concrete classes."""
    methods = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        methods.append(_generate_transform_of_concrete_class(cls=cls))

    writer = io.StringIO()
    writer.write(
        """\
/**
 * Serialize an AAS instance to XML parts.
 */
class Serializer extends AasTypes.AbstractTransformer<SerializedElement> {
"""
    )

    for method in methods:
        writer.write("\n\n")
        writer.write(indent_but_first_line(method, I))

    writer.write("\n}")

    return Stripped(writer.getvalue())


def _generate_root_dispatch_map(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the dispatch map from root XML local names to parse functions."""
    writer = io.StringIO()
    writer.write(
        f"""\
const ROOT_DISPATCH_BY_LOCAL_NAME =
{I}new Map<
{II}string,
{II}(
{III}cursor: XmlCursor,
{III}startTag: OpenTagToken
{II}) => AasCommon.Either<AasTypes.Class, DeserializationError>
{I}>([
"""
    )

    for i, cls in enumerate(symbol_table.concrete_classes):
        local_name_literal = typescript_common.string_literal(
            naming.xml_class_name(cls.name)
        )
        parse_function_name = _parse_function_name_for_concrete_class(cls=cls)

        writer.write(
            f"""\
{II}[
{III}{local_name_literal},
{III}{parse_function_name}
{II}]"""
        )

        if i < len(symbol_table.concrete_classes) - 1:
            writer.write(",\n")
        else:
            writer.write("\n")

    writer.write(
        f"""\
{I}]);"""
    )

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
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate code for XML de/serialization."""
    del spec_impls

    namespace_literal = typescript_common.string_literal(
        symbol_table.meta_model.xml_namespace
    )

    blocks = [
        Stripped(
            """\
/**
 * Provide de/serialization of AAS classes to/from XML.
 *
 * The implementation is incremental and follows a SAX-style parsing approach.
 */"""
        ),
        typescript_common.WARNING,
        Stripped(
            """\
import * as AasCommon from "./common";
import * as AasTypes from "./types";
import * as AasStringification from "./stringification";

import {
  CdataToken,
  CloseTagToken,
  CommentToken,
  EndToken,
  OpenTagToken,
  TextToken,
  XmlAnyToken,
  XmlSaxParser
} from "xmlsax-typescript";"""
        ),
        Stripped(
            f"""\
const NAMESPACE = {namespace_literal};"""
        ),
        Stripped(
            f"""\
/**
 * Represent a property name segment in an XML path.
 */
export class NameSegment {{
{I}readonly name: string;

{I}constructor(name: string) {{
{II}this.name = name;
{I}}}
}}"""
        ),
        Stripped(
            f"""\
/**
 * Represent an index segment in an XML path.
 */
export class IndexSegment {{
{I}readonly index: number;

{I}constructor(index: number) {{
{II}this.index = index;
{I}}}
}}"""
        ),
        Stripped(
            """\
export type Segment = NameSegment | IndexSegment;"""
        ),
        Stripped(
            f"""\
/**
 * Represent a relative path to the erroneous XML value.
 */
export class Path {{
{I}private readonly _segments = new Array<Segment>();

{I}segments(): Array<Segment> {{
{II}return this._segments;
{I}}}

{I}prepend(segment: Segment): void {{
{II}this._segments.unshift(segment);
{I}}}

{I}toString(): string {{
{II}if (this._segments.length === 0) {{
{III}return "";
{II}}}

{II}const parts = new Array<string>();
{II}for (const segment of this._segments) {{
{III}if (segment instanceof NameSegment) {{
{IIII}if (parts.length === 0) {{
{IIIII}parts.push(segment.name);
{IIII}}} else {{
{IIIII}parts.push(`.${{segment.name}}`);
{IIII}}}
{III}}} else if (segment instanceof IndexSegment) {{
{IIII}parts.push(`[${{segment.index}}]`);
{III}}}
{II}}}

{II}return parts.join("");
{I}}}
}}"""
        ),
        Stripped(
            f"""\
/**
 * Signal that XML de-serialization could not be performed.
 */
export class DeserializationError {{
{I}readonly message: string;
{I}readonly path: Path;

{I}constructor(message: string, path: Path | null = null) {{
{II}this.message = message;
{II}this.path = path ?? new Path();
{I}}}
}}"""
        ),
        Stripped(
            f"""\
/**
 * Signal that XML serialization could not be performed.
 */
export class SerializationError {{
{I}readonly message: string;
{I}readonly path: Path;

{I}constructor(message: string, path: Path | null = null) {{
{II}this.message = message;
{II}this.path = path ?? new Path();
{I}}}
}}"""
        ),
        Stripped(
            f"""\
function newDeserializationError<T>(
{I}message: string
): AasCommon.Either<T, DeserializationError> {{
{I}return new AasCommon.Either<T, DeserializationError>(
{II}null,
{II}new DeserializationError(message)
{I});
}}

function currentTokenKind(cursor: XmlCursor): string {{
{I}const token = cursor.current();
{I}if (token === null) {{
{II}return "end-of-token-stream";
{I}}}

{I}return token.kind;
}}

function localNameOfTag(tag: unknown): string {{
{I}const aTag = tag as {{
{II}name?: unknown,
{II}local?: unknown,
{II}localName?: unknown
{I}}};

{I}if (typeof aTag.local === "string") {{
{II}return aTag.local;
{I}}}
{I}if (typeof aTag.localName === "string") {{
{II}return aTag.localName;
{I}}}
{I}if (typeof aTag.name === "string") {{
{II}const colonIndex = aTag.name.indexOf(":");
{II}if (colonIndex >= 0) {{
{III}return aTag.name.substring(colonIndex + 1);
{II}}}
{II}return aTag.name;
{I}}}

{I}return "";
}}

function namespaceOfTag(tag: unknown): string {{
{I}const aTag = tag as {{ uri?: unknown, namespaceURI?: unknown }};
{I}if (typeof aTag.uri === "string") {{
{II}return aTag.uri;
{I}}}
{I}if (typeof aTag.namespaceURI === "string") {{
{II}return aTag.namespaceURI;
{I}}}
{I}return "";
}}

function checkExpectedOpenTagNamespace(
{I}openTag: OpenTagToken
): DeserializationError | null {{
{I}const namespace = namespaceOfTag(openTag.tag);
{I}if (namespace !== NAMESPACE) {{
{II}return new DeserializationError(
{III}"Expected XML namespace " +
{IIII}`'${{NAMESPACE}}', but got '${{namespace}}'`
{II});
{I}}}

{I}return null;
}}

function checkExpectedCloseTag(
{I}closeTag: CloseTagToken,
{I}expectedLocalName: string
): DeserializationError | null {{
{I}const namespace = namespaceOfTag(closeTag.tag);
{I}if (namespace !== NAMESPACE) {{
{II}return new DeserializationError(
{III}"Expected XML namespace " +
{IIII}`'${{NAMESPACE}}', but got '${{namespace}}'`
{II});
{I}}}

{I}const observedLocalName = localNameOfTag(closeTag.tag);
{I}if (observedLocalName !== expectedLocalName) {{
{II}return new DeserializationError(
{III}`Expected closing XML element '${{expectedLocalName}}', ` +
{III}`but got '${{observedLocalName}}'`
{II});
{I}}}

{I}return null;
}}

/**
 * Cursor over parsed XML SAX tokens.
 */
class XmlCursor {{
{I}private readonly _tokens: Array<XmlAnyToken>;
{I}private _index = 0;

{I}constructor(tokens: Array<XmlAnyToken>) {{
{II}this._tokens = tokens;
{I}}}

{I}current(): XmlAnyToken | null {{
{II}if (this._index >= this._tokens.length) {{
{III}return null;
{II}}}
{II}return this._tokens[this._index];
{I}}}

{I}advance(): void {{
{II}if (this._index < this._tokens.length) {{
{III}this._index++;
{II}}}
{I}}}

{I}skipIgnorable(): void {{
{II}while (true) {{
{III}const token = this.current();
{III}if (token === null) {{
{IIII}break;
{III}}}

{III}if (token instanceof CommentToken) {{
{IIII}this.advance();
{IIII}continue;
{III}}}

{III}if (token instanceof TextToken || token instanceof CdataToken) {{
{IIII}if (token.text.trim().length === 0) {{
{IIIII}this.advance();
{IIIII}continue;
{IIII}}}
{III}}}

{III}break;
{II}}}
{I}}}
}}

function tokenizeXml(
{I}xml: string
): AasCommon.Either<Array<XmlAnyToken>, DeserializationError> {{
{I}const parser = new XmlSaxParser({{ allowDoctype: false, xmlns: true }});
{I}const tokens = new Array<XmlAnyToken>();

{I}try {{
{II}for (const token of parser.feed(xml)) {{
{III}tokens.push(token);
{II}}}
{II}for (const token of parser.close()) {{
{III}if (!(token instanceof EndToken)) {{
{IIII}tokens.push(token);
{III}}}
{II}}}
{I}}} catch (error) {{
{II}return newDeserializationError<Array<XmlAnyToken>>(
{III}`Failed to parse XML: ${{error}}`
{II});
{I}}}

{I}return new AasCommon.Either<Array<XmlAnyToken>, DeserializationError>(
{II}tokens,
{II}null
{I});
}}

function readRequiredRootOpenTag(
{I}cursor: XmlCursor
): AasCommon.Either<OpenTagToken, DeserializationError> {{
{I}cursor.skipIgnorable();

{I}const token = cursor.current();
{I}if (token === null) {{
{II}return newDeserializationError<OpenTagToken>(
{III}"Expected a root XML element, but got an empty token stream"
{II});
{I}}}

{I}if (!(token instanceof OpenTagToken)) {{
{II}return newDeserializationError<OpenTagToken>(
{III}`Expected a root XML start element, but got token kind: ${{token.kind}}`
{II});
{I}}}

{I}const namespaceError = checkExpectedOpenTagNamespace(token);
{I}if (namespaceError !== null) {{
{II}return new AasCommon.Either<OpenTagToken, DeserializationError>(
{III}null,
{III}namespaceError
{II});
{I}}}

{I}cursor.advance();

{I}return new AasCommon.Either<OpenTagToken, DeserializationError>(
{II}token,
{II}null
{I});
}}

function readTextContentAndConsumeEndTag(
{I}cursor: XmlCursor,
{I}startTag: OpenTagToken
): AasCommon.Either<string, DeserializationError> {{
{I}cursor.skipIgnorable();

{I}let text = "";
{I}const maybeText = cursor.current();
{I}if (maybeText instanceof TextToken || maybeText instanceof CdataToken) {{
{II}text = maybeText.text;
{II}cursor.advance();
{II}cursor.skipIgnorable();
{I}}}

{I}const closeToken = cursor.current();
{I}if (!(closeToken instanceof CloseTagToken)) {{
{II}return newDeserializationError<string>(
{III}"Expected property closing XML element, but got token kind: " +
{IIII}currentTokenKind(cursor)
{II});
{I}}}

{I}const localName = localNameOfTag(startTag.tag);
{I}const closeError = checkExpectedCloseTag(closeToken, localName);
{I}if (closeError !== null) {{
{II}return new AasCommon.Either<string, DeserializationError>(
{III}null,
{III}closeError
{II});
{I}}}

{I}cursor.advance();

{I}return new AasCommon.Either<string, DeserializationError>(
{II}text,
{II}null
{I});
}}

function parseBooleanText(
{I}text: string
): AasCommon.Either<boolean, DeserializationError> {{
{I}if (text === "true" || text === "1") {{
{II}return new AasCommon.Either<boolean, DeserializationError>(true, null);
{I}}}
{I}if (text === "false" || text === "0") {{
{II}return new AasCommon.Either<boolean, DeserializationError>(false, null);
{I}}}

{I}return newDeserializationError<boolean>(
{II}`Expected xs:boolean text, but got: ${{text}}`
{I});
}}

function parseIntegerText(
{I}text: string
): AasCommon.Either<number, DeserializationError> {{
{I}if (!/^[+-]?\\d+$/.test(text)) {{
{II}return newDeserializationError<number>(
{III}`Expected integer text, but got: ${{text}}`
{II});
{I}}}

{I}const value = Number(text);
{I}if (!Number.isInteger(value)) {{
{II}return newDeserializationError<number>(
{III}`Expected integer text, but got: ${{text}}`
{II});
{I}}}

{I}return new AasCommon.Either<number, DeserializationError>(value, null);
}}

function parseFloatText(
{I}text: string
): AasCommon.Either<number, DeserializationError> {{
{I}if (text === "INF") {{
{II}return new AasCommon.Either<number, DeserializationError>(Infinity, null);
{I}}}
{I}if (text === "-INF") {{
{II}return new AasCommon.Either<number, DeserializationError>(-Infinity, null);
{I}}}
{I}if (text === "NaN") {{
{II}return new AasCommon.Either<number, DeserializationError>(NaN, null);
{I}}}

{I}const value = Number(text);
{I}if (Number.isNaN(value)) {{
{II}return newDeserializationError<number>(
{III}`Expected xs:double text, but got: ${{text}}`
{II});
{I}}}

{I}return new AasCommon.Either<number, DeserializationError>(value, null);
}}

function parseStringText(
{I}text: string
): AasCommon.Either<string, DeserializationError> {{
{I}return new AasCommon.Either<string, DeserializationError>(text, null);
}}

function parseBase64EncodedBytesText(
{I}text: string
): AasCommon.Either<Uint8Array, DeserializationError> {{
{I}const decodedOrError = AasCommon.base64Decode(text);
{I}if (decodedOrError.error !== null) {{
{II}return newDeserializationError<Uint8Array>(
{III}decodedOrError.error
{II});
{I}}}

{I}return new AasCommon.Either<Uint8Array, DeserializationError>(
{II}decodedOrError.mustValue(),
{II}null
{I});
}}

function parseClassValueInProperty(
{I}cursor: XmlCursor,
{I}propertyStartTag: OpenTagToken
): AasCommon.Either<AasTypes.Class, DeserializationError> {{
{I}cursor.skipIgnorable();

{I}const token = cursor.current();
{I}if (!(token instanceof OpenTagToken)) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}"Expected nested class element in XML property, but got token kind: " +
{IIII}currentTokenKind(cursor)
{II});
{I}}}

{I}const namespaceError = checkExpectedOpenTagNamespace(token);
{I}if (namespaceError !== null) {{
{II}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{III}null,
{III}namespaceError
{II});
{I}}}

{I}const localName = localNameOfTag(token.tag);
{I}const dispatch = ROOT_DISPATCH_BY_LOCAL_NAME.get(localName);
{I}if (dispatch === undefined) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}`Unexpected nested class XML element: ${{localName}}`
{II});
{I}}}

{I}cursor.advance();
{I}const instanceOrError = dispatch(cursor, token);
{I}if (instanceOrError.error !== null) {{
{II}return instanceOrError;
{I}}}

{I}cursor.skipIgnorable();
{I}const propertyCloseToken = cursor.current();
{I}if (!(propertyCloseToken instanceof CloseTagToken)) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}"Expected property closing XML element after nested class, but got token kind: " +
{IIII}currentTokenKind(cursor)
{II});
{I}}}

{I}const expectedPropertyLocalName = localNameOfTag(propertyStartTag.tag);
{I}const propertyCloseError = checkExpectedCloseTag(
{II}propertyCloseToken,
{II}expectedPropertyLocalName
{I});
{I}if (propertyCloseError !== null) {{
{II}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{III}null,
{III}propertyCloseError
{II});
{I}}}

{I}cursor.advance();

{I}return instanceOrError;
}}"""
        ),
    ]  # type: List[Stripped]

    for enumeration in symbol_table.enumerations:
        blocks.append(_generate_parse_text_as_enumeration(enumeration))

    for enumeration in symbol_table.enumerations:
        blocks.append(_generate_serialize_text_as_enumeration(enumeration))

    for concrete_cls in symbol_table.concrete_classes:
        blocks.append(_generate_parse_concrete_class(cls=concrete_cls))

    blocks.extend(
        [
            _generate_root_dispatch_map(symbol_table=symbol_table),
        Stripped(
            f"""\
/**
 * Parse an XML string as an AAS instance.
 *
 * @param xml - XML string to parse
 * @returns parsed AAS instance or an error
 */
export function fromXmlString(
{I}xml: string
): AasCommon.Either<AasTypes.Class, DeserializationError> {{
{I}if (xml.length === 0) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}"Expected an XML document, but got an empty string"
{II});
{I}}}

{I}const tokensOrError = tokenizeXml(xml);
{I}if (tokensOrError.error !== null) {{
{II}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{III}null,
{III}tokensOrError.error
{II});
{I}}}

{I}const cursor = new XmlCursor(tokensOrError.mustValue());

{I}const rootOpenTagOrError = readRequiredRootOpenTag(cursor);
{I}if (rootOpenTagOrError.error !== null) {{
{II}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{III}null,
{III}rootOpenTagOrError.error
{II});
{I}}}

{I}const rootOpenTag = rootOpenTagOrError.mustValue();
{I}const rootLocalName = localNameOfTag(rootOpenTag.tag);

{I}const dispatch = ROOT_DISPATCH_BY_LOCAL_NAME.get(rootLocalName);
{I}if (dispatch === undefined) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}`Unexpected root XML element: ${{rootLocalName}}`
{II});
{I}}}

{I}const instanceOrError = dispatch(cursor, rootOpenTag);
{I}if (instanceOrError.error !== null) {{
{II}return instanceOrError;
{I}}}

{I}cursor.skipIgnorable();
{I}const tokenAfterInstance = cursor.current();
{I}if (tokenAfterInstance !== null) {{
{II}if (!(tokenAfterInstance instanceof CloseTagToken)) {{
{III}return newDeserializationError<AasTypes.Class>(
{IIII}"Expected root closing XML element, but got token kind: " +
{IIII}currentTokenKind(cursor)
{III});
{II}}}

{II}const closeError = checkExpectedCloseTag(
{III}tokenAfterInstance,
{III}rootLocalName
{II});
{II}if (closeError !== null) {{
{III}return new AasCommon.Either<AasTypes.Class, DeserializationError>(
{IIII}null,
{IIII}closeError
{III});
{II}}}

{II}cursor.advance();
{I}}}

{I}cursor.skipIgnorable();
{I}if (cursor.current() !== null) {{
{II}return newDeserializationError<AasTypes.Class>(
{III}"Expected no tokens after the root XML element, but got token kind: " +
{IIII}currentTokenKind(cursor)
{II});
{I}}}

{I}return instanceOrError;
}}"""
        ),
    Stripped(
        f"""\
type SerializedElement = {{
{I}localName: string;
{I}innerXml: string;
}};

function openTag(localName: string, withNamespace = false): string {{
{I}if (withNamespace) {{
{II}return `<${{localName}} xmlns="${{NAMESPACE}}">`;
{I}}}

{I}return `<${{localName}}>`;
}}

function closeTag(localName: string): string {{
{I}return `</${{localName}}>`;
}}

function escapeXmlText(text: string): string {{
{I}return text
{II}.replace(/&/g, "&amp;")
{II}.replace(/</g, "&lt;")
{II}.replace(/>/g, "&gt;")
{II}.replace(/\"/g, "&quot;")
{II}.replace(/'/g, "&apos;");
}}

function serializeBooleanText(value: boolean): string {{
{I}return value ? "true" : "false";
}}

function serializeIntegerText(value: number): string {{
{I}if (!Number.isInteger(value)) {{
{II}throw new Error(`Expected an integer, but got: ${{value}}`);
{I}}}

{I}return `${{value}}`;
}}

function serializeFloatText(value: number): string {{
{I}if (Number.isNaN(value)) {{
{II}return "NaN";
{I}}}
{I}if (value === Infinity) {{
{II}return "INF";
{I}}}
{I}if (value === -Infinity) {{
{II}return "-INF";
{I}}}

{I}return `${{value}}`;
}}

function serializeStringText(value: string): string {{
{I}return escapeXmlText(value);
}}

function serializeBase64EncodedBytesText(value: Uint8Array): string {{
{I}return escapeXmlText(AasCommon.base64Encode(value));
}}"""
    ),
    _generate_serializer(symbol_table=symbol_table),
    Stripped("const SERIALIZER = new Serializer();"),
        Stripped(
            f"""\
/**
 * Serialize an AAS instance as an XML string.
 *
 * @param that - AAS instance to serialize
 * @returns serialized XML string
 */
export function toXmlString(that: AasTypes.Class): string {{
{I}const serialized = SERIALIZER.transform(that);
{I}const parts = new Array<string>();
{I}parts.push(openTag(serialized.localName, true));
{I}parts.push(serialized.innerXml);
{I}parts.push(closeTag(serialized.localName));
{I}return parts.join("");
}}"""
        ),
        typescript_common.WARNING,
        ]
    )

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
