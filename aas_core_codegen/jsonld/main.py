"""Generate JSON-LD context corresponding to the meta-model."""
import json
from typing import (
    Any,
    Dict,
    List,
    Set,
    TextIO,
    Optional,
    TypedDict,
    Tuple,
    Union,
    cast,
)
from typing_extensions import assert_never

from aas_core_codegen import (
    naming,
    intermediate,
    run,
)
from aas_core_codegen.common import Error, Stripped, Identifier
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
)


JsonLdType = Dict[str, Any]


def _property_uri(prop: intermediate.Property) -> str:
    property_vocab = rdf_shacl_naming.class_name(Identifier(prop.specified_for.name))
    prop_uri_fragment = rdf_shacl_naming.property_name(Identifier(prop.name))

    return f"aas:{property_vocab}/{prop_uri_fragment}"


def _get_our_type_from_type_annotation(
    type_annotation: Union[
        intermediate.PrimitiveTypeAnnotation,
        intermediate.ListTypeAnnotation,
        intermediate.OptionalTypeAnnotation,
        intermediate.PrimitiveTypeAnnotation,
        intermediate.TypeAnnotationUnion,
    ]
) -> Union[intermediate.OurType, intermediate.PrimitiveTypeAnnotation]:
    """Get the OurType or the PrimitiveTypeAnnotation from the type annotation
    :param type_annotation: the type annotation
    :returns: the our type or the primitive type annotation associated
    """
    if isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        return _get_our_type_from_type_annotation(type_annotation.value)
    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        return _get_our_type_from_type_annotation(type_annotation.items)
    elif isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return type_annotation
    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        return type_annotation.our_type
    else:
        return assert_never(type_annotation)


def _generate_properties(
    domain_aas_class: Optional[intermediate.ClassUnion],
    property_to_generate: intermediate.Property,
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    class_names_set_param: Optional[Set[str]] = None,
    exported_properties_list_param: Optional[List[str]] = None,
) -> JsonLdType:
    """Generate the Dict (JsonLdType) which contains all properties defintion for a
    dedicated class

    :param domain_aas_class: The AAS class which is the domain of the property (can be None if generic)
    :param property_to_generate: The property which will be exported
    :param symbol_table: The Symbol Table which has been extracted from the command context
    :param our_type_to_rdfs_range: The mapping between the AAS types and the rdfs range fragment
    :param class_names_param: The set of all class names which have been generated so far
    :param exported_properties_param: The list of properties exported so far (to avoid multiple exports)
    :returns: A dict (JsonLdType) which is the JSON LD of the dedicated property

    """
    class_names_set: Set[str] = (
        class_names_set_param if class_names_set_param is not None else set()
    )
    exported_properties_list: List[str] = (
        exported_properties_list_param
        if exported_properties_list_param is not None
        else []
    )
    property_type = property_to_generate.type_annotation
    property_vocab = rdf_shacl_naming.class_name(
        Identifier(property_to_generate.specified_for.name)
    )
    prop_uri_fragment = rdf_shacl_naming.property_name(
        Identifier(property_to_generate.name)
    )

    property_uri = f"aas:{property_vocab}/{prop_uri_fragment}"
    rdfs_range = rdf_shacl_common.rdfs_range_for_type_annotation(
        type_annotation=property_to_generate.type_annotation,
        our_type_to_rdfs_range=our_type_to_rdfs_range,
    )
    property_json_ld_context: JsonLdType = {"@id": property_uri}
    if isinstance(property_type, intermediate.ListTypeAnnotation):
        property_json_ld_context["@container"] = "@set"

    property_type_processed = _get_our_type_from_type_annotation(property_type)

    if isinstance(property_type_processed, intermediate.Enumeration):
        enum_fragment = rdf_shacl_naming.class_name(
            Identifier(property_type_processed.name)
        )
        property_json_ld_context["@context"] = cast(
            JsonLdType, {"@vocab": f"aas:{enum_fragment}/"}
        )
        property_json_ld_context["@type"] = "@vocab"

        for item in property_type_processed.literals:
            rdf_item_name = rdf_shacl_naming.enumeration_literal(item.name)
            json_item_name = item.value
            # Adds the property definition if :
            #  - the json item name does not start with "xs:" (already defined in XML Schema Datatypes definition).
            #  - the json item name references an alredy defined class name.
            #  - the json item name is different from the rdf item name (we have to define the correspondance here).
            # otherwise, the "@vocab" is enough
            if not json_item_name.startswith("xs:") and (
                (json_item_name in class_names_set) or json_item_name != rdf_item_name
            ):
                property_json_ld_context["@context"][json_item_name] = {
                    "@id": f"aas:{enum_fragment}/{rdf_item_name}"
                }

    elif rdfs_range.startswith("aas:"):
        property_json_ld_context["@type"] = "@id"
        range_our_type = _get_our_type_from_type_annotation(
            property_to_generate.type_annotation
        )

        if (
            isinstance(
                range_our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            )
            and domain_aas_class is not range_our_type
        ):
            property_json_ld_context["@context"] = {}
            for range_property in range_our_type.properties:
                range_property_id = naming.json_property(range_property.name)
                if range_property_id not in exported_properties_list:
                    property_json_ld_context["@context"][
                        range_property_id
                    ] = _generate_properties(
                        domain_aas_class=range_our_type,
                        property_to_generate=range_property,
                        symbol_table=symbol_table,
                        our_type_to_rdfs_range=our_type_to_rdfs_range,
                        class_names_set_param=class_names_set,
                        exported_properties_list_param=exported_properties_list,
                    )
    elif rdfs_range.startswith("xs:") and rdfs_range not in (
        "xs:string",
        "xs:boolean",
    ):
        property_json_ld_context["@type"] = rdfs_range
    elif rdfs_range == "rdf:langString":
        property_json_ld_context["@container"] = "@set"
        property_json_ld_context["@context"] = {
            "language": "@language",
            "text": "@value",
        }
    return property_json_ld_context


def _generate_class_context(
    aas_class: intermediate.ClassUnion,
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    class_names_set_param: Optional[Set[str]] = None,
    exported_properties_list_param: Optional[List[str]] = None,
) -> JsonLdType:
    """Generate the Dict (JsonLdType) for a dedicated class

    :param aas_class: The dedicated AAS class
    :param symbol_table: The Symbol Table which has been extracted from the command context
    :param our_type_to_rdfs_range: The mapping between the AAS types and the rdfs range fragment
    :param class_names_set_param: The set of all class names which have been generated so far
    :param exported_properties_list_param: The list of properties exported so far (to avoid multiple exports)
    :returns: A dict (JsonLdType) which is the JSON LD of the dedicated class

    """
    class_names_set: Set[str] = (
        class_names_set_param if class_names_set_param is not None else set()
    )
    exported_properties_list: List[str] = (
        exported_properties_list_param
        if exported_properties_list_param is not None
        else []
    )
    class_context_defintion: JsonLdType = {}
    class_identifier = naming.json_model_type(aas_class.name)
    uri_fragment = rdf_shacl_naming.class_name((Identifier(class_identifier)))
    class_context_defintion[class_identifier] = {
        "@id": uri_fragment,
        "@context": {
            "@vocab": f"{symbol_table.meta_model.xml_namespace}/{uri_fragment}/"
        },
    }
    for prop in aas_class.properties:
        property_identifier = naming.json_property(prop.name)
        if property_identifier in exported_properties_list:
            continue
        class_context_defintion[class_identifier]["@context"][
            property_identifier
        ] = _generate_properties(
            domain_aas_class=aas_class,
            property_to_generate=prop,
            symbol_table=symbol_table,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            class_names_set_param=class_names_set,
            exported_properties_list_param=exported_properties_list,
        )

    return class_context_defintion


ProperyUrisType = TypedDict(
    "ProperyUrisType",
    {
        "uri": str,
        "object": intermediate.Property,
    },
)


def _generate(
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the JSON-LD context based on the symbol_table.

    :param symbol_table: The Symbol Table which has been extracted from the command context
    :param our_type_to_rdfs_range: The mapping between the AAS types and the rdfs range fragment
    :returns: The JSON-LD context generated in JSON store in a string

    """
    xml_namespace = symbol_table.meta_model.xml_namespace
    json_ld_context: JsonLdType = {
        "aas": f"{xml_namespace}/",
        "xs": "http://www.w3.org/2001/XMLSchema#",
        "@vocab": f"{xml_namespace}/",
        "modelType": "@type",
    }
    errors: List[Error] = []

    # NOTE (murloc6, 2023-10-06)
    # List of all class names
    class_names_set: Set[str] = set()
    for cls in symbol_table.classes:
        if not isinstance(
            cls, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            continue
        class_names_set.add(naming.json_model_type(cls.name))

    # NOTE (murloc6, 2023-10-06)
    # Generate context for all properties
    double_uris_set = set()
    property_uris: Dict[str, ProperyUrisType] = {}
    for cls in symbol_table.classes:
        for prop in cls.properties:
            property_identifier = naming.json_property(prop.name)
            property_uri = _property_uri(prop)
            if (
                property_identifier in property_uris
                and property_uris[property_identifier]["uri"] != property_uri
            ):
                double_uris_set.add(property_identifier)
            property_uris[property_identifier] = {
                "uri": property_uri,
                "object": prop,
            }

    for prop_name in double_uris_set:
        del property_uris[prop_name]

    for property_full in property_uris.values():
        prop = property_full["object"]
        property_identifier = naming.json_property(prop.name)
        if property_identifier in json_ld_context:
            errors.append(
                Error(None, f"Duplicate key on JSON-LD Context ({property_identifier})")
            )
            continue
        json_ld_context[property_identifier] = _generate_properties(
            domain_aas_class=None,
            property_to_generate=prop,
            symbol_table=symbol_table,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            class_names_set_param=class_names_set,
            exported_properties_list_param=list(property_uris.keys()),
        )

    for cls in symbol_table.classes:
        class_context = _generate_class_context(
            aas_class=cls,
            symbol_table=symbol_table,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            class_names_set_param=class_names_set,
            exported_properties_list_param=list(property_uris.keys()),
        )
        if len(class_context.keys() & json_ld_context.keys()) > 0:
            errors.append(
                Error(
                    None,
                    f"Duplicate keys on JSON-LD Context and class context ({cls})",
                )
            )
        json_ld_context.update(class_context)

    return Stripped(json.dumps(json_ld_context, indent=2)), None


def _write_errors(context: run.Context, stderr: TextIO, errors: List[Error]) -> None:
    run.write_error_report(
        message=f"Failed to generate the JSON Schema " f"based on {context.model_path}",
        errors=[context.lineno_columner.error_message(error) for error in errors],
        stderr=stderr,
    )


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """NOTE (murloc6, 2023-10-06)
    JSON-LD (JSON Linked Data) Context Generation
    https://www.w3.org/TR/json-ld11/

    Developed by Fabien Amarger (murloc6), Elodie Thieblin (ethieblin), and
    Christian Glomb (wiresio) in order to generate an AAS JSON-LD Context.
    With the help of the JSON-LD Context AAS JSON files can be represented as
    triples. That enables applications to make use of Semantic technologies,
    such as storing of AAS data in triplestores or - with the help of
    appropriate SPARQL queries - data transformation, e.g., from AAS Asset
    Interface Description Submodel to W3C Web of Things Thing Description.
    """
    our_type_to_rdfs_range, error = rdf_shacl_common.map_our_type_to_rdfs_range(
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )
    if our_type_to_rdfs_range is None and error is not None:
        _write_errors(context, stderr, [error])
        return 1
    assert our_type_to_rdfs_range is not None

    json_ld_context, errors = _generate(
        symbol_table=context.symbol_table,
        our_type_to_rdfs_range=our_type_to_rdfs_range,
    )

    if errors is not None:
        _write_errors(context, stderr, errors)
        return 1

    assert json_ld_context is not None

    pth = context.output_dir / "context.jsonld"
    try:
        pth.write_text(json_ld_context, encoding="utf-8")
    except Exception as exception:
        _write_errors(context, stderr, [Error(None, str(exception))])
        return 1

    stdout.write(f"JSON-LD context generated to: {context.output_dir}\n")
    return 0
