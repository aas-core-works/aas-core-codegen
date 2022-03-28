"""Provide the meta model for Asset Administration Shell V3 Release Candidate 1."""
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

# region Book

__book_url__ = (
    "https://www.plattform-i40.de/IP/Redaktion/DE/Downloads/Publikation"
    "/Details_of_the_Asset_Administration_Shell_Part1_V3.pdf?__blob"
    "=publicationFile&v=5"
)
__book_version__ = "V3.0RC01"


# endregion

# region Verification

# noinspection SpellCheckingInspection
@verification
def is_IRI(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid IRI according to RFC 3987.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    scheme = "[a-zA-Z][a-zA-Z0-9+\\-.]*"
    ucschar = (
        "[\\xa0-\\ud7ff\\uf900-\\ufdcf\\ufdf0-\\uffef\\u10000-\\u1fffd"
        "\\u20000-\\u2fffd\\u30000-\\u3fffd\\u40000-\\u4fffd"
        "\\u50000-\\u5fffd\\u60000-\\u6fffd\\u70000-\\u7fffd"
        "\\u80000-\\u8fffd\\u90000-\\u9fffd\\ua0000-\\uafffd"
        "\\ub0000-\\ubfffd\\uc0000-\\ucfffd\\ud0000-\\udfffd"
        "\\ue1000-\\uefffd]"
    )
    iunreserved = f"([a-zA-Z0-9\\-._~]|{ucschar})"
    pct_encoded = "%[0-9A-Fa-f][0-9A-Fa-f]"
    sub_delims = "[!$&'()*+,;=]"
    iuserinfo = f"({iunreserved}|{pct_encoded}|{sub_delims}|:)*"
    h16 = "[0-9A-Fa-f]{1,4}"
    dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
    ipv4address = f"{dec_octet}\\.{dec_octet}\\.{dec_octet}\\.{dec_octet}"
    ls32 = f"({h16}:{h16}|{ipv4address})"
    ipv6address = (
        f"(({h16}:){{6}}{ls32}|::({h16}:){{5}}{ls32}|({h16})?::({h16}:){{4}}"
        f"{ls32}|(({h16}:)?{h16})?::({h16}:){{3}}{ls32}|(({h16}:){{2}}{h16})?::"
        f"({h16}:){{2}}{ls32}|(({h16}:){{3}}{h16})?::{h16}:{ls32}|(({h16}:){{4}}"
        f"{h16})?::{ls32}|(({h16}:){{5}}{h16})?::{h16}|(({h16}:){{6}}{h16})?::)"
    )
    unreserved = "[a-zA-Z0-9\\-._~]"
    ipvfuture = f"[vV][0-9A-Fa-f]+\\.({unreserved}|{sub_delims}|:)+"
    ip_literal = f"\\[({ipv6address}|{ipvfuture})\\]"
    ireg_name = f"({iunreserved}|{pct_encoded}|{sub_delims})*"
    ihost = f"({ip_literal}|{ipv4address}|{ireg_name})"
    port = "[0-9]*"
    iauthority = f"({iuserinfo}@)?{ihost}(:{port})?"
    ipchar = f"({iunreserved}|{pct_encoded}|{sub_delims}|[:@])"
    isegment = f"({ipchar})*"
    ipath_abempty = f"(/{isegment})*"
    isegment_nz = f"({ipchar})+"
    ipath_absolute = f"/({isegment_nz}(/{isegment})*)?"
    ipath_rootless = f"{isegment_nz}(/{isegment})*"
    ipath_empty = f"({ipchar}){{0}}"
    ihier_part = (
        f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|"
        f"{ipath_rootless}|{ipath_empty})"
    )
    iprivate = "[\\ue000-\\uf8ff\\uf0000-\\uffffd\\u100000-\\u10fffd]"
    iquery = f"({ipchar}|{iprivate}|[/?])*"
    ifragment = f"({ipchar}|[/?])*"
    isegment_nz_nc = f"({iunreserved}|{pct_encoded}|{sub_delims}|@)+"
    ipath_noscheme = f"{isegment_nz_nc}(/{isegment})*"
    irelative_part = (
        f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|"
        f"{ipath_noscheme}|{ipath_empty})"
    )
    irelative_ref = f"{irelative_part}(\\?{iquery})?(\\#{ifragment})?"
    iri = f"{scheme}:{ihier_part}(\\?{iquery})?(\\#{ifragment})?"
    iri_reference = f"({iri}|{irelative_ref})"

    return match(f"^{iri_reference}$", text) is not None


# noinspection SpellCheckingInspection
@verification
def is_IRDI(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid IRDI.

    See: https://wiki.eclass.eu/wiki/IRDI

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    numeric = r"[0-9]"
    safe_char = r"[A-Za-z0-9:_.]"

    irdi = (
        f"{numeric}{{4}}-{safe_char}{{1,35}}(-{safe_char}{{1,35}})?"
        f"#{safe_char}{{2}}-{safe_char}{{6}}"
        f"#{numeric}{{1,35}}"
    )

    return match(f"^{irdi}$", text) is not None


# noinspection SpellCheckingInspection
@verification
def is_ID_short(text: str) -> bool:
    """
    Check that :paramref:`text` is a valid ID short according to the book.

    :param text: Text to be checked
    :returns: True if the :paramref:`text` conforms to the pattern
    """
    return match(r"^[a-zA-Z][a-zA-Z_0-9]*$", text) is not None


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


# noinspection PyUnusedLocal
@verification
@implementation_specific
def value_and_data_type_match(value: str, data_type: "Data_type_def") -> bool:
    """Check that the actual type of :paramref:`value` matches :paramref:`data_type`."""
    raise NotImplementedError()


# endregion

# region Constrained primitive types


@invariant(lambda self: len(self) >= 1)
class Non_empty_string(str, DBC):
    """Represent a string with at least one character."""

    pass


@invariant(lambda self: is_MIME_type(self))
class MIME_typed(Non_empty_string, DBC):
    """Represent a string that follows the pattern of a MIME type."""


# endregion


@abstract
@reference_in_the_book(
    section=(4, 7, 2, 7), fragment="4.7.2.1 Extensions (HasExtensions)"
)
class Has_semantics(DBC):
    """
    Element that can have a semantic definition.
    """

    semantic_ID: Optional["Reference"]
    """
    Identifier of the semantic definition of the element. It is called semantic ID
    of the element.
    """

    def __init__(self, semantic_ID: Optional["Reference"] = None) -> None:
        self.semantic_ID = semantic_ID


@reference_in_the_book(section=(4, 7, 2, 1), index=2)
class Extension(Has_semantics):
    """
    Single extension of an element.
    """

    name: Non_empty_string
    """
    Name of the extension.

    :constraint AASd-077:
        The name of an extension within HasExtensions needs to be
        unique.
    """

    value_type: Optional["Data_type_def"]
    """
    Type of the value of the extension.

    Default: xsd:string
    """

    value: Optional[str]
    """
    Value of the extension
    """

    refers_to: Optional["Reference"]
    """
    Reference to an element the extension refers to.
    """

    def __init__(
        self,
        name: Non_empty_string,
        semantic_ID: Optional["Reference"] = None,
        value_type: Optional["Data_type_def"] = None,
        value: Optional[str] = None,
        refers_to: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        self.name = name
        self.value_type = value_type
        self.value = value
        self.refers_to = refers_to


@abstract
@reference_in_the_book(
    section=(4, 7, 2, 1),
    fragment="4.7.2.7 Semantic References Attributes (HasSemantics))",
)
class Has_extensions(DBC):
    """
    Element that can be extended by proprietary extensions.

    Note: Extensions are proprietary, i.e. they do not support global interoperability.
    """

    extensions: Optional[List["Extension"]]
    """
    An extension of the element.
    """

    def __init__(self, extensions: Optional[List["Extension"]] = None) -> None:
        self.extensions = extensions


@abstract
@invariant(lambda self: is_ID_short(self.ID_short), "Constraint AASd-002")
@serialization(with_model_type=True)
@reference_in_the_book(section=(4, 7, 2, 2))
class Referable(Has_extensions):
    """
    An element that is referable by its :attr:`~ID_short`.

    This identifier is not globally unique.
    This identifier is unique within the name space of the element.
    """

    ID_short: Non_empty_string
    """
    In case of identifiable this attribute is a short name of the element.
    In case of referable this ID is an identifying string of
    the element within its name space.

    .. note::

        In case the element is a property and the property has a semantic definition
        (:class:`.Has_semantics`) conformant to IEC61360 the idShort is typically
        identical to the short name in English.
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
    * the short name of the concept description-the idShort of the element
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

    The description can be provided in several languages. If no description is defined,
    then the definition of the concept description that defines the semantics
    of the element is used. Additional information can be provided,
    *e.g.*, if the element is qualified and which qualifier types can be expected
    in which context or which additional data specification templates are provided.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
    ) -> None:
        Has_extensions.__init__(self, extensions=extensions)

        self.ID_short = ID_short
        self.display_name = display_name
        self.category = category
        self.description = description


@abstract
@reference_in_the_book(section=(4, 7, 2, 3))
class Identifiable(Referable):
    """An element that has a globally unique identifier."""

    administration: Optional["Administrative_information"]
    """
    Administrative information of an identifiable element.

    .. note::

        Some of the administrative information like the version number might need to
        be part of the identification.
    """

    identification: "Identifier"
    """The globally unique identification of the element."""

    def __init__(
        self,
        ID_short: Non_empty_string,
        identification: "Identifier",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        administration: Optional["Administrative_information"] = None,
    ) -> None:
        Referable.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
        )

        self.identification = identification
        self.administration = administration


# fmt: off
@invariant(
    lambda self:
    not (self.ID_type == Identifier_type.IRDI) or is_IRDI(self.ID)
)
@invariant(
    lambda self:
    not (self.ID_type == Identifier_type.IRI) or is_IRI(self.ID)
)
@reference_in_the_book(section=(4, 7, 2, 4), index=0)
# fmt: on
class Identifier(DBC):
    """
    Used to uniquely identify an entity by using an identifier.
    """

    ID_type: "Identifier_type"
    """
    Type of the  Identifier, e.g. IRI, IRDI *etc.* The supported Identifier types are
    defined in the enumeration :class:`.Identifier_type`.
    """

    ID: Non_empty_string
    """
    Globally unique identifier of the element.

    Its type is defined in :attr:`~ID_type`.
    """

    def __init__(
        self,
        ID_type: "Identifier_type",
        ID: Non_empty_string,
    ) -> None:
        self.ID = ID
        self.ID_type = ID_type


@reference_in_the_book(section=(4, 7, 2, 4), index=1)
class Identifier_type(Enum):
    """Enumeration of different types of Identifiers for global identification"""

    IRDI = "IRDI"
    """
    IRDI according to ISO29002-5 as an Identifier scheme for properties
    and classifications.
    """

    IRI = "IRI"
    """IRI according to Rfc 3987. Every URIis an IRI"""

    Custom = "Custom"
    """Custom identifiers like GUIDs (globally unique identifiers)"""


@reference_in_the_book(section=(4, 7, 2, 5), index=1)
class Modeling_kind(Enum):
    """Enumeration for denoting whether an element is a template or an instance."""

    Template = "Template"
    """
    Software element which specifies the common attributes shared by all instances of
    the template.

    [SOURCE: IEC TR 62390:2005-01, 3.1.25] modified
    """

    Instance = "Instance"
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


@abstract
@reference_in_the_book(
    section=(4, 7, 2, 5),
    index=0,
    fragment=("4.7.2.5 Template or Instance of Model " "Element Attributes (HasKind)"),
)
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
    #  (See page 54 in the book V3RC1, kind has the cardinality ``0..1``.)
    def __init__(self, kind: Optional["Modeling_kind"] = None) -> None:
        self.kind = kind if kind is not None else Modeling_kind.Instance


@abstract
@reference_in_the_book(
    section=(4, 7, 2, 13),
    fragment=(
        "4.7.2.13 Used Templates for Data Specification Attributes "
        "(HasDataSpecification)"
    ),
)
class Has_data_specification(DBC):
    """
    Element that can be extended by using data specification templates.

    A data specification template defines a named set of additional attributes an
    element may or shall have. The data specifications used are explicitly specified
    with their global ID.
    """

    data_specifications: Optional[List["Reference"]]
    """
    Global reference to the data specification template used by the element.
    """

    # TODO (all, 2021-09-24): need to implement the constraint:
    #  page 60 in V3RC1
    #  :constraint AASd-050:
    #  If the DataSpecificationContent
    #  DataSpecificationIEC61360 is used for an element then the value of
    #  hasDataSpecification/dataSpecification shall contain the global reference to the
    #  IRI of the corresponding data specification template https://admin-
    #  shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0.

    def __init__(self, data_specifications: Optional[List["Reference"]] = None) -> None:
        self.data_specifications = data_specifications


# fmt: off
@invariant(
    lambda self:
    not (self.revision is not None) or self.version is not None,
    "Constraint AASd-005"
)
@reference_in_the_book(section=(4, 7, 2, 6))
# fmt: on
class Administrative_information(Has_data_specification):
    """
    Administrative meta-information for an element like version information.
    """

    version: Optional[Non_empty_string]
    """Version of the element."""

    revision: Optional[Non_empty_string]
    """Revision of the element."""

    def __init__(
        self,
        data_specifications: Optional[List["Reference"]] = None,
        version: Optional[Non_empty_string] = None,
        revision: Optional[Non_empty_string] = None,
    ) -> None:
        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.version = version
        self.revision = revision


# fmt: off
# TODO (mristin, 2021-11-17): review this constraint once the ``Constraint`` has been
#  implemented.
# @invariant(
#     lambda self:
#     are_unique(
#         constraint.qualifier_type
#         for constraint in self.qualifiers
#         if isinstance(constraint, Qualifier)
#     ),
#     "Constraint AASd-021"
# )
@abstract
@reference_in_the_book(section=(4, 7, 2, 8))
# fmt: on
class Qualifiable(DBC):
    """
    The value of a qualifiable element may be further qualified by one or more
    qualifiers or complex formulas.
    """

    qualifiers: Optional[List["Constraint"]]
    """Additional qualification of a qualifiable element."""

    def __init__(self, qualifiers: Optional[List["Constraint"]] = None) -> None:
        self.qualifiers = qualifiers


@abstract
@reference_in_the_book(section=(4, 7, 2, 9))
@serialization(with_model_type=True)
class Constraint(DBC):
    """A constraint is used to further qualify or restrict an element."""


# fmt: off
# TODO (mristin, 2021-11-17): rewrite using XSD constraints on strings
# @invariant(
#     lambda self:
#     not (self.value is not None) or is_of_type(self.value, self.value_type),
#     "Constraint AASd-020"
# )
@reference_in_the_book(section=(4, 7, 2, 11))
@serialization(with_model_type=True)
# fmt: on
class Qualifier(Constraint, Has_semantics):
    """
    A qualifier is a type-value-pair that makes additional statements w.r.t.  the value
    of the element.
    """

    type: Non_empty_string
    """
    The qualifier type describes the type of the qualifier that is applied to
    the element.
    """

    value_type: "Data_type_def"
    """
    Data type of the qualifier value.
    """

    value: Optional[str]
    """
    The qualifier value is the value of the qualifier.
    """

    value_ID: Optional["Reference"]
    """
    Reference to the global unique ID of a coded value.
    """

    def __init__(
        self,
        type: Non_empty_string,
        value_type: "Data_type_def",
        semantic_ID: Optional["Reference"] = None,
        value: Optional[str] = None,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        self.type = type
        self.value_type = value_type
        self.value = value
        self.value_ID = value_ID


@reference_in_the_book(section=(4, 7, 2, 12))
@serialization(with_model_type=True)
class Formula(Constraint):
    """
    A formula is used to describe constraints by a logical expression.
    """

    depends_on: Optional[List["Reference"]]
    """
    A formula may depend on referable or even external global elements that are used in
    the logical expression.

    The value of the referenced elements needs to be accessible so that it can be
    evaluated in the formula to true or false in the corresponding logical expression
    it is used in.
    """

    def __init__(self, depends_on: Optional[List["Reference"]]) -> None:
        self.depends_on = depends_on


@reference_in_the_book(section=(4, 7, 3))
class Asset_administration_shell(Identifiable, Has_data_specification):
    """Structure a digital representation of an :class:`.Asset`."""

    derived_from: Optional["Reference"]
    """The reference to the AAS the AAS was derived from."""

    security: Optional["Security"]
    """Definition of the security relevant aspects of the AAS."""

    asset_information: "Asset_information"
    """Meta-information about the asset the AAS is representing."""

    submodels: Optional[List["Reference"]]
    """
    References to submodels of the AAS.

    A submodel is a description of an aspect of the asset the AAS is representing.
    The asset of an AAS is typically described by one or more submodels. Temporarily
    no submodel might be assigned to the AAS.
    """

    views: Optional[List["View"]]
    """
    Stakeholder-specific views defined for the AAS.

    If needed, stakeholder specific views can be defined on the elements of the AAS.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        identification: "Identifier",
        asset_information: "Asset_information",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List["Reference"]] = None,
        derived_from: Optional["Reference"] = None,
        security: Optional["Security"] = None,
        submodels: Optional[List["Reference"]] = None,
        views: Optional[List["View"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.derived_from = derived_from
        self.asset_information = asset_information
        self.security = security
        self.submodels = submodels
        self.views = views


@reference_in_the_book(section=(4, 7, 4))
class Asset(Identifiable, Has_data_specification):
    """
    An Asset describes meta data of an asset that is represented by an AAS and is
    identical for all AAS representing this asset.

    The asset has a globally unique identifier.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        identification: "Identifier",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)


@reference_in_the_book(section=(4, 7, 5), index=0)
class Asset_information(DBC):
    """
    Identifying meta data of the asset that is represented by an AAS.

    The asset may either represent an asset type or an asset instance. The asset has
    a globally unique identifier plus – if needed – additional domain-specific
    (proprietary) identifiers. However, to support the corner case of very first
    phase of lifecycle where a stabilized/constant global asset identifier does not
    already exist, the corresponding attribute :attr:`~global_asset_ID` is optional.
    """

    asset_kind: "Asset_kind"
    """
    Denotes whether the Asset is of kind "Type" or "Instance".
    """

    global_asset_ID: Optional["Reference"]
    """
    Reference to either an Asset object or a global reference to the asset the AAS is
    representing.

    This attribute is required as soon as the AAS is exchanged via partners in the life
    cycle of the asset. In a first phase of the life cycle the asset might not yet have
    a global ID but already an internal identifier. The internal identifier would be
    modelled via :attr:`~specific_asset_IDs`.
    """

    specific_asset_IDs: Optional[List["Identifier_key_value_pair"]]
    """
    Additional domain-specific, typically proprietary, Identifier for the asset.

    For example, serial number.
    """

    bill_of_material: Optional[List["Reference"]]
    """
    A reference to a Submodel that defines the bill of material of the asset represented
    by the AAS.

    The submodels contain a set of entities describing the material used to compose
    the composite I4.0 Component.
    """

    default_thumbnail: Optional["File"]
    """
    Thumbnail of the asset represented by the asset administration shell.

    Used as default.
    """

    def __init__(
        self,
        asset_kind: "Asset_kind",
        global_asset_ID: Optional["Reference"] = None,
        specific_asset_IDs: Optional[List["Identifier_key_value_pair"]] = None,
        bill_of_material: Optional[List["Reference"]] = None,
        default_thumbnail: Optional["File"] = None,
    ) -> None:
        # TODO (Nico & Marko, 2021-09-24):
        #  We did not know how to implement Constraint AASd-023,
        #  see page 63 in the book V3RC1
        self.asset_kind = asset_kind
        self.global_asset_ID = global_asset_ID
        self.specific_asset_IDs = specific_asset_IDs
        self.bill_of_material = bill_of_material
        self.default_thumbnail = default_thumbnail


@reference_in_the_book(section=(4, 7, 5), index=1)
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


@reference_in_the_book(section=(4, 7, 5), index=2)
class Identifier_key_value_pair(Has_semantics):
    """
    An IdentifierKeyValuePair describes a generic identifier as key-value pair.
    """

    key: Non_empty_string
    """Key of the identifier"""

    value: "Non_empty_string"
    """The value of the identifier with the corresponding key."""

    external_subject_ID: "Reference"
    """The (external) subject the key belongs to or has meaning to."""

    def __init__(
        self,
        key: Non_empty_string,
        value: Non_empty_string,
        external_subject_ID: "Reference",
        semantic_ID: Optional["Reference"] = None,
    ) -> None:
        Has_semantics.__init__(self, semantic_ID)
        self.key = key
        self.value = value
        self.external_subject_ID = external_subject_ID


@reference_in_the_book(section=(4, 7, 6))
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

    submodel_elements: Optional[List["Submodel_element"]]
    """A submodel consists of zero or more submodel elements."""

    def __init__(
        self,
        ID_short: Non_empty_string,
        identification: "Identifier",
        submodel_elements: Optional[List["Submodel_element"]],
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        administration: Optional["Administrative_information"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        # TODO (Nico & Marko, 2021-09-24):
        #  How should we implement Constraint AASd-062 (page 64 in V3RC1)?
        #  Isn't this a constraint on the SubmodelElement?
        #  A submodel does not contain any attribute called ``Property``.

        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            administration=administration,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.submodel_elements = submodel_elements


@abstract
@reference_in_the_book(section=(4, 7, 7))
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
        ID_short: Non_empty_string,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Referable.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
        )

        Has_kind.__init__(self, kind=kind)

        Has_semantics.__init__(self, semantic_ID=semantic_ID)

        Qualifiable.__init__(self, qualifiers=qualifiers)

        Has_data_specification.__init__(self, data_specifications=data_specifications)


# TODO (mristin, 2021-10-27, page 77):
#  :constraint AASd-055:
#  If the semanticId of a RelationshipElement or an
#  AnnotatedRelationshipElement submodel element references a  ConceptDescription then
#  the ConceptDescription/category shall be one of following values: RELATIONSHIP.
#
#  🠒 We really need to think hard how we resolve the references. Should this class be
#  implementation-specific?
@reference_in_the_book(section=(4, 7, 8, 14))
class Relationship_element(Submodel_element):
    """
    A relationship element is used to define a relationship between two referable
    elements.

    :constraint AASd-055:
        If the semanticId of a RelationshipElement or an
        AnnotatedRelationshipElement submodel element references a ConceptDescription
        then the ConceptDescription/category shall be one of following values:
        RELATIONSHIP.
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
        ID_short: Non_empty_string,
        first: "Reference",
        second: "Reference",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.first = first
        self.second = second


@reference_in_the_book(section=(4, 7, 8, 15))
class Submodel_element_collection(Submodel_element):
    """
    A submodel element collection is a set or list of submodel elements.

    :constraint AASd-059:
        If the semanticId of a SubmodelElementCollection references a
        ConceptDescription then the category of the ConceptDescription shall be
        COLLECTION or ENTITY.

    :constraint AASd-092:
        If the semanticId of a SubmodelElementCollection with
        SubmodelElementCollection/allowDuplicates == false references
        a ConceptDescription then the ConceptDescription/category shall be ENTITY.

    :constraint AASd-093:
        If the semanticId of a SubmodelElementCollection with
        SubmodelElementCollection/allowDuplicates == true references
        a ConceptDescription then the ConceptDescription/category shall be COLLECTION.

    Example: A set of documents is referencing a concept description of category
    COLLECTION. A document within this collection is described as
    a SubmodelElementCollection referencing a concept description of category ENTITY.

    .. note::
       This means that no generic semanticId can be assigned to an element within
       a submodel element collection with allowDuplicates == false: every element within
       the entity needs a clear and unique semantics.
    """

    value: Optional[List["Submodel_element"]]
    """
    Submodel element contained in the collection.
    """

    ordered: Optional[bool]
    """
    If ordered=false, then the elements in the collection are not ordered.
    If ordered=true, then the elements in the collection are ordered.
    Default = false

    .. note::
      An ordered submodel element collection is typically implemented as an indexed
      array.
    """

    allow_duplicates: Optional[bool]
    """
    If allowDuplicates==true, then it is allowed that the collection contains several
    elements with the same semantics (i.e. the same semanticId).

    Default = false

    :constraint AASd-026:
        If allowDuplicates==false then it is not allowed that
        the collection contains several elements with the same semantics (i.e. the same
        semanticId).
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional[List["Submodel_element"]] = None,
        ordered: Optional[bool] = None,
        allow_duplicates: Optional[bool] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value
        self.ordered = ordered
        self.allow_duplicates = allow_duplicates


@abstract
@reference_in_the_book(section=(4, 7, 8, 5))
class Data_element(Submodel_element):
    """
    A data element is a submodel element that is not further composed out of
    other submodel elements.

    A data element is a submodel element that has a value. The type of value differs
    for different subtypes of data elements.

    .. note::

        A controlled value is a value whose meaning is given in an external source
        (see “ISO/TS 29002-10)

    :constraint AASd-090:
        For data elements DataElement/category shall be one of the
        following values: CONSTANT, PARAMETER or VARIABLE.
        Exception: File and Blob data elements.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(4, 7, 8, 11))
class Property(Data_element):
    """
    A property is a data element that has a single value.

    :constraint AASd-007:
        If both, the Property/value and the Property/valueId are
        present then the value of Property/value needs to be identical to the value of
        the referenced coded value in Property/valueId.

    :constraint AASd-052a:
        If the semanticId of a Property references a
        ConceptDescription then the ConceptDescription/category shall be one of
        following values: VALUE, PROPERTY.

    :constraint AASd-065:
        If the semanticId of a Property or MultiLanguageProperty
        references a ConceptDescription with the category VALUE then the value of the
        property is identical to DataSpecificationIEC61360/value and the valueId of the
        property is identical to DataSpecificationIEC61360/valueId.

    :constraint AASd-066:
        If the semanticId of a Property or MultiLanguageProperty
        references a ConceptDescription with the category PROPERTY and
        DataSpecificationIEC61360/valueList is defined the value and valueId of the
        property is identical to one of the value reference pair types references in the
        value list, i.e. ValueReferencePairType/value or ValueReferencePairType/valueId,
        resp.
    """

    value_type: "Data_type_def"
    """
    Data type of the value
    """

    value: Optional[str]
    """
    The value of the property instance.

    See :constraintref:`AASd-065`
    See :constraintref:`AASd-007`
    """

    value_ID: Optional["Reference"]
    """
    Reference to the global unique id of a coded value.

    See :constraintref:`AASd-065`
    See :constraintref:`AASd-007`
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        value_type: "Data_type_def",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional[str] = None,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value_type = value_type
        self.value = value
        self.value_ID = value_ID


@reference_in_the_book(section=(4, 7, 8, 9))
class Multi_language_property(Data_element):
    """
    A property is a data element that has a multi-language value.

    See :constraintref:`AASd-065`

    :constraint AASd-052b:
        If the semanticId of a MultiLanguageProperty references
        a ConceptDescription then the ConceptDescription/category shall be one of
        following values: PROPERTY.

    :constraint AASd-012:
        If both, the MultiLanguageProperty/value and the
        MultiLanguageProperty/valueId are present then for each string in a specific
        language the meaning must be the same as specified in
        MultiLanguageProperty/valueId.

    :constraint AASd-067:
        If the semanticId of a MultiLanguageProperty references a
        ConceptDescription then DataSpecificationIEC61360/dataType shall be
        STRING_TRANSLATABLE.
    """

    value: Optional["Lang_string_set"]
    """
    The value of the property instance.
    See :constraintref:`AASd-012`
    See :constraintref:`AASd-065`
    """

    value_ID: Optional["Reference"]
    """
    Reference to the global unique id of a coded value.
    See :constraintref:`AASd-012`
    See :constraintref:`AASd-065`
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Lang_string_set"] = None,
        value_ID: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value
        self.value_ID = value_ID


@reference_in_the_book(section=(4, 7, 8, 12))
class Range(Data_element):
    """
    A range data element is a data element that defines a range with min and max.

    :constraint AASd-053:
        If the semanticId of a Range submodel element references a
        ConceptDescription then the ConceptDescription/category shall be one of following
        values: PROPERTY.

    :constraint AASd-068:
        If the semanticId of a Range submodel element references a
        ConceptDescription then DataSpecificationIEC61360/dataType shall be a numerical
        one, i.e. REAL_* or RATIONAL_*.

    :constraint AASd-069:
        If the semanticId of a Range references a ConceptDescription
        then DataSpecificationIEC61360/levelType shall be identical to the set
        {Min, Max}.
    """

    value_type: "Data_type_def"
    """
    Data type of the min und max
    """

    min: Optional[str]
    """
    The minimum value of the range.
    If the min value is missing, then the value is assumed to be negative infinite.
    """

    max: Optional[str]
    """
    The maximum value of the range.
    If the max value is missing,  then the value is assumed to be positive infinite.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        value_type: "Data_type_def",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        min: Optional[str] = None,
        max: Optional[str] = None,
    ) -> None:
        Data_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value_type = value_type
        self.min = min
        self.max = max


@reference_in_the_book(section=(4, 7, 8, 13))
class Reference_element(Data_element):
    """
    A reference element is a data element that defines a logical reference to another
    element within the same or another AAS or a reference to an external object or
    entity.
    """

    value: Optional["Reference"]
    """
    Reference to any other referable element of the same of any other AAS or a
    reference to an external object or entity.

    :constraint AASd-054:
        If the semanticId of a ReferenceElement submodel element
        references a ConceptDescription then the ConceptDescription/category shall be
        one of following values: REFERENCE.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional["Reference"] = None,
    ) -> None:
        Data_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.value = value


@reference_in_the_book(section=(4, 7, 8, 4))
class Blob(Data_element):
    """
    A BLOB is a data element that represents a file that is contained with its source
    code in the value attribute.
    """

    MIME_type: MIME_typed
    """
    MIME type of the content of the BLOB.

    The MIME type states which file extensions the file can have.
    Valid values are e.g. “application/json”, “application/xls”, ”image/jpg”
    The allowed values are defined as in RFC2046.
    """

    value: Optional[bytearray]
    """
    The value of the BLOB instance of a blob data element.

    .. note::
      In contrast to the file property the file content is stored directly as value
      in the Blob data element.

    :constraint AASd-057:
        The semanticId of a File or Blob submodel element shall only
        reference a ConceptDescription with the category DOCUMENT.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        MIME_type: MIME_typed,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional[bytearray] = None,
    ) -> None:
        Data_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.MIME_type = MIME_type
        self.value = value


@reference_in_the_book(section=(4, 7, 8, 8))
class File(Data_element):
    """
    A File is a data element that represents an address to a file.
    The value is an URI that can represent an absolute or relative path.

    See :constraintref:`AASd-057`
    """

    MIME_type: MIME_typed
    """
    MIME  type of the content of the BLOB.

    The  MIME  type states which file extensions the file can have.
    """

    value: Optional[str]
    """
    Path and name of the referenced file (with file extension).
    The path can be absolute or relative.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        MIME_type: MIME_typed,
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        value: Optional[str] = None,
    ) -> None:
        Data_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.MIME_type = MIME_type
        self.value = value


@reference_in_the_book(section=(4, 7, 8, 1))
class Annotated_relationship_element(Relationship_element):
    """
    An annotated relationship element is a relationship element that can be annotated
    with additional data elements.
    """

    annotations: Optional[List["Reference"]]
    """
    A reference to a data element that represents an annotation that holds for
    the relationship between the two elements.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        first: "Reference",
        second: "Reference",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        annotations: Optional[List["Reference"]] = None,
    ) -> None:
        Relationship_element.__init__(
            self,
            first=first,
            second=second,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.annotations = annotations


# TODO (mristin, 2021-10-27):
#  Most of the classes inheriting from Data_element need to specify the invariant:
#  "Constraint AASd-090"
#  For data elements DataElement/category shall be one of the
#  following values: CONSTANT, PARAMETER or VARIABLE. Exception: File and Blob
#  data elements.

# TODO (mristin, 2021-10-29): We can not implement this constraint, correct?
#  🠒 Double-check with Nico!
#  :constraint AASd-061:
#  If the semanticId of a Event submodel element references
#  a ConceptDescription then the category of the ConceptDescription shall be one of
#  the following: EVENT.


@reference_in_the_book(section=(4, 7, 8, 6), index=1)
class Entity_type(Enum):
    """
    Enumeration for denoting whether an entity is a self-managed entity or a co-managed
    entity.
    """

    Co_managed_entity = "CoManagedEntity"
    """
    For co-managed entities there is no separate AAS. Co-managed entities need to be
    part of a self-managed entity.
    """

    Self_managed_entity = "SelfManagedEntity"
    """
    Self-Managed Entities have their own AAS but can be part of the bill of material of
    a composite self-managed entity. The asset of an I4.0 Component is a self-managed
    entity per definition."
    """


@reference_in_the_book(section=(4, 7, 8, 6))
class Entity(Submodel_element):
    """
    An entity is a submodel element that is used to model entities.

    :constraint AASd-056:
        If the semanticId of a Entity submodel element
        references a ConceptDescription then the ConceptDescription/category shall
        be one of following values: ENTITY. The ConceptDescription describes
        the elements assigned to the entity via Entity/statement.
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

    :constraint AASd-014:
        Either the attribute globalAssetId or specificAssetId of an
        Entity must be set if Entity/entityType is set to “SelfManagedEntity”. They are
        not existing otherwise.
    """

    specific_asset_ID: Optional["Identifier_key_value_pair"]
    """
    Reference to an identifier key value pair representing a specific identifier
    of the asset represented by the asset administration shell.
    See :constraintref:`AASd-014`
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        entity_type: "Entity_type",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        statements: Optional[List["Submodel_element"]] = None,
        global_asset_ID: Optional["Reference"] = None,
        specific_asset_ID: Optional["Identifier_key_value_pair"] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.statements = statements
        self.entity_type = entity_type
        self.global_asset_ID = global_asset_ID
        self.specific_asset_ID = specific_asset_ID


@abstract
@reference_in_the_book(section=(4, 7, 8, 7))
class Event(Submodel_element):
    """
    An event.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List["Extension"]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional[Modeling_kind] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(4, 7, 8, 2))
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
        ID_short: Non_empty_string,
        observed: "Reference",
        extensions: Optional[List["Extension"]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional[Modeling_kind] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List[Constraint]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Event.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.observed = observed


@reference_in_the_book(section=(4, 7, 8, 10))
class Operation(Submodel_element):
    """
    An operation is a submodel element with input and output variables.

    :constraint AASd-060:
        If the semanticId of a Operation submodel element
        references a ConceptDescription then the category of the ConceptDescription
        shall be one of the following values: FUNCTION.
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
        ID_short: Non_empty_string,
        extensions: Optional[List["Extension"]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
        input_variables: Optional[List["Operation_variable"]] = None,
        output_variables: Optional[List["Operation_variable"]] = None,
        inoutput_variables: Optional[List["Operation_variable"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )

        self.input_variables = input_variables
        self.output_variables = output_variables
        self.inoutput_variables = inoutput_variables


@reference_in_the_book(section=(4, 7, 8, 10), index=1)
class Operation_variable:
    """
    An operation variable is a submodel element that is used as input or output variable
    of an operation.
    """

    value: "Submodel_element"
    """
    Describes the needed argument for an operation via a submodel element of
    kind=Template.
    Constraint AASd-008: The submodel element value of an operation variable shall be
    of kind=Template.
    """

    def __init__(self, value: "Submodel_element") -> None:
        self.value = value


@reference_in_the_book(section=(4, 7, 8, 3))
class Capability(Submodel_element):
    """
    A capability is the implementation-independent description of the potential of an
    asset to achieve a certain effect in the physical or virtual world.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List["Extension"]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        kind: Optional["Modeling_kind"] = None,
        semantic_ID: Optional["Reference"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        data_specifications: Optional[List["Reference"]] = None,
    ) -> None:
        Submodel_element.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            kind=kind,
            semantic_ID=semantic_ID,
            qualifiers=qualifiers,
            data_specifications=data_specifications,
        )


@reference_in_the_book(section=(4, 7, 9))
class Concept_description(Identifiable, Has_data_specification):
    """
    The semantics of a property or other elements that may have a semantic description
    is defined by a concept description. The description of the concept should follow a
    standardized schema (realized as data specification template).

    :constraint AASd-051:
        A ConceptDescription shall have one of the following
        categories:
        VALUE, PROPERTY, REFERENCE, DOCUMENT, CAPABILITY, RELATIONSHIP, COLLECTION,
        FUNCTION, EVENT, ENTITY, APPLICATION_CLASS, QUALIFIER, VIEW. Default: PROPERTY.
    """

    is_case_of: Optional[List["Reference"]]
    """
    Reference to an external definition the concept is compatible to or was derived
    from.

    .. note::
       Compare to is-case-of relationship in ISO 13584-32 & IEC EN 61360"
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        identification: "Identifier",
        extensions: Optional[List[Extension]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        administration: Optional["Administrative_information"] = None,
        data_specifications: Optional[List["Reference"]] = None,
        is_case_of: Optional[List["Reference"]] = None,
    ) -> None:
        Identifiable.__init__(
            self,
            identification=identification,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
            administration=administration,
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.is_case_of = is_case_of


@reference_in_the_book(section=(4, 7, 10))
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

    contained_elements: Optional[List["Reference"]]
    """
    Reference to a referable element that is contained in the view.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        extensions: Optional[List["Extension"]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        semantic_ID: Optional["Reference"] = None,
        data_specifications: Optional[List["Reference"]] = None,
        contained_elements: Optional[List["Reference"]] = None,
    ) -> None:
        Referable.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
        )

        Has_semantics.__init__(self, semantic_ID)

        Has_data_specification.__init__(
            self,
            data_specifications=data_specifications,
        )

        self.contained_elements = contained_elements


@invariant(lambda self: len(self.keys) >= 1)
@reference_in_the_book(
    section=(4, 7, 11),
    fragment="4.7.11 Referencing in Asset Administration Shells",
)
class Reference(DBC):
    """
    Reference to either a model element of the same or another AAs or to an external
    entity.

    A reference is an ordered list of keys, each key referencing an element. The
    complete list of keys may for example be concatenated to a path that then gives
    unique access to an element or entity.
    """

    keys: List["Key"]
    """Unique references in their name space."""

    def __init__(self, keys: List["Key"]) -> None:
        self.keys = keys


# fmt: off
@invariant(
    lambda self:
    not (self.ID_type == Key_type.IRI) or is_IRI(self.value)
)
@invariant(
    lambda self:
    not (self.ID_type == Key_type.IRDI) or is_IRDI(self.value)
)
@invariant(
    lambda self:
    not (self.type == Key_elements.Global_reference)
    or (self.ID_type != Key_type.ID_short and self.ID_type != Key_type.Fragment_ID),
    "Constraint AASd-080"
)
@invariant(
    lambda self:
    not (self.type == Key_elements.Asset_administration_shell)
    or (self.ID_type != Key_type.ID_short and self.ID_type != Key_type.Fragment_ID),
    "Constraint AASd-081"
)
@reference_in_the_book(
    section=(4, 7, 11), index=1,
    fragment="4.7.11 Referencing in Asset Administration Shells")
# fmt: on
class Key(DBC):
    """A key is a reference to an element by its id."""

    type: "Key_elements"
    """
    Denote which kind of entity is referenced.

    In case type = :attr:`~Key_elements.Global_reference` then the key represents
    a global unique id.

    In case type = :attr:`~Key_type.Fragment_ID` the key represents a bookmark or
    a similar local identifier within its parent element as specified by the key that
    precedes this key.

    In all other cases the key references a model element of the same or of another AAS.
    The name of the model element is explicitly listed.
    """

    value: Non_empty_string
    """The key value, for example an IRDI if the :attr:`~ID_type` is IRDI."""

    ID_type: "Key_type"
    """
    Type of the key value.

    :constraint AASd-080:
        In case Key/type == GlobalReference idType shall not be any
        LocalKeyType (IdShort, FragmentId).

    :constraint AASd-081:
        In case Key/type==AssetAdministrationShell Key/idType shall
        not be any LocalKeyType (IdShort, FragmentId).
    """

    def __init__(
        self, type: "Key_elements", value: Non_empty_string, ID_type: "Key_type"
    ) -> None:
        self.type = type
        self.value = value
        self.ID_type = ID_type


@reference_in_the_book(
    section=(4, 7, 11),
    index=4,
    fragment="4.7.11 Referencing in Asset Administration Shells",
)
class Identifiable_elements(Enum):
    """Enumeration of all identifiable elements within an asset administration shell."""

    Asset = "Asset"
    Asset_administration_shell = "AssetAdministrationShell"
    Concept_description = "ConceptDescription"
    Submodel = "Submodel"


@reference_in_the_book(
    section=(4, 7, 11),
    index=3,
    fragment="4.7.11 Referencing in Asset Administration Shells",
)
@is_superset_of(enums=[Identifiable_elements])
class Referable_elements(Enum):
    """Enumeration of all referable elements within an asset administration shell"""

    Access_permission_rule = "AccessPermissionRule"
    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset = "Asset"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event = "BasicEvent"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Concept_dictionary = "ConceptDictionary"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a Property, a File *etc.*
    """

    Entity = "Entity"
    Event = "Event"
    """
    Event.

    .. note::

        Event is abstract.
    """

    File = "File"
    Multi_language_property = "MultiLanguageProperty"
    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    Reference_element = "ReferenceElement"
    Relationship_element = "RelationshipElement"
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`~Submodel_element`
        the reference may be a Property, a :class:`.Submodel_element_collection`,
        an Operation *etc.*
    """

    Submodel_element_collection = "SubmodelElementCollection"
    View = "View"


@reference_in_the_book(
    section=(4, 7, 11),
    index=2,
    fragment="4.7.11 Referencing in Asset Administration Shells",
)
@is_superset_of(enums=[Referable_elements])
class Key_elements(Enum):
    """Enumeration of different key value types within a key."""

    Global_reference = "GlobalReference"
    """reference to an element not belonging to an asset administration shell"""

    Fragment_reference = "FragmentReference"
    """
    unique reference to an element within a file.

    The file itself is assumed to be part of an asset administration shell.
    """

    Access_permission_rule = "AccessPermissionRule"
    Annotated_relationship_element = "AnnotatedRelationshipElement"
    Asset = "Asset"
    Asset_administration_shell = "AssetAdministrationShell"
    Basic_event = "BasicEvent"
    Blob = "Blob"
    Capability = "Capability"
    Concept_description = "ConceptDescription"
    Concept_dictionary = "ConceptDictionary"
    Data_element = "DataElement"
    """
    Data element.

    .. note::

        Data Element is abstract, *i.e.* if a key uses :attr:`~Data_element`
        the reference may be a Property, a File *etc.*
    """

    Entity = "Entity"
    Event = "Event"
    """
    Event.

    .. note::

        Event is abstract.
    """

    File = "File"
    Multi_language_property = "MultiLanguageProperty"
    """Property with a value that can be provided in multiple languages"""

    Operation = "Operation"
    Property = "Property"
    Range = "Range"
    """Range with min and max"""

    Reference_element = "ReferenceElement"
    Relationship_element = "RelationshipElement"
    Submodel = "Submodel"
    Submodel_element = "SubmodelElement"
    """
    Submodel Element

    .. note::

        Submodel Element is abstract, *i.e.* if a key uses :attr:`~Submodel_element`
        the reference may be a Property, a :class:`.Submodel_element_collection`,
        an Operation *etc.*
    """

    Submodel_element_collection = "SubmodelElementCollection"
    View = "View"


@reference_in_the_book(
    section=(4, 7, 11),
    index=6,
    fragment="4.7.11 Referencing in Asset Administration Shells",
)
class Local_key_type(Enum):
    """Enumeration of different key value types within a key."""

    ID_short = "IdShort"
    """idShort of a referable element"""

    Fragment_ID = "FragmentId"
    """Identifier of a fragment within a file"""


@reference_in_the_book(
    section=(4, 7, 11),
    index=5,
    fragment="4.7.11 Referencing in Asset Administration Shells",
)
@is_superset_of(enums=[Local_key_type, Identifier_type])
class Key_type(Enum):
    """Enumeration of different key value types within a key."""

    ID_short = "IdShort"
    """idShort of a referable element"""

    Fragment_ID = "FragmentId"
    """Identifier of a fragment within a file"""

    IRDI = "IRDI"
    """
    IRDI according to ISO29002-5 as an Identifier scheme for properties and
    classifications.
    """

    IRI = "IRI"
    """IRI according to Rfc 3987. Every URI is an IRI."""

    Custom = "Custom"
    """Custom identifiers like GUIDs (globally unique identifiers)"""


@reference_in_the_book(section=(4, 7, 13, 2), fragment="4.7.13.2 Data Types")
class Data_type_def(Enum):
    Any_URI = "anyUri"
    Base64_binary = "base64Binary"
    Boolean = "boolean"
    Date = "date"
    Datetime = "dateTime"
    Datetime_stamp = "dateTimeStamp"
    Decimal = "decimal"
    Integer = "integer"
    Long = "long"
    Int = "int"
    Short = "short"
    Byte = "byte"
    Non_negative_integer = "nonNegativeInteger"
    Positive_integer = "positiveInteger"
    Unsigned_long = "unsignedLong"
    Unsigned_int = "unsignedInt"
    Unsigned_short = "unsignedShort"
    Unsigned_byte = "unsignedByte"
    Non_positive_integer = "nonPositiveInteger"
    Negative_integer = "negativeInteger"
    Double = "double"
    Duration = "duration"
    Day_time_duration = "dayTimeDuration"
    Year_month_duration = "yearMonthDuration"
    Float = "float"
    G_day = "gDay"
    G_month = "gMonth"
    G_month_day = "gMonthDay"
    G_year = "gYear"
    G_year_month = "gYearMonth"
    Hex_binary = "hexBinary"
    Notation = "NOTATION"
    Q_name = "QName"
    String = "string"
    Normalized_string = "normalizedString"
    Token = "token"
    Language = "language"
    Name = "Name"
    N_C_name = "NCName"
    Entity = "ENTITY"
    ID = "ID"
    IDREF = "IDREF"
    N_M_token = "NMTOKEN"
    Time = "time"


@implementation_specific
@reference_in_the_book(section=(4, 7, 13, 2), index=2, fragment="4.7.13.2 Data Types")
class Lang_string_set(DBC):
    """
    A set of strings, each annotated by the language of the string.

    The meaning of the string in each language shall be the same.
    """


@abstract
@reference_in_the_book(
    section=(4, 8, 1),
    fragment="4.8.1 Concept of Data Specification Templates",
)
class Data_specification_content(DBC):
    # No table for class in the book
    # to be implemented
    pass


@reference_in_the_book(
    section=(4, 8, 2),
    index=3,
    fragment=("4.8.2 Predefined Templates for Property and Value Descriptions"),
)
class Data_type_IEC_61360(Enum):
    Date = "DATE"
    String = "STRING"
    String_translatable = "STRING_TRANSLATABLE"
    Integer_Measure = "INTEGER_MEASURE"
    Integer_count = "INTEGER_COUNT"
    Integer_currency = "INTEGER_CURRENCY"
    Real_measure = "REAL_MEASURE"
    Real_count = "REAL_COUNT"
    Real_currency = "REAL_CURRENCY"
    Boolean = "BOOLEAN"
    URL = "URL"
    Rational = "RATIONAL"
    Rational_measure = "RATIONAL_MEASURE"
    Time = "TIME"
    Timestamp = "TIMESTAMP"


@reference_in_the_book(
    section=(4, 8, 2),
    index=4,
    fragment=("4.8.2 Predefined Templates for Property and Value Descriptions"),
)
class Level_type(Enum):
    Min = "Min"
    Max = "Max"
    Nom = "Nom"
    Typ = "Typ"


@reference_in_the_book(
    section=(4, 8, 2),
    index=2,
    fragment=("4.8.2 Predefined Templates for Property and Value Descriptions"),
)
class Value_reference_pair(DBC):
    """
    A value reference pair within a value list. Each value has a global unique id
    defining its semantic.
    """

    value: str
    """
    The value of the referenced concept definition of the value in valueId.
    """

    value_ID: "Reference"
    """
    Global unique id of the value.
    """

    def __init__(self, value: str, value_ID: "Reference") -> None:
        self.value = value
        self.value_ID = value_ID


@invariant(lambda self: len(self.value_reference_pair_types) >= 1)
@reference_in_the_book(
    section=(4, 8, 2),
    index=1,
    fragment=("4.8.2 Predefined Templates for Property and Value Descriptions"),
)
class Value_list(DBC):
    """
    A set of value reference pairs.
    """

    value_reference_pair_types: List["Value_reference_pair"]
    """
    A pair of a value together with its global unique id.
    """

    def __init__(
        self, value_reference_pair_types: List["Value_reference_pair"]
    ) -> None:
        self.value_reference_pair_types = value_reference_pair_types


@reference_in_the_book(
    section=(4, 8, 2),
    fragment=("4.8.2 Predefined Templates for Property and Value Descriptions"),
)
class Data_specification_IEC_61360(Data_specification_content):
    """
    Content of data specification template for concept descriptions conformant to
    IEC 61360.
    Although the IEC61360 attributes listed in this template are defined for properties
    and values and value lists only it is also possible to use the template for other
    definition This is shown in the tables Table 7, Table 8, Table 9 and Table 10.

    :constraint AASd-075:
        For all ConceptDescriptions using data specification template
        IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0)
        values for the attributes not being marked as mandatory or optional in tables
        Table 7, Table 8, Table 9 and Table 10.depending on its category are ignored and
        handled as undefined.
    """

    preferred_name: "Lang_string_set"
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

    data_type: Optional["Data_type_IEC_61360"]
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
        DataSpecificationIEC61360/dataType shall be one of the following values:
        STRING or URL.

    :constraint AASd-073:
        For a ConceptDescription with category QUALIFIER using data
        specification template IEC61360
        (http://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/2/0) -
        DataSpecificationIEC61360/dataType is mandatory and shall be defined.
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
    """

    value: Optional[str]
    """
    Value
    """

    value_ID: Optional["Reference"]
    """
    Unique value id
    """

    level_type: Optional["Level_type"]
    """
    Set of levels.
    """

    def __init__(
        self,
        preferred_name: "Lang_string_set",
        short_name: Optional["Lang_string_set"] = None,
        unit: Optional[Non_empty_string] = None,
        unit_ID: Optional["Reference"] = None,
        source_of_definition: Optional[Non_empty_string] = None,
        symbol: Optional[Non_empty_string] = None,
        data_type: Optional["Data_type_IEC_61360"] = None,
        definition: Optional["Lang_string_set"] = None,
        value_format: Optional[Non_empty_string] = None,
        value_list: Optional["Value_list"] = None,
        value: Optional[str] = None,
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


@reference_in_the_book(
    section=(4, 8, 3),
    fragment="4.8.3 Predefined Templates for Unit Concept Descriptions",
)
class Data_specification_physical_unit(Data_specification_content):
    # TODO (sadu, 2021-11-17): No table for class in the book

    unit_name: Non_empty_string
    """
    TODO
    """

    unit_symbol: Non_empty_string
    """
    TODO
    """

    definition: "Lang_string_set"
    """
    TODO
    """

    SI_notation: Optional[Non_empty_string]
    """
    TODO
    """

    SI_name: Optional[Non_empty_string]
    """
    TODO
    """

    DIN_notation: Optional[Non_empty_string]
    """
    TODO
    """

    ECE_name: Optional[Non_empty_string]
    """
    TODO
    """

    ECE_code: Optional[Non_empty_string]
    """
    TODO
    """

    NIST_name: Optional[Non_empty_string]
    """
    TODO
    """

    source_of_definition: Optional[Non_empty_string]
    """
    TODO
    """

    conversion_factor: Optional[Non_empty_string]
    """
    TODO
    """

    registration_authority_ID: Optional[Non_empty_string]
    """
    TODO
    """

    supplier: Optional[Non_empty_string]
    """
    TODO
    """

    def __init__(
        self,
        unit_name: Non_empty_string,
        unit_symbol: Non_empty_string,
        definition: "Lang_string_set",
        SI_notation: Optional[Non_empty_string] = None,
        SI_name: Optional[Non_empty_string] = None,
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
        self.SI_name = SI_name
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

# TODO (mristin, 2021-10-27): write a code generator that outputs the JSON schema and
#  then compare it against the
#  https://github.com/admin-shell-io/aas-specs/blob/master/schemas/json/aas.json


@abstract
@serialization(with_model_type=True)
@reference_in_the_book(section=(5, 3, 3))
class Certificate(DBC):
    """
    Certificate
    """

    policy_administration_point: "Policy_administration_point"
    """
    The access control administration policy point of the AAS.
    """

    def __init__(
        self, policy_administration_point: "Policy_administration_point"
    ) -> None:
        self.policy_administration_point = policy_administration_point


@reference_in_the_book(section=(5, 3, 3), index=1)
class Blob_certificate(Certificate):
    """
    Certificate provided as BLOB
    """

    blob_certificate: "Blob"
    """
    Certificate as BLOB.
    """

    last_certificate: bool
    """
    Denotes whether this certificate is the certificated that fast added last.
    """

    contained_extensions: Optional[List["Reference"]]
    """
    Extensions contained in the certificate.
    """

    def __init__(
        self,
        policy_administration_point: "Policy_administration_point",
        blob_certificate: "Blob",
        last_certificate: bool,
        contained_extensions: Optional[List["Reference"]] = None,
    ) -> None:
        Certificate.__init__(
            self, policy_administration_point=policy_administration_point
        )

        self.blob_certificate = blob_certificate
        self.last_certificate = last_certificate
        self.contained_extensions = contained_extensions


@reference_in_the_book(section=(5, 3, 5), index=3)
@invariant(lambda self: len(self.object_attributes) >= 1)
class Object_attributes(DBC):
    """
    A set of data elements that describe object attributes. These attributes need to
    refer to a data element within an existing submodel.
    """

    object_attributes: List[Reference]
    """
    Reference to a data element that further classifies an object.
    """

    def __init__(self, object_attributes: List[Reference]) -> None:
        self.object_attributes = object_attributes


@reference_in_the_book(section=(5, 3, 5), index=4)
class Permission(DBC):
    """
    Description of a single permission.
    """

    permission: Reference
    """
    Reference to a property that defines the semantics of the permission.

    Constraint AASs-010: The property referenced in Permission/permission shall have
    the category “CONSTANT”.
    Constraint AASs-011: The property referenced in Permission/permission shall be
    part of the submodel that is referenced within the “selectablePermissions” attribute
    of “AccessControl”."
    """

    kind_of_permission: "Permission_kind"
    """
    Description of the kind of permission. Possible kind of permission also include the
    denial of the permission.

    Values:
    * Allow
    * Deny
    * NotApplicable
    * Undefined"
    """

    def __init__(
        self, permission: Reference, kind_of_permission: "Permission_kind"
    ) -> None:
        self.permission = permission
        self.kind_of_permission = kind_of_permission


@reference_in_the_book(section=(5, 3, 5), index=5)
@invariant(lambda self: len(self.subject_attributes) >= 1)
class Subject_attributes:
    """
    A set of data elements that further classifies a specific subject.
    """

    subject_attributes: List["Reference"]
    """
    A data element that further classifies a specific subject.

    :constraint AASs-015:
        The data element SubjectAttributes/subjectAttribute shall be
        part of the submodel that is referenced within the “selectableSubjectAttributes”
        attribute of “AccessControl”."
    """

    def __init__(self, subject_attributes: List["Reference"]) -> None:
        self.subject_attributes = subject_attributes


@reference_in_the_book(section=(5, 3, 5), index=2)
class Permissions_per_object(DBC):
    """
    Table that defines access permissions for a specified object. The object is any
    referable element in the AAS. Additionally, object attributes can be defined that
    further specify the kind of object the permissions apply to.
    """

    object: Reference
    """
    Element to which permission shall be assigned.
    """

    target_object_attributes: Optional["Object_attributes"]
    """
    Target object attributes that need to be fulfilled so that the access permissions
    apply to the accessing subject.
    """

    permissions: Optional[List["Permission"]]
    """
    Permissions assigned to the object.
    The permissions hold for all subjects as specified in the access permission rule."
    """

    def __init__(
        self,
        object: Reference,
        target_object_attributes: Optional["Object_attributes"] = None,
        permissions: Optional[List["Permission"]] = None,
    ) -> None:
        self.object = object
        self.target_object_attributes = target_object_attributes
        self.permissions = permissions


@reference_in_the_book(section=(5, 3, 5), index=1)
class Access_permission_rule(Referable, Qualifiable):
    """
    Table that defines access permissions per authenticated subject for a set of objects
    (referable elements).
    """

    target_subject_attributes: "Subject_attributes"
    """
    Target subject attributes that need to be fulfilled by accessing subject to get the
    permissions defined by this rule.
    """

    permissions_per_object: Optional[List["Permissions_per_object"]]
    """
    Set of object-permission pairs that define the permissions per object within
    the access permission rule.
    """

    def __init__(
        self,
        ID_short: Non_empty_string,
        target_subject_attributes: "Subject_attributes",
        extensions: Optional[List["Extension"]] = None,
        display_name: Optional["Lang_string_set"] = None,
        category: Optional[Non_empty_string] = None,
        description: Optional["Lang_string_set"] = None,
        qualifiers: Optional[List["Constraint"]] = None,
        permissions_per_object: Optional[List["Permissions_per_object"]] = None,
    ) -> None:
        Referable.__init__(
            self,
            ID_short=ID_short,
            display_name=display_name,
            category=category,
            description=description,
            extensions=extensions,
        )

        Qualifiable.__init__(self, qualifiers=qualifiers)

        self.target_subject_attributes = target_subject_attributes
        self.permissions_per_object = permissions_per_object


@reference_in_the_book(section=(5, 3, 5))
class Access_control(DBC):
    """
    Access Control defines the local access control policy administration point.
    Access Control has the major task to define the access permission rules.
    """

    access_permission_rules: Optional[List["Access_permission_rule"]]
    """
    Access permission rules of the AAS describing the rights assigned to (already
    authenticated) subjects to access elements of the AAS.
    """

    selectable_subject_attributes: Optional[Reference]
    """
    Reference to a submodel defining the authenticated subjects that are configured for
    the AAS. They are selectable by the access permission rules to assign permissions
    to the subjects.

    Default: reference to the submodel referenced via defaultSubjectAttributes.
    """

    default_subject_attributes: Reference
    """
    Reference to a submodel defining the default subjects’ attributes for the AAS that
    can be used to describe access permission rules.

    The submodel is of kind=Template.
    """

    selectable_permissions: Optional[Reference]
    """
    Reference to a submodel defining which permissions can be assigned to the subjects.

    Default: reference to the submodel referenced via defaultPermissions
    """

    default_permissions: Reference
    """
    Reference to a submodel defining the default permissions for the AAS.
    """

    selectable_environment_attributes: Optional[Reference]
    """
    Reference to a submodel defining which environment attributes can be accessed
    *via* the permission rules defined for the AAS, i.e. attributes that are
    not describing the asset itself.

    Default: reference to the submodel referenced via defaultEnvironmentAttributes
    """

    default_environment_attributes: Optional[Reference]
    """
    Reference to a submodel defining default environment attributes, *i.e.* attributes
    that are not describing the asset itself.

    The submodel is of kind=Template.

    At the same type the values of these environment attributes need to be accessible
    when evaluating the access permission rules. This is realized as a policy
    information point.
    """

    def __init__(
        self,
        default_subject_attributes: Reference,
        default_permissions: Reference,
        access_permission_rules: Optional[List["Access_permission_rule"]] = None,
        selectable_subject_attributes: Optional[Reference] = None,
        selectable_permissions: Optional[Reference] = None,
        selectable_environment_attributes: Optional[Reference] = None,
        default_environment_attributes: Optional[Reference] = None,
    ) -> None:
        self.default_subject_attributes = default_subject_attributes
        self.selectable_permissions = selectable_permissions
        self.default_permissions = default_permissions
        self.access_permission_rules = access_permission_rules
        self.selectable_subject_attributes = selectable_subject_attributes
        self.selectable_environment_attributes = selectable_environment_attributes
        self.default_environment_attributes = default_environment_attributes


@reference_in_the_book(section=(5, 3, 4), index=1)
class Policy_administration_point(DBC):
    """
    Definition of a security policy administration point (PAP).
    """

    external_access_control: bool
    """
    If :attr:`~external_access_control` True then an Endpoint to an external access
    control defining a policy administration point to be used by the AAS needs
    to be configured.
    """

    local_access_control: Optional["Access_control"]
    """
    The policy administration point of access control as realized by the AAS itself.

    Constraint AASs-009: Either there is an external policy administration point
    endpoint defined (PolicyAdministrationPoint/externalPolicyDecisionPoints=true) or
    the AAS has its own access control.
    """

    def __init__(
        self,
        external_access_control: bool,
        local_access_control: Optional["Access_control"] = None,
    ) -> None:
        self.external_access_control = external_access_control
        self.local_access_control = local_access_control


@reference_in_the_book(section=(5, 3, 4), index=2)
class Policy_information_points(DBC):
    """
    Defines the security policy information points (PIP).
    Serves as the retrieval source of attributes, or the data required for policy
    evaluation to provide the information needed by the policy decision point to make
    the decisions.
    """

    external_information_points: bool
    """
    If externalInformationPoints True then at least one Endpoint to external available
    information needs to be configured for the AAS.
    """

    internal_information_points: Optional[List[Reference]]
    """
    Reference to a  Submodel defining information used by security access permission
    rules.
    """

    def __init__(
        self,
        external_information_points: bool,
        internal_information_points: Optional[List[Reference]] = None,
    ) -> None:
        self.external_information_points = external_information_points
        self.internal_information_points = internal_information_points


@reference_in_the_book(section=(5, 3, 4), index=3)
class Policy_enforcement_points(DBC):
    """
    Defines the security policy enforcement points (PEP).
    """

    external_policy_enforcement_point: bool
    """
    If externalPolicyEnforcementPoint True then an Endpoint to external available
    enforcement point taking needs to be configured for the AAS.
    """

    def __init__(self, external_policy_enforcement_point: bool) -> None:
        self.external_policy_enforcement_point = external_policy_enforcement_point


@reference_in_the_book(section=(5, 3, 4), index=4)
class Policy_decision_point(DBC):
    """
    Defines the security policy decision points (PDP).
    """

    external_policy_decision_points: bool
    """
    If externalPolicyDecisionPoints True then Endpoints to external available decision
    points taking into consideration for access control for the AAS need to be
    configured.
    """

    def __init__(self, external_policy_decision_points: bool) -> None:
        self.external_policy_decision_points = external_policy_decision_points


@reference_in_the_book(section=(5, 3, 4))
class Access_control_policy_points(DBC):
    """
    Container for access control policy points.
    """

    policy_administration_point: "Policy_administration_point"
    """
    The access control administration policy point of the AAS.
    """

    policy_decision_point: "Policy_decision_point"
    """
    The access control policy decision point of the AAS.
    """

    policy_enforcement_points: "Policy_enforcement_points"
    """
    The access control policy enforcement point of the AAS.
    """

    policy_information_points: Optional["Policy_information_points"]
    """
    The access control policy information points of the AAS.
    """

    def __init__(
        self,
        policy_administration_point: "Policy_administration_point",
        policy_decision_point: "Policy_decision_point",
        policy_enforcement_points: "Policy_enforcement_points",
        policy_information_points: Optional["Policy_information_points"] = None,
    ) -> None:
        self.policy_administration_point = policy_administration_point
        self.policy_decision_point = policy_decision_point
        self.policy_enforcement_points = policy_enforcement_points
        self.policy_information_points = policy_information_points


@reference_in_the_book(section=(5, 3, 2))
class Security(DBC):
    """
    Container for security relevant information of the AAS.
    """

    access_control_policy_points: "Access_control_policy_points"
    """
    Access control policy points of the AAS.
    """

    certificates: Optional[List["Certificate"]]
    """
    Authenticating Certificates of the AAS and its submodels etc.
    """

    required_certificate_extensions: Optional[List["Reference"]]
    """
    Certificate extensions as required by the AAS
    """

    def __init__(
        self,
        access_control_policy_points: "Access_control_policy_points",
        certificates: Optional[List["Certificate"]] = None,
        required_certificate_extensions: Optional[List["Reference"]] = None,
    ) -> None:
        self.access_control_policy_points = access_control_policy_points
        self.certificates = certificates
        self.required_certificate_extensions = required_certificate_extensions


@reference_in_the_book(section=(5, 3, 5), index=6)
class Permission_kind(Enum):
    """
    Enumeration of the kind of permissions that is given to the assignment of
    a permission to a subject.
    """

    Allow = "Allow"
    """
    Allow the permission given to the subject.
    """

    Deny = "Deny"
    """
    Explicitly deny the permission given to the subject.
    """

    Not_applicable = "NotApplicable"
    """
    The permission is not applicable to the subject.
    """

    Undefined = "Undefined"
    """
    It is undefined whether the permission is allowed, not applicable or denied to
    the subject.
    """


# TODO: make this environment implementation-specific in the final implementation.
#  + Sketch what methods it should implement.
#  + Sketch what invariants it should implement.
class Asset_administration_shell_environment:
    """Model the environment as the entry point for referencing and serialization."""

    asset_administration_shells: Optional[List[Asset_administration_shell]]

    assets: Optional[List[Asset]]

    submodels: Optional[List[Submodel]]

    concept_descriptions: Optional[List[Concept_description]]

    def __init__(
        self,
        asset_administration_shells: Optional[List[Asset_administration_shell]] = None,
        assets: Optional[List[Asset]] = None,
        submodels: Optional[List[Submodel]] = None,
        concept_descriptions: Optional[List[Concept_description]] = None,
    ) -> None:
        self.asset_administration_shells = asset_administration_shells
        self.assets = assets
        self.submodels = submodels
        self.concept_descriptions = concept_descriptions
