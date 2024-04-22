"""
Generate JSON-LD context corresponding to the meta-model.

With the help of the JSON-LD (JSON Linked Data) Context, AAS JSON files can be
represented as triples. That enables applications to make use of Semantic technologies,
such as storing of AAS data in triplestores or -- with the help of appropriate SPARQL
queries -- data transformation, *e.g.*, from AAS Asset Interface Description Submodel
to W3C Web of Things Thing Description.

For more information about JSON-LD, see https://www.w3.org/TR/json-ld11/.

This code has been originally developed by Fabien Amarger (murloc6),
Elodie Thieblin (ethieblin), and Christian Glomb (wiresio).
"""

import collections
import dataclasses
import json
from typing import (
    Any,
    Dict,
    List,
    Set,
    TextIO,
    Optional,
    Tuple,
    Union,
    cast,
    OrderedDict,
)

from icontract import require

from aas_core_codegen import (
    naming,
    intermediate,
    run,
)
from aas_core_codegen.common import Error, Stripped, Identifier, assert_never
from aas_core_codegen.rdf_shacl import (
    naming as rdf_shacl_naming,
    common as rdf_shacl_common,
)

JsonLdType = OrderedDict[str, Any]


def _property_uri(prop: intermediate.Property) -> Stripped:
    """Generate a JSON-LD URI corresponding to the property."""
    property_vocab = rdf_shacl_naming.class_name(prop.specified_for.name)
    prop_uri_fragment = rdf_shacl_naming.property_name(prop.name)

    return Stripped(f"aas:{property_vocab}/{prop_uri_fragment}")


def _get_underlying_atomic_type(
    type_annotation: Union[
        intermediate.PrimitiveTypeAnnotation,
        intermediate.ListTypeAnnotation,
        intermediate.OptionalTypeAnnotation,
        intermediate.PrimitiveTypeAnnotation,
        intermediate.TypeAnnotationUnion,
    ]
) -> Union[intermediate.OurType, intermediate.PrimitiveTypeAnnotation]:
    """Flatten recursively ``our_type`` to obtain the underlying atomic type."""
    if isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        return _get_underlying_atomic_type(type_annotation.value)
    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        return _get_underlying_atomic_type(type_annotation.items)
    elif isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return type_annotation
    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        return type_annotation.our_type
    else:
        return assert_never(type_annotation)


# fmt: off
@require(
    lambda cls, prop:
    not (cls is not None) or id(prop) in cls.property_id_set
)
# fmt: on
def _generate_for_property(
    cls: Optional[intermediate.ClassUnion],
    prop: intermediate.Property,
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    name_set_of_generated_classes: Optional[Set[str]] = None,
    name_set_of_exported_properties: Optional[Set[str]] = None,
) -> JsonLdType:
    """
    Generate the definition of a property of a class.

    :param cls:
        The class which defines the domain of the property.

        If ``cls`` is None, it means the domain is generic.
    :param prop: The property which will be exported
    :param symbol_table:
        The symbol table corresponding to the AAS meta-model
    :param our_type_to_rdfs_range:
        The mapping between the AAS types and the RDFS range fragment
    :param name_set_of_generated_classes:
        The set of all class names which have been generated so far
    :param name_set_of_exported_properties:
        The set of properties exported so far.

        We specify this set to avoid multiple exports.
    :return: A JSON LD definition of the property
    """
    name_set_of_generated_classes = (
        name_set_of_generated_classes
        if name_set_of_generated_classes is not None
        else set()
    )

    # NOTE (mristin, 2023-10-28):
    # This is necessary for mypy.
    assert name_set_of_generated_classes is not None

    name_set_of_exported_properties = (
        name_set_of_exported_properties
        if name_set_of_exported_properties is not None
        else set()
    )

    # NOTE (mristin, 2023-10-28):
    # This is necessary for mypy.
    assert name_set_of_exported_properties is not None

    property_vocab = rdf_shacl_naming.class_name(prop.specified_for.name)
    prop_uri_fragment = rdf_shacl_naming.property_name(prop.name)

    property_uri = f"aas:{property_vocab}/{prop_uri_fragment}"
    rdfs_range = rdf_shacl_common.rdfs_range_for_type_annotation(
        type_annotation=prop.type_annotation,
        our_type_to_rdfs_range=our_type_to_rdfs_range,
    )
    property_json_ld_context: JsonLdType = collections.OrderedDict(
        [("@id", property_uri)]
    )
    if isinstance(
        intermediate.beneath_optional(prop.type_annotation),
        intermediate.ListTypeAnnotation,
    ):
        property_json_ld_context["@container"] = "@set"

    underlying_atomic_type_annotation = _get_underlying_atomic_type(
        prop.type_annotation
    )

    if isinstance(underlying_atomic_type_annotation, intermediate.Enumeration):
        enum_fragment = rdf_shacl_naming.class_name(
            underlying_atomic_type_annotation.name
        )
        property_json_ld_context["@context"] = cast(
            JsonLdType, collections.OrderedDict([("@vocab", f"aas:{enum_fragment}/")])
        )
        property_json_ld_context["@type"] = "@vocab"

        for item in underlying_atomic_type_annotation.literals:
            rdf_item_name = rdf_shacl_naming.enumeration_literal(item.name)
            json_item_name = item.value
            # Add the property definition if:
            #  * The JSON item name does not start with "xs:" (already defined in XML
            #    Schema Datatypes definition),
            #  * The JSON item name references an already defined class name,
            #  * The JSON item name is different from the RDF item name (we have to
            #    define the correspondance here).
            #
            # Otherwise, adding the "@vocab" is enough.
            if not json_item_name.startswith("xs:") and (
                (json_item_name in name_set_of_generated_classes)
                or json_item_name != rdf_item_name
            ):
                property_json_ld_context["@context"][
                    json_item_name
                ] = collections.OrderedDict(
                    [("@id", f"aas:{enum_fragment}/{rdf_item_name}")]
                )

    elif rdfs_range.startswith("aas:"):
        property_json_ld_context["@type"] = "@id"

        if (
            isinstance(
                underlying_atomic_type_annotation,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            )
            and cls is not underlying_atomic_type_annotation
        ):
            property_json_ld_context["@context"] = collections.OrderedDict()
            for range_property in underlying_atomic_type_annotation.properties:
                range_property_name = naming.json_property(range_property.name)

                if range_property_name not in name_set_of_exported_properties:
                    property_json_ld_context["@context"][
                        range_property_name
                    ] = _generate_for_property(
                        cls=underlying_atomic_type_annotation,
                        prop=range_property,
                        symbol_table=symbol_table,
                        our_type_to_rdfs_range=our_type_to_rdfs_range,
                        name_set_of_generated_classes=name_set_of_generated_classes,
                        name_set_of_exported_properties=name_set_of_exported_properties,
                    )
    elif rdfs_range.startswith("xs:") and rdfs_range not in (
        "xs:string",
        "xs:boolean",
    ):
        property_json_ld_context["@type"] = rdfs_range
    elif rdfs_range == "rdf:langString":
        property_json_ld_context["@container"] = "@set"
        property_json_ld_context["@context"] = collections.OrderedDict(
            [
                ("language", "@language"),
                ("text", "@value"),
            ]
        )
    return property_json_ld_context


def _generate_class_context(
    cls: intermediate.ClassUnion,
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
    name_set_of_generated_classes: Optional[Set[str]] = None,
    name_set_of_exported_properties: Optional[Set[str]] = None,
) -> JsonLdType:
    """
    Generate the JSON LD representation for a dedicated class

    :param cls: The dedicated AAS class
    :param symbol_table: The symbol table corresponding to the AAS meta-model
    :param our_type_to_rdfs_range:
        The mapping between the AAS types and the RDFS range fragment
    :param name_set_of_generated_classes:
        The set of all class names which have been generated so far
    :param name_set_of_exported_properties:
        The set of properties exported so far.

         We specify this set to avoid multiple exports.
    :return: The JSON LD representation of the dedicated class

    """
    name_set_of_generated_classes = (
        name_set_of_generated_classes
        if name_set_of_generated_classes is not None
        else set()
    )

    # NOTE (mristin, 2023-10-28):
    # This is necessary for mypy.
    assert name_set_of_generated_classes is not None

    name_set_of_exported_properties = (
        name_set_of_exported_properties
        if name_set_of_exported_properties is not None
        else set()
    )

    # NOTE (mristin, 2023-10-28):
    # This is necessary for mypy.
    assert name_set_of_exported_properties is not None

    class_context_definition: JsonLdType = collections.OrderedDict()
    class_name = naming.json_model_type(cls.name)
    uri_fragment = rdf_shacl_naming.class_name(cls.name)
    class_context_definition[class_name] = collections.OrderedDict(
        [
            ("@id", uri_fragment),
            (
                "@context",
                collections.OrderedDict(
                    [
                        (
                            "@vocab",
                            f"{symbol_table.meta_model.xml_namespace}/{uri_fragment}/",
                        )
                    ]
                ),
            ),
        ]
    )

    for prop in cls.properties:
        property_name = naming.json_property(prop.name)
        if property_name in name_set_of_exported_properties:
            continue

        class_context_definition[class_name]["@context"][
            property_name
        ] = _generate_for_property(
            cls=cls,
            prop=prop,
            symbol_table=symbol_table,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            name_set_of_generated_classes=name_set_of_generated_classes,
            name_set_of_exported_properties=name_set_of_exported_properties,
        )

    return class_context_definition


@dataclasses.dataclass
class UriAndProperty:
    """Capture a URI for a property along with the property."""

    uri: Stripped
    prop: intermediate.Property


def _generate(
    symbol_table: intermediate.SymbolTable,
    our_type_to_rdfs_range: rdf_shacl_common.OurTypeToRdfsRange,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """
    Generate the JSON-LD context based on the symbol_table.

    :param symbol_table: The symbol table corresponding to the AAS meta-model
    :param our_type_to_rdfs_range:
        The mapping between the AAS types and the RDFS range fragment
    :return: The JSON-LD context as text
    """
    xml_namespace = symbol_table.meta_model.xml_namespace
    json_ld_context: JsonLdType = collections.OrderedDict(
        [
            ("aas", f"{xml_namespace}/"),
            ("xs", "http://www.w3.org/2001/XMLSchema#"),
            ("@vocab", f"{xml_namespace}/"),
            ("modelType", "@type"),
        ]
    )
    errors: List[Error] = []

    class_name_set: Set[str] = set(
        naming.json_model_type(cls.name) for cls in symbol_table.classes
    )

    set_of_property_names_with_double_uris: Set[Identifier] = set()

    uris_and_properties_by_name: Dict[str, UriAndProperty] = dict()

    for cls in symbol_table.classes:
        for prop in cls.properties:
            property_name = naming.json_property(prop.name)
            property_uri = _property_uri(prop)

            if (
                property_name in uris_and_properties_by_name
                and uris_and_properties_by_name[property_name].uri != property_uri
            ):
                set_of_property_names_with_double_uris.add(property_name)

            uris_and_properties_by_name[property_name] = UriAndProperty(
                uri=property_uri, prop=prop
            )

    for property_name in set_of_property_names_with_double_uris:
        del uris_and_properties_by_name[property_name]

    for uri_and_property in uris_and_properties_by_name.values():
        prop = uri_and_property.prop
        property_name = naming.json_property(prop.name)

        if property_name in json_ld_context:
            errors.append(
                Error(
                    prop.parsed.node,
                    f"The property {prop.name!r} will define a duplicate key "
                    f"in JSON-LD Context: {property_name!r}",
                )
            )
            continue

        json_ld_context[property_name] = _generate_for_property(
            cls=None,
            prop=prop,
            symbol_table=symbol_table,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            name_set_of_generated_classes=class_name_set,
            name_set_of_exported_properties=set(uris_and_properties_by_name.keys()),
        )

    for cls in symbol_table.classes:
        class_context = _generate_class_context(
            cls=cls,
            symbol_table=symbol_table,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
            name_set_of_generated_classes=class_name_set,
            name_set_of_exported_properties=set(uris_and_properties_by_name.keys()),
        )
        if len(class_context.keys() & json_ld_context.keys()) > 0:
            errors.append(
                Error(
                    cls.parsed.node,
                    f"The class {cls.name!r} will have duplicate keys in "
                    f"JSON-LD Context and class context",
                )
            )
        json_ld_context.update(class_context)

    if len(errors) > 0:
        return None, errors

    return Stripped(json.dumps({"@context": json_ld_context}, indent=2)), None


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the JSON LD context."""
    our_type_to_rdfs_range, error = rdf_shacl_common.map_our_type_to_rdfs_range(
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )
    if error is not None:
        run.write_error_report(
            message=f"Failed to determine the mapping our type to ``rdfs:range`` "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert our_type_to_rdfs_range is not None

    json_ld_context, errors = _generate(
        symbol_table=context.symbol_table,
        our_type_to_rdfs_range=our_type_to_rdfs_range,
    )

    if errors is not None:
        run.write_error_report(
            message=(
                f"Failed to generate the JSON LD Context based on {context.model_path}"
            ),
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert json_ld_context is not None

    pth = context.output_dir / "context.jsonld"
    try:
        pth.write_text(json_ld_context, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the JSON LD Context to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    stdout.write(f"JSON-LD context generated to: {context.output_dir}\n")
    return 0
