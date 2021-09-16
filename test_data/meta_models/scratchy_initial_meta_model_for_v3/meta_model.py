"""Provide meta model for Asset Administration Shell (v3)."""
from enum import Enum
from typing import Final, List, Optional

from icontract import require, ensure, DBC

from aas_core3_meta.marker import (
    abstract,
    implementation_specific,
    comment
)
from aas_core3_meta.pattern import is_IRI, is_IRDI, is_id_short


# TODO (mristin, 2021-05-28): rename all enums, classes,
#  properties according to snake case: abbreviations UPPERCASE, rest snake case
# TODO (mristin):
# * Work out the table on p.34 🠒 4.4.4 Tabelle 2: ConceptDescription, View, Qualifier
# * Add descriptions to the classes
# * Write a linter for the meta-model:
#   * all properties require a docstring
#   * all classes require a docstring
#   * CamelCase is not good for classes — require snake_case
#   * camelCase is not good for properties, functions and arguments — require snake_case


@abstract
class Has_extension(DBC):
    # NOTE (mristin, 2021-05-28):
    # We do not implement extensions at the moment.
    # This needs to be further discussed.
    pass


class Lang_string(DBC):
    """Give a text in a specific language."""

    language: Final[str]
    """Language of the ``text``"""

    text: str
    """Content of the string"""

    # TODO (mristin, 2021-05-28): what is the format of the ``language``?
    def __init__(self, language: str, text: str) -> None:
        self.language = language
        self.text = text


@implementation_specific
class Lang_string_set(DBC):
    """
    A set of strings, each annotated by the language of the string.

    The meaning of the string in each language shall be the same.
    """

    lang_strings: List[Lang_string]
    """Different translations of the string."""

    # TODO (mristin, 2021-05-28): @Andreas: should the language be unique?
    #  Or can we have duplicate entries for, say, "EN"?
    # fmt: off
    @require(lambda lang_strings: len(lang_strings) > 0)
    @require(
        lambda lang_strings:
        (
                languages := [lang_string.language for lang_string in lang_strings],
                len(languages) == len(set(languages))
        )[1],
        "No duplicate languages allowed"
    )
    # fmt: on
    def __init__(self, lang_strings: List[Lang_string]) -> None:
        self.lang_strings = lang_strings

        # The strings need to be accessed by a dictionary;
        # how this dictionary is initialized is left to the individual implementation.

    @ensure(
        lambda self, language, result:
        not result
        or any(language == lang_string.language for lang_string in self.lang_strings)
    )
    def has_language(self, language: str) -> bool:
        """
        Check whether the string is available in the given language.

        :param language: language of interest
        :return: True if the string is available in the language
        """
        # The strings need to be accessed by a dictionary;
        # how this dictionary is accessed is left to the individual implementation.

    @ensure(
        lambda self, language, result:
        not (self.has_language(language) ^ (result is not None))
    )
    def by_language(self, language: str) -> Optional[str]:
        """
        Retrieve the string in the given language.

        :param language: language of interest
        :return: the string in the language, if available
        """
        # The strings need to be accessed by a dictionary;
        # how this dictionary is accessed is left to the individual implementation.


@abstract
class Referable(Has_extension):
    """
    An element that is referable by its :py:attr:`~id_short`.

    This identifier is not globally unique.
    This identifier is unique within the name space of the element.
    """

    id_short: str
    """
    In case of identifiables this attribute is a short name of the element. 
    In case of referable this id is an identifying string of 
    the element within its name space.
    """

    display_name: Optional[Lang_string_set]
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

    category: Optional[str]
    """
    The category is a value that gives further meta information 
    w.r.t. to the class of the element. 
    It affects the expected existence of attributes and the applicability of 
    constraints.
    """

    description: Optional[Lang_string_set]
    """
    Description or comments on the element.

    The description can be provided in several languages. If no description is defined,
    then the definition of the concept description that defines the semantics 
    of the element is used. Additional information can be provided,
    *e.g.*, if the element is qualified and which qualifier types can be expected 
    in which context or which additional data specification templates are provided.
    """

    @require(lambda id_short: is_id_short(id_short), "Constraint AASd-002")
    def __init__(
            self,
            id_short: str,
            display_name: Optional[Lang_string_set] = None,
            category: Optional[str] = None,
            description: Optional[Lang_string_set] = None
    ) -> None:
        self.id_short = id_short
        self.display_name = display_name
        self.category = category
        self.description = description

class Identifier_type(Enum):
    """Enumeration of different types of Identifiersfor global identification"""

    IRDI = "IRDI"
    """
    IRDI according to ISO29002-5 as an Identifier scheme for properties 
    and classifications.
    """

    IRI = "IRI"
    """IRI according to Rfc 3987. Every URIis an IRI"""

    CUSTOM = "Custom"
    """Custom identifiers like GUIDs (globally unique identifiers)"""


class Identifier(DBC):
    # TODO (mristin, 2021-05-28) @Andreas: Type Id is not defined in the book.
    #  Shouldn't ``id`` be a string with constraints? Or is it meant that individual
    #  implementations pick their own objects?
    # fmt: off
    @require(
        lambda id, id_type:
        not (id_type == Identifier_type.IRDI) or is_IRDI(id)
    )
    @require(
        lambda id, id_type:
        not (id_type == Identifier_type.IRI) or is_IRI(id)
    )
    # fmt: on
    def __init__(
            self,
            id: str,
            id_type: Identifier_type,

    ) -> None:
        self.id = id
        self.id_type = id_type


class Administrative_information(DBC):
    @require(
        lambda version, revision:
        not (revision is not None) or version is not None
    )
    def __init__(
            self,
            version: Optional[str] = None,
            revision: Optional[str] = None
    ) -> None:
        self.version = version
        self.revision = revision


@abstract
class Identifiable(Referable):
    @require(lambda id_short: is_id_short(id_short))
    def __init__(
            self,
            identification: Identifier,
            id_short: str,
            display_name: Optional[Lang_string_set] = None,
            category: Optional[str] = None,
            description: Optional[Lang_string_set] = None,
            administration: Optional[Administrative_information] = None
    ) -> None:
        self.identification = identification
        self.administration = administration

        Referable.__init__(
            id_short=id_short,
            display_name=display_name,
            category=category,
            description=description)


class Modeling_kind(Enum):
    # TODO (mristin, 2021-05-28): how to document the enums?
    TEMPLATE = "Template"
    INSTANCE = "Instance"


@abstract
class Has_kind(DBC):
    # TODO (mristin, 2021-05-28): @Andreas, how can ``kind`` be optional
    #  and have a default value?
    def __init__(self, kind: Modeling_kind) -> None:
        self.kind = kind


class Local_key_type(Enum):
    ID_SHORT = "IdShort"
    FRAGMENT_ID = "FragmentId"


class Key_type(Enum):
    ID_SHORT = "IdShort"
    FRAGMENT_ID = "FragmentId"
    CUSTOM = "Custom"
    IRDI = "IRDI"
    IRI = "IRI"


# TODO (mristin, 2021-05-28): add assertion that KeyType is union of
#  LocalKeyType and IdentifierType

class Identifiable_elements(Enum):
    ASSET = "Asset"
    ASSET_ADMINISTRATION_SHELL = "AssetAdministrationShell"
    CONCEPT_DESCRIPTION = "ConceptDescription"
    SUBMODEL = "Submodel"


class Referable_elements(Enum):
    ACCESS_PERMISSION_RULE = "AccessPermissionRule"
    ANNOTATED_RELATIONSHIP_ELEMENT = "AnnotatedRelationshipElement"
    ASSET = "Asset"
    ASSET_ADMINISTRATION_SHELL = "AssetAdministrationShell"
    BASIC_EVENT = "BasicEvent"
    BLOB = "Blob"
    CAPABILITY = "Capability"
    CONCEPT_DESCRIPTION = "ConceptDescription"
    CONCEPT_DICTIONARY = "ConceptDictionary"
    DATA_ELEMENT = "DataElement"
    ENTITY = "Entity"
    EVENT = "Event"
    FILE = "File"
    MULTI_LANGUAGE_PROPERTY = "MultiLanguageProperty"
    OPERATION = "Operation"
    PROPERTY = "Property"
    RANGE = "Range"
    REFERENCE_ELEMENT = "ReferenceElement"
    RELATIONSHIP_ELEMENT = "RelationshipElement"
    SUBMODEL = "Submodel"
    SUBMODEL_ELEMENT = "SubmodelElement"
    SUBMODEL_ELEMENT_COLLECTION = "SubmodelElementCollection"
    VIEW = "View"


# TODO (mristin, 2021-05-28): add assertion that ReferableElements also contains
#  all IdentifiableElements

class Key_elements(Enum):
    GLOBAL_REFERENCE = "GlobalReference"
    FRAGMENT_REFERENCE = "FragmentReference"
    ACCESS_PERMISSION_RULE = "AccessPermissionRule"
    ANNOTATED_RELATIONSHIP_ELEMENT = "AnnotatedRelationshipElement"
    ASSET = "Asset"
    ASSET_ADMINISTRATION_SHELL = "AssetAdministrationShell"
    BASIC_EVENT = "BasicEvent"
    BLOB = "Blob"
    CAPABILITY = "Capability"
    CONCEPT_DESCRIPTION = "ConceptDescription"
    CONCEPT_DICTIONARY = "ConceptDictionary"
    DATA_ELEMENT = "DataElement"
    ENTITY = "Entity"
    EVENT = "Event"
    FILE = "File"
    MULTI_LANGUAGE_PROPERTY = "MultiLanguageProperty"
    OPERATION = "Operation"
    PROPERTY = "Property"
    RANGE = "Range"
    REFERENCE_ELEMENT = "ReferenceElement"
    RELATIONSHIP_ELEMENT = "RelationshipElement"
    SUBMODEL = "Submodel"
    SUBMODEL_ELEMENT = "SubmodelElement"
    SUBMODEL_ELEMENT_COLLECTION = "SubmodelElementCollection"
    VIEW = "View"


# TODO (mristin, 2021-05-28): add assertion that KeyElements also contains
#  all ReferableElements


class Key(DBC):
    # fmt: off
    @require(
        lambda value, id_type:
        not (id_type == Key_type.IRI) or is_IRI(value)
    )
    @require(
        lambda value, id_type:
        not (id_type == Key_type.IRDI) or is_IRDI(value)
    )
    @require(
        lambda type, id_type:
        not (type == Key_elements.GLOBAL_REFERENCE)
        or (id_type != Key_type.ID_SHORT and id_type != Key_type.FRAGMENT_ID),
        "Constraint AASd-080"
    )
    @require(
        lambda type, id_type:
        not (type == Key_elements.ASSET_ADMINISTRATION_SHELL)
        or (id_type != Key_type.ID_SHORT and id_type != Key_type.FRAGMENT_ID),
        "Constraint AASd-081"
    )
    # fmt: on
    def __init__(self, type: Key_elements, value: str, id_type: Key_type) -> None:
        self.type = type
        self.value = value
        self.id_type = id_type


class Reference(DBC):
    @require(lambda keys: len(keys) >= 1)
    def __init__(self, keys: List[Key]) -> None:
        self.keys = keys

    @require(lambda keys: len(keys) >= 1)
    def set_keys(self, keys: List[Key]) -> None:
        self.keys = keys


@abstract
class Has_semantics(DBC):
    def __init__(self, semantic_id: Optional[Reference] = None) -> None:
        self.semantic_id = semantic_id


# TODO (mristin, 2021-05-28): Uncomment and implement once the codegen is running. 
# class Constraint(DBC):
#     pass
# 
# 
# QualifierType = str
# 
# 
# class DataTypeDef(Enum):
#     ANY_URI = "anyUri"
#     # TODO: translate others
#     # "base64Binary"
#     # "boolean"
#     # "date"
#     # "dateTime"
#     # "dateTimeStamp"
#     # "decimal"
#     # "integer"
#     # "long"
#     # "int"
#     # "short"
#     # "byte"
#     # "nonNegativeInteger"
#     # "positiveInteger"
#     # "unsignedLong"
#     # "unsignedInt"
#     # "unsignedShort"
#     # "unsignedByte"
#     # "nonPositiveInteger"
#     # "negativeInteger"
#     # "double"
#     # "duration"
#     # "dayTimeDuration"
#     # "yearMonthDuration"
#     # "float"
#     # "gDay"
#     # "gMonth"
#     # "gMonthDay"
#     # "gYear"
#     # "gYearMonth"
#     # "hexBinary"
#     # "NOTATION"
#     # "QName"
#     # "string"
#     # "normalizedString"
#     # "token"
#     # "language"
#     # "Name"
#     # "NCName"
#     # "ENTITY"
#     # "ID"
#     # "IDREF"
#     # "NMTOKEN"
#     # "time"
# 
# 
# class ValueDataType(DBC):
#     raise NeedToBeImplemented()
# 
# 
# def is_of_type(value: ValueDataType, value_type: DataTypeDef) -> bool:
#     raise NeedToBeImplemented()
# 
# 
# class Qualifier(Constraint, HasSemantics):
#     # fmt: off
# 
#     @require(
#         lambda value_type, value:
#         not (value is not None) or is_of_type(value, value_type),
#         "Constraint AASd-020"
#     )
#     # fmt: on
#     def __init__(
#             self,
#             qualifier_type: QualifierType,
#             value_type: DataTypeDef,
#             value: Optional[ValueDataType] = None,
#             value_id: Optional[Reference] = None,
#             semantic_id: Optional[Reference] = None) -> None:
#         self.qualifier_type = qualifier_type
#         self.value_type = value_type
#         self.value = value
#         self.value_id = value_id
# 
#         HasSemantics.__init__(self, semantic_id=semantic_id)
# 
# 
# class Formula(Constraint):
#     def __init__(self, depends_on: List[Reference]) -> None:
#         self.depends_on = depends_on
# 
# 
# # TODO (mristin, 2021-05-28): @Andreas: This is very confusing.
# #   Should not the property be called ``constraints`` instead of ``qualifiers``?
# #   Should not the class be called ``Constrainable``?
# class Qualifiable(DBC):
#     # fmt: off
#     @require(
#         lambda qualifiers:
#         (
#                 qualifier_types := [
#                     constraint.qualifier_type
#                     for constraint in qualifiers
#                     if isinstance(constraint, Qualifier)
#                 ],
#                 len(set(qualifier_types)) == len(qualifier_types)
#         )[1],
#         "Constraint AASd-021"
#     )
#     # fmt: on
#     def __init__(self, qualifiers: List[Constraint]) -> None:
#         self.qualifiers = qualifiers


@abstract
class Has_data_specification(DBC):
    def __init__(self, data_specifications: Optional[List[Reference]] = None) -> None:
        self.data_specifications = (
            data_specifications if data_specifications is not None else []
        )


class Asset_administration_shell(Identifiable, Has_data_specification):
    """Structure a digital representation of an :class:`.Asset`."""

    # TODO (mristin, 2021-05-28): fields are missing, such as ``security`` and many others!

    derived_from: Final[Optional['Asset_administration_shell']]
    """The reference to the AAS this AAS was derived from."""

    def __init__(
            self,
            identification: Identifier,
            id_short: str,
            display_name: Optional[Lang_string_set] = None,
            category: Optional[str] = None,
            description: Optional[Lang_string_set] = None,
            administration: Optional[Administrative_information] = None,
            data_specifications: Optional[List[Reference]] = None,
            derived_from: Optional['Asset_administration_shell'] = None
    ) -> None:
        Identifiable.__init__(
            self,
            identification=identification,
            id_short=id_short,
            display_name=display_name,
            category=category,
            description=description,
            administration=administration
        )

        Has_data_specification.__init__(self, data_specifications=data_specifications)

        self.derived_from = derived_from

# TODO (mristin, 2021-05-28): This was the initial version
#  before we really tackled the mix-ins properly.
#
#
# class Asset(DBC, Identifiable, HasDataSpecification):
#     @require(lambda id_short: is_id_short(id_short))
#     @require(lambda id: id.id_type == ID_Type.IRI)
#     def __init__(self, id: Identifier, id_short: str) -> None:
#         Identifiable.__init__(self, id=id, id_short=id_short)
#
#
# class Submodel(
#     DBC, Identifiable, HasKind, HasSemantics, Quantifiable, HasDataSpecification):
#     pass
#
#
# class SubmodelTemplate(Submodel):
#     # fmt: off
#     @require(lambda id_short: is_id_short(id_short))
#     @require(lambda id: id.id_type in (ID_Type.IRI, ID_Type.IRDI))
#     @require(
#         lambda semantic_id:
#         semantic_id is None
#         or semantic_id.id_type in (ID_Type.IRI, ID_Type.IRDI)
#     )
#     # fmt: on
#     def __init__(
#             self,
#             id: Identifier,
#             id_short: str,
#             semantic_id: Optional[Identifier]
#     ) -> None:
#         Identifiable.__init__(self, id=id, id_short=id_short)
#         self.semantic_id = semantic_id
#
#
# class SubmodelInstance(Submodel):
#     # fmt: off
#     @require(lambda id_short: is_id_short(id_short))
#     @require(lambda id: id.id_type in (ID_Type.IRI, ID_Type.CUSTOM))
#     @require(
#         lambda semantic_id:
#         semantic_id is None
#         or semantic_id.id_type in (ID_Type.IRI, ID_Type.IRDI)
#     )
#     # fmt: on
#     def __init__(
#             self,
#             id: Identifier,
#             id_short: str,
#             semantic_id: Optional[Identifier]
#     ) -> None:
#         Identifiable.__init__(self, id=id, id_short=id_short)
#         self.semantic_id = semantic_id
#
#
# class SubmodelElement(Referable, HasSemantics):
#     @require(lambda id_short: is_id_short(id_short))
#     def __init__(
#             self,
#             id_short: str,
#             semantic_id: Optional[Identifier]
#     ) -> None:
#         Referable.__init__(self, id_short=id_short)
#         self.semantic_id = semantic_id
#
#
# class ConceptDescription:
#     raise NotImplementedError()
#
#
# # TODO (mristin, 2021-05-28): @Andreas: ConceptDescription lacks ``definition`` property.
# #   How are we supposed to retrieve it here?
# #   See also `get_description`.
# def get_display_name(
#         language: str,
#         referable: Referable,
#         concept_description: Optional[ConceptDescription]) -> str:
#     # TODO (mristin, 2021-05-28): Implement this once we defined ConceptDescirption.
#     #  See the logic on p.51 Details.
#     text: Optional[str] = referable.display_name.by_language.get(
#         language, None)
#
#     if text is not None:
#         return text
#
#     raise NotImplementedError()
#
#
# def get_description(
#         language: str,
#         referable: Referable,
#         concept_description: Optional[ConceptDescription]) -> str:
#     # TODO (mristin, 2021-05-28): Implement this once we defined ConceptDescirption.
#     #  See the logic on p.51 Details.
#     raise NotImplementedError()

# TODO: describe all entities
# TODO: how can we deal with IRI/IRDI/CustomIdentifier such that they are just strings?
# TODO: how should we deal with ``id``? ``id`` is a built-in — Nico will have a look in Aachen repo.
# TODO: write readme

# TODO (mristin, 2021-05-28): We need a ``verify`` function that checks
#  for type=FragmentId.
#  See https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part1_V3.pdf?__blob=publicationFile&v=5
#  page 82, ``type`` row

# TODO (mristin, 2021-05-28): We need to list the constraints which we could not implement.
