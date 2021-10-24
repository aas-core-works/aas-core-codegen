"""Provide meta model for Asset Administration Shell (v3)."""
from enum import Enum
from typing import Final, List, Optional

from icontract import invariant, DBC

from aas_core3_meta.marker import (
    abstract,
    implementation_specific,
    comment
)
from aas_core3_meta.pattern import is_IRI, is_IRDI, is_ID_short


@abstract
class Has_extension(DBC):
    # NOTE (mristin, 2021-05-28):
    # We do not implement extensions at the moment.
    # This needs to be further discussed.
    pass


class Lang_string(DBC):
    """Give a text in a specific language."""

    language: Final[str]
    """Language of the :py:attr:`text`"""

    text: str
    """Content of the string"""

    # TODO (mristin, 2021-05-28): what is the format of the ``language``?
    def __init__(self, language: str, text: str) -> None:
        self.language = language
        self.text = text


@invariant(lambda self: len(self.lang_strings) > 0)
@implementation_specific
class Lang_string_set(DBC):
    """
    A set of strings, each annotated by the language of the string.

    The meaning of the string in each language shall be the same.
    """

    lang_strings: List[Lang_string]
    """Different translations of the string."""

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
@invariant(lambda self: is_ID_short(self.id_short), "Constraint AASd-002")
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


@invariant(
    lambda self:
    not (self.id_type == Identifier_type.IRDI) or is_IRDI(self.id)
)
@invariant(
    lambda self:
    not (self.id_type == Identifier_type.IRI) or is_IRI(self.id)
)
# fmt: on
class Identifier(DBC):
    id: str
    id_type: Identifier_type

    def __init__(
            self,
            id: str,
            id_type: Identifier_type = Identifier_type.IRDI
    ) -> None:
        self.id = id
        self.id_type = id_type


@invariant(
    lambda self:
    not (self.revision is not None) or self.version is not None
)
class Administrative_information(DBC):
    version: Optional[str]
    revision: Optional[str]

    def __init__(
            self,
            version: Optional[str] = None,
            revision: Optional[str] = None
    ) -> None:
        self.version = version
        self.revision = revision


@abstract
class Identifiable(Referable):
    identification: Identifier
    administration: Optional[Administrative_information]

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
            self,
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
    kind: Modeling_kind

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

# fmt: off
@invariant(
    condition=lambda self:
    not (self.id_type == Key_type.IRI) or is_IRI(self.value),
    description="If ID type is IRI, it must be an IRI"
)
@invariant(
    lambda self:
    not (self.id_type == Key_type.IRDI) or is_IRDI(self.value)
)
@invariant(
    lambda self:
    not (self.type == Key_elements.GLOBAL_REFERENCE)
    or (self.id_type != Key_type.ID_SHORT and self.id_type != Key_type.FRAGMENT_ID),
    "Constraint AASd-080"
)
@invariant(
    lambda self:
    not (self.type == Key_elements.ASSET_ADMINISTRATION_SHELL)
    or (self.id_type != Key_type.ID_SHORT and self.id_type != Key_type.FRAGMENT_ID),
    "Constraint AASd-081"
)
# fmt: on
class Key(DBC):
    type: Key_elements
    value: str
    id_type: Key_type

    def __init__(self, type: Key_elements, value: str, id_type: Key_type) -> None:
        self.type = type
        self.value = value
        self.id_type = id_type


@invariant(lambda self: len(self.keys) >= 1)
class Reference(DBC):
    keys: List[Key]

    def __init__(self, keys: List[Key]) -> None:
        self.keys = keys


@abstract
class Has_semantics(DBC):
    semantic_id: Optional[Reference]

    def __init__(self, semantic_id: Optional[Reference] = None) -> None:
        self.semantic_id = semantic_id


@abstract
class Has_data_specification(DBC):
    data_specifications: List[Reference]

    def __init__(self, data_specifications: Optional[List[Reference]] = None) -> None:
        self.data_specifications = (
            data_specifications if data_specifications is not None else []
        )


class Asset_administration_shell(Identifiable, Has_data_specification):
    """Structure a digital representation of an Asset."""

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
