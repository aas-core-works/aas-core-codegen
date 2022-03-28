"""Provide the meta model for Asset Administration Shell V3.0 Release Candidate 2."""
from enum import Enum
from re import match
from typing import List, Optional

from icontract import invariant, DBC

from aas_core_meta.marker import (
    abstract,
    serialization,
    implementation_specific,
    reference_in_the_book,
    is_superset_of,
    verification,
)

# TODO (sadu, 2021-11-17): book URL should be updated when published
__book_url__ = "TBA"
__book_version__ = "V3.0RC02"


# region Verification

# noinspection SpellCheckingInspection
@verification
def is_MIME_type(text: str) -> bool:
    """
    Check that :paramref:`text` conforms to the pattern of MIME type.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    tchar = "[!#$%&'*+\\-.^_`|~0-9a-zA-Z]"
    token = f"({tchar})+"
    type = f"{token}"
    subtype = f"{token}"
    ows = "[ \t]*"
    obs_text = "[\\x80-\\xff]"
    qd_text = f"([\t !#-\\[\\]-~]|{obs_text})"
    quoted_pair = f"\\\\([\t !-~]|{obs_text})"
    quoted_string = f'"({qd_text}|{quoted_pair})*"'
    parameter = f"{token}=({token}|{quoted_string})"
    media_type = f"{type}/{subtype}({ows};{ows}{parameter})*"

    return match(media_type, text) is not None


@verification
@implementation_specific
def is_model_reference_to(
    reference: "Model_reference", expected_type: "Key_elements"
) -> bool:
    """Check that the target of the model reference matches the expected ``target``."""
    # This implementation is only for reference. It needs to be adapted for each
    # implementation separately.
    return len(reference.keys) == 0 or reference.keys[-1].type == expected_type


# endregion

# region Constrained primitive types


class Resource(DBC):
    """
    Resource represents an address to a file (a locator). The value is an URI that
    can represent an absolute or relative path
    """

    path: "Asset_kind"
    """
    Path and name of the resource (with file extension).
    The path can be absolute or relative.

    """
    content_type: Optional["Content_type"]
    """
    Content type of the content of the file.
    The content type states which file extensions the file can have.

    """

    def __init__(
        self,
        path: "Asset_kind",
        content_type: Optional["Content_type"] = None,
    ) -> None:
        self.path = path
        self.content_type = content_type


class Date_time(str, DBC):
    pass


class Date_time_stamp(str, DBC):
    pass


@invariant(lambda self: len(self) >= 1)
class Non_empty_string(str, DBC):
    """Represent a string with at least one character."""

    pass


@reference_in_the_book(section=(5, 7, 11, 2))
class Blob_type(bytearray, DBC):
    """
    Group of bytes to represent file content (binaries and non-binaries)

    """

    pass


@reference_in_the_book(section=(5, 7, 12, 3), index=4)
class Data_type_def_RDF(Enum):
    """
    Enumeration listing all RDF types
    """

    Lang_string = "rdf:langString"
    """
    String with a language tag

    .. note::

        RDF requires IETF BCP 47  language tags, i.e. simple two-letter language tags
        for Locales like “de” conformant to ISO 639-1 are allowed as well as language
        tags plus extension like “de-DE” for country code, dialect etc. like in “en-US”
        or “en-GB” for English (United Kingdom) and English (United States).
        IETF language tags are referencing ISO 639, ISO 3166 and ISO 15924.

    """


@reference_in_the_book(section=(7, 7, 11, 3), index=1)
class Decimal_build_in_types(Enum):
    Integer = "xs:integer"
    Long = "xs:long"
    Int = "xs:int"
    Short = "xs:short"
    Byte = "xs:byte"
    Non_negative_integer = "xs:NonNegativeInteger"
    Positive_integer = "xs:positiveInteger"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_short = "xs:unsignedShort"
    Unsigned_byte = "xs:unsignedByte"
    Non_positive_integer = "xs:nonPositiveInteger"
    Negative_integer = "xs:negativeInteger"


@reference_in_the_book(section=(5, 7, 11, 3), index=2)
class Duration_build_in_types(Enum):
    Day_time_duration = "xs:dayTimeDuration"
    Year_month_duration = "xs:yearMonthDuration"


@reference_in_the_book(section=(5, 7, 11, 3), index=3)
class Primitive_types(Enum):
    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Date = "xs:date"
    Date_time = "xs:dateTime"
    Date_time_stamp = "xs:dateTimeStamp"
    Decimal = "xs:decimal"
    Double = "xs:double"
    Duration = "xs:duration"
    Float = "xs:float"
    G_day = "xs:gDay"
    G_month = "xs:gMonth"
    G_month_day = "xs:gMonthDay"
    G_year = "xs:gYear"
    G_year_month = "xs:gYearMonth"
    Hex_binary = "xs:hexBinary"
    String = "xs:string"
    Time = "xs:time"


@reference_in_the_book(section=(5, 7, 11, 3))
@is_superset_of(
    enums=[
        Decimal_build_in_types,
        Duration_build_in_types,
        Primitive_types,
    ]
)
class Data_type_def_XSD(Enum):
    """
    Enumeration listing all xsd anySimpleTypes
    """

    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Date = "xs:date"
    Date_time = "xs:dateTime"
    Date_time_stamp = "xs:dateTimeStamp"
    Decimal = "xs:decimal"
    Double = "xs:double"
    Duration = "xs:duration"
    Float = "xs:float"
    G_day = "xs:gDay"
    G_month = "xs:gMonth"
    G_month_day = "xs:gMonthDay"
    G_year = "xs:gYear"
    G_year_month = "xs:gYearMonth"
    Hex_binary = "xs:hexBinary"
    String = "xs:string"
    Time = "xs:time"
    Day_time_duration = "xs:dayTimeDuration"
    Year_month_duration = "xs:yearMonthDuration"
    Integer = "xs:integer"
    Long = "xs:long"
    Int = "xs:int"
    Short = "xs:short"
    Byte = "xs:byte"
    Non_negative_integer = "xs:NonNegativeInteger"
    Positive_integer = "xs:positiveInteger"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_short = "xs:unsignedShort"
    Unsigned_byte = "xs:unsignedByte"
    Non_positive_integer = "xs:nonPositiveInteger"
    Negative_integer = "xs:negativeInteger"


@is_superset_of(enums=[Data_type_def_XSD, Data_type_def_RDF])
class Data_type_def(Enum):
    """
    string with values of enumerations DataTypeDefXsd, Data_type_def_Rdf
    """

    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Date = "xs:date"
    Date_time = "xs:dateTime"
    Date_time_stamp = "xs:dateTimeStamp"
    Decimal = "xs:decimal"
    Double = "xs:double"
    Duration = "xs:duration"
    Float = "xs:float"
    G_day = "xs:gDay"
    G_month = "xs:gMonth"
    G_month_day = "xs:gMonthDay"
    G_year = "xs:gYear"
    G_year_month = "xs:gYearMonth"
    Hex_binary = "xs:hexBinary"
    String = "xs:string"
    Time = "xs:time"
    Day_time_duration = "xs:dayTimeDuration"
    Year_month_duration = "xs:yearMonthDuration"
    Integer = "xs:integer"
    Long = "xs:long"
    Int = "xs:int"
    Short = "xs:short"
    Byte = "xs:byte"
    Non_negative_integer = "xs:NonNegativeInteger"
    Positive_integer = "xs:positiveInteger"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_short = "xs:unsignedShort"
    Unsigned_byte = "xs:unsignedByte"
    Non_positive_integer = "xs:nonPositiveInteger"
    Negative_integer = "xs:negativeInteger"
    Lang_string = "rdf:langString"


class Identifier(Non_empty_string, DBC):
    """
    string
    """

    pass


class Lang_string_set(Non_empty_string, DBC):
    """
    Array of elements of type langString

    .. note::
        langString is a RDF data type.

    A langString is a string value tagged with a language code.
    It depends on the serialization rules for a technology how
    this is realized.
    """

    pass


@invariant(lambda self: is_MIME_type(self))
class Content_type(Non_empty_string, DBC):
    """
    string

    .. note::
        Any content type as in RFC2046.

    A media type (also MIME type and content type) […] is a two-part
    identifier for file formats and format contents transmitted on
    the Internet. The Internet Assigned Numbers Authority (IANA) is
    the official authority for the standardization and publication of
    these classifications. Media types were originally defined in
    Request for Comments 2045 in November 1996 as a part of MIME
    (Multipurpose Internet Mail Extensions) specification, for denoting
    type of email message content and attachments.
    """

    pass


class Path_type(Non_empty_string, DBC):
    """
    string

    .. note::

        Any string conformant to RFC8089 , the “file” URI scheme (for
        relative and absolute file paths)
    """

    pass


class Qualifier_type(Non_empty_string, DBC):
    """
    string
    """

    pass


@is_superset_of(enums=[Data_type_def_XSD])
class Value_data_type(Enum):
    """
    any xsd atomic type as specified via DataTypeDefXsd
    """

    Any_URI = "xs:anyURI"
    Base_64_binary = "xs:base64Binary"
    Boolean = "xs:boolean"
    Date = "xs:date"
    Date_time = "xs:dateTime"
    Date_time_stamp = "xs:dateTimeStamp"
    Decimal = "xs:decimal"
    Double = "xs:double"
    Duration = "xs:duration"
    Float = "xs:float"
    G_day = "xs:gDay"
    G_month = "xs:gMonth"
    G_month_day = "xs:gMonthDay"
    G_year = "xs:gYear"
    G_year_month = "xs:gYearMonth"
    Hex_binary = "xs:hexBinary"
    String = "xs:string"
    Time = "xs:time"
    Day_time_duration = "xs:dayTimeDuration"
    Year_month_duration = "xs:yearMonthDuration"
    Integer = "xs:integer"
    Long = "xs:long"
    Int = "xs:int"
    Short = "xs:short"
    Byte = "xs:byte"
    Non_negative_integer = "xs:NonNegativeInteger"
    Positive_integer = "xs:positiveInteger"
    Unsigned_long = "xs:unsignedLong"
    Unsigned_int = "xs:unsignedInt"
    Unsigned_short = "xs:unsignedShort"
    Unsigned_byte = "xs:unsignedByte"
    Non_positive_integer = "xs:nonPositiveInteger"
    Negative_integer = "xs:negativeInteger"


@invariant(lambda self: is_MIME_type(self))
class MIME_typed(Non_empty_string, DBC):
    """Represent a string that follows the pattern of a MIME type."""


# endregion


@abstract
@reference_in_the_book(section=(5, 7, 10, 4))
@serialization(with_model_type=True)
class Reference(DBC):
    """
    Reference to either a model element of the same or another AAs or to an external
    entity.
    """


@abstract
@reference_in_the_book(section=(5, 7, 2, 1))
class Has_extensions(DBC):
    """
    Element that can be extended by proprietary extensions.

    Note: Extensions are proprietary, i.e. they do not support global interoperability.
    """

    extensions: List["Extension"]
    """
    An extension of the element.
    """

    def __init__(self, extensions: Optional[List["Extension"]] = None) -> None:
        self.extensions = extensions if extensions is not None else []


@abstract
@reference_in_the_book(section=(5, 7, 2, 2))
@serialization(with_model_type=True)
class Referable(Has_extensions):
    """
    An element that is referable by its :attr:`~ID_short`.

    This identifier is not globally unique.
    This identifier is unique within the name space of the element.
    """

    ID_short: Optional[Non_empty_string]
    """
    In case of identifiables this attribute is a short name of the element.
    In case of referable this ID is an identifying string of
    the element within its name space.

    .. note::

        In case the element is a property and the property has a semantic definition
        (:class:`.Has_semantics`) conformant to IEC61360 the idShort is typically
        identical to the short name in English.

    :constraint AASd-027:
        idShort of Referables shall have a maximum length of 128
        characters.
    """

    display_name: Optional["Lang_string_set"]
    """
    Display name. Can be provided in several languages.

    If no display name is defined in the language requested by the application,
    then the display name is selected in the following order if available:

    * the preferred name in the requested language of the concept description defining
      the semantics of the element
    * If there is a default language list defined in the application,
      then the corresponding preferred name in the language is chosen
      according to this order.
    * the English preferred name of the concept description defining
      the semantics of the element
    * the short name of the concept description
    * the idShort of the element
    """

    category: Optional[Non_empty_string]
    """
    The category is a value that gives further meta information
    w.r.t. to the class of the element.
    It affects the expected existence of attributes and the applicability of
    constraints.

    .. note::

        The category is not identical to the semantic definition
        (:class:`.Has_semantics`) of an element. The category
        *e.g.* could denote that the element is a measurement value whereas the
        semantic definition of the element would
        denote that it is the measured temperature.
    """

    description: Optional["Lang_string_set"]
    """
    Description or comments on the element.

    The description can be provided in several languages.

    If no description is defined, then the definition of the concept
    description that defines the semantics of the element is used.

    Additional information can be provided, *e.g.*, if the element is
    qualified and which qualifier types can be expected in which
    context or which additional data specification templates are
    provided.
    """

    checksum: Optional["Non_empty_string"]
    """
    Checksum to be used to determine if an Referable (including its
    aggregated hild elements) has changed.

    The checksum is calculated by the user's tool environment.
    The checksum has no semantic meaning for an asset administration
    shell model and there is no requirement for asset administration
    shell tools to manage the checksum

    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
    ) -> None:
        Has_extensions.__init__(self, extensions=extensions)

        self.ID_short = ID_short
        self.display_name = display_name
        self.category = category
        self.description = description
        self.checksum = checksum


@abstract
@reference_in_the_book(section=(5, 7, 2, 4))
class Has_kind(DBC):
    """
    An element with a kind is an element that can either represent a template or an
    instance.

    Default for an element is that it is representing an instance.
    """

    kind: Optional["Modeling_kind"]
    """
    Kind of the element: either type or instance.

    Default Value = Instance
    """

    # TODO (all, 2021-05-28): how can ``kind`` be optional
    #  and have a default value?
    #  (See page 52 in the book V3.0RC02, kind has the cardinality ``0..1``.)
    def __init__(self, kind: Optional["Modeling_kind"] = None) -> None:
        self.kind = kind if kind is not None else Modeling_kind.Instance


@abstract
@reference_in_the_book(section=(5, 7, 2, 6))
class Has_semantics(DBC):
    """
    Element that can have a semantic definition.
    """

    semantic_ID: Optional["Global_reference"]
    """
    Identifier of the semantic definition of the element. It is called semantic ID
    of the element.
    """

    def __init__(self, semantic_ID: Optional["Global_reference"] = None) -> None:
        self.semantic_ID = semantic_ID


@abstract
@reference_in_the_book(section=(5, 7, 2, 7))
@serialization(with_model_type=True)
# fmt: on
class Qualifiable(DBC):
    """
    The value of a qualifiable element may be further qualified by one or more
    qualifiers or complex formulas.
    """

    qualifiers: List["Qualifier"]
    """
    Additional qualification of a qualifiable element.

    :constraint AASd-021:
        Every qualifiable can only have one qualifier with the same Qualifier/type.
    """

    def __init__(self, qualifiers: Optional[List["Qualifier"]] = None) -> None:
        self.qualifiers = qualifiers if qualifiers is not None else []


@abstract
@reference_in_the_book(section=(5, 7, 2, 9))
class Has_data_specification(DBC):
    """
    Element that can be extended by using data specification templates.

    A data specification template defines a named set of additional attributes an
    element may or shall have. The data specifications used are explicitly specified
    with their global ID.
    """

    data_specifications: Optional[List["Global_reference"]]
    """
    Global reference to the data specification template used by the element.
    """

    def __init__(
        self, data_specifications: Optional[List["Global_reference"]] = None
    ) -> None:
        self.data_specifications = (
            data_specifications if data_specifications is not None else []
        )


@abstract
@reference_in_the_book(section=(5, 7, 6))
class Submodel_element(
    Referable, Has_kind, Has_semantics, Qualifiable, Has_data_specification
):
    """
    A submodel element is an element suitable for the description and differentiation of
    assets.

    It is recommended to add a semantic ID to a submodel element.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)


# fmt: off
# TODO (mristin, 2021-11-17): rewrite using XSD constraints on strings
# @invariant(
#     lambda self:
#     not (self.value is not None) or is_of_type(self.value, self.value_type),
#     "Constraint AASd-020"
# )
@reference_in_the_book(section=(5, 7, 2, 8))
@serialization(with_model_type=True)
# fmt: on
class Qualifier(Has_semantics):
    """
    A qualifier is a type-value-pair that makes additional statements w.r.t.  the value
    of the element.

    :constraint AASd-006:
        If both, the value and the valueId of a Qualifier are present then the value
        needs to be identical to the value of the referenced coded value in
        Qualifier/valueId.

    :constraint AASd-020:
        The value of Qualifier/value shall be consistent to the data type as defined in
        Qualifier/valueType
    """

    type: "Qualifier_type"
    """
    The qualifier type describes the type of the qualifier that is applied to
    the element.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the qualifier value.
    """

    value: Optional["Value_data_type"]
    """
    The qualifier value is the value of the qualifier.
    """

    value_ID: Optional["Global_reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        type: "Qualifier_type",
        value_type: "Data_type_def_XSD",
        semantic_ID: Optional["Global_reference"] = None,
        value: Optional["Value_data_type"] = None,
        value_ID: Optional["Global_reference"] = None,
    ) -> None:
        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        self.type = type
        self.value_type = value_type
        self.value = value
        self.value_ID = value_ID


@abstract
@reference_in_the_book(section=(5, 7, 7, 5))
class Data_element(Submodel_element):
    """
    A data element is a submodel element that is not further composed out of
    other submodel elements.

    A data element is a submodel element that has a value. The type of value differs
    for different subtypes of data elements.

    A controlled value is a value whose meaning is given in an external source
    (see “ISO/TS 29002-10:2009(E)”).

    :constraint AASd-090:
        For data elements DataElement/category shall be one of the following values:
        CONSTANT, PARAMETER or VARIABLE.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(5, 7, 7, 15))
class Reference_element(Data_element):
    """
    A reference element is a data element that defines a logical reference to another
    element within the same or another AAS or a reference to an external object or
    entity.

    """

    value: Optional["Reference"]
    """
    Global reference to an external object or entity or a logical reference to
    another element within the same or another AAS (i.e. a model reference to
    a Referable).
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        value: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value


# TODO (mristin, 2022-03-26):
#  Uncomment once the discussion regarding the covariant return types has been resolved.
# @reference_in_the_book(section=(5, 7, 7, 9))
# class Global_reference_element(Reference_element):
#     """
#     A global reference element is a data element that references an external object or entity.
#     """
#
#     value: Optional["Global_reference"]
#     """
#     Global reference to an external object or entity.
#     """
#
#     def __init__(
#         self,
#         ID_short: Non_empty_string,
#         extensions: Optional[List["Extension"]] = None,
#         display_name: Optional["Lang_string_set"] = None,
#         category: Optional[Non_empty_string] = None,
#         description: Optional["Lang_string_set"] = None,
#         kind: Optional["Modeling_kind"] = None,
#         semantic_ID: Optional["Global_reference"] = None,
#         qualifiers: Optional[List[Qualifier]] = None,
#         data_specifications: Optional[List["Global_reference"]] = None,
#         value: Optional["Global_reference"] = None,
#     ) -> None:
#         Reference_element.__init__(
#             self,
#             extensions=extensions,
#             ID_short=ID_short,
#             display_name=display_name,
#             category=category,
#             description=description,
#             kind=kind,
#             semantic_ID=semantic_ID,
#             qualifiers=qualifiers,
#             data_specifications=data_specifications,
#         )
#         self.value = value
#
#
# @reference_in_the_book(section=(5, 7, 7, 10))
# class Model_reference_element(Reference_element):
#     """
#     A model reference element is a data element that defines
#     a logical reference to another element within the same or another AAS
#     """
#
#     value: Optional["Model_reference"]
#     """
#     A logical reference to another element within the same or another AAS
#     """
#
#     def __init__(
#         self,
#         ID_short: Non_empty_string,
#         extensions: Optional[List["Extension"]] = None,
#         display_name: Optional["Lang_string_set"] = None,
#         category: Optional[Non_empty_string] = None,
#         description: Optional["Lang_string_set"] = None,
#         kind: Optional["Modeling_kind"] = None,
#         semantic_ID: Optional["Global_reference"] = None,
#         qualifiers: Optional[List[Qualifier]] = None,
#         data_specifications: Optional[List["Global_reference"]] = None,
#         value: Optional["Model_reference"] = None,
#     ) -> None:
#         Reference_element.__init__(
#             self,
#             extensions=extensions,
#             ID_short=ID_short,
#             display_name=display_name,
#             category=category,
#             description=description,
#             kind=kind,
#             semantic_ID=semantic_ID,
#             qualifiers=qualifiers,
#             data_specifications=data_specifications,
#         )
#         self.value = value


@reference_in_the_book(section=(5, 7, 10, 2))
@serialization(with_model_type=True)
class Global_reference(Reference):
    """
    Reference to an external entity.
    """

    value: "Identifier"
    """
    Unique identifier

    The identifier can be a concatenation of different identifiers, for example
    representing an IRDI path etc.
    """

    def __init__(self, value: "Identifier") -> None:
        self.value = value


@invariant(lambda self: len(self.keys) >= 1)
@reference_in_the_book(section=(5, 7, 10, 3))
@serialization(with_model_type=True)
class Model_reference(Reference):
    """
    Reference to a model element of the same or another AAS.
    A model reference is an ordered list of keys, each key referencing an element.
    The complete list of keys may for example be concatenated to a path that then gives
    unique access to an element.
    """

    keys: List["Key"]
    """
    Unique references in their name space.
    """

    referred_semantic_ID: Optional["Global_reference"]
    """
    SemanticId of the referenced model element.
    """

    def __init__(
        self,
        keys: List["Key"],
        referred_semantic_ID: Optional["Global_reference"] = None,
    ) -> None:
        self.keys = keys
        self.referred_semantic_ID = referred_semantic_ID


@reference_in_the_book(section=(5, 7, 10, 3), index=1)
class Key(DBC):
    """A key is a reference to an element by its ID."""

    type: "Key_elements"
    # TODO (g1zzm0, 2021-12-13):
    #  We had to introduce ``Key_elements.Global_reference`` as it was missing in
    #  the meta-model, but was referenced here in the book.
    #  Analogously for ``Key_elements.Fragment_reference``. It was written here as
    #  ``Fragment_ID``. This description needs to be revised either here or in the book.
    """
    Denote which kind of entity is referenced.

    In case type = :attr:`~Key_elements.Global_reference` then the key represents
    a global unique id.

    In case type = :attr:`~Key_elements.Fragment_reference` the key represents
    a bookmark or a similar local identifier within its parent element as specified by
    the key that precedes this key.

    In all other cases the key references a model element of the same or of another AAS.
    The name of the model element is explicitly listed.
    """

    value: Non_empty_string

    # TODO (g1zzm0, 2021-12-13):
    #  The docstring references a non-existing attribute ``ID_type`` which has been
    #  removed in this version, but existed in V3RC01. The description needs to be
    #  revised in the book.
    # """The key value, for example an IRDI if the :attr:`~ID_type` is IRDI."""

    def __init__(self, type: "Key_elements", value: Non_empty_string) -> None:
        self.type = type
        self.value = value


@reference_in_the_book(section=(5, 7, 2, 1), index=1)
class Extension(Has_semantics):
    """
    Single extension of an element.
    """

    name: Non_empty_string
    """
    Name of the extension.

    :constraint AASd-077:
        The name of an extension within HasExtensions needs to be unique.
    """

    value_type: Optional["Data_type_def_XSD"]
    """
    Type of the value of the extension.

    Default: xsd:string
    """

    value: Optional["Value_data_type"]
    """
    Value of the extension
    """

    refers_to: Optional["Model_reference"]
    """
    Reference to an element the extension refers to.
    """

    def __init__(
        self,
        name: Non_empty_string,
        semantic_ID: Optional["Global_reference"] = None,
        value_type: Optional["Data_type_def_XSD"] = None,
        value: Optional["Value_data_type"] = None,
        # ToDo: Make refs_to -> ModelReference<Referable>
        refers_to: Optional["Model_reference"] = None,
    ) -> None:
        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        self.name = name
        self.value_type = value_type
        self.value = value
        self.refers_to = refers_to


@abstract
@reference_in_the_book(section=(5, 7, 2, 3))
class Identifiable(Referable):
    """An element that has a globally unique identifier."""

    ID: "Identifier"
    """The globally unique identification of the element."""

    administration: Optional["Administrative_information"]
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    def __init__(
        self,
        ID: "Identifier",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
        )

        self.ID = ID
        self.administration = administration


@reference_in_the_book(section=(5, 7, 2, 4), index=1)
class Modeling_kind(Enum):
    """Enumeration for denoting whether an element is a template or an instance."""

    Template = "TEMPLATE"
    """
    Software element which specifies the common attributes shared by all instances of
    the template.

    [SOURCE: IEC TR 62390:2005-01, 3.1.25] modified
    """

    Instance = "INSTANCE"
    """
    Concrete, clearly identifiable component of a certain template.

    .. note::

        It becomes an individual entity of a  template,  for example a
        device model, by defining specific property values.

    .. note::

        In an object oriented view,  an instance denotes an object of a
        template (class).

    [SOURCE: IEC 62890:2016, 3.1.16 65/617/CDV]  modified
    """


# fmt: off
@invariant(
    lambda self:
    not (self.revision is not None) or self.version is not None,
    "Constraint AASd-005"
)
@reference_in_the_book(section=(5, 7, 2, 5))
# fmt: on
class Administrative_information(Has_data_specification):
    """
    Administrative meta-information for an element like version
    information.

    :constraint AASd-005:
        If AdministrativeInformation/version is not specified than also
        AdministrativeInformation/revision shall be unspecified. This means, a revision
        requires a version. If there is no version there is no revision neither.
        Revision is optional.
    """

    version: Optional[Non_empty_string]
    """Version of the element."""

    revision: Optional[Non_empty_string]
    """Revision of the element."""

    def __init__(
        self,
        data_specifications: Optional[List["Global_reference"]] = None,
        version: Optional[Non_empty_string] = None,
        revision: Optional[Non_empty_string] = None,
    ) -> None:
        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.version = version
        self.revision = revision


@reference_in_the_book(section=(5, 7, 3))
@serialization(with_model_type=True)
class Asset_administration_shell(Identifiable, Has_data_specification):
    """An asset administration shell."""

    asset_information: "Asset_information"
    """Meta-information about the asset the AAS is representing."""

    # todo: Nico Model_reference --> ModelReference<Submodel>
    submodels: List["Model_reference"]
    """
    References to submodels of the AAS.

    A submodel is a description of an aspect of the asset the AAS is representing.
    The asset of an AAS is typically described by one or more submodels.
    Temporarily no submodel might be assigned to the AAS.
    """

    # todo: Nico Model_reference --> ModelReference<AssetAdministrationShell>
    derived_from: Optional["Model_reference"]
    """The reference to the AAS the AAS was derived from."""

    def __init__(
        self,
        ID: Identifier,
        asset_information: "Asset_information",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        submodels: Optional[List["Model_reference"]] = None,
        derived_from: Optional["Model_reference"] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.derived_from = derived_from
        self.asset_information = asset_information
        self.submodels = submodels if submodels is not None else []


@reference_in_the_book(section=(5, 7, 4))
class Asset_information(DBC):
    """
    In AssetInformation identifying meta data of the asset that is represented by an AAS
    is defined.

    The asset may either represent an asset type or an asset instance.
    The asset has a globally unique identifier plus – if needed – additional domain
    specific (proprietary) identifiers. However, to support the corner case of very
    first phase of lifecycle where a stabilised/constant global asset identifier does
    not already exist, the corresponding attribute “globalAssetId” is optional.

    """

    asset_kind: "Asset_kind"
    """
    Denotes whether the Asset is of kind "Type" or "Instance".
    """

    global_asset_ID: Optional["Global_reference"]
    """
    Reference to either an Asset object or a global reference to the asset the AAS is
    representing.

    This attribute is required as soon as the AAS is exchanged via partners in the life
    cycle of the asset. In a first phase of the life cycle the asset might not yet have
    a global ID but already an internal identifier. The internal identifier would be
    modelled via :attr:`~specific_asset_ID`.
    """

    specific_asset_ID: Optional["Identifier_key_value_pair"]
    """
    Additional domain-specific, typically proprietary, Identifier for the asset.

    For example, serial number.
    """

    default_thumbnail: Optional["Resource"]
    """
    Thumbnail of the asset represented by the asset administration shell.

    Used as default.
    """

    def __init__(
        self,
        asset_kind: "Asset_kind",
        global_asset_ID: Optional["Global_reference"] = None,
        specific_asset_ID: Optional["Identifier_key_value_pair"] = None,
        default_thumbnail: Optional["Resource"] = None,
    ) -> None:
        self.asset_kind = asset_kind
        self.global_asset_ID = global_asset_ID
        self.specific_asset_ID = specific_asset_ID
        self.default_thumbnail = default_thumbnail


@reference_in_the_book(section=(5, 7, 4), index=2)
class Asset_kind(Enum):
    """
    Enumeration for denoting whether an element is a type or an instance.
    """

    Type = "Type"
    """
    hardware or software element which specifies the common attributes shared by all
    instances of the type

    [SOURCE: IEC TR 62390:2005-01, 3.1.25]
    """

    Instance = "Instance"
    """
    concrete, clearly identifiable component of a certain type

    .. note::

        It becomes an individual entity of a type, for example a device, by defining
        specific property values.

    .. note::

        In an object oriented view, an instance denotes an object of a class
        (of a type).

    [SOURCE: IEC 62890:2016, 3.1.16] 65/617/CDV
    """


@reference_in_the_book(section=(5, 7, 4), index=3)
class Identifier_key_value_pair(Has_semantics):
    """
    An IdentifierKeyValuePair describes a generic identifier as key-value pair.
    """

    key: Non_empty_string
    """Key of the identifier"""

    value: Non_empty_string
    """The value of the identifier with the corresponding key."""

    external_subject_ID: Optional["Global_reference"]
    """The (external) subject the key belongs to or has meaning to."""

    def __init__(
        self,
        key: Non_empty_string,
        value: Non_empty_string,
        semantic_ID: Optional["Global_reference"] = None,
        external_subject_ID: Optional["Global_reference"] = None,
    ) -> None:
        Has_semantics.__init__(self, semantic_ID)
        self.key = key
        self.value = value
        self.external_subject_ID = external_subject_ID


@reference_in_the_book(section=(5, 7, 5))
class Submodel(
    Identifiable, Has_kind, Has_semantics, Qualifiable, Has_data_specification
):
    """
    A submodel defines a specific aspect of the asset represented by the AAS.

    A submodel is used to structure the digital representation and technical
    functionality of an Administration Shell into distinguishable parts. Each submodel
    refers to a well-defined domain or subject matter. Submodels can become
    standardized and, thus, become submodels templates.
    """

    submodel_elements: List["Submodel_element"]
    """A submodel consists of zero or more submodel elements."""

    def __init__(
        self,
        ID: Identifier,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        submodel_elements: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            administration=administration,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.submodel_elements = (
            submodel_elements if submodel_elements is not None else []
        )


# TODO (mristin, 2021-10-27, page 77):
#  :constraint AASd-055: If the semanticId of a RelationshipElement or an
#  AnnotatedRelationshipElement submodel element references a  ConceptDescription then
#  the ConceptDescription/category shall be one of following values: RELATIONSHIP.
#
#  🠒 We really need to think hard how we resolve the references. Should this class be
#  implementation-specific?
@reference_in_the_book(section=(5, 7, 7, 16))
@abstract
class Relationship_element(Submodel_element):
    """
    A relationship element is used to define a relationship between two elements
    being either referable (model reference) or external (global reference).

    """

    first: "Reference"
    """
    Reference to the first element in the relationship taking the role of the subject.
    """

    second: "Reference"
    """
    Reference to the second element in the relationship taking the role of the object.
    """

    def __init__(
        self,
        first: "Reference",
        second: "Reference",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.first = first
        self.second = second


@reference_in_the_book(section=(5, 7, 7, 17))
class Submodel_element_list(Submodel_element):
    """
    A submodel element list is an ordered collection of submodel elements.

    :constraint AASd-107:
        If a first level child element in a SubmodelElementList has a semanticId it
        shall be identical to SubmodelElementList/semanticIdListElement.

    :constraint AASd-114:
        If two first level child elements in a SubmodelElementList have a semanticId
        then they shall be identical.

    :constraint AASd-115:
        If a first level child element in a SubmodelElementList does not specify
        a semanticId then the value is assumed to be identical to
        SubmodelElementList/semanticIdListElement.

    :constraint AASd-108:
        All first level child elements in a SubmodelElementList shall have the same
        submodel element type as specified in SubmodelElementList/typeValueListElement.

    :constraint AASd-109:
        If SubmodelElementList/typeValueListElement equal to Property or Range
        SubmodelElementList/valueTypeListElement shall be set and all first level
        child elements in the SubmodelElementList shall have the the value type as
        specified in SubmodelElementList/valueTypeListElement.
    """

    type_value_list_element: "Submodel_element_elements"
    """
    The submodel element type of the submodel elements contained in the list.
    """

    order_relevant: Optional["bool"]
    """
    Defines whether order in list is relevant. If orderRelevant = False then the list
    is representing a set or a bag.
    Default: True
    """

    values: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the list.
    The list is ordered.

    """
    semantic_id_list_element: Optional["Global_reference"]
    """
    The submodel element type of the submodel elements contained in the list.
    """

    value_type_list_element: Optional["Data_type_def_XSD"]
    """
    The value type of the submodel element contained in the list.
    """

    def __init__(
        self,
        type_value_list_element: "Submodel_element_elements",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        order_relevant: Optional["bool"] = None,
        values: Optional[List["Submodel_element"]] = None,
        semantic_id_list_element: Optional["Global_reference"] = None,
        value_type_list_element: Optional["Data_type_def_XSD"] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.type_value_list_element = type_value_list_element
        self.order_relevant = order_relevant
        self.values = values if values is not None else []
        self.semantic_id_list_element = semantic_id_list_element
        self.value_type_list_element = value_type_list_element


@reference_in_the_book(section=(5, 7, 7, 18))
class Submodel_element_struct(Submodel_element):
    """
    A submodel element struct is is a logical encapsulation of multiple values. It has
    a number of of submodel elements.
    """

    values: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the struct.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        values: Optional[List["Submodel_element"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.values = values if values is not None else []


@reference_in_the_book(section=(5, 7, 7, 13))
class Property(Data_element):
    """
    A property is a data element that has a single value.

    :constraint AASd-007:
        If both, the Property/value and the Property/valueId are present then the value
        of Property/value needs to be identical to the value of the referenced coded
        value in Property/valueId.
    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the value
    """

    value: Optional["Value_data_type"]
    """
    The value of the property instance.
    """

    value_ID: Optional["Global_reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        value: Optional["Value_data_type"] = None,
        value_ID: Optional["Global_reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value_type = value_type
        self.value = value
        self.value_ID = value_ID


@reference_in_the_book(section=(5, 7, 7, 11))
class Multi_language_property(Data_element):
    """
    A property is a data element that has a multi-language value.

    :constraint AASd-012:
        If both, the MultiLanguageProperty/value and the MultiLanguageProperty/valueId
        are present then for each string in a specific language the meaning must be
        the same as specified in MultiLanguageProperty/valueId.
    """

    value: Optional["Lang_string_set"]
    """
    The value of the property instance.
    """

    value_ID: Optional["Global_reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        value: Optional["Lang_string_set"] = None,
        value_ID: Optional["Global_reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value
        self.value_ID = value_ID


@reference_in_the_book(section=(5, 7, 7, 14))
class Range(Data_element):
    """
    A range data element is a data element that defines a range with min and max.

    """

    value_type: "Data_type_def_XSD"
    """
    Data type of the min und max
    """

    min: Optional["Value_data_type"]
    """
    The minimum value of the range.
    If the min value is missing, then the value is assumed to be negative infinite.
    """

    max: Optional["Value_data_type"]
    """
    The maximum value of the range.
    If the max value is missing,  then the value is assumed to be positive infinite.
    """

    def __init__(
        self,
        value_type: "Data_type_def_XSD",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        min: Optional["Value_data_type"] = None,
        max: Optional["Value_data_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value_type = value_type
        self.min = min
        self.max = max


@reference_in_the_book(section=(5, 7, 7, 4))
@invariant(lambda self: is_MIME_type(self.MIME_type))
class Blob(Data_element):
    """
    A BLOB is a data element that represents a file that is contained with its source
    code in the value attribute.
    """

    MIME_type: MIME_typed
    """
    Mime type of the content of the BLOB.
    The mime type states which file extensions the file can have.
    Valid values are e.g. “application/json”, “application/xls”, ”image/jpg”
    The allowed values are defined as in RFC2046.
    """

    value: Optional["Blob_type"]
    """
    The value of the BLOB instance of a blob data element.

    .. note::

        In contrast to the file property the file content is stored directly as value
        in the Blob data element.
    """

    def __init__(
        self,
        MIME_type: MIME_typed,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        value: Optional["Blob_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.MIME_type = MIME_type
        self.value = value


@reference_in_the_book(section=(5, 7, 7, 8))
@invariant(lambda self: is_MIME_type(self.content_type))
class File(Data_element):
    """
    A File is a data element that represents an address to a file.

    The value is an URI that can represent an absolute or relative path.
    """

    content_type: "Content_type"
    """
    Content type of the content of the file.

    The content type states which file extensions the file can have.
    """

    value: Optional["Path_type"]
    """
    Path and name of the referenced file (with file extension).
    The path can be absolute or relative.
    """

    def __init__(
        self,
        content_type: "Content_type",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        value: Optional["Path_type"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.content_type = content_type
        self.value = value


@reference_in_the_book(section=(5, 7, 7, 1))
class Annotated_relationship_element(Relationship_element):
    """
    An annotated relationship element is a relationship element that can be annotated
    with additional data elements.
    """

    annotation: List[Data_element]
    """
    A data element that represents an annotation that holds for the relationship
    between the two elements
    """

    def __init__(
        self,
        first: "Reference",
        second: "Reference",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        annotation: Optional[List[Data_element]] = None,
    ) -> None:
        Relationship_element.__init__(
            self,
            first=first,
            second=second,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.annotation = annotation if annotation is not None else []


@reference_in_the_book(section=(5, 7, 7, 2), index=1)
class Direction(Enum):
    """
    Direction
    """

    input = "INPUT"
    """
    Input direction.
    """

    output = "OUTPUT"
    """
    Output direction
    """


@reference_in_the_book(section=(5, 7, 7, 2), index=2)
class State_of_event(Enum):
    """
    State of an event
    """

    on = "ON"
    """
    Event is on
    """

    off = "OFF"
    """
    Event is off.
    """


@abstract
@reference_in_the_book(section=(5, 7, 7, 7))
class Event_element(Submodel_element):
    """
    An event element.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(5, 7, 7, 2))
class Basic_event_element(Event_element):
    """
    A basic event element.
    """

    observed: "Model_reference"
    """
    Reference to the Referable, which defines the scope of the event. Can be AAS, Submodel
    or SubmodelElement. Reference to a referable, e.g. a data element or a submodel, that
    is being observed.
    """

    direction: "Direction"
    """
    Direction of event.
    Can be { Input, Output }.
    """

    state: "State_of_event"
    """
    State of event.
    Can be { On, Off }.
    """

    message_topic: Optional["Non_empty_string"]
    """
    Information for the outer message infrastructure for scheduling the event to the
    respective communication channel.
    """

    message_broker: Optional["Model_reference"]
    """
    Information, which outer message infrastructure shall handle messages for
    the EventElement. Refers to a Submodel, SubmodelElementList, SubmodelElementStruct or
    Entity, which contains DataElements describing the proprietary specification for
    the message broker.

    .. note::
        for different message infrastructure, e.g. OPC UA or MQTT or AMQP, these
        proprietary specification could be standardized by having respective Submodels.
    """

    last_update: Optional["Date_time"]
    """
    Timestamp in UTC, when the last event was received (input direction) or sent
    (output direction).
    """

    min_interval: Optional["Date_time"]
    """
    For input direction, reports on the maximum frequency, the software entity behind
    the respective Referable can handle input events. For output events, specifies
    the maximum frequency of outputting this event to an outer infrastructure.
    Might be not specified, that is, there is no minimum interval.
    """

    max_interval: Optional["Date_time"]
    """
    For input direction: not applicable.
    For output direction: maximum interval in time, the respective Referable shall send
    an update of the status of the event, even if no other trigger condition for
    the event was not met. Might be not specified, that is, there is no maximum interval.
    """

    def __init__(
        self,
        observed: "Model_reference",
        direction: "Direction",
        state: "State_of_event",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        message_topic: Optional["Non_empty_string"] = None,
        message_broker: Optional["Model_reference"] = None,
        last_update: Optional["Date_time"] = None,
        min_interval: Optional["Date_time"] = None,
        max_interval: Optional["Date_time"] = None,
    ) -> None:
        Event_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.observed = observed
        self.direction = direction
        self.state = state
        self.message_topic = message_topic
        self.message_broker = message_broker
        self.last_update = last_update
        self.min_interval = min_interval
        self.max_interval = max_interval


@reference_in_the_book(section=(5, 7, 7, 2), index=3)
class Event_payload(DBC):
    """
    Defines the necessary information of an event instance sent out or received.

    .. note::
        the payload is not part of the information model as exchanged via
        the AASX package format but used in re-active Asset Administration Shells.
    """

    source: "Model_reference"
    """
    Reference to the source event element, including identification of AAS, Submodel,
    SubmodelElements.
    """

    source_semantic_id: Optional["Global_reference"]
    """
    semanticId of the source event element, if available
    """

    observable_reference: "Model_reference"
    """
    Reference to the referable, which defines the scope of the event.
    Can be AAS, Submodel or SubmodelElement.
    """

    observable_semantic_id: Optional["Global_reference"]
    """
    semanticId of the referable which defines the scope of the event, if available.
    """

    topic: Optional["Non_empty_string"]
    """
    Information for the outer message infrastructure for scheduling the event to
    the respective communication channel.
    """

    subject_id: Optional["Global_reference"]
    """
    Subject, who/which initiated the creation.
    """

    time_stamp: "Date_time_stamp"
    """
    Timestamp in UTC, when this event was triggered.
    """

    payload: Optional["Non_empty_string"]
    """
    Event specific payload.
    """

    def __init__(
        self,
        source: "Model_reference",
        observable_reference: "Model_reference",
        time_stamp: "Date_time_stamp",
        source_semantic_id: Optional["Global_reference"] = None,
        observable_semantic_id: Optional["Global_reference"] = None,
        topic: Optional["Non_empty_string"] = None,
        subject_id: Optional["Global_reference"] = None,
        payload: Optional["Non_empty_string"] = None,
    ) -> None:

        self.source = source
        self.observable_reference = observable_reference
        self.time_stamp = time_stamp
        self.source_semantic_id = source_semantic_id
        self.observable_semantic_id = observable_semantic_id
        self.topic = topic
        self.subject_id = subject_id
        self.payload = payload


@reference_in_the_book(section=(5, 7, 7, 6), index=1)
class Entity_type(Enum):
    """
    Enumeration for denoting whether an entity is a self-managed entity or a co-managed
    entity.
    """

    Co_managed_entity = "COMANAGEDENTITY"
    """
    For co-managed entities there is no separate AAS. Co-managed entities need to be
    part of a self-managed entity.
    """

    Self_managed_entity = "SELFMANAGEDENTITY"
    """
    Self-Managed Entities have their own AAS but can be part of the bill of material of
    a composite self-managed entity. The asset of an I4.0 Component is a self-managed
    entity per definition."
    """


@reference_in_the_book(section=(5, 7, 7, 6))
class Entity(Submodel_element):
    """
    An entity is a submodel element that is used to model entities.

    :constraint AASd-014:
        Either the attribute globalAssetId or specificAssetId of an Entity must be set
        if Entity/entityType is set to “SelfManagedEntity”. They are not existing
        otherwise.
    """

    entity_type: "Entity_type"
    """
    Describes whether the entity is a co- managed entity or a self-managed entity.
    """

    statements: Optional[List["Submodel_element"]]
    """
    Describes statements applicable to the entity by a set of submodel elements,
    typically with a qualified value.
    """

    global_asset_ID: Optional["Reference"]
    """
    Reference to the asset the entity is representing.
    """

    specific_asset_ID: Optional["Identifier_key_value_pair"]
    """
    Reference to an identifier key value pair representing a specific identifier
    of the asset represented by the asset administration shell.
    """

    def __init__(
        self,
        entity_type: "Entity_type",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        statements: Optional[List["Submodel_element"]] = None,
        global_asset_ID: Optional["Reference"] = None,
        specific_asset_ID: Optional["Identifier_key_value_pair"] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.statements = statements if statements is not None else []
        self.entity_type = entity_type
        self.global_asset_ID = global_asset_ID
        self.specific_asset_ID = specific_asset_ID


@abstract
@reference_in_the_book(section=(6, 7, 7, 7))
class Event(Submodel_element):
    """
    An event.

    :constraint AASd-061:
        If the semanticId of a Event submodel element references a ConceptDescription
        then the category of the ConceptDescription shall be one of the following:
        EVENT.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional[Modeling_kind] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(6, 7, 7, 2))
class Basic_Event(Event):
    """
    A basic event.
    """

    observed: "Reference"
    """
    Reference to a referable, e.g. a data element or a submodel, that is being
    observed.
    """

    def __init__(
        self,
        observed: "Reference",
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional[Modeling_kind] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List[Qualifier]] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
    ) -> None:
        Event.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.observed = observed


@reference_in_the_book(section=(5, 7, 7, 12))
class Operation(Submodel_element):
    """
    An operation is a submodel element with input and output variables.
    """

    input_variables: Optional[List["Operation_variable"]]
    """
    Input parameter of the operation.
    """

    output_variables: Optional[List["Operation_variable"]]
    """
    Output parameter of the operation.
    """

    inoutput_variables: Optional[List["Operation_variable"]]
    """
    Parameter that is input and output of the operation.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List[Global_reference]] = None,
        input_variables: Optional[List["Operation_variable"]] = None,
        output_variables: Optional[List["Operation_variable"]] = None,
        inoutput_variables: Optional[List["Operation_variable"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.input_variables = input_variables if input_variables is not None else []
        self.output_variables = output_variables if output_variables is not None else []
        self.inoutput_variables = (
            inoutput_variables if inoutput_variables is not None else []
        )


@reference_in_the_book(section=(5, 7, 7, 13), index=1)
class Operation_variable(DBC):
    """
    An operation variable is a submodel element that is used as input or output variable
    of an operation.

    .. note::
        Note: OperationVariable is introduced as separate class to enable future extensions,
        e.g. for adding a default value, cardinality (option/mandatory).
    """

    value: "Submodel_element"
    """
    Describes the needed argument for an operation via a submodel element
    """

    def __init__(self, value: "Submodel_element") -> None:
        self.value = value


@reference_in_the_book(section=(5, 7, 7, 4))
class Capability(Submodel_element):
    """
    A capability is the implementation-independent description of the potential of an
    asset to achieve a certain effect in the physical or virtual world.

    .. note::
        The semanticId of a capability is typically an ontology. Thus, reasoning on
        capabilities is enabled.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        qualifiers: Optional[List["Qualifier"]] = None,
        data_specifications: Optional[List[Global_reference]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(5, 7, 8))
@serialization(with_model_type=True)
class Concept_description(Identifiable, Has_data_specification):
    """
    The semantics of a property or other elements that may have a semantic description
    is defined by a concept description. The description of the concept should follow a
    standardized schema (realized as data specification template).

    :constraint AASd-051:
        A ConceptDescription shall have one of the following categories
        VALUE, PROPERTY, REFERENCE, DOCUMENT, CAPABILITY, RELATIONSHIP, COLLECTION,
        FUNCTION, EVENT, ENTITY, APPLICATION_CLASS, QUALIFIER, VIEW.

        Default: PROPERTY.
    """

    is_case_of: Optional[List["Global_reference"]]
    """
    Reference to an external definition the concept is compatible to or was derived from

    .. note::
       Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360"
    """

    def __init__(
        self,
        ID: Identifier,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List[Global_reference]] = None,
        is_case_of: Optional[List["Global_reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            ID=ID,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.is_case_of = is_case_of if is_case_of is not None else []


@reference_in_the_book(section=(5, 7, 9))
@serialization(with_model_type=True)
class View(Referable, Has_semantics, Has_data_specification):
    """
    A view is a collection of referable elements w.r.t. to a specific viewpoint of one
    or more stakeholders.

    .. note::

       Views are a projection of submodel elements for a given perspective.
       They are not equivalent to submodels.

    :constraint AASd-064:
        If the semanticId of a View references a ConceptDescription
        then the category of the ConceptDescription shall be VIEW.
    """

    contained_elements: List["Reference"]
    """
    Reference to a referable element that is contained in the view.
    """

    def __init__(
        self,
        extensions: Optional[List["Extension"]] = None,
        ID_short: Optional[Non_empty_string] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        checksum: Optional["Non_empty_string"] = None,
        semantic_ID: Optional["Global_reference"] = None,
        data_specifications: Optional[List["Global_reference"]] = None,
        contained_elements: Optional[List["Reference"]] = None,
    ) -> None:
        Referable.__init__(
            self,
            extensions=extensions,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            checksum=checksum,
        )

        Has_semantics.__init__(self, semantic_ID)

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.contained_elements = (
            contained_elements if contained_elements is not None else []
        )


@reference_in_the_book(section=(5, 7, 10, 3), index=5)
class Identifiable_elements(Enum):
    """
    Enumeration of all identifiable elements within an asset administration shell.
    """

    Asset_administration_shell = "AssetAdministrationShell"
    Concept_description = "ConceptDescription"
    Submodel = "Submodel"


@reference_in_the_book(section=(5, 7, 10, 3), index=4)
class Submodel_element_elements(Enum):
    """
    Enumeration of all referable elements within an asset administration shell.
    """

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Data_element = "DataElement"
    """
    Data Element.

    .. note::
        Data Element is abstract, *i.e.* if a key uses “DataElement” the reference may
        be a Property, a File etc.
    """
    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event element

    .. note::

        Event is abstract
    """
    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """
    Property with a value that can be provided in multiple languages
    """
    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """
    Range with min and max
    """
    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """

    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, i.e. if a key uses “SubmodelElement”
        the reference may be a Property, a SubmodelElementList,
        an Operation etc.
    """
    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """
    Submodel_element_struct = "SubmodelElementStruct"
    """
    Struct of Submodel Elements
    """


@reference_in_the_book(section=(5, 7, 10, 3), index=3)
@is_superset_of(enums=[Submodel_element_elements, Identifiable_elements])
class Referable_elements(Enum):
    """
    Enumeration of all referable elements within an asset administration shell
    """

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a Property, a File *etc.*
    """

    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event.

    .. note::

        Event Element is abstract.
    """

    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """
    Property with a value that can be provided in multiple languages
    """
    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """
    Range with min and max
    """
    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`~Submodel_element`
        the reference may be a Property, a SubmodelElementCollection,
        an Operation *etc.*
    """

    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """
    Submodel_element_struct = "SubmodelElementStruct"
    """
    Struct of Submodel Elements
    """


@reference_in_the_book(section=(5, 7, 10, 3), index=2)
@is_superset_of(enums=[Referable_elements])
class Key_elements(Enum):
    """Enumeration of different key value types within a key."""

    Fragment_reference = "FragmentReference"
    """
    Bookmark or a similar local identifier of a subordinate part of
    a primary resource
    """

    Global_reference = "GlobalReference"

    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event_element = "BasicEventElement"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a Property, a File *etc.*
    """

    Entity = "Entity"
    Event_element = "EventElement"
    """
    Event.

    .. note::

        Event element is abstract.
    """

    File = "File"

    Multi_language_property = "MultiLanguageProperty"
    """Property with a value that can be provided in multiple languages"""

    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """Range with min and max"""

    Reference_element = "ReferenceElement"
    """
    Reference
    """
    Relationship_element = "RelationshipElement"
    """
    Relationship
    """
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`~Submodel_element`
        the reference may be a Property, a SubmodelElementCollection`,
        an Operation *etc.*
    """

    Submodel_element_list = "SubmodelElementList"
    """
    List of Submodel Elements
    """
    Submodel_element_struct = "SubmodelElementStruct"
    """
    Struct of Submodel Elements
    """


@abstract
@serialization(with_model_type=True)
@reference_in_the_book(section=(6, 1))
class Data_specification_content(DBC):
    """
    Missing summary.

    .. note::
        The Data Specification Templates do not belong to the meta-model of the Asset
        Administration Shell. In serializations that choose specific templates
        the corresponding data specification content may be directly incorporated.
    """

    # TODO (sadu 2021-11-17)
    # No table for class in the book
    # to be implemented
    pass


@reference_in_the_book(section=(6, 8, 2, 3), index=2)
class Data_type_IEC61360(Enum):
    Date = "DATE"
    """
    values containing a calendar date, conformant to ISO 8601:2004 Format yyyy-mm-dd
    Example from IEC 61360-1:2017: "1999-05-31" is the [DATE] representation of:
    31 May 1999.
    """
    String = "STRING"
    """
    values consisting of sequence of characters but cannot be translated into other
    languages
    """
    String_translatable = "STRING_TRANSLATABLE"
    """
    values containing string but shall be represented as different string in different
    languages
    """
    Integer_Measure = "INTEGER_MEASURE"
    """
    values containing values that are measure of type INTEGER. In addition such a value
    comes with a physical unit.
    """
    Integer_count = "INTEGER_COUNT"
    """
    values containing values of type INTEGER but are no currencies or measures
    """
    Integer_currency = "INTEGER_CURRENCY"
    """
    values containing values of type INTEGER that are currencies
    """
    Real_measure = "REAL_MEASURE"
    """
    values containing values that are measures of type REAL. In addition such a value
    comes with a physical unit.
    """
    Real_count = "REAL_COUNT"
    """
    values containing numbers that can be written as a terminating or non-terminating
    decimal; a rational or irrational number but are no currencies or measures
    """
    Real_currency = "REAL_CURRENCY"
    """
    values containing values of type REAL that are currencies
    """
    Boolean = "BOOLEAN"
    """
    values representing truth of logic or Boolean algebra (TRUE, FALSE)
    """
    IRI = "IRI"
    """
    values containing values of type STRING conformant to Rfc 3987

    .. note::
        In IEC61360-1 (2017) only URI is supported. An Iri type allows in particular to
        express a URL or an URI
    """
    IRDI = "IRDI"
    """
    values conforming to ISO/IEC 11179 series global identifier sequences IRDI can be
    used instead of the more specific data types ICID or ISO29002_IRDI. ICID values are
    value conformant to an IRDI, where the delimiter between RAI and ID is “#” while the
    delimiter between DI and VI is confined to “##” ISO29002_IRDI values are values
    containing a global identifier that identifies an administrated item in a registry.
    The structure of this identifier complies with identifier syntax defined in ISO/TS
    29002-5. The identifier shall fulfill the requirements specified in ISO/TS 29002-5
    for an "international registration data identifier" (IRDI).
    """
    Rational = "RATIONAL"
    """
    values containing values of type rational
    """
    Rational_measure = "RATIONAL_MEASURE"
    """
    values containing values of type rational.
    In addition such a value comes with a physical unit.
    """
    Time = "TIME"
    """
    values containing a time, conformant to ISO 8601:2004 but restricted to
    what is allowed in the corresponding type in xml.
    Format hh:mm (ECLASS) Example from IEC 61360-1:2017: "13:20:00-05:00" is the [TIME]
    representation of: 1.20 p.m. for Eastern Standard Time,
    which is 5 hours behind Coordinated Universal Time (UTC).
    """
    Timestamp = "TIMESTAMP"
    """
    values containing a time, conformant to ISO 8601:2004 but restricted to
    what is allowed in the corresponding type in xml. Format yyyy-mm-dd hh:mm (ECLASS)
    """
    File = "FILE"
    """
    values containing an address to a file. The values are of type URI and can represent
    an absolute or relative path. IEC61360 does not support the file type.
    """
    HTML = "HTML"
    """
    Values containing string with any sequence of characters, using the syntax of HTML5
    (see W3C Recommendation 28:2014)
    """
    Blob = "BLOB"
    """
    values containing the content of a file. Values may be binaries.
    HTML conformant to HTML5 is a special blob. In IEC61360 binary is for a sequence of
    bits, each bit being represented by “0” and “1” only. A binary is a blob but a blob
    may also contain other source code.
    """


@reference_in_the_book(section=(6, 8, 2, 3), index=5)
class Level_type(Enum):
    Min = "Min"
    Max = "Max"
    Nom = "Nom"
    Type = "Type"


@reference_in_the_book(section=(6, 8, 2, 3), index=4)
class Value_reference_pair(DBC):
    """
    A value reference pair within a value list. Each value has a global unique id
    defining its semantic.
    """

    value: Non_empty_string
    """
    The value of the referenced concept definition of the value in valueId.
    """

    value_ID: "Reference"
    """
    Global unique id of the value.

    :constraint AASd-078:
        If the valueId of a ValueReferencePair references a
        ConceptDescription then the ConceptDescription/category shall be one of
        following values: VALUE.
    """

    def __init__(self, value: Non_empty_string, value_ID: "Reference") -> None:
        self.value = value
        self.value_ID = value_ID


@reference_in_the_book(section=(6, 8, 2, 3), index=3)
class Value_list(DBC):
    """
    A set of value reference pairs.
    """

    value_reference_pairs: List["Value_reference_pair"]
    """
    A pair of a value together with its global unique id.
    """

    def __init__(
        self, value_reference_pairs: Optional[List["Value_reference_pair"]] = None
    ) -> None:
        self.value_reference_pairs = (
            value_reference_pairs if value_reference_pairs is not None else []
        )


@reference_in_the_book(section=(6, 8, 2, 3))
class Data_specification_IEC61360(Data_specification_content):
    """
    Content of data specification template for concept descriptions conformant to
    IEC 61360.
    """

    preferred_name: Optional["Lang_string_set"]
    """
    Preferred name

    :constraint AASd-076:
        For all ConceptDescriptions using data specification template
        IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0)
        at least a preferred name in English shall be defined.
    """

    short_name: Optional["Lang_string_set"]
    """
    Short name
    """

    unit: Optional[Non_empty_string]
    """
    Unit
    """

    unit_ID: Optional["Reference"]
    """
    Unique unit id
    """

    source_of_definition: Optional[Non_empty_string]
    """
    Source of definition
    """

    symbol: Optional[Non_empty_string]
    """
    Symbol
    """

    data_type: Optional["Data_type_IEC61360"]
    """
    Data Type

    :constraint AASd-070:
        For a ConceptDescription with category PROPERTY or VALUE using
        data specification template IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0) -
        DataSpecificationIEC61360/dataType is mandatory and shall be defined.

    :constraint AASd-071:
        For a ConceptDescription with category REFERENCE using data
        specification template IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0) -
        DataSpecificationIEC61360/dataType is STRING by default.

    :constraint AASd-072:
        For a ConceptDescription with category DOCUMENT using data
        specification template IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0) -
        DataSpecificationIEC61360/dataType shall be one of the following values: STRING or
        URL.

    :constraint AASd-073:
        For a ConceptDescription with category QUALIFIER using data
        specification template IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0) -
        DataSpecificationIEC61360/dataType is mandatory and shall be defined.

    :constraint AASd-103:
        If DataSpecificationIEC61360/-dataType one of: INTEGER_MEASURE,
        REAL_MEASURE, RATIONAL_MEASURE, INTEGER_CURRENCY, REAL_CURRENCY, then
        DataSpecificationIEC61360/unit or DataSpecificationIEC61360/unitId shall be
        defined.
    """

    definition: Optional["Lang_string_set"]
    """
    Definition in different languages

    :constraint AASd-074:
        For all ConceptDescriptions except for ConceptDescriptions of
        category VALUE using data specification template IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0) -
        DataSpecificationIEC61360/definition is mandatory and shall be defined at least
        in English.
    """

    value_format: Optional[Non_empty_string]
    """
    Value Format
    """

    value_list: Optional["Value_list"]
    """
    List of allowed values

    See :constraintref:`AASd-102`
    """

    value: Optional[Non_empty_string]
    """
    Value

    :constraint AASd-101:
        If DataSpecificationIEC61360/category equal to VALUE then
        DataSpecificationIEC61360/value shall be set.

    :constraint AASd-102:
        If DataSpecificationIEC61360/value or
        DataSpecificationIEC61360/valueId is not empty then
        DataSpecificationIEC61360/valueList shall be empty and vice versa.
    """

    value_ID: Optional["Reference"]
    """
    Unique value id

    See :constraintref:`AASd-102`
    """

    level_type: Optional["Level_type"]
    """
    Set of levels.
    """

    def __init__(
        self,
        preferred_name: Optional["Lang_string_set"] = None,
        short_name: Optional["Lang_string_set"] = None,
        unit: Optional[Non_empty_string] = None,
        unit_ID: Optional["Reference"] = None,
        source_of_definition: Optional[Non_empty_string] = None,
        symbol: Optional[Non_empty_string] = None,
        data_type: Optional["Data_type_IEC61360"] = None,
        definition: Optional["Lang_string_set"] = None,
        value_format: Optional[Non_empty_string] = None,
        value_list: Optional["Value_list"] = None,
        value: Optional[Non_empty_string] = None,
        value_ID: Optional["Reference"] = None,
        level_type: Optional["Level_type"] = None,
    ) -> None:
        self.preferred_name = preferred_name
        self.short_name = short_name
        self.unit = unit
        self.unit_ID = unit_ID
        self.source_of_definition = source_of_definition
        self.symbol = symbol
        self.data_type = data_type
        self.definition = definition
        self.value_format = value_format
        self.value_list = value_list
        self.value = value
        self.value_ID = value_ID
        self.level_type = level_type


@reference_in_the_book(section=(6, 8, 3, 2))
class Data_specification_physical_unit(Data_specification_content):
    """TODO"""

    # TODO (sadu 2021-11-17)
    # No table for class in the book

    unit_name: Optional[Non_empty_string]
    """
    Unit Name
    """

    unit_symbol: Optional[Non_empty_string]
    """
    Unit Symbol
    """

    definition: Optional["Lang_string_set"]
    """
    Definition
    """

    SI_notation: Optional[Non_empty_string]
    """
    SI Notation
    """

    DIN_notation: Optional[Non_empty_string]
    """
    DIN Notation
    """

    ECE_name: Optional[Non_empty_string]
    """
    ECE Name
    """

    ECE_code: Optional[Non_empty_string]
    """
    ECE Code
    """

    NIST_name: Optional[Non_empty_string]
    """
    NIST Name
    """

    source_of_definition: Optional[Non_empty_string]
    """
    Source Of Definition
    """

    conversion_factor: Optional[Non_empty_string]
    """
    Conversion Factor
    """

    registration_authority_ID: Optional[Non_empty_string]
    """
    Registration Authority ID
    """

    supplier: Optional[Non_empty_string]
    """
    Supplier
    """

    def __init__(
        self,
        unit_name: Optional[Non_empty_string] = None,
        unit_symbol: Optional[Non_empty_string] = None,
        definition: Optional["Lang_string_set"] = None,
        SI_notation: Optional[Non_empty_string] = None,
        DIN_notation: Optional[Non_empty_string] = None,
        ECE_name: Optional[Non_empty_string] = None,
        ECE_code: Optional[Non_empty_string] = None,
        NIST_name: Optional[Non_empty_string] = None,
        source_of_definition: Optional[Non_empty_string] = None,
        conversion_factor: Optional[Non_empty_string] = None,
        registration_authority_ID: Optional[Non_empty_string] = None,
        supplier: Optional[Non_empty_string] = None,
    ) -> None:
        self.unit_name = unit_name
        self.unit_symbol = unit_symbol
        self.definition = definition
        self.SI_notation = SI_notation
        self.DIN_notation = DIN_notation
        self.ECE_name = ECE_name
        self.ECE_code = ECE_code
        self.NIST_name = NIST_name
        self.source_of_definition = source_of_definition
        self.conversion_factor = conversion_factor
        self.registration_authority_ID = registration_authority_ID
        self.supplier = supplier


# TODO (Nico & Marko, 2021-09-24):
#  We need to list in a comment all the constraints which were not implemented.

# TODO (mristin, 2021-10-27): re-order the entities so that they follow the structure
#  in the book as much as possible, but be careful about the inheritance


@reference_in_the_book(section=(5, 7, 9))
class Environment:
    """
    Container for the sets of different identifiables.

    .. note::
        w.r.t. file exchange: There is exactly one environment independent on how many
        files the contained elements are splitted. If the file is splitted then there
        shall be no element with the same identifier in two different files.
    """

    asset_administration_shells: Optional[List[Asset_administration_shell]]
    """
    Asset administration shell
    """

    submodels: Optional[List[Submodel]]
    """
    Submodel
    """

    concept_descriptions: Optional[List[Concept_description]]
    """
    Concept description
    """

    def __init__(
        self,
        asset_administration_shells: Optional[List[Asset_administration_shell]] = None,
        submodels: Optional[List[Submodel]] = None,
        concept_descriptions: Optional[List[Concept_description]] = None,
    ) -> None:
        self.asset_administration_shells = asset_administration_shells
        self.submodels = submodels
        self.concept_descriptions = concept_descriptions


@reference_in_the_book(section=(6, 1))
class Data_specification(DBC):
    """
    A template consists of the DataSpecificationContent containing the additional attributes
    to be added to the element instance that references the data specification template and
    meta information about the template itself.

    .. note::
        The Data Specification Templates do not belong to the metamodel of the asset
        administration shell. In serializations that choose specific templates
        the corresponding data specification content may be directly incorporated.
    """

    ID: "Identifier"
    """The globally unique identification of the element."""

    administration: Optional["Administrative_information"]
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    description: Optional["Lang_string_set"]
    """
    Description or comments on the element.

    The description can be provided in several languages.

    If no description is defined, then the definition of the concept
    description that defines the semantics of the element is used.

    Additional information can be provided, *e.g.*, if the element is
    qualified and which qualifier types can be expected in which
    context or which additional data specification templates are
    provided.
    """

    data_specification_content: Optional["Data_specification_content"]

    def __init__(
        self,
        ID: "Identifier",
        administration: Optional["Administrative_information"] = None,
        description: Optional["Lang_string_set"] = None,
        data_specification_content: Optional["Data_specification_content"] = None,
    ) -> None:
        self.ID = ID
        self.administration = administration
        self.description = description
        self.data_specification_content = data_specification_content
