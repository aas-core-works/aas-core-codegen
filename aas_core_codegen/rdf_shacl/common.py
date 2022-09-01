"""Provide common functions for both RDF and SHACL generators."""
from typing import MutableMapping, Tuple, Optional, List

from icontract import ensure

from aas_core_codegen import intermediate, specific_implementations
from aas_core_codegen.common import (
    Stripped,
    Error,
    assert_never,
)
from aas_core_codegen.rdf_shacl import naming as rdf_shacl_naming

INDENT = "    "
INDENT2 = INDENT * 2
INDENT3 = INDENT * 3
INDENT4 = INDENT * 4


def string_literal(text: str) -> Stripped:
    """Generate a valid and escaped string literal based on the free-form ``text``."""
    if len(text) == 0:
        return Stripped('""')

    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return Stripped(f'"{escaped}"')


OurTypeToRdfsRange = MutableMapping[intermediate.OurType, Stripped]


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def map_our_type_to_rdfs_range(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[OurTypeToRdfsRange], Optional[Error]]:
    """
    Iterate over all our types and determine their value as ``rdfs:range``.

    This also applies for ``sh:datatype`` in SHACL.
    """
    our_type_to_rdfs_range = dict()  # type: OurTypeToRdfsRange
    errors = []  # type: List[Error]

    for our_type in symbol_table.our_types:
        if our_type.name == "Lang_string":
            # NOTE (mristin, 2022-09-01):
            # We hard-wire the langString's to rdf:langString. Admittedly, this is
            # hacky. We could have made the class ``Lang_string``
            # implementation-specific and defined its ``rdfs:range`` manually as
            # a snippet.
            #
            # However, we decided against that as such a design would force us to
            # define langString for every language and schema which do not natively
            # support it, write custom data generation methods *etc.* Given that
            # RDF+SHACL codegen is one out of many code generators we leave the
            # other code generators and test data generators as simple as possible,
            # and make this schema generator a bit hacky in return.
            our_type_to_rdfs_range[our_type] = Stripped("rdf:langString")

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if our_type.is_implementation_specific:
                implementation_key = specific_implementations.ImplementationKey(
                    f"rdf/{our_type.name}/as_rdfs_range.ttl"
                )
                implementation = spec_impls.get(implementation_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The implementation snippet for "
                            f"how to represent the class {our_type.parsed.name} "
                            f"as ``rdfs:range`` is missing: {implementation_key}",
                        )
                    )
                else:
                    our_type_to_rdfs_range[our_type] = implementation
            else:
                # NOTE (mristin, 2022-09-01):
                # We do not define any special rdfs:range for the class. The function
                # :function:`.rdfs_range_for_type_annotation` will take care of the
                # general cases.
                pass

        else:
            # NOTE (mristin, 2022-09-01):
            # No pre-defined rdfs:range for this our type.
            pass

    if len(errors) > 0:
        return None, Error(
            None,
            "Failed to determine the mapping our type 🠒 ``rdfs:range`` "
            "for one or more of our types",
            errors,
        )

    return our_type_to_rdfs_range, None


def rdfs_range_for_type_annotation(
    type_annotation: intermediate.TypeAnnotationUnion,
    our_type_to_rdfs_range: OurTypeToRdfsRange,
) -> Stripped:
    """Determine the ``rdfs:range`` corresponding to the ``type_annotation``."""
    type_anno = intermediate.beneath_optional(type_annotation)

    rdfs_range = None  # type: Optional[str]

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        rdfs_range = PRIMITIVE_MAP[type_anno.a_type]

    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        rdfs_range = our_type_to_rdfs_range.get(type_anno.our_type, None)

        if rdfs_range is None:
            if isinstance(
                type_anno.our_type,
                (
                    intermediate.Enumeration,
                    intermediate.AbstractClass,
                    intermediate.ConcreteClass,
                ),
            ):
                cls_name = rdf_shacl_naming.class_name(type_anno.our_type.name)
                rdfs_range = f"aas:{cls_name}"

            elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                rdfs_range = PRIMITIVE_MAP[type_anno.our_type.constrainee]
            else:
                assert_never(type_anno.our_type)

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        rdfs_range = rdfs_range_for_type_annotation(
            type_annotation=type_anno.items,
            our_type_to_rdfs_range=our_type_to_rdfs_range,
        )
    else:
        assert_never(type_anno)

    assert rdfs_range is not None

    return Stripped(rdfs_range)


PRIMITIVE_MAP = {
    intermediate.PrimitiveType.BOOL: "xs:boolean",
    intermediate.PrimitiveType.INT: "xs:long",
    intermediate.PrimitiveType.FLOAT: "xs:double",
    intermediate.PrimitiveType.STR: "xs:string",
    intermediate.PrimitiveType.BYTEARRAY: "xs:base64Binary",
}
assert all(literal in PRIMITIVE_MAP for literal in intermediate.PrimitiveType)
