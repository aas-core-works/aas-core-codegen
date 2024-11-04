# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.


"""Convert instances from and to Protocol Buffers."""


from typing import Mapping, TypeVar

import google.protobuf.message

from aas_core3 import types
import aas_core3_protobuf.types_pb2 as types_pb


# region From Protocol Buffers


# fmt: off
_HAS_SEMANTICS_FROM_PB_CHOICE_MAP = {
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        ),
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        ),
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'capability':
        lambda that: capability_from_pb(
            that.capability
        ),
    'entity':
        lambda that: entity_from_pb(
            that.entity
        ),
    'extension':
        lambda that: extension_from_pb(
            that.extension
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'operation':
        lambda that: operation_from_pb(
            that.operation
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'qualifier':
        lambda that: qualifier_from_pb(
            that.qualifier
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        ),
    'specific_asset_id':
        lambda that: specific_asset_id_from_pb(
            that.specific_asset_id
        ),
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        ),
    'submodel_element_collection':
        lambda that: submodel_element_collection_from_pb(
            that.submodel_element_collection
        ),
    'submodel_element_list':
        lambda that: submodel_element_list_from_pb(
            that.submodel_element_list
        )
}
# fmt: on


def has_semantics_from_pb_choice(
    that: types_pb.HasSemantics_choice
) -> types.HasSemantics:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_semantics_from_pb_choice

        some_bytes = b'... serialized types_pb.HasSemantics_choice ...'
        has_semantics_choice_pb = types_pb.HasSemantics_choice()
        has_semantics_choice_pb.FromString(
            some_bytes
        )

        has_semantics = has_semantics_from_pb_choice(
            has_semantics_choice_pb
        )
        # Do something with the has_semantics...
    """
    get_concrete_instance_from_pb = (
        _HAS_SEMANTICS_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.HasSemantics)
    return result


def extension_from_pb(
    that: types_pb.Extension
) -> types.Extension:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import extension_from_pb

        some_bytes = b'... serialized types_pb.Extension ...'
        extension_pb = types_pb.Extension()
        extension_pb.FromString(
            some_bytes
        )

        extension = extension_from_pb(
            extension_pb
        )
        # Do something with the extension...

    """
    return types.Extension(
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        name=that.name,
        value_type=(
            data_type_def_xsd_from_pb(
                that.value_type
            )
            if that.HasField('value_type')
            else None
        ),
        value=(
            that.value
            if that.HasField('value')
            else None
        ),
        refers_to=(
            list(map(
                reference_from_pb,
                that.refers_to
            ))
            if len(that.refers_to) > 0
            else None
        )
    )


# fmt: off
_HAS_EXTENSIONS_FROM_PB_CHOICE_MAP = {
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        ),
    'asset_administration_shell':
        lambda that: asset_administration_shell_from_pb(
            that.asset_administration_shell
        ),
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        ),
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'capability':
        lambda that: capability_from_pb(
            that.capability
        ),
    'concept_description':
        lambda that: concept_description_from_pb(
            that.concept_description
        ),
    'entity':
        lambda that: entity_from_pb(
            that.entity
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'operation':
        lambda that: operation_from_pb(
            that.operation
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        ),
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        ),
    'submodel_element_collection':
        lambda that: submodel_element_collection_from_pb(
            that.submodel_element_collection
        ),
    'submodel_element_list':
        lambda that: submodel_element_list_from_pb(
            that.submodel_element_list
        )
}
# fmt: on


def has_extensions_from_pb_choice(
    that: types_pb.HasExtensions_choice
) -> types.HasExtensions:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_extensions_from_pb_choice

        some_bytes = b'... serialized types_pb.HasExtensions_choice ...'
        has_extensions_choice_pb = types_pb.HasExtensions_choice()
        has_extensions_choice_pb.FromString(
            some_bytes
        )

        has_extensions = has_extensions_from_pb_choice(
            has_extensions_choice_pb
        )
        # Do something with the has_extensions...
    """
    get_concrete_instance_from_pb = (
        _HAS_EXTENSIONS_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.HasExtensions)
    return result


# fmt: off
_REFERABLE_FROM_PB_CHOICE_MAP = {
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        ),
    'asset_administration_shell':
        lambda that: asset_administration_shell_from_pb(
            that.asset_administration_shell
        ),
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        ),
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'capability':
        lambda that: capability_from_pb(
            that.capability
        ),
    'concept_description':
        lambda that: concept_description_from_pb(
            that.concept_description
        ),
    'entity':
        lambda that: entity_from_pb(
            that.entity
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'operation':
        lambda that: operation_from_pb(
            that.operation
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        ),
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        ),
    'submodel_element_collection':
        lambda that: submodel_element_collection_from_pb(
            that.submodel_element_collection
        ),
    'submodel_element_list':
        lambda that: submodel_element_list_from_pb(
            that.submodel_element_list
        )
}
# fmt: on


def referable_from_pb_choice(
    that: types_pb.Referable_choice
) -> types.Referable:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import referable_from_pb_choice

        some_bytes = b'... serialized types_pb.Referable_choice ...'
        referable_choice_pb = types_pb.Referable_choice()
        referable_choice_pb.FromString(
            some_bytes
        )

        referable = referable_from_pb_choice(
            referable_choice_pb
        )
        # Do something with the referable...
    """
    get_concrete_instance_from_pb = (
        _REFERABLE_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.Referable)
    return result


# fmt: off
_IDENTIFIABLE_FROM_PB_CHOICE_MAP = {
    'asset_administration_shell':
        lambda that: asset_administration_shell_from_pb(
            that.asset_administration_shell
        ),
    'concept_description':
        lambda that: concept_description_from_pb(
            that.concept_description
        ),
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        )
}
# fmt: on


def identifiable_from_pb_choice(
    that: types_pb.Identifiable_choice
) -> types.Identifiable:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import identifiable_from_pb_choice

        some_bytes = b'... serialized types_pb.Identifiable_choice ...'
        identifiable_choice_pb = types_pb.Identifiable_choice()
        identifiable_choice_pb.FromString(
            some_bytes
        )

        identifiable = identifiable_from_pb_choice(
            identifiable_choice_pb
        )
        # Do something with the identifiable...
    """
    get_concrete_instance_from_pb = (
        _IDENTIFIABLE_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.Identifiable)
    return result


# fmt: off
_MODELLING_KIND_FROM_PB_MAP = {
    types_pb.ModellingKind.Modellingkind_TEMPLATE:
        types.ModellingKind.TEMPLATE,
    types_pb.ModellingKind.Modellingkind_INSTANCE:
        types.ModellingKind.INSTANCE
}  # type: Mapping[types_pb.ModellingKind, types.ModellingKind]
# fmt: on


def modelling_kind_from_pb(
    that: types_pb.ModellingKind
) -> types.ModellingKind:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import modelling_kind_from_pb
    >>> modelling_kind_from_pb(
    ...     types_pb.ModellingKind.Modellingkind_TEMPLATE
    ... )
    <ModellingKind.TEMPLATE: 'Template'>
    """
    return _MODELLING_KIND_FROM_PB_MAP[that]


# fmt: off
_HAS_KIND_FROM_PB_CHOICE_MAP = {
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        )
}
# fmt: on


def has_kind_from_pb_choice(
    that: types_pb.HasKind_choice
) -> types.HasKind:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_kind_from_pb_choice

        some_bytes = b'... serialized types_pb.HasKind_choice ...'
        has_kind_choice_pb = types_pb.HasKind_choice()
        has_kind_choice_pb.FromString(
            some_bytes
        )

        has_kind = has_kind_from_pb_choice(
            has_kind_choice_pb
        )
        # Do something with the has_kind...
    """
    get_concrete_instance_from_pb = (
        _HAS_KIND_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.HasKind)
    return result


# fmt: off
_HAS_DATA_SPECIFICATION_FROM_PB_CHOICE_MAP = {
    'administrative_information':
        lambda that: administrative_information_from_pb(
            that.administrative_information
        ),
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        ),
    'asset_administration_shell':
        lambda that: asset_administration_shell_from_pb(
            that.asset_administration_shell
        ),
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        ),
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'capability':
        lambda that: capability_from_pb(
            that.capability
        ),
    'concept_description':
        lambda that: concept_description_from_pb(
            that.concept_description
        ),
    'entity':
        lambda that: entity_from_pb(
            that.entity
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'operation':
        lambda that: operation_from_pb(
            that.operation
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        ),
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        ),
    'submodel_element_collection':
        lambda that: submodel_element_collection_from_pb(
            that.submodel_element_collection
        ),
    'submodel_element_list':
        lambda that: submodel_element_list_from_pb(
            that.submodel_element_list
        )
}
# fmt: on


def has_data_specification_from_pb_choice(
    that: types_pb.HasDataSpecification_choice
) -> types.HasDataSpecification:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_data_specification_from_pb_choice

        some_bytes = b'... serialized types_pb.HasDataSpecification_choice ...'
        has_data_specification_choice_pb = types_pb.HasDataSpecification_choice()
        has_data_specification_choice_pb.FromString(
            some_bytes
        )

        has_data_specification = has_data_specification_from_pb_choice(
            has_data_specification_choice_pb
        )
        # Do something with the has_data_specification...
    """
    get_concrete_instance_from_pb = (
        _HAS_DATA_SPECIFICATION_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.HasDataSpecification)
    return result


def administrative_information_from_pb(
    that: types_pb.AdministrativeInformation
) -> types.AdministrativeInformation:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import administrative_information_from_pb

        some_bytes = b'... serialized types_pb.AdministrativeInformation ...'
        administrative_information_pb = types_pb.AdministrativeInformation()
        administrative_information_pb.FromString(
            some_bytes
        )

        administrative_information = administrative_information_from_pb(
            administrative_information_pb
        )
        # Do something with the administrative_information...

    """
    return types.AdministrativeInformation(
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        version=(
            that.version
            if that.HasField('version')
            else None
        ),
        revision=(
            that.revision
            if that.HasField('revision')
            else None
        ),
        creator=(
            reference_from_pb(
                that.creator
            )
            if that.HasField('creator')
            else None
        ),
        template_id=(
            that.template_id
            if that.HasField('template_id')
            else None
        )
    )


# fmt: off
_QUALIFIABLE_FROM_PB_CHOICE_MAP = {
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        ),
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        ),
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'capability':
        lambda that: capability_from_pb(
            that.capability
        ),
    'entity':
        lambda that: entity_from_pb(
            that.entity
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'operation':
        lambda that: operation_from_pb(
            that.operation
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        ),
    'submodel':
        lambda that: submodel_from_pb(
            that.submodel
        ),
    'submodel_element_collection':
        lambda that: submodel_element_collection_from_pb(
            that.submodel_element_collection
        ),
    'submodel_element_list':
        lambda that: submodel_element_list_from_pb(
            that.submodel_element_list
        )
}
# fmt: on


def qualifiable_from_pb_choice(
    that: types_pb.Qualifiable_choice
) -> types.Qualifiable:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import qualifiable_from_pb_choice

        some_bytes = b'... serialized types_pb.Qualifiable_choice ...'
        qualifiable_choice_pb = types_pb.Qualifiable_choice()
        qualifiable_choice_pb.FromString(
            some_bytes
        )

        qualifiable = qualifiable_from_pb_choice(
            qualifiable_choice_pb
        )
        # Do something with the qualifiable...
    """
    get_concrete_instance_from_pb = (
        _QUALIFIABLE_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.Qualifiable)
    return result


# fmt: off
_QUALIFIER_KIND_FROM_PB_MAP = {
    types_pb.QualifierKind.Qualifierkind_VALUE_QUALIFIER:
        types.QualifierKind.VALUE_QUALIFIER,
    types_pb.QualifierKind.Qualifierkind_CONCEPT_QUALIFIER:
        types.QualifierKind.CONCEPT_QUALIFIER,
    types_pb.QualifierKind.Qualifierkind_TEMPLATE_QUALIFIER:
        types.QualifierKind.TEMPLATE_QUALIFIER
}  # type: Mapping[types_pb.QualifierKind, types.QualifierKind]
# fmt: on


def qualifier_kind_from_pb(
    that: types_pb.QualifierKind
) -> types.QualifierKind:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import qualifier_kind_from_pb
    >>> qualifier_kind_from_pb(
    ...     types_pb.QualifierKind.Qualifierkind_VALUE_QUALIFIER
    ... )
    <QualifierKind.VALUE_QUALIFIER: 'ValueQualifier'>
    """
    return _QUALIFIER_KIND_FROM_PB_MAP[that]


def qualifier_from_pb(
    that: types_pb.Qualifier
) -> types.Qualifier:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import qualifier_from_pb

        some_bytes = b'... serialized types_pb.Qualifier ...'
        qualifier_pb = types_pb.Qualifier()
        qualifier_pb.FromString(
            some_bytes
        )

        qualifier = qualifier_from_pb(
            qualifier_pb
        )
        # Do something with the qualifier...

    """
    return types.Qualifier(
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        kind=(
            qualifier_kind_from_pb(
                that.kind
            )
            if that.HasField('kind')
            else None
        ),
        type=that.type,
        value_type=data_type_def_xsd_from_pb(
            that.value_type
        ),
        value=(
            that.value
            if that.HasField('value')
            else None
        ),
        value_id=(
            reference_from_pb(
                that.value_id
            )
            if that.HasField('value_id')
            else None
        )
    )


def asset_administration_shell_from_pb(
    that: types_pb.AssetAdministrationShell
) -> types.AssetAdministrationShell:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import asset_administration_shell_from_pb

        some_bytes = b'... serialized types_pb.AssetAdministrationShell ...'
        asset_administration_shell_pb = types_pb.AssetAdministrationShell()
        asset_administration_shell_pb.FromString(
            some_bytes
        )

        asset_administration_shell = asset_administration_shell_from_pb(
            asset_administration_shell_pb
        )
        # Do something with the asset_administration_shell...

    """
    return types.AssetAdministrationShell(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        administration=(
            administrative_information_from_pb(
                that.administration
            )
            if that.HasField('administration')
            else None
        ),
        id=that.id,
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        derived_from=(
            reference_from_pb(
                that.derived_from
            )
            if that.HasField('derived_from')
            else None
        ),
        asset_information=asset_information_from_pb(
            that.asset_information
        ),
        submodels=(
            list(map(
                reference_from_pb,
                that.submodels
            ))
            if len(that.submodels) > 0
            else None
        )
    )


def asset_information_from_pb(
    that: types_pb.AssetInformation
) -> types.AssetInformation:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import asset_information_from_pb

        some_bytes = b'... serialized types_pb.AssetInformation ...'
        asset_information_pb = types_pb.AssetInformation()
        asset_information_pb.FromString(
            some_bytes
        )

        asset_information = asset_information_from_pb(
            asset_information_pb
        )
        # Do something with the asset_information...

    """
    return types.AssetInformation(
        asset_kind=asset_kind_from_pb(
            that.asset_kind
        ),
        global_asset_id=(
            that.global_asset_id
            if that.HasField('global_asset_id')
            else None
        ),
        specific_asset_ids=(
            list(map(
                specific_asset_id_from_pb,
                that.specific_asset_ids
            ))
            if len(that.specific_asset_ids) > 0
            else None
        ),
        asset_type=(
            that.asset_type
            if that.HasField('asset_type')
            else None
        ),
        default_thumbnail=(
            resource_from_pb(
                that.default_thumbnail
            )
            if that.HasField('default_thumbnail')
            else None
        )
    )


def resource_from_pb(
    that: types_pb.Resource
) -> types.Resource:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import resource_from_pb

        some_bytes = b'... serialized types_pb.Resource ...'
        resource_pb = types_pb.Resource()
        resource_pb.FromString(
            some_bytes
        )

        resource = resource_from_pb(
            resource_pb
        )
        # Do something with the resource...

    """
    return types.Resource(
        path=that.path,
        content_type=(
            that.content_type
            if that.HasField('content_type')
            else None
        )
    )


# fmt: off
_ASSET_KIND_FROM_PB_MAP = {
    types_pb.AssetKind.Assetkind_TYPE:
        types.AssetKind.TYPE,
    types_pb.AssetKind.Assetkind_INSTANCE:
        types.AssetKind.INSTANCE,
    types_pb.AssetKind.Assetkind_NOT_APPLICABLE:
        types.AssetKind.NOT_APPLICABLE
}  # type: Mapping[types_pb.AssetKind, types.AssetKind]
# fmt: on


def asset_kind_from_pb(
    that: types_pb.AssetKind
) -> types.AssetKind:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import asset_kind_from_pb
    >>> asset_kind_from_pb(
    ...     types_pb.AssetKind.Assetkind_TYPE
    ... )
    <AssetKind.TYPE: 'Type'>
    """
    return _ASSET_KIND_FROM_PB_MAP[that]


def specific_asset_id_from_pb(
    that: types_pb.SpecificAssetId
) -> types.SpecificAssetID:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import specific_asset_id_from_pb

        some_bytes = b'... serialized types_pb.SpecificAssetId ...'
        specific_asset_id_pb = types_pb.SpecificAssetId()
        specific_asset_id_pb.FromString(
            some_bytes
        )

        specific_asset_id = specific_asset_id_from_pb(
            specific_asset_id_pb
        )
        # Do something with the specific_asset_id...

    """
    return types.SpecificAssetID(
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        name=that.name,
        value=that.value,
        external_subject_id=(
            reference_from_pb(
                that.external_subject_id
            )
            if that.HasField('external_subject_id')
            else None
        )
    )


def submodel_from_pb(
    that: types_pb.Submodel
) -> types.Submodel:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_from_pb

        some_bytes = b'... serialized types_pb.Submodel ...'
        submodel_pb = types_pb.Submodel()
        submodel_pb.FromString(
            some_bytes
        )

        submodel = submodel_from_pb(
            submodel_pb
        )
        # Do something with the submodel...

    """
    return types.Submodel(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        administration=(
            administrative_information_from_pb(
                that.administration
            )
            if that.HasField('administration')
            else None
        ),
        id=that.id,
        kind=(
            modelling_kind_from_pb(
                that.kind
            )
            if that.HasField('kind')
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        submodel_elements=(
            list(map(
                submodel_element_from_pb_choice,
                that.submodel_elements
            ))
            if len(that.submodel_elements) > 0
            else None
        )
    )


# fmt: off
_SUBMODEL_ELEMENT_FROM_PB_CHOICE_MAP = {
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        ),
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        ),
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'capability':
        lambda that: capability_from_pb(
            that.capability
        ),
    'entity':
        lambda that: entity_from_pb(
            that.entity
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'operation':
        lambda that: operation_from_pb(
            that.operation
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        ),
    'submodel_element_collection':
        lambda that: submodel_element_collection_from_pb(
            that.submodel_element_collection
        ),
    'submodel_element_list':
        lambda that: submodel_element_list_from_pb(
            that.submodel_element_list
        )
}
# fmt: on


def submodel_element_from_pb_choice(
    that: types_pb.SubmodelElement_choice
) -> types.SubmodelElement:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_element_from_pb_choice

        some_bytes = b'... serialized types_pb.SubmodelElement_choice ...'
        submodel_element_choice_pb = types_pb.SubmodelElement_choice()
        submodel_element_choice_pb.FromString(
            some_bytes
        )

        submodel_element = submodel_element_from_pb_choice(
            submodel_element_choice_pb
        )
        # Do something with the submodel_element...
    """
    get_concrete_instance_from_pb = (
        _SUBMODEL_ELEMENT_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.SubmodelElement)
    return result


# fmt: off
_RELATIONSHIP_ELEMENT_FROM_PB_CHOICE_MAP = {
    'relationship_element':
        lambda that: relationship_element_from_pb(
            that.relationship_element
        ),
    'annotated_relationship_element':
        lambda that: annotated_relationship_element_from_pb(
            that.annotated_relationship_element
        )
}
# fmt: on


def relationship_element_from_pb_choice(
    that: types_pb.RelationshipElement_choice
) -> types.RelationshipElement:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import relationship_element_from_pb_choice

        some_bytes = b'... serialized types_pb.RelationshipElement_choice ...'
        relationship_element_choice_pb = types_pb.RelationshipElement_choice()
        relationship_element_choice_pb.FromString(
            some_bytes
        )

        relationship_element = relationship_element_from_pb_choice(
            relationship_element_choice_pb
        )
        # Do something with the relationship_element...
    """
    get_concrete_instance_from_pb = (
        _RELATIONSHIP_ELEMENT_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.RelationshipElement)
    return result


def relationship_element_from_pb(
    that: types_pb.RelationshipElement
) -> types.RelationshipElement:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import relationship_element_from_pb

        some_bytes = b'... serialized types_pb.RelationshipElement ...'
        relationship_element_pb = types_pb.RelationshipElement()
        relationship_element_pb.FromString(
            some_bytes
        )

        relationship_element = relationship_element_from_pb(
            relationship_element_pb
        )
        # Do something with the relationship_element...

    """
    return types.RelationshipElement(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        first=reference_from_pb(
            that.first
        ),
        second=reference_from_pb(
            that.second
        )
    )


# fmt: off
_AAS_SUBMODEL_ELEMENTS_FROM_PB_MAP = {
    types_pb.AasSubmodelElements.Aassubmodelelements_ANNOTATED_RELATIONSHIP_ELEMENT:
        types.AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_BASIC_EVENT_ELEMENT:
        types.AASSubmodelElements.BASIC_EVENT_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_BLOB:
        types.AASSubmodelElements.BLOB,
    types_pb.AasSubmodelElements.Aassubmodelelements_CAPABILITY:
        types.AASSubmodelElements.CAPABILITY,
    types_pb.AasSubmodelElements.Aassubmodelelements_DATA_ELEMENT:
        types.AASSubmodelElements.DATA_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_ENTITY:
        types.AASSubmodelElements.ENTITY,
    types_pb.AasSubmodelElements.Aassubmodelelements_EVENT_ELEMENT:
        types.AASSubmodelElements.EVENT_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_FILE:
        types.AASSubmodelElements.FILE,
    types_pb.AasSubmodelElements.Aassubmodelelements_MULTI_LANGUAGE_PROPERTY:
        types.AASSubmodelElements.MULTI_LANGUAGE_PROPERTY,
    types_pb.AasSubmodelElements.Aassubmodelelements_OPERATION:
        types.AASSubmodelElements.OPERATION,
    types_pb.AasSubmodelElements.Aassubmodelelements_PROPERTY:
        types.AASSubmodelElements.PROPERTY,
    types_pb.AasSubmodelElements.Aassubmodelelements_RANGE:
        types.AASSubmodelElements.RANGE,
    types_pb.AasSubmodelElements.Aassubmodelelements_REFERENCE_ELEMENT:
        types.AASSubmodelElements.REFERENCE_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_RELATIONSHIP_ELEMENT:
        types.AASSubmodelElements.RELATIONSHIP_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_SUBMODEL_ELEMENT:
        types.AASSubmodelElements.SUBMODEL_ELEMENT,
    types_pb.AasSubmodelElements.Aassubmodelelements_SUBMODEL_ELEMENT_LIST:
        types.AASSubmodelElements.SUBMODEL_ELEMENT_LIST,
    types_pb.AasSubmodelElements.Aassubmodelelements_SUBMODEL_ELEMENT_COLLECTION:
        types.AASSubmodelElements.SUBMODEL_ELEMENT_COLLECTION
}  # type: Mapping[types_pb.AasSubmodelElements, types.AASSubmodelElements]
# fmt: on


def aas_submodel_elements_from_pb(
    that: types_pb.AasSubmodelElements
) -> types.AASSubmodelElements:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import aas_submodel_elements_from_pb
    >>> aas_submodel_elements_from_pb(
    ...     types_pb.AasSubmodelElements.Aassubmodelelements_ANNOTATED_RELATIONSHIP_ELEMENT
    ... )
    <AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT: 'AnnotatedRelationshipElement'>
    """
    return _AAS_SUBMODEL_ELEMENTS_FROM_PB_MAP[that]


def submodel_element_list_from_pb(
    that: types_pb.SubmodelElementList
) -> types.SubmodelElementList:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_element_list_from_pb

        some_bytes = b'... serialized types_pb.SubmodelElementList ...'
        submodel_element_list_pb = types_pb.SubmodelElementList()
        submodel_element_list_pb.FromString(
            some_bytes
        )

        submodel_element_list = submodel_element_list_from_pb(
            submodel_element_list_pb
        )
        # Do something with the submodel_element_list...

    """
    return types.SubmodelElementList(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        order_relevant=(
            that.order_relevant
            if that.HasField('order_relevant')
            else None
        ),
        semantic_id_list_element=(
            reference_from_pb(
                that.semantic_id_list_element
            )
            if that.HasField('semantic_id_list_element')
            else None
        ),
        type_value_list_element=aas_submodel_elements_from_pb(
            that.type_value_list_element
        ),
        value_type_list_element=(
            data_type_def_xsd_from_pb(
                that.value_type_list_element
            )
            if that.HasField('value_type_list_element')
            else None
        ),
        value=(
            list(map(
                submodel_element_from_pb_choice,
                that.value
            ))
            if len(that.value) > 0
            else None
        )
    )


def submodel_element_collection_from_pb(
    that: types_pb.SubmodelElementCollection
) -> types.SubmodelElementCollection:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_element_collection_from_pb

        some_bytes = b'... serialized types_pb.SubmodelElementCollection ...'
        submodel_element_collection_pb = types_pb.SubmodelElementCollection()
        submodel_element_collection_pb.FromString(
            some_bytes
        )

        submodel_element_collection = submodel_element_collection_from_pb(
            submodel_element_collection_pb
        )
        # Do something with the submodel_element_collection...

    """
    return types.SubmodelElementCollection(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value=(
            list(map(
                submodel_element_from_pb_choice,
                that.value
            ))
            if len(that.value) > 0
            else None
        )
    )


# fmt: off
_DATA_ELEMENT_FROM_PB_CHOICE_MAP = {
    'blob':
        lambda that: blob_from_pb(
            that.blob
        ),
    'file':
        lambda that: file_from_pb(
            that.file
        ),
    'multi_language_property':
        lambda that: multi_language_property_from_pb(
            that.multi_language_property
        ),
    'property':
        lambda that: property_from_pb(
            that.property
        ),
    'range':
        lambda that: range_from_pb(
            that.range
        ),
    'reference_element':
        lambda that: reference_element_from_pb(
            that.reference_element
        )
}
# fmt: on


def data_element_from_pb_choice(
    that: types_pb.DataElement_choice
) -> types.DataElement:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import data_element_from_pb_choice

        some_bytes = b'... serialized types_pb.DataElement_choice ...'
        data_element_choice_pb = types_pb.DataElement_choice()
        data_element_choice_pb.FromString(
            some_bytes
        )

        data_element = data_element_from_pb_choice(
            data_element_choice_pb
        )
        # Do something with the data_element...
    """
    get_concrete_instance_from_pb = (
        _DATA_ELEMENT_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.DataElement)
    return result


def property_from_pb(
    that: types_pb.Property
) -> types.Property:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import property_from_pb

        some_bytes = b'... serialized types_pb.Property ...'
        property_pb = types_pb.Property()
        property_pb.FromString(
            some_bytes
        )

        property = property_from_pb(
            property_pb
        )
        # Do something with the property...

    """
    return types.Property(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value_type=data_type_def_xsd_from_pb(
            that.value_type
        ),
        value=(
            that.value
            if that.HasField('value')
            else None
        ),
        value_id=(
            reference_from_pb(
                that.value_id
            )
            if that.HasField('value_id')
            else None
        )
    )


def multi_language_property_from_pb(
    that: types_pb.MultiLanguageProperty
) -> types.MultiLanguageProperty:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import multi_language_property_from_pb

        some_bytes = b'... serialized types_pb.MultiLanguageProperty ...'
        multi_language_property_pb = types_pb.MultiLanguageProperty()
        multi_language_property_pb.FromString(
            some_bytes
        )

        multi_language_property = multi_language_property_from_pb(
            multi_language_property_pb
        )
        # Do something with the multi_language_property...

    """
    return types.MultiLanguageProperty(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value=(
            list(map(
                lang_string_text_type_from_pb,
                that.value
            ))
            if len(that.value) > 0
            else None
        ),
        value_id=(
            reference_from_pb(
                that.value_id
            )
            if that.HasField('value_id')
            else None
        )
    )


def range_from_pb(
    that: types_pb.Range
) -> types.Range:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import range_from_pb

        some_bytes = b'... serialized types_pb.Range ...'
        range_pb = types_pb.Range()
        range_pb.FromString(
            some_bytes
        )

        range = range_from_pb(
            range_pb
        )
        # Do something with the range...

    """
    return types.Range(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value_type=data_type_def_xsd_from_pb(
            that.value_type
        ),
        min=(
            that.min
            if that.HasField('min')
            else None
        ),
        max=(
            that.max
            if that.HasField('max')
            else None
        )
    )


def reference_element_from_pb(
    that: types_pb.ReferenceElement
) -> types.ReferenceElement:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import reference_element_from_pb

        some_bytes = b'... serialized types_pb.ReferenceElement ...'
        reference_element_pb = types_pb.ReferenceElement()
        reference_element_pb.FromString(
            some_bytes
        )

        reference_element = reference_element_from_pb(
            reference_element_pb
        )
        # Do something with the reference_element...

    """
    return types.ReferenceElement(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value=(
            reference_from_pb(
                that.value
            )
            if that.HasField('value')
            else None
        )
    )


def blob_from_pb(
    that: types_pb.Blob
) -> types.Blob:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import blob_from_pb

        some_bytes = b'... serialized types_pb.Blob ...'
        blob_pb = types_pb.Blob()
        blob_pb.FromString(
            some_bytes
        )

        blob = blob_from_pb(
            blob_pb
        )
        # Do something with the blob...

    """
    return types.Blob(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value=(
            bytearray(that.value)
            if that.HasField('value')
            else None
        ),
        content_type=that.content_type
    )


def file_from_pb(
    that: types_pb.File
) -> types.File:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import file_from_pb

        some_bytes = b'... serialized types_pb.File ...'
        file_pb = types_pb.File()
        file_pb.FromString(
            some_bytes
        )

        file = file_from_pb(
            file_pb
        )
        # Do something with the file...

    """
    return types.File(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        value=(
            that.value
            if that.HasField('value')
            else None
        ),
        content_type=that.content_type
    )


def annotated_relationship_element_from_pb(
    that: types_pb.AnnotatedRelationshipElement
) -> types.AnnotatedRelationshipElement:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import annotated_relationship_element_from_pb

        some_bytes = b'... serialized types_pb.AnnotatedRelationshipElement ...'
        annotated_relationship_element_pb = types_pb.AnnotatedRelationshipElement()
        annotated_relationship_element_pb.FromString(
            some_bytes
        )

        annotated_relationship_element = annotated_relationship_element_from_pb(
            annotated_relationship_element_pb
        )
        # Do something with the annotated_relationship_element...

    """
    return types.AnnotatedRelationshipElement(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        first=reference_from_pb(
            that.first
        ),
        second=reference_from_pb(
            that.second
        ),
        annotations=(
            list(map(
                data_element_from_pb_choice,
                that.annotations
            ))
            if len(that.annotations) > 0
            else None
        )
    )


def entity_from_pb(
    that: types_pb.Entity
) -> types.Entity:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import entity_from_pb

        some_bytes = b'... serialized types_pb.Entity ...'
        entity_pb = types_pb.Entity()
        entity_pb.FromString(
            some_bytes
        )

        entity = entity_from_pb(
            entity_pb
        )
        # Do something with the entity...

    """
    return types.Entity(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        statements=(
            list(map(
                submodel_element_from_pb_choice,
                that.statements
            ))
            if len(that.statements) > 0
            else None
        ),
        entity_type=entity_type_from_pb(
            that.entity_type
        ),
        global_asset_id=(
            that.global_asset_id
            if that.HasField('global_asset_id')
            else None
        ),
        specific_asset_ids=(
            list(map(
                specific_asset_id_from_pb,
                that.specific_asset_ids
            ))
            if len(that.specific_asset_ids) > 0
            else None
        )
    )


# fmt: off
_ENTITY_TYPE_FROM_PB_MAP = {
    types_pb.EntityType.Entitytype_CO_MANAGED_ENTITY:
        types.EntityType.CO_MANAGED_ENTITY,
    types_pb.EntityType.Entitytype_SELF_MANAGED_ENTITY:
        types.EntityType.SELF_MANAGED_ENTITY
}  # type: Mapping[types_pb.EntityType, types.EntityType]
# fmt: on


def entity_type_from_pb(
    that: types_pb.EntityType
) -> types.EntityType:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import entity_type_from_pb
    >>> entity_type_from_pb(
    ...     types_pb.EntityType.Entitytype_CO_MANAGED_ENTITY
    ... )
    <EntityType.CO_MANAGED_ENTITY: 'CoManagedEntity'>
    """
    return _ENTITY_TYPE_FROM_PB_MAP[that]


# fmt: off
_DIRECTION_FROM_PB_MAP = {
    types_pb.Direction.Direction_INPUT:
        types.Direction.INPUT,
    types_pb.Direction.Direction_OUTPUT:
        types.Direction.OUTPUT
}  # type: Mapping[types_pb.Direction, types.Direction]
# fmt: on


def direction_from_pb(
    that: types_pb.Direction
) -> types.Direction:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import direction_from_pb
    >>> direction_from_pb(
    ...     types_pb.Direction.Direction_INPUT
    ... )
    <Direction.INPUT: 'input'>
    """
    return _DIRECTION_FROM_PB_MAP[that]


# fmt: off
_STATE_OF_EVENT_FROM_PB_MAP = {
    types_pb.StateOfEvent.Stateofevent_ON:
        types.StateOfEvent.ON,
    types_pb.StateOfEvent.Stateofevent_OFF:
        types.StateOfEvent.OFF
}  # type: Mapping[types_pb.StateOfEvent, types.StateOfEvent]
# fmt: on


def state_of_event_from_pb(
    that: types_pb.StateOfEvent
) -> types.StateOfEvent:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import state_of_event_from_pb
    >>> state_of_event_from_pb(
    ...     types_pb.StateOfEvent.Stateofevent_ON
    ... )
    <StateOfEvent.ON: 'on'>
    """
    return _STATE_OF_EVENT_FROM_PB_MAP[that]


def event_payload_from_pb(
    that: types_pb.EventPayload
) -> types.EventPayload:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import event_payload_from_pb

        some_bytes = b'... serialized types_pb.EventPayload ...'
        event_payload_pb = types_pb.EventPayload()
        event_payload_pb.FromString(
            some_bytes
        )

        event_payload = event_payload_from_pb(
            event_payload_pb
        )
        # Do something with the event_payload...

    """
    return types.EventPayload(
        source=reference_from_pb(
            that.source
        ),
        source_semantic_id=(
            reference_from_pb(
                that.source_semantic_id
            )
            if that.HasField('source_semantic_id')
            else None
        ),
        observable_reference=reference_from_pb(
            that.observable_reference
        ),
        observable_semantic_id=(
            reference_from_pb(
                that.observable_semantic_id
            )
            if that.HasField('observable_semantic_id')
            else None
        ),
        topic=(
            that.topic
            if that.HasField('topic')
            else None
        ),
        subject_id=(
            reference_from_pb(
                that.subject_id
            )
            if that.HasField('subject_id')
            else None
        ),
        time_stamp=that.time_stamp,
        payload=(
            bytearray(that.payload)
            if that.HasField('payload')
            else None
        )
    )


# fmt: off
_EVENT_ELEMENT_FROM_PB_CHOICE_MAP = {
    'basic_event_element':
        lambda that: basic_event_element_from_pb(
            that.basic_event_element
        )
}
# fmt: on


def event_element_from_pb_choice(
    that: types_pb.EventElement_choice
) -> types.EventElement:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import event_element_from_pb_choice

        some_bytes = b'... serialized types_pb.EventElement_choice ...'
        event_element_choice_pb = types_pb.EventElement_choice()
        event_element_choice_pb.FromString(
            some_bytes
        )

        event_element = event_element_from_pb_choice(
            event_element_choice_pb
        )
        # Do something with the event_element...
    """
    get_concrete_instance_from_pb = (
        _EVENT_ELEMENT_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.EventElement)
    return result


def basic_event_element_from_pb(
    that: types_pb.BasicEventElement
) -> types.BasicEventElement:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import basic_event_element_from_pb

        some_bytes = b'... serialized types_pb.BasicEventElement ...'
        basic_event_element_pb = types_pb.BasicEventElement()
        basic_event_element_pb.FromString(
            some_bytes
        )

        basic_event_element = basic_event_element_from_pb(
            basic_event_element_pb
        )
        # Do something with the basic_event_element...

    """
    return types.BasicEventElement(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        observed=reference_from_pb(
            that.observed
        ),
        direction=direction_from_pb(
            that.direction
        ),
        state=state_of_event_from_pb(
            that.state
        ),
        message_topic=(
            that.message_topic
            if that.HasField('message_topic')
            else None
        ),
        message_broker=(
            reference_from_pb(
                that.message_broker
            )
            if that.HasField('message_broker')
            else None
        ),
        last_update=(
            that.last_update
            if that.HasField('last_update')
            else None
        ),
        min_interval=(
            that.min_interval
            if that.HasField('min_interval')
            else None
        ),
        max_interval=(
            that.max_interval
            if that.HasField('max_interval')
            else None
        )
    )


def operation_from_pb(
    that: types_pb.Operation
) -> types.Operation:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import operation_from_pb

        some_bytes = b'... serialized types_pb.Operation ...'
        operation_pb = types_pb.Operation()
        operation_pb.FromString(
            some_bytes
        )

        operation = operation_from_pb(
            operation_pb
        )
        # Do something with the operation...

    """
    return types.Operation(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        input_variables=(
            list(map(
                operation_variable_from_pb,
                that.input_variables
            ))
            if len(that.input_variables) > 0
            else None
        ),
        output_variables=(
            list(map(
                operation_variable_from_pb,
                that.output_variables
            ))
            if len(that.output_variables) > 0
            else None
        ),
        inoutput_variables=(
            list(map(
                operation_variable_from_pb,
                that.inoutput_variables
            ))
            if len(that.inoutput_variables) > 0
            else None
        )
    )


def operation_variable_from_pb(
    that: types_pb.OperationVariable
) -> types.OperationVariable:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import operation_variable_from_pb

        some_bytes = b'... serialized types_pb.OperationVariable ...'
        operation_variable_pb = types_pb.OperationVariable()
        operation_variable_pb.FromString(
            some_bytes
        )

        operation_variable = operation_variable_from_pb(
            operation_variable_pb
        )
        # Do something with the operation_variable...

    """
    return types.OperationVariable(
        value=submodel_element_from_pb_choice(
            that.value
        )
    )


def capability_from_pb(
    that: types_pb.Capability
) -> types.Capability:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import capability_from_pb

        some_bytes = b'... serialized types_pb.Capability ...'
        capability_pb = types_pb.Capability()
        capability_pb.FromString(
            some_bytes
        )

        capability = capability_from_pb(
            capability_pb
        )
        # Do something with the capability...

    """
    return types.Capability(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        semantic_id=(
            reference_from_pb(
                that.semantic_id
            )
            if that.HasField('semantic_id')
            else None
        ),
        supplemental_semantic_ids=(
            list(map(
                reference_from_pb,
                that.supplemental_semantic_ids
            ))
            if len(that.supplemental_semantic_ids) > 0
            else None
        ),
        qualifiers=(
            list(map(
                qualifier_from_pb,
                that.qualifiers
            ))
            if len(that.qualifiers) > 0
            else None
        ),
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        )
    )


def concept_description_from_pb(
    that: types_pb.ConceptDescription
) -> types.ConceptDescription:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import concept_description_from_pb

        some_bytes = b'... serialized types_pb.ConceptDescription ...'
        concept_description_pb = types_pb.ConceptDescription()
        concept_description_pb.FromString(
            some_bytes
        )

        concept_description = concept_description_from_pb(
            concept_description_pb
        )
        # Do something with the concept_description...

    """
    return types.ConceptDescription(
        extensions=(
            list(map(
                extension_from_pb,
                that.extensions
            ))
            if len(that.extensions) > 0
            else None
        ),
        category=(
            that.category
            if that.HasField('category')
            else None
        ),
        id_short=(
            that.id_short
            if that.HasField('id_short')
            else None
        ),
        display_name=(
            list(map(
                lang_string_name_type_from_pb,
                that.display_name
            ))
            if len(that.display_name) > 0
            else None
        ),
        description=(
            list(map(
                lang_string_text_type_from_pb,
                that.description
            ))
            if len(that.description) > 0
            else None
        ),
        administration=(
            administrative_information_from_pb(
                that.administration
            )
            if that.HasField('administration')
            else None
        ),
        id=that.id,
        embedded_data_specifications=(
            list(map(
                embedded_data_specification_from_pb,
                that.embedded_data_specifications
            ))
            if len(that.embedded_data_specifications) > 0
            else None
        ),
        is_case_of=(
            list(map(
                reference_from_pb,
                that.is_case_of
            ))
            if len(that.is_case_of) > 0
            else None
        )
    )


# fmt: off
_REFERENCE_TYPES_FROM_PB_MAP = {
    types_pb.ReferenceTypes.Referencetypes_EXTERNAL_REFERENCE:
        types.ReferenceTypes.EXTERNAL_REFERENCE,
    types_pb.ReferenceTypes.Referencetypes_MODEL_REFERENCE:
        types.ReferenceTypes.MODEL_REFERENCE
}  # type: Mapping[types_pb.ReferenceTypes, types.ReferenceTypes]
# fmt: on


def reference_types_from_pb(
    that: types_pb.ReferenceTypes
) -> types.ReferenceTypes:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import reference_types_from_pb
    >>> reference_types_from_pb(
    ...     types_pb.ReferenceTypes.Referencetypes_EXTERNAL_REFERENCE
    ... )
    <ReferenceTypes.EXTERNAL_REFERENCE: 'ExternalReference'>
    """
    return _REFERENCE_TYPES_FROM_PB_MAP[that]


def reference_from_pb(
    that: types_pb.Reference
) -> types.Reference:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import reference_from_pb

        some_bytes = b'... serialized types_pb.Reference ...'
        reference_pb = types_pb.Reference()
        reference_pb.FromString(
            some_bytes
        )

        reference = reference_from_pb(
            reference_pb
        )
        # Do something with the reference...

    """
    return types.Reference(
        type=reference_types_from_pb(
            that.type
        ),
        referred_semantic_id=(
            reference_from_pb(
                that.referred_semantic_id
            )
            if that.HasField('referred_semantic_id')
            else None
        ),
        keys=list(map(
            key_from_pb,
            that.keys
        ))
    )


def key_from_pb(
    that: types_pb.Key
) -> types.Key:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import key_from_pb

        some_bytes = b'... serialized types_pb.Key ...'
        key_pb = types_pb.Key()
        key_pb.FromString(
            some_bytes
        )

        key = key_from_pb(
            key_pb
        )
        # Do something with the key...

    """
    return types.Key(
        type=key_types_from_pb(
            that.type
        ),
        value=that.value
    )


# fmt: off
_KEY_TYPES_FROM_PB_MAP = {
    types_pb.KeyTypes.Keytypes_ANNOTATED_RELATIONSHIP_ELEMENT:
        types.KeyTypes.ANNOTATED_RELATIONSHIP_ELEMENT,
    types_pb.KeyTypes.Keytypes_ASSET_ADMINISTRATION_SHELL:
        types.KeyTypes.ASSET_ADMINISTRATION_SHELL,
    types_pb.KeyTypes.Keytypes_BASIC_EVENT_ELEMENT:
        types.KeyTypes.BASIC_EVENT_ELEMENT,
    types_pb.KeyTypes.Keytypes_BLOB:
        types.KeyTypes.BLOB,
    types_pb.KeyTypes.Keytypes_CAPABILITY:
        types.KeyTypes.CAPABILITY,
    types_pb.KeyTypes.Keytypes_CONCEPT_DESCRIPTION:
        types.KeyTypes.CONCEPT_DESCRIPTION,
    types_pb.KeyTypes.Keytypes_DATA_ELEMENT:
        types.KeyTypes.DATA_ELEMENT,
    types_pb.KeyTypes.Keytypes_ENTITY:
        types.KeyTypes.ENTITY,
    types_pb.KeyTypes.Keytypes_EVENT_ELEMENT:
        types.KeyTypes.EVENT_ELEMENT,
    types_pb.KeyTypes.Keytypes_FILE:
        types.KeyTypes.FILE,
    types_pb.KeyTypes.Keytypes_FRAGMENT_REFERENCE:
        types.KeyTypes.FRAGMENT_REFERENCE,
    types_pb.KeyTypes.Keytypes_GLOBAL_REFERENCE:
        types.KeyTypes.GLOBAL_REFERENCE,
    types_pb.KeyTypes.Keytypes_IDENTIFIABLE:
        types.KeyTypes.IDENTIFIABLE,
    types_pb.KeyTypes.Keytypes_MULTI_LANGUAGE_PROPERTY:
        types.KeyTypes.MULTI_LANGUAGE_PROPERTY,
    types_pb.KeyTypes.Keytypes_OPERATION:
        types.KeyTypes.OPERATION,
    types_pb.KeyTypes.Keytypes_PROPERTY:
        types.KeyTypes.PROPERTY,
    types_pb.KeyTypes.Keytypes_RANGE:
        types.KeyTypes.RANGE,
    types_pb.KeyTypes.Keytypes_REFERABLE:
        types.KeyTypes.REFERABLE,
    types_pb.KeyTypes.Keytypes_REFERENCE_ELEMENT:
        types.KeyTypes.REFERENCE_ELEMENT,
    types_pb.KeyTypes.Keytypes_RELATIONSHIP_ELEMENT:
        types.KeyTypes.RELATIONSHIP_ELEMENT,
    types_pb.KeyTypes.Keytypes_SUBMODEL:
        types.KeyTypes.SUBMODEL,
    types_pb.KeyTypes.Keytypes_SUBMODEL_ELEMENT:
        types.KeyTypes.SUBMODEL_ELEMENT,
    types_pb.KeyTypes.Keytypes_SUBMODEL_ELEMENT_COLLECTION:
        types.KeyTypes.SUBMODEL_ELEMENT_COLLECTION,
    types_pb.KeyTypes.Keytypes_SUBMODEL_ELEMENT_LIST:
        types.KeyTypes.SUBMODEL_ELEMENT_LIST
}  # type: Mapping[types_pb.KeyTypes, types.KeyTypes]
# fmt: on


def key_types_from_pb(
    that: types_pb.KeyTypes
) -> types.KeyTypes:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import key_types_from_pb
    >>> key_types_from_pb(
    ...     types_pb.KeyTypes.Keytypes_ANNOTATED_RELATIONSHIP_ELEMENT
    ... )
    <KeyTypes.ANNOTATED_RELATIONSHIP_ELEMENT: 'AnnotatedRelationshipElement'>
    """
    return _KEY_TYPES_FROM_PB_MAP[that]


# fmt: off
_DATA_TYPE_DEF_XSD_FROM_PB_MAP = {
    types_pb.DataTypeDefXsd.Datatypedefxsd_ANY_URI:
        types.DataTypeDefXSD.ANY_URI,
    types_pb.DataTypeDefXsd.Datatypedefxsd_BASE_64_BINARY:
        types.DataTypeDefXSD.BASE_64_BINARY,
    types_pb.DataTypeDefXsd.Datatypedefxsd_BOOLEAN:
        types.DataTypeDefXSD.BOOLEAN,
    types_pb.DataTypeDefXsd.Datatypedefxsd_BYTE:
        types.DataTypeDefXSD.BYTE,
    types_pb.DataTypeDefXsd.Datatypedefxsd_DATE:
        types.DataTypeDefXSD.DATE,
    types_pb.DataTypeDefXsd.Datatypedefxsd_DATE_TIME:
        types.DataTypeDefXSD.DATE_TIME,
    types_pb.DataTypeDefXsd.Datatypedefxsd_DECIMAL:
        types.DataTypeDefXSD.DECIMAL,
    types_pb.DataTypeDefXsd.Datatypedefxsd_DOUBLE:
        types.DataTypeDefXSD.DOUBLE,
    types_pb.DataTypeDefXsd.Datatypedefxsd_DURATION:
        types.DataTypeDefXSD.DURATION,
    types_pb.DataTypeDefXsd.Datatypedefxsd_FLOAT:
        types.DataTypeDefXSD.FLOAT,
    types_pb.DataTypeDefXsd.Datatypedefxsd_G_DAY:
        types.DataTypeDefXSD.G_DAY,
    types_pb.DataTypeDefXsd.Datatypedefxsd_G_MONTH:
        types.DataTypeDefXSD.G_MONTH,
    types_pb.DataTypeDefXsd.Datatypedefxsd_G_MONTH_DAY:
        types.DataTypeDefXSD.G_MONTH_DAY,
    types_pb.DataTypeDefXsd.Datatypedefxsd_G_YEAR:
        types.DataTypeDefXSD.G_YEAR,
    types_pb.DataTypeDefXsd.Datatypedefxsd_G_YEAR_MONTH:
        types.DataTypeDefXSD.G_YEAR_MONTH,
    types_pb.DataTypeDefXsd.Datatypedefxsd_HEX_BINARY:
        types.DataTypeDefXSD.HEX_BINARY,
    types_pb.DataTypeDefXsd.Datatypedefxsd_INT:
        types.DataTypeDefXSD.INT,
    types_pb.DataTypeDefXsd.Datatypedefxsd_INTEGER:
        types.DataTypeDefXSD.INTEGER,
    types_pb.DataTypeDefXsd.Datatypedefxsd_LONG:
        types.DataTypeDefXSD.LONG,
    types_pb.DataTypeDefXsd.Datatypedefxsd_NEGATIVE_INTEGER:
        types.DataTypeDefXSD.NEGATIVE_INTEGER,
    types_pb.DataTypeDefXsd.Datatypedefxsd_NON_NEGATIVE_INTEGER:
        types.DataTypeDefXSD.NON_NEGATIVE_INTEGER,
    types_pb.DataTypeDefXsd.Datatypedefxsd_NON_POSITIVE_INTEGER:
        types.DataTypeDefXSD.NON_POSITIVE_INTEGER,
    types_pb.DataTypeDefXsd.Datatypedefxsd_POSITIVE_INTEGER:
        types.DataTypeDefXSD.POSITIVE_INTEGER,
    types_pb.DataTypeDefXsd.Datatypedefxsd_SHORT:
        types.DataTypeDefXSD.SHORT,
    types_pb.DataTypeDefXsd.Datatypedefxsd_STRING:
        types.DataTypeDefXSD.STRING,
    types_pb.DataTypeDefXsd.Datatypedefxsd_TIME:
        types.DataTypeDefXSD.TIME,
    types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_BYTE:
        types.DataTypeDefXSD.UNSIGNED_BYTE,
    types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_INT:
        types.DataTypeDefXSD.UNSIGNED_INT,
    types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_LONG:
        types.DataTypeDefXSD.UNSIGNED_LONG,
    types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_SHORT:
        types.DataTypeDefXSD.UNSIGNED_SHORT
}  # type: Mapping[types_pb.DataTypeDefXsd, types.DataTypeDefXSD]
# fmt: on


def data_type_def_xsd_from_pb(
    that: types_pb.DataTypeDefXsd
) -> types.DataTypeDefXSD:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import data_type_def_xsd_from_pb
    >>> data_type_def_xsd_from_pb(
    ...     types_pb.DataTypeDefXsd.Datatypedefxsd_ANY_URI
    ... )
    <DataTypeDefXSD.ANY_URI: 'xs:anyURI'>
    """
    return _DATA_TYPE_DEF_XSD_FROM_PB_MAP[that]


# fmt: off
_ABSTRACT_LANG_STRING_FROM_PB_CHOICE_MAP = {
    'lang_string_definition_type_iec_61360':
        lambda that: lang_string_definition_type_iec_61360_from_pb(
            that.lang_string_definition_type_iec_61360
        ),
    'lang_string_name_type':
        lambda that: lang_string_name_type_from_pb(
            that.lang_string_name_type
        ),
    'lang_string_preferred_name_type_iec_61360':
        lambda that: lang_string_preferred_name_type_iec_61360_from_pb(
            that.lang_string_preferred_name_type_iec_61360
        ),
    'lang_string_short_name_type_iec_61360':
        lambda that: lang_string_short_name_type_iec_61360_from_pb(
            that.lang_string_short_name_type_iec_61360
        ),
    'lang_string_text_type':
        lambda that: lang_string_text_type_from_pb(
            that.lang_string_text_type
        )
}
# fmt: on


def abstract_lang_string_from_pb_choice(
    that: types_pb.AbstractLangString_choice
) -> types.AbstractLangString:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import abstract_lang_string_from_pb_choice

        some_bytes = b'... serialized types_pb.AbstractLangString_choice ...'
        abstract_lang_string_choice_pb = types_pb.AbstractLangString_choice()
        abstract_lang_string_choice_pb.FromString(
            some_bytes
        )

        abstract_lang_string = abstract_lang_string_from_pb_choice(
            abstract_lang_string_choice_pb
        )
        # Do something with the abstract_lang_string...
    """
    get_concrete_instance_from_pb = (
        _ABSTRACT_LANG_STRING_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.AbstractLangString)
    return result


def lang_string_name_type_from_pb(
    that: types_pb.LangStringNameType
) -> types.LangStringNameType:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_name_type_from_pb

        some_bytes = b'... serialized types_pb.LangStringNameType ...'
        lang_string_name_type_pb = types_pb.LangStringNameType()
        lang_string_name_type_pb.FromString(
            some_bytes
        )

        lang_string_name_type = lang_string_name_type_from_pb(
            lang_string_name_type_pb
        )
        # Do something with the lang_string_name_type...

    """
    return types.LangStringNameType(
        language=that.language,
        text=that.text
    )


def lang_string_text_type_from_pb(
    that: types_pb.LangStringTextType
) -> types.LangStringTextType:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_text_type_from_pb

        some_bytes = b'... serialized types_pb.LangStringTextType ...'
        lang_string_text_type_pb = types_pb.LangStringTextType()
        lang_string_text_type_pb.FromString(
            some_bytes
        )

        lang_string_text_type = lang_string_text_type_from_pb(
            lang_string_text_type_pb
        )
        # Do something with the lang_string_text_type...

    """
    return types.LangStringTextType(
        language=that.language,
        text=that.text
    )


def environment_from_pb(
    that: types_pb.Environment
) -> types.Environment:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import environment_from_pb

        some_bytes = b'... serialized types_pb.Environment ...'
        environment_pb = types_pb.Environment()
        environment_pb.FromString(
            some_bytes
        )

        environment = environment_from_pb(
            environment_pb
        )
        # Do something with the environment...

    """
    return types.Environment(
        asset_administration_shells=(
            list(map(
                asset_administration_shell_from_pb,
                that.asset_administration_shells
            ))
            if len(that.asset_administration_shells) > 0
            else None
        ),
        submodels=(
            list(map(
                submodel_from_pb,
                that.submodels
            ))
            if len(that.submodels) > 0
            else None
        ),
        concept_descriptions=(
            list(map(
                concept_description_from_pb,
                that.concept_descriptions
            ))
            if len(that.concept_descriptions) > 0
            else None
        )
    )


# fmt: off
_DATA_SPECIFICATION_CONTENT_FROM_PB_CHOICE_MAP = {
    'data_specification_iec_61360':
        lambda that: data_specification_iec_61360_from_pb(
            that.data_specification_iec_61360
        )
}
# fmt: on


def data_specification_content_from_pb_choice(
    that: types_pb.DataSpecificationContent_choice
) -> types.DataSpecificationContent:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import data_specification_content_from_pb_choice

        some_bytes = b'... serialized types_pb.DataSpecificationContent_choice ...'
        data_specification_content_choice_pb = types_pb.DataSpecificationContent_choice()
        data_specification_content_choice_pb.FromString(
            some_bytes
        )

        data_specification_content = data_specification_content_from_pb_choice(
            data_specification_content_choice_pb
        )
        # Do something with the data_specification_content...
    """
    get_concrete_instance_from_pb = (
        _DATA_SPECIFICATION_CONTENT_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.DataSpecificationContent)
    return result


def embedded_data_specification_from_pb(
    that: types_pb.EmbeddedDataSpecification
) -> types.EmbeddedDataSpecification:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import embedded_data_specification_from_pb

        some_bytes = b'... serialized types_pb.EmbeddedDataSpecification ...'
        embedded_data_specification_pb = types_pb.EmbeddedDataSpecification()
        embedded_data_specification_pb.FromString(
            some_bytes
        )

        embedded_data_specification = embedded_data_specification_from_pb(
            embedded_data_specification_pb
        )
        # Do something with the embedded_data_specification...

    """
    return types.EmbeddedDataSpecification(
        data_specification=reference_from_pb(
            that.data_specification
        ),
        data_specification_content=data_specification_content_from_pb_choice(
            that.data_specification_content
        )
    )


# fmt: off
_DATA_TYPE_IEC_61360_FROM_PB_MAP = {
    types_pb.DataTypeIec61360.Datatypeiec61360_DATE:
        types.DataTypeIEC61360.DATE,
    types_pb.DataTypeIec61360.Datatypeiec61360_STRING:
        types.DataTypeIEC61360.STRING,
    types_pb.DataTypeIec61360.Datatypeiec61360_STRING_TRANSLATABLE:
        types.DataTypeIEC61360.STRING_TRANSLATABLE,
    types_pb.DataTypeIec61360.Datatypeiec61360_INTEGER_MEASURE:
        types.DataTypeIEC61360.INTEGER_MEASURE,
    types_pb.DataTypeIec61360.Datatypeiec61360_INTEGER_COUNT:
        types.DataTypeIEC61360.INTEGER_COUNT,
    types_pb.DataTypeIec61360.Datatypeiec61360_INTEGER_CURRENCY:
        types.DataTypeIEC61360.INTEGER_CURRENCY,
    types_pb.DataTypeIec61360.Datatypeiec61360_REAL_MEASURE:
        types.DataTypeIEC61360.REAL_MEASURE,
    types_pb.DataTypeIec61360.Datatypeiec61360_REAL_COUNT:
        types.DataTypeIEC61360.REAL_COUNT,
    types_pb.DataTypeIec61360.Datatypeiec61360_REAL_CURRENCY:
        types.DataTypeIEC61360.REAL_CURRENCY,
    types_pb.DataTypeIec61360.Datatypeiec61360_BOOLEAN:
        types.DataTypeIEC61360.BOOLEAN,
    types_pb.DataTypeIec61360.Datatypeiec61360_IRI:
        types.DataTypeIEC61360.IRI,
    types_pb.DataTypeIec61360.Datatypeiec61360_IRDI:
        types.DataTypeIEC61360.IRDI,
    types_pb.DataTypeIec61360.Datatypeiec61360_RATIONAL:
        types.DataTypeIEC61360.RATIONAL,
    types_pb.DataTypeIec61360.Datatypeiec61360_RATIONAL_MEASURE:
        types.DataTypeIEC61360.RATIONAL_MEASURE,
    types_pb.DataTypeIec61360.Datatypeiec61360_TIME:
        types.DataTypeIEC61360.TIME,
    types_pb.DataTypeIec61360.Datatypeiec61360_TIMESTAMP:
        types.DataTypeIEC61360.TIMESTAMP,
    types_pb.DataTypeIec61360.Datatypeiec61360_FILE:
        types.DataTypeIEC61360.FILE,
    types_pb.DataTypeIec61360.Datatypeiec61360_HTML:
        types.DataTypeIEC61360.HTML,
    types_pb.DataTypeIec61360.Datatypeiec61360_BLOB:
        types.DataTypeIEC61360.BLOB
}  # type: Mapping[types_pb.DataTypeIec61360, types.DataTypeIEC61360]
# fmt: on


def data_type_iec_61360_from_pb(
    that: types_pb.DataTypeIec61360
) -> types.DataTypeIEC61360:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import data_type_iec_61360_from_pb
    >>> data_type_iec_61360_from_pb(
    ...     types_pb.DataTypeIec61360.Datatypeiec61360_DATE
    ... )
    <DataTypeIEC61360.DATE: 'DATE'>
    """
    return _DATA_TYPE_IEC_61360_FROM_PB_MAP[that]


def level_type_from_pb(
    that: types_pb.LevelType
) -> types.LevelType:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import level_type_from_pb

        some_bytes = b'... serialized types_pb.LevelType ...'
        level_type_pb = types_pb.LevelType()
        level_type_pb.FromString(
            some_bytes
        )

        level_type = level_type_from_pb(
            level_type_pb
        )
        # Do something with the level_type...

    """
    return types.LevelType(
        min=that.min,
        nom=that.nom,
        typ=that.typ,
        max=that.max
    )


def value_reference_pair_from_pb(
    that: types_pb.ValueReferencePair
) -> types.ValueReferencePair:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import value_reference_pair_from_pb

        some_bytes = b'... serialized types_pb.ValueReferencePair ...'
        value_reference_pair_pb = types_pb.ValueReferencePair()
        value_reference_pair_pb.FromString(
            some_bytes
        )

        value_reference_pair = value_reference_pair_from_pb(
            value_reference_pair_pb
        )
        # Do something with the value_reference_pair...

    """
    return types.ValueReferencePair(
        value=that.value,
        value_id=reference_from_pb(
            that.value_id
        )
    )


def value_list_from_pb(
    that: types_pb.ValueList
) -> types.ValueList:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import value_list_from_pb

        some_bytes = b'... serialized types_pb.ValueList ...'
        value_list_pb = types_pb.ValueList()
        value_list_pb.FromString(
            some_bytes
        )

        value_list = value_list_from_pb(
            value_list_pb
        )
        # Do something with the value_list...

    """
    return types.ValueList(
        value_reference_pairs=list(map(
            value_reference_pair_from_pb,
            that.value_reference_pairs
        ))
    )


def lang_string_preferred_name_type_iec_61360_from_pb(
    that: types_pb.LangStringPreferredNameTypeIec61360
) -> types.LangStringPreferredNameTypeIEC61360:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_preferred_name_type_iec_61360_from_pb

        some_bytes = b'... serialized types_pb.LangStringPreferredNameTypeIec61360 ...'
        lang_string_preferred_name_type_iec_61360_pb = types_pb.LangStringPreferredNameTypeIec61360()
        lang_string_preferred_name_type_iec_61360_pb.FromString(
            some_bytes
        )

        lang_string_preferred_name_type_iec_61360 = lang_string_preferred_name_type_iec_61360_from_pb(
            lang_string_preferred_name_type_iec_61360_pb
        )
        # Do something with the lang_string_preferred_name_type_iec_61360...

    """
    return types.LangStringPreferredNameTypeIEC61360(
        language=that.language,
        text=that.text
    )


def lang_string_short_name_type_iec_61360_from_pb(
    that: types_pb.LangStringShortNameTypeIec61360
) -> types.LangStringShortNameTypeIEC61360:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_short_name_type_iec_61360_from_pb

        some_bytes = b'... serialized types_pb.LangStringShortNameTypeIec61360 ...'
        lang_string_short_name_type_iec_61360_pb = types_pb.LangStringShortNameTypeIec61360()
        lang_string_short_name_type_iec_61360_pb.FromString(
            some_bytes
        )

        lang_string_short_name_type_iec_61360 = lang_string_short_name_type_iec_61360_from_pb(
            lang_string_short_name_type_iec_61360_pb
        )
        # Do something with the lang_string_short_name_type_iec_61360...

    """
    return types.LangStringShortNameTypeIEC61360(
        language=that.language,
        text=that.text
    )


def lang_string_definition_type_iec_61360_from_pb(
    that: types_pb.LangStringDefinitionTypeIec61360
) -> types.LangStringDefinitionTypeIEC61360:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_definition_type_iec_61360_from_pb

        some_bytes = b'... serialized types_pb.LangStringDefinitionTypeIec61360 ...'
        lang_string_definition_type_iec_61360_pb = types_pb.LangStringDefinitionTypeIec61360()
        lang_string_definition_type_iec_61360_pb.FromString(
            some_bytes
        )

        lang_string_definition_type_iec_61360 = lang_string_definition_type_iec_61360_from_pb(
            lang_string_definition_type_iec_61360_pb
        )
        # Do something with the lang_string_definition_type_iec_61360...

    """
    return types.LangStringDefinitionTypeIEC61360(
        language=that.language,
        text=that.text
    )


def data_specification_iec_61360_from_pb(
    that: types_pb.DataSpecificationIec61360
) -> types.DataSpecificationIEC61360:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import data_specification_iec_61360_from_pb

        some_bytes = b'... serialized types_pb.DataSpecificationIec61360 ...'
        data_specification_iec_61360_pb = types_pb.DataSpecificationIec61360()
        data_specification_iec_61360_pb.FromString(
            some_bytes
        )

        data_specification_iec_61360 = data_specification_iec_61360_from_pb(
            data_specification_iec_61360_pb
        )
        # Do something with the data_specification_iec_61360...

    """
    return types.DataSpecificationIEC61360(
        preferred_name=list(map(
            lang_string_preferred_name_type_iec_61360_from_pb,
            that.preferred_name
        )),
        short_name=(
            list(map(
                lang_string_short_name_type_iec_61360_from_pb,
                that.short_name
            ))
            if len(that.short_name) > 0
            else None
        ),
        unit=(
            that.unit
            if that.HasField('unit')
            else None
        ),
        unit_id=(
            reference_from_pb(
                that.unit_id
            )
            if that.HasField('unit_id')
            else None
        ),
        source_of_definition=(
            that.source_of_definition
            if that.HasField('source_of_definition')
            else None
        ),
        symbol=(
            that.symbol
            if that.HasField('symbol')
            else None
        ),
        data_type=(
            data_type_iec_61360_from_pb(
                that.data_type
            )
            if that.HasField('data_type')
            else None
        ),
        definition=(
            list(map(
                lang_string_definition_type_iec_61360_from_pb,
                that.definition
            ))
            if len(that.definition) > 0
            else None
        ),
        value_format=(
            that.value_format
            if that.HasField('value_format')
            else None
        ),
        value_list=(
            value_list_from_pb(
                that.value_list
            )
            if that.HasField('value_list')
            else None
        ),
        value=(
            that.value
            if that.HasField('value')
            else None
        ),
        level_type=(
            level_type_from_pb(
                that.level_type
            )
            if that.HasField('level_type')
            else None
        )
    )


# fmt: off
_FROM_PB_MAP = {
    types_pb.HasSemantics_choice:
        has_semantics_from_pb_choice,
    types_pb.Extension:
        extension_from_pb,
    types_pb.HasExtensions_choice:
        has_extensions_from_pb_choice,
    types_pb.Referable_choice:
        referable_from_pb_choice,
    types_pb.Identifiable_choice:
        identifiable_from_pb_choice,
    types_pb.HasKind_choice:
        has_kind_from_pb_choice,
    types_pb.HasDataSpecification_choice:
        has_data_specification_from_pb_choice,
    types_pb.AdministrativeInformation:
        administrative_information_from_pb,
    types_pb.Qualifiable_choice:
        qualifiable_from_pb_choice,
    types_pb.Qualifier:
        qualifier_from_pb,
    types_pb.AssetAdministrationShell:
        asset_administration_shell_from_pb,
    types_pb.AssetInformation:
        asset_information_from_pb,
    types_pb.Resource:
        resource_from_pb,
    types_pb.SpecificAssetId:
        specific_asset_id_from_pb,
    types_pb.Submodel:
        submodel_from_pb,
    types_pb.SubmodelElement_choice:
        submodel_element_from_pb_choice,
    types_pb.RelationshipElement_choice:
        relationship_element_from_pb_choice,
    types_pb.SubmodelElementList:
        submodel_element_list_from_pb,
    types_pb.SubmodelElementCollection:
        submodel_element_collection_from_pb,
    types_pb.DataElement_choice:
        data_element_from_pb_choice,
    types_pb.Property:
        property_from_pb,
    types_pb.MultiLanguageProperty:
        multi_language_property_from_pb,
    types_pb.Range:
        range_from_pb,
    types_pb.ReferenceElement:
        reference_element_from_pb,
    types_pb.Blob:
        blob_from_pb,
    types_pb.File:
        file_from_pb,
    types_pb.AnnotatedRelationshipElement:
        annotated_relationship_element_from_pb,
    types_pb.Entity:
        entity_from_pb,
    types_pb.EventPayload:
        event_payload_from_pb,
    types_pb.EventElement_choice:
        event_element_from_pb_choice,
    types_pb.BasicEventElement:
        basic_event_element_from_pb,
    types_pb.Operation:
        operation_from_pb,
    types_pb.OperationVariable:
        operation_variable_from_pb,
    types_pb.Capability:
        capability_from_pb,
    types_pb.ConceptDescription:
        concept_description_from_pb,
    types_pb.Reference:
        reference_from_pb,
    types_pb.Key:
        key_from_pb,
    types_pb.AbstractLangString_choice:
        abstract_lang_string_from_pb_choice,
    types_pb.LangStringNameType:
        lang_string_name_type_from_pb,
    types_pb.LangStringTextType:
        lang_string_text_type_from_pb,
    types_pb.Environment:
        environment_from_pb,
    types_pb.DataSpecificationContent_choice:
        data_specification_content_from_pb_choice,
    types_pb.EmbeddedDataSpecification:
        embedded_data_specification_from_pb,
    types_pb.LevelType:
        level_type_from_pb,
    types_pb.ValueReferencePair:
        value_reference_pair_from_pb,
    types_pb.ValueList:
        value_list_from_pb,
    types_pb.LangStringPreferredNameTypeIec61360:
        lang_string_preferred_name_type_iec_61360_from_pb,
    types_pb.LangStringShortNameTypeIec61360:
        lang_string_short_name_type_iec_61360_from_pb,
    types_pb.LangStringDefinitionTypeIec61360:
        lang_string_definition_type_iec_61360_from_pb,
    types_pb.DataSpecificationIec61360:
        data_specification_iec_61360_from_pb
}
# fmt: on


def from_pb(
    that: google.protobuf.message.Message
) -> types.Class:
    """
    Parse ``that`` Protocol Buffer into a model instance.

    The concrete parsing is determined based on the runtime type of ``that``
    Protocol Buffer. It is assumed that ``that`` is an instance of a message
    coming from the Protocol Buffer definitions corresponding to the meta-model.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import from_pb

        some_bytes = b'... serialized types_pb.Extension ...'
        instance_pb = types_pb.Extension()
        instance_pb.FromString(
            some_bytes
        )

        instance = from_pb(
            instance_pb
        )
        # Do something with the instance...
    """
    from_pb_func = _FROM_PB_MAP.get(that.__class__, None)

    if from_pb_func is None:
        raise ValueError(
            f"We do not know how to parse the protocol buffer "
            f"of type {that.__class__} into a model instance."
        )

    result = from_pb_func(that)  # type: ignore
    assert isinstance(result, types.Class)
    return result


# endregion From Protocol Buffers


# region To Protocol Buffers


T = TypeVar("T")


class _PartialVisitorWithContext(types.AbstractVisitorWithContext[T]):
    """
    Visit instances in context with double-dispatch.

    This class is meant to be inherited from. If you do not override a method,
    it will raise an exception. This is a partial visitor, meaning that some
    visits are unexpected by design.
    """
    # pylint: disable=missing-docstring

    def visit_extension_with_context(
        self,
        that: types.Extension,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_administrative_information_with_context(
        self,
        that: types.AdministrativeInformation,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_qualifier_with_context(
        self,
        that: types.Qualifier,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_asset_administration_shell_with_context(
        self,
        that: types.AssetAdministrationShell,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_asset_information_with_context(
        self,
        that: types.AssetInformation,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_resource_with_context(
        self,
        that: types.Resource,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_specific_asset_id_with_context(
        self,
        that: types.SpecificAssetID,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_property_with_context(
        self,
        that: types.Property,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_range_with_context(
        self,
        that: types.Range,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_file_with_context(
        self,
        that: types.File,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_event_payload_with_context(
        self,
        that: types.EventPayload,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_operation_variable_with_context(
        self,
        that: types.OperationVariable,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_concept_description_with_context(
        self,
        that: types.ConceptDescription,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_reference_with_context(
        self,
        that: types.Reference,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_key_with_context(
        self,
        that: types.Key,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_lang_string_name_type_with_context(
        self,
        that: types.LangStringNameType,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_lang_string_text_type_with_context(
        self,
        that: types.LangStringTextType,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_environment_with_context(
        self,
        that: types.Environment,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_embedded_data_specification_with_context(
        self,
        that: types.EmbeddedDataSpecification,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_level_type_with_context(
        self,
        that: types.LevelType,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_value_reference_pair_with_context(
        self,
        that: types.ValueReferencePair,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_value_list_with_context(
        self,
        that: types.ValueList,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_lang_string_preferred_name_type_iec_61360_with_context(
        self,
        that: types.LangStringPreferredNameTypeIEC61360,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_lang_string_short_name_type_iec_61360_with_context(
        self,
        that: types.LangStringShortNameTypeIEC61360,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_lang_string_definition_type_iec_61360_with_context(
        self,
        that: types.LangStringDefinitionTypeIEC61360,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_data_specification_iec_61360_with_context(
        self,
        that: types.DataSpecificationIEC61360,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")


class _HasSemanticsToPbChoice(
    _PartialVisitorWithContext[
        types_pb.HasSemantics_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.capability``
        according to ``that`` instance.
        """
        capability_to_pb(
            that,
            context.capability
        )

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.entity``
        according to ``that`` instance.
        """
        entity_to_pb(
            that,
            context.entity
        )

    def visit_extension_with_context(
        self,
        that: types.Extension,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.extension``
        according to ``that`` instance.
        """
        extension_to_pb(
            that,
            context.extension
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.operation``
        according to ``that`` instance.
        """
        operation_to_pb(
            that,
            context.operation
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_qualifier_with_context(
        self,
        that: types.Qualifier,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.qualifier``
        according to ``that`` instance.
        """
        qualifier_to_pb(
            that,
            context.qualifier
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )

    def visit_specific_asset_id_with_context(
        self,
        that: types.SpecificAssetID,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.specific_asset_id``
        according to ``that`` instance.
        """
        specific_asset_id_to_pb(
            that,
            context.specific_asset_id
        )

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_collection``
        according to ``that`` instance.
        """
        submodel_element_collection_to_pb(
            that,
            context.submodel_element_collection
        )

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: types_pb.HasSemantics_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_list``
        according to ``that`` instance.
        """
        submodel_element_list_to_pb(
            that,
            context.submodel_element_list
        )


_HAS_SEMANTICS_TO_PB_CHOICE = _HasSemanticsToPbChoice()


def has_semantics_to_pb_choice(
    that: types.HasSemantics,
    target: types_pb.HasSemantics_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_semantics_to_pb_choice

        has_semantics = types.RelationshipElement(
            ... # some constructor arguments
        )

        has_semantics_choice_pb = types_pb.HasSemantics_choice()
        has_semantics_to_pb_choice(
            has_semantics,
            has_semantics_choice_pb
        )

        some_bytes = has_semantics_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _HAS_SEMANTICS_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def extension_to_pb(
    that: types.Extension,
    target: types_pb.Extension
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import extension_to_pb

        extension = types.Extension(
            ... # some constructor arguments
        )

        extension_pb = types_pb.Extension()
        extension_to_pb(
            extension,
            extension_pb
        )

        some_bytes = extension_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    target.name = that.name

    if that.value_type is not None:
        target.value_type = data_type_def_xsd_to_pb(
            that.value_type
        )

    if that.value is not None:
        target.value = that.value

    if that.refers_to is not None:
        for refers_to_item in that.refers_to:
            refers_to_item_pb = target.refers_to.add()
            reference_to_pb(
                refers_to_item,
                refers_to_item_pb)


class _HasExtensionsToPbChoice(
    _PartialVisitorWithContext[
        types_pb.HasExtensions_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )

    def visit_asset_administration_shell_with_context(
        self,
        that: types.AssetAdministrationShell,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.asset_administration_shell``
        according to ``that`` instance.
        """
        asset_administration_shell_to_pb(
            that,
            context.asset_administration_shell
        )

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.capability``
        according to ``that`` instance.
        """
        capability_to_pb(
            that,
            context.capability
        )

    def visit_concept_description_with_context(
        self,
        that: types.ConceptDescription,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.concept_description``
        according to ``that`` instance.
        """
        concept_description_to_pb(
            that,
            context.concept_description
        )

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.entity``
        according to ``that`` instance.
        """
        entity_to_pb(
            that,
            context.entity
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.operation``
        according to ``that`` instance.
        """
        operation_to_pb(
            that,
            context.operation
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_collection``
        according to ``that`` instance.
        """
        submodel_element_collection_to_pb(
            that,
            context.submodel_element_collection
        )

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: types_pb.HasExtensions_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_list``
        according to ``that`` instance.
        """
        submodel_element_list_to_pb(
            that,
            context.submodel_element_list
        )


_HAS_EXTENSIONS_TO_PB_CHOICE = _HasExtensionsToPbChoice()


def has_extensions_to_pb_choice(
    that: types.HasExtensions,
    target: types_pb.HasExtensions_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_extensions_to_pb_choice

        has_extensions = types.RelationshipElement(
            ... # some constructor arguments
        )

        has_extensions_choice_pb = types_pb.HasExtensions_choice()
        has_extensions_to_pb_choice(
            has_extensions,
            has_extensions_choice_pb
        )

        some_bytes = has_extensions_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _HAS_EXTENSIONS_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


class _ReferableToPbChoice(
    _PartialVisitorWithContext[
        types_pb.Referable_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )

    def visit_asset_administration_shell_with_context(
        self,
        that: types.AssetAdministrationShell,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.asset_administration_shell``
        according to ``that`` instance.
        """
        asset_administration_shell_to_pb(
            that,
            context.asset_administration_shell
        )

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.capability``
        according to ``that`` instance.
        """
        capability_to_pb(
            that,
            context.capability
        )

    def visit_concept_description_with_context(
        self,
        that: types.ConceptDescription,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.concept_description``
        according to ``that`` instance.
        """
        concept_description_to_pb(
            that,
            context.concept_description
        )

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.entity``
        according to ``that`` instance.
        """
        entity_to_pb(
            that,
            context.entity
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.operation``
        according to ``that`` instance.
        """
        operation_to_pb(
            that,
            context.operation
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_collection``
        according to ``that`` instance.
        """
        submodel_element_collection_to_pb(
            that,
            context.submodel_element_collection
        )

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: types_pb.Referable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_list``
        according to ``that`` instance.
        """
        submodel_element_list_to_pb(
            that,
            context.submodel_element_list
        )


_REFERABLE_TO_PB_CHOICE = _ReferableToPbChoice()


def referable_to_pb_choice(
    that: types.Referable,
    target: types_pb.Referable_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import referable_to_pb_choice

        referable = types.RelationshipElement(
            ... # some constructor arguments
        )

        referable_choice_pb = types_pb.Referable_choice()
        referable_to_pb_choice(
            referable,
            referable_choice_pb
        )

        some_bytes = referable_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _REFERABLE_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


class _IdentifiableToPbChoice(
    _PartialVisitorWithContext[
        types_pb.Identifiable_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_asset_administration_shell_with_context(
        self,
        that: types.AssetAdministrationShell,
        context: types_pb.Identifiable_choice
    ) -> None:
        """
        Set the fields of ``context.asset_administration_shell``
        according to ``that`` instance.
        """
        asset_administration_shell_to_pb(
            that,
            context.asset_administration_shell
        )

    def visit_concept_description_with_context(
        self,
        that: types.ConceptDescription,
        context: types_pb.Identifiable_choice
    ) -> None:
        """
        Set the fields of ``context.concept_description``
        according to ``that`` instance.
        """
        concept_description_to_pb(
            that,
            context.concept_description
        )

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.Identifiable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )


_IDENTIFIABLE_TO_PB_CHOICE = _IdentifiableToPbChoice()


def identifiable_to_pb_choice(
    that: types.Identifiable,
    target: types_pb.Identifiable_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import identifiable_to_pb_choice

        identifiable = types.AssetAdministrationShell(
            ... # some constructor arguments
        )

        identifiable_choice_pb = types_pb.Identifiable_choice()
        identifiable_to_pb_choice(
            identifiable,
            identifiable_choice_pb
        )

        some_bytes = identifiable_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _IDENTIFIABLE_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


# fmt: off
_MODELLING_KIND_TO_PB_MAP = {
    types.ModellingKind.TEMPLATE:
        types_pb.ModellingKind.Modellingkind_TEMPLATE,
    types.ModellingKind.INSTANCE:
        types_pb.ModellingKind.Modellingkind_INSTANCE
}  # type: Mapping[types.ModellingKind, types_pb.ModellingKind]
# fmt: on


def modelling_kind_to_pb(
    that: types.ModellingKind
) -> types_pb.ModellingKind:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import modelling_kind_to_pb
    >>> import aas_core3.types as types
    >>> modelling_kind_to_pb(
    ...     types.ModellingKind.TEMPLATE
    ... )
    1
    """
    return _MODELLING_KIND_TO_PB_MAP[that]


class _HasKindToPbChoice(
    _PartialVisitorWithContext[
        types_pb.HasKind_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.HasKind_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )


_HAS_KIND_TO_PB_CHOICE = _HasKindToPbChoice()


def has_kind_to_pb_choice(
    that: types.HasKind,
    target: types_pb.HasKind_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_kind_to_pb_choice

        has_kind = types.Submodel(
            ... # some constructor arguments
        )

        has_kind_choice_pb = types_pb.HasKind_choice()
        has_kind_to_pb_choice(
            has_kind,
            has_kind_choice_pb
        )

        some_bytes = has_kind_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _HAS_KIND_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


class _HasDataSpecificationToPbChoice(
    _PartialVisitorWithContext[
        types_pb.HasDataSpecification_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_administrative_information_with_context(
        self,
        that: types.AdministrativeInformation,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.administrative_information``
        according to ``that`` instance.
        """
        administrative_information_to_pb(
            that,
            context.administrative_information
        )

    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )

    def visit_asset_administration_shell_with_context(
        self,
        that: types.AssetAdministrationShell,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.asset_administration_shell``
        according to ``that`` instance.
        """
        asset_administration_shell_to_pb(
            that,
            context.asset_administration_shell
        )

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.capability``
        according to ``that`` instance.
        """
        capability_to_pb(
            that,
            context.capability
        )

    def visit_concept_description_with_context(
        self,
        that: types.ConceptDescription,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.concept_description``
        according to ``that`` instance.
        """
        concept_description_to_pb(
            that,
            context.concept_description
        )

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.entity``
        according to ``that`` instance.
        """
        entity_to_pb(
            that,
            context.entity
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.operation``
        according to ``that`` instance.
        """
        operation_to_pb(
            that,
            context.operation
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_collection``
        according to ``that`` instance.
        """
        submodel_element_collection_to_pb(
            that,
            context.submodel_element_collection
        )

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: types_pb.HasDataSpecification_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_list``
        according to ``that`` instance.
        """
        submodel_element_list_to_pb(
            that,
            context.submodel_element_list
        )


_HAS_DATA_SPECIFICATION_TO_PB_CHOICE = _HasDataSpecificationToPbChoice()


def has_data_specification_to_pb_choice(
    that: types.HasDataSpecification,
    target: types_pb.HasDataSpecification_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import has_data_specification_to_pb_choice

        has_data_specification = types.AdministrativeInformation(
            ... # some constructor arguments
        )

        has_data_specification_choice_pb = types_pb.HasDataSpecification_choice()
        has_data_specification_to_pb_choice(
            has_data_specification,
            has_data_specification_choice_pb
        )

        some_bytes = has_data_specification_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _HAS_DATA_SPECIFICATION_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def administrative_information_to_pb(
    that: types.AdministrativeInformation,
    target: types_pb.AdministrativeInformation
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import administrative_information_to_pb

        administrative_information = types.AdministrativeInformation(
            ... # some constructor arguments
        )

        administrative_information_pb = types_pb.AdministrativeInformation()
        administrative_information_to_pb(
            administrative_information,
            administrative_information_pb
        )

        some_bytes = administrative_information_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.version is not None:
        target.version = that.version

    if that.revision is not None:
        target.revision = that.revision

    if that.creator is not None:
        # We clear so that the field is set even if all the properties are None.
        target.creator.Clear()

        reference_to_pb(
            that.creator,
            target.creator
        )

    if that.template_id is not None:
        target.template_id = that.template_id


class _QualifiableToPbChoice(
    _PartialVisitorWithContext[
        types_pb.Qualifiable_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.capability``
        according to ``that`` instance.
        """
        capability_to_pb(
            that,
            context.capability
        )

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.entity``
        according to ``that`` instance.
        """
        entity_to_pb(
            that,
            context.entity
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.operation``
        according to ``that`` instance.
        """
        operation_to_pb(
            that,
            context.operation
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )

    def visit_submodel_with_context(
        self,
        that: types.Submodel,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel``
        according to ``that`` instance.
        """
        submodel_to_pb(
            that,
            context.submodel
        )

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_collection``
        according to ``that`` instance.
        """
        submodel_element_collection_to_pb(
            that,
            context.submodel_element_collection
        )

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: types_pb.Qualifiable_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_list``
        according to ``that`` instance.
        """
        submodel_element_list_to_pb(
            that,
            context.submodel_element_list
        )


_QUALIFIABLE_TO_PB_CHOICE = _QualifiableToPbChoice()


def qualifiable_to_pb_choice(
    that: types.Qualifiable,
    target: types_pb.Qualifiable_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import qualifiable_to_pb_choice

        qualifiable = types.RelationshipElement(
            ... # some constructor arguments
        )

        qualifiable_choice_pb = types_pb.Qualifiable_choice()
        qualifiable_to_pb_choice(
            qualifiable,
            qualifiable_choice_pb
        )

        some_bytes = qualifiable_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _QUALIFIABLE_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


# fmt: off
_QUALIFIER_KIND_TO_PB_MAP = {
    types.QualifierKind.VALUE_QUALIFIER:
        types_pb.QualifierKind.Qualifierkind_VALUE_QUALIFIER,
    types.QualifierKind.CONCEPT_QUALIFIER:
        types_pb.QualifierKind.Qualifierkind_CONCEPT_QUALIFIER,
    types.QualifierKind.TEMPLATE_QUALIFIER:
        types_pb.QualifierKind.Qualifierkind_TEMPLATE_QUALIFIER
}  # type: Mapping[types.QualifierKind, types_pb.QualifierKind]
# fmt: on


def qualifier_kind_to_pb(
    that: types.QualifierKind
) -> types_pb.QualifierKind:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import qualifier_kind_to_pb
    >>> import aas_core3.types as types
    >>> qualifier_kind_to_pb(
    ...     types.QualifierKind.VALUE_QUALIFIER
    ... )
    1
    """
    return _QUALIFIER_KIND_TO_PB_MAP[that]


def qualifier_to_pb(
    that: types.Qualifier,
    target: types_pb.Qualifier
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import qualifier_to_pb

        qualifier = types.Qualifier(
            ... # some constructor arguments
        )

        qualifier_pb = types_pb.Qualifier()
        qualifier_to_pb(
            qualifier,
            qualifier_pb
        )

        some_bytes = qualifier_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.kind is not None:
        target.kind = qualifier_kind_to_pb(
            that.kind
        )

    target.type = that.type

    target.value_type = data_type_def_xsd_to_pb(
        that.value_type
    )

    if that.value is not None:
        target.value = that.value

    if that.value_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.value_id.Clear()

        reference_to_pb(
            that.value_id,
            target.value_id
        )


def asset_administration_shell_to_pb(
    that: types.AssetAdministrationShell,
    target: types_pb.AssetAdministrationShell
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import asset_administration_shell_to_pb

        asset_administration_shell = types.AssetAdministrationShell(
            ... # some constructor arguments
        )

        asset_administration_shell_pb = types_pb.AssetAdministrationShell()
        asset_administration_shell_to_pb(
            asset_administration_shell,
            asset_administration_shell_pb
        )

        some_bytes = asset_administration_shell_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.administration is not None:
        # We clear so that the field is set even if all the properties are None.
        target.administration.Clear()

        administrative_information_to_pb(
            that.administration,
            target.administration
        )

    target.id = that.id

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.derived_from is not None:
        # We clear so that the field is set even if all the properties are None.
        target.derived_from.Clear()

        reference_to_pb(
            that.derived_from,
            target.derived_from
        )

    # We clear so that the field is set even if all the properties are None.
    target.asset_information.Clear()

    asset_information_to_pb(
        that.asset_information,
        target.asset_information
    )

    if that.submodels is not None:
        for submodels_item in that.submodels:
            submodels_item_pb = target.submodels.add()
            reference_to_pb(
                submodels_item,
                submodels_item_pb)


def asset_information_to_pb(
    that: types.AssetInformation,
    target: types_pb.AssetInformation
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import asset_information_to_pb

        asset_information = types.AssetInformation(
            ... # some constructor arguments
        )

        asset_information_pb = types_pb.AssetInformation()
        asset_information_to_pb(
            asset_information,
            asset_information_pb
        )

        some_bytes = asset_information_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.asset_kind = asset_kind_to_pb(
        that.asset_kind
    )

    if that.global_asset_id is not None:
        target.global_asset_id = that.global_asset_id

    if that.specific_asset_ids is not None:
        for specific_asset_ids_item in that.specific_asset_ids:
            specific_asset_ids_item_pb = target.specific_asset_ids.add()
            specific_asset_id_to_pb(
                specific_asset_ids_item,
                specific_asset_ids_item_pb)

    if that.asset_type is not None:
        target.asset_type = that.asset_type

    if that.default_thumbnail is not None:
        # We clear so that the field is set even if all the properties are None.
        target.default_thumbnail.Clear()

        resource_to_pb(
            that.default_thumbnail,
            target.default_thumbnail
        )


def resource_to_pb(
    that: types.Resource,
    target: types_pb.Resource
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import resource_to_pb

        resource = types.Resource(
            ... # some constructor arguments
        )

        resource_pb = types_pb.Resource()
        resource_to_pb(
            resource,
            resource_pb
        )

        some_bytes = resource_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.path = that.path

    if that.content_type is not None:
        target.content_type = that.content_type


# fmt: off
_ASSET_KIND_TO_PB_MAP = {
    types.AssetKind.TYPE:
        types_pb.AssetKind.Assetkind_TYPE,
    types.AssetKind.INSTANCE:
        types_pb.AssetKind.Assetkind_INSTANCE,
    types.AssetKind.NOT_APPLICABLE:
        types_pb.AssetKind.Assetkind_NOT_APPLICABLE
}  # type: Mapping[types.AssetKind, types_pb.AssetKind]
# fmt: on


def asset_kind_to_pb(
    that: types.AssetKind
) -> types_pb.AssetKind:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import asset_kind_to_pb
    >>> import aas_core3.types as types
    >>> asset_kind_to_pb(
    ...     types.AssetKind.TYPE
    ... )
    1
    """
    return _ASSET_KIND_TO_PB_MAP[that]


def specific_asset_id_to_pb(
    that: types.SpecificAssetID,
    target: types_pb.SpecificAssetId
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import specific_asset_id_to_pb

        specific_asset_id = types.SpecificAssetID(
            ... # some constructor arguments
        )

        specific_asset_id_pb = types_pb.SpecificAssetId()
        specific_asset_id_to_pb(
            specific_asset_id,
            specific_asset_id_pb
        )

        some_bytes = specific_asset_id_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    target.name = that.name

    target.value = that.value

    if that.external_subject_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.external_subject_id.Clear()

        reference_to_pb(
            that.external_subject_id,
            target.external_subject_id
        )


def submodel_to_pb(
    that: types.Submodel,
    target: types_pb.Submodel
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_to_pb

        submodel = types.Submodel(
            ... # some constructor arguments
        )

        submodel_pb = types_pb.Submodel()
        submodel_to_pb(
            submodel,
            submodel_pb
        )

        some_bytes = submodel_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.administration is not None:
        # We clear so that the field is set even if all the properties are None.
        target.administration.Clear()

        administrative_information_to_pb(
            that.administration,
            target.administration
        )

    target.id = that.id

    if that.kind is not None:
        target.kind = modelling_kind_to_pb(
            that.kind
        )

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.submodel_elements is not None:
        for submodel_elements_item in that.submodel_elements:
            submodel_elements_item_pb = target.submodel_elements.add()
            submodel_element_to_pb_choice(
                submodel_elements_item,
                submodel_elements_item_pb)


class _SubmodelElementToPbChoice(
    _PartialVisitorWithContext[
        types_pb.SubmodelElement_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )

    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )

    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_capability_with_context(
        self,
        that: types.Capability,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.capability``
        according to ``that`` instance.
        """
        capability_to_pb(
            that,
            context.capability
        )

    def visit_entity_with_context(
        self,
        that: types.Entity,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.entity``
        according to ``that`` instance.
        """
        entity_to_pb(
            that,
            context.entity
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_operation_with_context(
        self,
        that: types.Operation,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.operation``
        according to ``that`` instance.
        """
        operation_to_pb(
            that,
            context.operation
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )

    def visit_submodel_element_collection_with_context(
        self,
        that: types.SubmodelElementCollection,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_collection``
        according to ``that`` instance.
        """
        submodel_element_collection_to_pb(
            that,
            context.submodel_element_collection
        )

    def visit_submodel_element_list_with_context(
        self,
        that: types.SubmodelElementList,
        context: types_pb.SubmodelElement_choice
    ) -> None:
        """
        Set the fields of ``context.submodel_element_list``
        according to ``that`` instance.
        """
        submodel_element_list_to_pb(
            that,
            context.submodel_element_list
        )


_SUBMODEL_ELEMENT_TO_PB_CHOICE = _SubmodelElementToPbChoice()


def submodel_element_to_pb_choice(
    that: types.SubmodelElement,
    target: types_pb.SubmodelElement_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_element_to_pb_choice

        submodel_element = types.RelationshipElement(
            ... # some constructor arguments
        )

        submodel_element_choice_pb = types_pb.SubmodelElement_choice()
        submodel_element_to_pb_choice(
            submodel_element,
            submodel_element_choice_pb
        )

        some_bytes = submodel_element_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _SUBMODEL_ELEMENT_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


class _RelationshipElementToPbChoice(
    _PartialVisitorWithContext[
        types_pb.RelationshipElement_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_relationship_element_with_context(
        self,
        that: types.RelationshipElement,
        context: types_pb.RelationshipElement_choice
    ) -> None:
        """
        Set the fields of ``context.relationship_element``
        according to ``that`` instance.
        """
        relationship_element_to_pb(
            that,
            context.relationship_element
        )

    def visit_annotated_relationship_element_with_context(
        self,
        that: types.AnnotatedRelationshipElement,
        context: types_pb.RelationshipElement_choice
    ) -> None:
        """
        Set the fields of ``context.annotated_relationship_element``
        according to ``that`` instance.
        """
        annotated_relationship_element_to_pb(
            that,
            context.annotated_relationship_element
        )


_RELATIONSHIP_ELEMENT_TO_PB_CHOICE = _RelationshipElementToPbChoice()


def relationship_element_to_pb_choice(
    that: types.RelationshipElement,
    target: types_pb.RelationshipElement_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import relationship_element_to_pb_choice

        relationship_element = types.AnnotatedRelationshipElement(
            ... # some constructor arguments
        )

        relationship_element_choice_pb = types_pb.RelationshipElement_choice()
        relationship_element_to_pb_choice(
            relationship_element,
            relationship_element_choice_pb
        )

        some_bytes = relationship_element_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _RELATIONSHIP_ELEMENT_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def relationship_element_to_pb(
    that: types.RelationshipElement,
    target: types_pb.RelationshipElement
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import relationship_element_to_pb

        relationship_element = types.RelationshipElement(
            ... # some constructor arguments
        )

        relationship_element_pb = types_pb.RelationshipElement()
        relationship_element_to_pb(
            relationship_element,
            relationship_element_pb
        )

        some_bytes = relationship_element_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    # We clear so that the field is set even if all the properties are None.
    target.first.Clear()

    reference_to_pb(
        that.first,
        target.first
    )

    # We clear so that the field is set even if all the properties are None.
    target.second.Clear()

    reference_to_pb(
        that.second,
        target.second
    )


# fmt: off
_AAS_SUBMODEL_ELEMENTS_TO_PB_MAP = {
    types.AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_ANNOTATED_RELATIONSHIP_ELEMENT,
    types.AASSubmodelElements.BASIC_EVENT_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_BASIC_EVENT_ELEMENT,
    types.AASSubmodelElements.BLOB:
        types_pb.AasSubmodelElements.Aassubmodelelements_BLOB,
    types.AASSubmodelElements.CAPABILITY:
        types_pb.AasSubmodelElements.Aassubmodelelements_CAPABILITY,
    types.AASSubmodelElements.DATA_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_DATA_ELEMENT,
    types.AASSubmodelElements.ENTITY:
        types_pb.AasSubmodelElements.Aassubmodelelements_ENTITY,
    types.AASSubmodelElements.EVENT_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_EVENT_ELEMENT,
    types.AASSubmodelElements.FILE:
        types_pb.AasSubmodelElements.Aassubmodelelements_FILE,
    types.AASSubmodelElements.MULTI_LANGUAGE_PROPERTY:
        types_pb.AasSubmodelElements.Aassubmodelelements_MULTI_LANGUAGE_PROPERTY,
    types.AASSubmodelElements.OPERATION:
        types_pb.AasSubmodelElements.Aassubmodelelements_OPERATION,
    types.AASSubmodelElements.PROPERTY:
        types_pb.AasSubmodelElements.Aassubmodelelements_PROPERTY,
    types.AASSubmodelElements.RANGE:
        types_pb.AasSubmodelElements.Aassubmodelelements_RANGE,
    types.AASSubmodelElements.REFERENCE_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_REFERENCE_ELEMENT,
    types.AASSubmodelElements.RELATIONSHIP_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_RELATIONSHIP_ELEMENT,
    types.AASSubmodelElements.SUBMODEL_ELEMENT:
        types_pb.AasSubmodelElements.Aassubmodelelements_SUBMODEL_ELEMENT,
    types.AASSubmodelElements.SUBMODEL_ELEMENT_LIST:
        types_pb.AasSubmodelElements.Aassubmodelelements_SUBMODEL_ELEMENT_LIST,
    types.AASSubmodelElements.SUBMODEL_ELEMENT_COLLECTION:
        types_pb.AasSubmodelElements.Aassubmodelelements_SUBMODEL_ELEMENT_COLLECTION
}  # type: Mapping[types.AASSubmodelElements, types_pb.AasSubmodelElements]
# fmt: on


def aas_submodel_elements_to_pb(
    that: types.AASSubmodelElements
) -> types_pb.AasSubmodelElements:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import aas_submodel_elements_to_pb
    >>> import aas_core3.types as types
    >>> aas_submodel_elements_to_pb(
    ...     types.AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT
    ... )
    1
    """
    return _AAS_SUBMODEL_ELEMENTS_TO_PB_MAP[that]


def submodel_element_list_to_pb(
    that: types.SubmodelElementList,
    target: types_pb.SubmodelElementList
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_element_list_to_pb

        submodel_element_list = types.SubmodelElementList(
            ... # some constructor arguments
        )

        submodel_element_list_pb = types_pb.SubmodelElementList()
        submodel_element_list_to_pb(
            submodel_element_list,
            submodel_element_list_pb
        )

        some_bytes = submodel_element_list_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.order_relevant is not None:
        target.order_relevant = that.order_relevant

    if that.semantic_id_list_element is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id_list_element.Clear()

        reference_to_pb(
            that.semantic_id_list_element,
            target.semantic_id_list_element
        )

    target.type_value_list_element = aas_submodel_elements_to_pb(
        that.type_value_list_element
    )

    if that.value_type_list_element is not None:
        target.value_type_list_element = data_type_def_xsd_to_pb(
            that.value_type_list_element
        )

    if that.value is not None:
        for value_item in that.value:
            value_item_pb = target.value.add()
            submodel_element_to_pb_choice(
                value_item,
                value_item_pb)


def submodel_element_collection_to_pb(
    that: types.SubmodelElementCollection,
    target: types_pb.SubmodelElementCollection
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import submodel_element_collection_to_pb

        submodel_element_collection = types.SubmodelElementCollection(
            ... # some constructor arguments
        )

        submodel_element_collection_pb = types_pb.SubmodelElementCollection()
        submodel_element_collection_to_pb(
            submodel_element_collection,
            submodel_element_collection_pb
        )

        some_bytes = submodel_element_collection_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.value is not None:
        for value_item in that.value:
            value_item_pb = target.value.add()
            submodel_element_to_pb_choice(
                value_item,
                value_item_pb)


class _DataElementToPbChoice(
    _PartialVisitorWithContext[
        types_pb.DataElement_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_blob_with_context(
        self,
        that: types.Blob,
        context: types_pb.DataElement_choice
    ) -> None:
        """
        Set the fields of ``context.blob``
        according to ``that`` instance.
        """
        blob_to_pb(
            that,
            context.blob
        )

    def visit_file_with_context(
        self,
        that: types.File,
        context: types_pb.DataElement_choice
    ) -> None:
        """
        Set the fields of ``context.file``
        according to ``that`` instance.
        """
        file_to_pb(
            that,
            context.file
        )

    def visit_multi_language_property_with_context(
        self,
        that: types.MultiLanguageProperty,
        context: types_pb.DataElement_choice
    ) -> None:
        """
        Set the fields of ``context.multi_language_property``
        according to ``that`` instance.
        """
        multi_language_property_to_pb(
            that,
            context.multi_language_property
        )

    def visit_property_with_context(
        self,
        that: types.Property,
        context: types_pb.DataElement_choice
    ) -> None:
        """
        Set the fields of ``context.property``
        according to ``that`` instance.
        """
        property_to_pb(
            that,
            context.property
        )

    def visit_range_with_context(
        self,
        that: types.Range,
        context: types_pb.DataElement_choice
    ) -> None:
        """
        Set the fields of ``context.range``
        according to ``that`` instance.
        """
        range_to_pb(
            that,
            context.range
        )

    def visit_reference_element_with_context(
        self,
        that: types.ReferenceElement,
        context: types_pb.DataElement_choice
    ) -> None:
        """
        Set the fields of ``context.reference_element``
        according to ``that`` instance.
        """
        reference_element_to_pb(
            that,
            context.reference_element
        )


_DATA_ELEMENT_TO_PB_CHOICE = _DataElementToPbChoice()


def data_element_to_pb_choice(
    that: types.DataElement,
    target: types_pb.DataElement_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import data_element_to_pb_choice

        data_element = types.Blob(
            ... # some constructor arguments
        )

        data_element_choice_pb = types_pb.DataElement_choice()
        data_element_to_pb_choice(
            data_element,
            data_element_choice_pb
        )

        some_bytes = data_element_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _DATA_ELEMENT_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def property_to_pb(
    that: types.Property,
    target: types_pb.Property
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import property_to_pb

        property = types.Property(
            ... # some constructor arguments
        )

        property_pb = types_pb.Property()
        property_to_pb(
            property,
            property_pb
        )

        some_bytes = property_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    target.value_type = data_type_def_xsd_to_pb(
        that.value_type
    )

    if that.value is not None:
        target.value = that.value

    if that.value_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.value_id.Clear()

        reference_to_pb(
            that.value_id,
            target.value_id
        )


def multi_language_property_to_pb(
    that: types.MultiLanguageProperty,
    target: types_pb.MultiLanguageProperty
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import multi_language_property_to_pb

        multi_language_property = types.MultiLanguageProperty(
            ... # some constructor arguments
        )

        multi_language_property_pb = types_pb.MultiLanguageProperty()
        multi_language_property_to_pb(
            multi_language_property,
            multi_language_property_pb
        )

        some_bytes = multi_language_property_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.value is not None:
        for value_item in that.value:
            value_item_pb = target.value.add()
            lang_string_text_type_to_pb(
                value_item,
                value_item_pb)

    if that.value_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.value_id.Clear()

        reference_to_pb(
            that.value_id,
            target.value_id
        )


def range_to_pb(
    that: types.Range,
    target: types_pb.Range
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import range_to_pb

        range = types.Range(
            ... # some constructor arguments
        )

        range_pb = types_pb.Range()
        range_to_pb(
            range,
            range_pb
        )

        some_bytes = range_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    target.value_type = data_type_def_xsd_to_pb(
        that.value_type
    )

    if that.min is not None:
        target.min = that.min

    if that.max is not None:
        target.max = that.max


def reference_element_to_pb(
    that: types.ReferenceElement,
    target: types_pb.ReferenceElement
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import reference_element_to_pb

        reference_element = types.ReferenceElement(
            ... # some constructor arguments
        )

        reference_element_pb = types_pb.ReferenceElement()
        reference_element_to_pb(
            reference_element,
            reference_element_pb
        )

        some_bytes = reference_element_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.value is not None:
        # We clear so that the field is set even if all the properties are None.
        target.value.Clear()

        reference_to_pb(
            that.value,
            target.value
        )


def blob_to_pb(
    that: types.Blob,
    target: types_pb.Blob
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import blob_to_pb

        blob = types.Blob(
            ... # some constructor arguments
        )

        blob_pb = types_pb.Blob()
        blob_to_pb(
            blob,
            blob_pb
        )

        some_bytes = blob_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.value is not None:
        target.value = bytes(that.value)

    target.content_type = that.content_type


def file_to_pb(
    that: types.File,
    target: types_pb.File
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import file_to_pb

        file = types.File(
            ... # some constructor arguments
        )

        file_pb = types_pb.File()
        file_to_pb(
            file,
            file_pb
        )

        some_bytes = file_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.value is not None:
        target.value = that.value

    target.content_type = that.content_type


def annotated_relationship_element_to_pb(
    that: types.AnnotatedRelationshipElement,
    target: types_pb.AnnotatedRelationshipElement
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import annotated_relationship_element_to_pb

        annotated_relationship_element = types.AnnotatedRelationshipElement(
            ... # some constructor arguments
        )

        annotated_relationship_element_pb = types_pb.AnnotatedRelationshipElement()
        annotated_relationship_element_to_pb(
            annotated_relationship_element,
            annotated_relationship_element_pb
        )

        some_bytes = annotated_relationship_element_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    # We clear so that the field is set even if all the properties are None.
    target.first.Clear()

    reference_to_pb(
        that.first,
        target.first
    )

    # We clear so that the field is set even if all the properties are None.
    target.second.Clear()

    reference_to_pb(
        that.second,
        target.second
    )

    if that.annotations is not None:
        for annotations_item in that.annotations:
            annotations_item_pb = target.annotations.add()
            data_element_to_pb_choice(
                annotations_item,
                annotations_item_pb)


def entity_to_pb(
    that: types.Entity,
    target: types_pb.Entity
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import entity_to_pb

        entity = types.Entity(
            ... # some constructor arguments
        )

        entity_pb = types_pb.Entity()
        entity_to_pb(
            entity,
            entity_pb
        )

        some_bytes = entity_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.statements is not None:
        for statements_item in that.statements:
            statements_item_pb = target.statements.add()
            submodel_element_to_pb_choice(
                statements_item,
                statements_item_pb)

    target.entity_type = entity_type_to_pb(
        that.entity_type
    )

    if that.global_asset_id is not None:
        target.global_asset_id = that.global_asset_id

    if that.specific_asset_ids is not None:
        for specific_asset_ids_item in that.specific_asset_ids:
            specific_asset_ids_item_pb = target.specific_asset_ids.add()
            specific_asset_id_to_pb(
                specific_asset_ids_item,
                specific_asset_ids_item_pb)


# fmt: off
_ENTITY_TYPE_TO_PB_MAP = {
    types.EntityType.CO_MANAGED_ENTITY:
        types_pb.EntityType.Entitytype_CO_MANAGED_ENTITY,
    types.EntityType.SELF_MANAGED_ENTITY:
        types_pb.EntityType.Entitytype_SELF_MANAGED_ENTITY
}  # type: Mapping[types.EntityType, types_pb.EntityType]
# fmt: on


def entity_type_to_pb(
    that: types.EntityType
) -> types_pb.EntityType:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import entity_type_to_pb
    >>> import aas_core3.types as types
    >>> entity_type_to_pb(
    ...     types.EntityType.CO_MANAGED_ENTITY
    ... )
    1
    """
    return _ENTITY_TYPE_TO_PB_MAP[that]


# fmt: off
_DIRECTION_TO_PB_MAP = {
    types.Direction.INPUT:
        types_pb.Direction.Direction_INPUT,
    types.Direction.OUTPUT:
        types_pb.Direction.Direction_OUTPUT
}  # type: Mapping[types.Direction, types_pb.Direction]
# fmt: on


def direction_to_pb(
    that: types.Direction
) -> types_pb.Direction:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import direction_to_pb
    >>> import aas_core3.types as types
    >>> direction_to_pb(
    ...     types.Direction.INPUT
    ... )
    1
    """
    return _DIRECTION_TO_PB_MAP[that]


# fmt: off
_STATE_OF_EVENT_TO_PB_MAP = {
    types.StateOfEvent.ON:
        types_pb.StateOfEvent.Stateofevent_ON,
    types.StateOfEvent.OFF:
        types_pb.StateOfEvent.Stateofevent_OFF
}  # type: Mapping[types.StateOfEvent, types_pb.StateOfEvent]
# fmt: on


def state_of_event_to_pb(
    that: types.StateOfEvent
) -> types_pb.StateOfEvent:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import state_of_event_to_pb
    >>> import aas_core3.types as types
    >>> state_of_event_to_pb(
    ...     types.StateOfEvent.ON
    ... )
    1
    """
    return _STATE_OF_EVENT_TO_PB_MAP[that]


def event_payload_to_pb(
    that: types.EventPayload,
    target: types_pb.EventPayload
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import event_payload_to_pb

        event_payload = types.EventPayload(
            ... # some constructor arguments
        )

        event_payload_pb = types_pb.EventPayload()
        event_payload_to_pb(
            event_payload,
            event_payload_pb
        )

        some_bytes = event_payload_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    # We clear so that the field is set even if all the properties are None.
    target.source.Clear()

    reference_to_pb(
        that.source,
        target.source
    )

    if that.source_semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.source_semantic_id.Clear()

        reference_to_pb(
            that.source_semantic_id,
            target.source_semantic_id
        )

    # We clear so that the field is set even if all the properties are None.
    target.observable_reference.Clear()

    reference_to_pb(
        that.observable_reference,
        target.observable_reference
    )

    if that.observable_semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.observable_semantic_id.Clear()

        reference_to_pb(
            that.observable_semantic_id,
            target.observable_semantic_id
        )

    if that.topic is not None:
        target.topic = that.topic

    if that.subject_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.subject_id.Clear()

        reference_to_pb(
            that.subject_id,
            target.subject_id
        )

    target.time_stamp = that.time_stamp

    if that.payload is not None:
        target.payload = bytes(that.payload)


class _EventElementToPbChoice(
    _PartialVisitorWithContext[
        types_pb.EventElement_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_basic_event_element_with_context(
        self,
        that: types.BasicEventElement,
        context: types_pb.EventElement_choice
    ) -> None:
        """
        Set the fields of ``context.basic_event_element``
        according to ``that`` instance.
        """
        basic_event_element_to_pb(
            that,
            context.basic_event_element
        )


_EVENT_ELEMENT_TO_PB_CHOICE = _EventElementToPbChoice()


def event_element_to_pb_choice(
    that: types.EventElement,
    target: types_pb.EventElement_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import event_element_to_pb_choice

        event_element = types.BasicEventElement(
            ... # some constructor arguments
        )

        event_element_choice_pb = types_pb.EventElement_choice()
        event_element_to_pb_choice(
            event_element,
            event_element_choice_pb
        )

        some_bytes = event_element_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _EVENT_ELEMENT_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def basic_event_element_to_pb(
    that: types.BasicEventElement,
    target: types_pb.BasicEventElement
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import basic_event_element_to_pb

        basic_event_element = types.BasicEventElement(
            ... # some constructor arguments
        )

        basic_event_element_pb = types_pb.BasicEventElement()
        basic_event_element_to_pb(
            basic_event_element,
            basic_event_element_pb
        )

        some_bytes = basic_event_element_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    # We clear so that the field is set even if all the properties are None.
    target.observed.Clear()

    reference_to_pb(
        that.observed,
        target.observed
    )

    target.direction = direction_to_pb(
        that.direction
    )

    target.state = state_of_event_to_pb(
        that.state
    )

    if that.message_topic is not None:
        target.message_topic = that.message_topic

    if that.message_broker is not None:
        # We clear so that the field is set even if all the properties are None.
        target.message_broker.Clear()

        reference_to_pb(
            that.message_broker,
            target.message_broker
        )

    if that.last_update is not None:
        target.last_update = that.last_update

    if that.min_interval is not None:
        target.min_interval = that.min_interval

    if that.max_interval is not None:
        target.max_interval = that.max_interval


def operation_to_pb(
    that: types.Operation,
    target: types_pb.Operation
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import operation_to_pb

        operation = types.Operation(
            ... # some constructor arguments
        )

        operation_pb = types_pb.Operation()
        operation_to_pb(
            operation,
            operation_pb
        )

        some_bytes = operation_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.input_variables is not None:
        for input_variables_item in that.input_variables:
            input_variables_item_pb = target.input_variables.add()
            operation_variable_to_pb(
                input_variables_item,
                input_variables_item_pb)

    if that.output_variables is not None:
        for output_variables_item in that.output_variables:
            output_variables_item_pb = target.output_variables.add()
            operation_variable_to_pb(
                output_variables_item,
                output_variables_item_pb)

    if that.inoutput_variables is not None:
        for inoutput_variables_item in that.inoutput_variables:
            inoutput_variables_item_pb = target.inoutput_variables.add()
            operation_variable_to_pb(
                inoutput_variables_item,
                inoutput_variables_item_pb)


def operation_variable_to_pb(
    that: types.OperationVariable,
    target: types_pb.OperationVariable
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import operation_variable_to_pb

        operation_variable = types.OperationVariable(
            ... # some constructor arguments
        )

        operation_variable_pb = types_pb.OperationVariable()
        operation_variable_to_pb(
            operation_variable,
            operation_variable_pb
        )

        some_bytes = operation_variable_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    submodel_element_to_pb_choice(
        that.value,
        target.value
    )


def capability_to_pb(
    that: types.Capability,
    target: types_pb.Capability
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import capability_to_pb

        capability = types.Capability(
            ... # some constructor arguments
        )

        capability_pb = types_pb.Capability()
        capability_to_pb(
            capability,
            capability_pb
        )

        some_bytes = capability_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.semantic_id.Clear()

        reference_to_pb(
            that.semantic_id,
            target.semantic_id
        )

    if that.supplemental_semantic_ids is not None:
        for supplemental_semantic_ids_item in that.supplemental_semantic_ids:
            supplemental_semantic_ids_item_pb = target.supplemental_semantic_ids.add()
            reference_to_pb(
                supplemental_semantic_ids_item,
                supplemental_semantic_ids_item_pb)

    if that.qualifiers is not None:
        for qualifiers_item in that.qualifiers:
            qualifiers_item_pb = target.qualifiers.add()
            qualifier_to_pb(
                qualifiers_item,
                qualifiers_item_pb)

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)


def concept_description_to_pb(
    that: types.ConceptDescription,
    target: types_pb.ConceptDescription
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import concept_description_to_pb

        concept_description = types.ConceptDescription(
            ... # some constructor arguments
        )

        concept_description_pb = types_pb.ConceptDescription()
        concept_description_to_pb(
            concept_description,
            concept_description_pb
        )

        some_bytes = concept_description_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.extensions is not None:
        for extensions_item in that.extensions:
            extensions_item_pb = target.extensions.add()
            extension_to_pb(
                extensions_item,
                extensions_item_pb)

    if that.category is not None:
        target.category = that.category

    if that.id_short is not None:
        target.id_short = that.id_short

    if that.display_name is not None:
        for display_name_item in that.display_name:
            display_name_item_pb = target.display_name.add()
            lang_string_name_type_to_pb(
                display_name_item,
                display_name_item_pb)

    if that.description is not None:
        for description_item in that.description:
            description_item_pb = target.description.add()
            lang_string_text_type_to_pb(
                description_item,
                description_item_pb)

    if that.administration is not None:
        # We clear so that the field is set even if all the properties are None.
        target.administration.Clear()

        administrative_information_to_pb(
            that.administration,
            target.administration
        )

    target.id = that.id

    if that.embedded_data_specifications is not None:
        for embedded_data_specifications_item in that.embedded_data_specifications:
            embedded_data_specifications_item_pb = target.embedded_data_specifications.add()
            embedded_data_specification_to_pb(
                embedded_data_specifications_item,
                embedded_data_specifications_item_pb)

    if that.is_case_of is not None:
        for is_case_of_item in that.is_case_of:
            is_case_of_item_pb = target.is_case_of.add()
            reference_to_pb(
                is_case_of_item,
                is_case_of_item_pb)


# fmt: off
_REFERENCE_TYPES_TO_PB_MAP = {
    types.ReferenceTypes.EXTERNAL_REFERENCE:
        types_pb.ReferenceTypes.Referencetypes_EXTERNAL_REFERENCE,
    types.ReferenceTypes.MODEL_REFERENCE:
        types_pb.ReferenceTypes.Referencetypes_MODEL_REFERENCE
}  # type: Mapping[types.ReferenceTypes, types_pb.ReferenceTypes]
# fmt: on


def reference_types_to_pb(
    that: types.ReferenceTypes
) -> types_pb.ReferenceTypes:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import reference_types_to_pb
    >>> import aas_core3.types as types
    >>> reference_types_to_pb(
    ...     types.ReferenceTypes.EXTERNAL_REFERENCE
    ... )
    1
    """
    return _REFERENCE_TYPES_TO_PB_MAP[that]


def reference_to_pb(
    that: types.Reference,
    target: types_pb.Reference
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import reference_to_pb

        reference = types.Reference(
            ... # some constructor arguments
        )

        reference_pb = types_pb.Reference()
        reference_to_pb(
            reference,
            reference_pb
        )

        some_bytes = reference_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.type = reference_types_to_pb(
        that.type
    )

    if that.referred_semantic_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.referred_semantic_id.Clear()

        reference_to_pb(
            that.referred_semantic_id,
            target.referred_semantic_id
        )

    for keys_item in that.keys:
        keys_item_pb = target.keys.add()
        key_to_pb(
            keys_item,
            keys_item_pb)


def key_to_pb(
    that: types.Key,
    target: types_pb.Key
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import key_to_pb

        key = types.Key(
            ... # some constructor arguments
        )

        key_pb = types_pb.Key()
        key_to_pb(
            key,
            key_pb
        )

        some_bytes = key_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.type = key_types_to_pb(
        that.type
    )

    target.value = that.value


# fmt: off
_KEY_TYPES_TO_PB_MAP = {
    types.KeyTypes.ANNOTATED_RELATIONSHIP_ELEMENT:
        types_pb.KeyTypes.Keytypes_ANNOTATED_RELATIONSHIP_ELEMENT,
    types.KeyTypes.ASSET_ADMINISTRATION_SHELL:
        types_pb.KeyTypes.Keytypes_ASSET_ADMINISTRATION_SHELL,
    types.KeyTypes.BASIC_EVENT_ELEMENT:
        types_pb.KeyTypes.Keytypes_BASIC_EVENT_ELEMENT,
    types.KeyTypes.BLOB:
        types_pb.KeyTypes.Keytypes_BLOB,
    types.KeyTypes.CAPABILITY:
        types_pb.KeyTypes.Keytypes_CAPABILITY,
    types.KeyTypes.CONCEPT_DESCRIPTION:
        types_pb.KeyTypes.Keytypes_CONCEPT_DESCRIPTION,
    types.KeyTypes.DATA_ELEMENT:
        types_pb.KeyTypes.Keytypes_DATA_ELEMENT,
    types.KeyTypes.ENTITY:
        types_pb.KeyTypes.Keytypes_ENTITY,
    types.KeyTypes.EVENT_ELEMENT:
        types_pb.KeyTypes.Keytypes_EVENT_ELEMENT,
    types.KeyTypes.FILE:
        types_pb.KeyTypes.Keytypes_FILE,
    types.KeyTypes.FRAGMENT_REFERENCE:
        types_pb.KeyTypes.Keytypes_FRAGMENT_REFERENCE,
    types.KeyTypes.GLOBAL_REFERENCE:
        types_pb.KeyTypes.Keytypes_GLOBAL_REFERENCE,
    types.KeyTypes.IDENTIFIABLE:
        types_pb.KeyTypes.Keytypes_IDENTIFIABLE,
    types.KeyTypes.MULTI_LANGUAGE_PROPERTY:
        types_pb.KeyTypes.Keytypes_MULTI_LANGUAGE_PROPERTY,
    types.KeyTypes.OPERATION:
        types_pb.KeyTypes.Keytypes_OPERATION,
    types.KeyTypes.PROPERTY:
        types_pb.KeyTypes.Keytypes_PROPERTY,
    types.KeyTypes.RANGE:
        types_pb.KeyTypes.Keytypes_RANGE,
    types.KeyTypes.REFERABLE:
        types_pb.KeyTypes.Keytypes_REFERABLE,
    types.KeyTypes.REFERENCE_ELEMENT:
        types_pb.KeyTypes.Keytypes_REFERENCE_ELEMENT,
    types.KeyTypes.RELATIONSHIP_ELEMENT:
        types_pb.KeyTypes.Keytypes_RELATIONSHIP_ELEMENT,
    types.KeyTypes.SUBMODEL:
        types_pb.KeyTypes.Keytypes_SUBMODEL,
    types.KeyTypes.SUBMODEL_ELEMENT:
        types_pb.KeyTypes.Keytypes_SUBMODEL_ELEMENT,
    types.KeyTypes.SUBMODEL_ELEMENT_COLLECTION:
        types_pb.KeyTypes.Keytypes_SUBMODEL_ELEMENT_COLLECTION,
    types.KeyTypes.SUBMODEL_ELEMENT_LIST:
        types_pb.KeyTypes.Keytypes_SUBMODEL_ELEMENT_LIST
}  # type: Mapping[types.KeyTypes, types_pb.KeyTypes]
# fmt: on


def key_types_to_pb(
    that: types.KeyTypes
) -> types_pb.KeyTypes:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import key_types_to_pb
    >>> import aas_core3.types as types
    >>> key_types_to_pb(
    ...     types.KeyTypes.ANNOTATED_RELATIONSHIP_ELEMENT
    ... )
    1
    """
    return _KEY_TYPES_TO_PB_MAP[that]


# fmt: off
_DATA_TYPE_DEF_XSD_TO_PB_MAP = {
    types.DataTypeDefXSD.ANY_URI:
        types_pb.DataTypeDefXsd.Datatypedefxsd_ANY_URI,
    types.DataTypeDefXSD.BASE_64_BINARY:
        types_pb.DataTypeDefXsd.Datatypedefxsd_BASE_64_BINARY,
    types.DataTypeDefXSD.BOOLEAN:
        types_pb.DataTypeDefXsd.Datatypedefxsd_BOOLEAN,
    types.DataTypeDefXSD.BYTE:
        types_pb.DataTypeDefXsd.Datatypedefxsd_BYTE,
    types.DataTypeDefXSD.DATE:
        types_pb.DataTypeDefXsd.Datatypedefxsd_DATE,
    types.DataTypeDefXSD.DATE_TIME:
        types_pb.DataTypeDefXsd.Datatypedefxsd_DATE_TIME,
    types.DataTypeDefXSD.DECIMAL:
        types_pb.DataTypeDefXsd.Datatypedefxsd_DECIMAL,
    types.DataTypeDefXSD.DOUBLE:
        types_pb.DataTypeDefXsd.Datatypedefxsd_DOUBLE,
    types.DataTypeDefXSD.DURATION:
        types_pb.DataTypeDefXsd.Datatypedefxsd_DURATION,
    types.DataTypeDefXSD.FLOAT:
        types_pb.DataTypeDefXsd.Datatypedefxsd_FLOAT,
    types.DataTypeDefXSD.G_DAY:
        types_pb.DataTypeDefXsd.Datatypedefxsd_G_DAY,
    types.DataTypeDefXSD.G_MONTH:
        types_pb.DataTypeDefXsd.Datatypedefxsd_G_MONTH,
    types.DataTypeDefXSD.G_MONTH_DAY:
        types_pb.DataTypeDefXsd.Datatypedefxsd_G_MONTH_DAY,
    types.DataTypeDefXSD.G_YEAR:
        types_pb.DataTypeDefXsd.Datatypedefxsd_G_YEAR,
    types.DataTypeDefXSD.G_YEAR_MONTH:
        types_pb.DataTypeDefXsd.Datatypedefxsd_G_YEAR_MONTH,
    types.DataTypeDefXSD.HEX_BINARY:
        types_pb.DataTypeDefXsd.Datatypedefxsd_HEX_BINARY,
    types.DataTypeDefXSD.INT:
        types_pb.DataTypeDefXsd.Datatypedefxsd_INT,
    types.DataTypeDefXSD.INTEGER:
        types_pb.DataTypeDefXsd.Datatypedefxsd_INTEGER,
    types.DataTypeDefXSD.LONG:
        types_pb.DataTypeDefXsd.Datatypedefxsd_LONG,
    types.DataTypeDefXSD.NEGATIVE_INTEGER:
        types_pb.DataTypeDefXsd.Datatypedefxsd_NEGATIVE_INTEGER,
    types.DataTypeDefXSD.NON_NEGATIVE_INTEGER:
        types_pb.DataTypeDefXsd.Datatypedefxsd_NON_NEGATIVE_INTEGER,
    types.DataTypeDefXSD.NON_POSITIVE_INTEGER:
        types_pb.DataTypeDefXsd.Datatypedefxsd_NON_POSITIVE_INTEGER,
    types.DataTypeDefXSD.POSITIVE_INTEGER:
        types_pb.DataTypeDefXsd.Datatypedefxsd_POSITIVE_INTEGER,
    types.DataTypeDefXSD.SHORT:
        types_pb.DataTypeDefXsd.Datatypedefxsd_SHORT,
    types.DataTypeDefXSD.STRING:
        types_pb.DataTypeDefXsd.Datatypedefxsd_STRING,
    types.DataTypeDefXSD.TIME:
        types_pb.DataTypeDefXsd.Datatypedefxsd_TIME,
    types.DataTypeDefXSD.UNSIGNED_BYTE:
        types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_BYTE,
    types.DataTypeDefXSD.UNSIGNED_INT:
        types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_INT,
    types.DataTypeDefXSD.UNSIGNED_LONG:
        types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_LONG,
    types.DataTypeDefXSD.UNSIGNED_SHORT:
        types_pb.DataTypeDefXsd.Datatypedefxsd_UNSIGNED_SHORT
}  # type: Mapping[types.DataTypeDefXSD, types_pb.DataTypeDefXsd]
# fmt: on


def data_type_def_xsd_to_pb(
    that: types.DataTypeDefXSD
) -> types_pb.DataTypeDefXsd:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import data_type_def_xsd_to_pb
    >>> import aas_core3.types as types
    >>> data_type_def_xsd_to_pb(
    ...     types.DataTypeDefXSD.ANY_URI
    ... )
    1
    """
    return _DATA_TYPE_DEF_XSD_TO_PB_MAP[that]


class _AbstractLangStringToPbChoice(
    _PartialVisitorWithContext[
        types_pb.AbstractLangString_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_lang_string_definition_type_iec_61360_with_context(
        self,
        that: types.LangStringDefinitionTypeIEC61360,
        context: types_pb.AbstractLangString_choice
    ) -> None:
        """
        Set the fields of ``context.lang_string_definition_type_iec_61360``
        according to ``that`` instance.
        """
        lang_string_definition_type_iec_61360_to_pb(
            that,
            context.lang_string_definition_type_iec_61360
        )

    def visit_lang_string_name_type_with_context(
        self,
        that: types.LangStringNameType,
        context: types_pb.AbstractLangString_choice
    ) -> None:
        """
        Set the fields of ``context.lang_string_name_type``
        according to ``that`` instance.
        """
        lang_string_name_type_to_pb(
            that,
            context.lang_string_name_type
        )

    def visit_lang_string_preferred_name_type_iec_61360_with_context(
        self,
        that: types.LangStringPreferredNameTypeIEC61360,
        context: types_pb.AbstractLangString_choice
    ) -> None:
        """
        Set the fields of ``context.lang_string_preferred_name_type_iec_61360``
        according to ``that`` instance.
        """
        lang_string_preferred_name_type_iec_61360_to_pb(
            that,
            context.lang_string_preferred_name_type_iec_61360
        )

    def visit_lang_string_short_name_type_iec_61360_with_context(
        self,
        that: types.LangStringShortNameTypeIEC61360,
        context: types_pb.AbstractLangString_choice
    ) -> None:
        """
        Set the fields of ``context.lang_string_short_name_type_iec_61360``
        according to ``that`` instance.
        """
        lang_string_short_name_type_iec_61360_to_pb(
            that,
            context.lang_string_short_name_type_iec_61360
        )

    def visit_lang_string_text_type_with_context(
        self,
        that: types.LangStringTextType,
        context: types_pb.AbstractLangString_choice
    ) -> None:
        """
        Set the fields of ``context.lang_string_text_type``
        according to ``that`` instance.
        """
        lang_string_text_type_to_pb(
            that,
            context.lang_string_text_type
        )


_ABSTRACT_LANG_STRING_TO_PB_CHOICE = _AbstractLangStringToPbChoice()


def abstract_lang_string_to_pb_choice(
    that: types.AbstractLangString,
    target: types_pb.AbstractLangString_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import abstract_lang_string_to_pb_choice

        abstract_lang_string = types.LangStringDefinitionTypeIEC61360(
            ... # some constructor arguments
        )

        abstract_lang_string_choice_pb = types_pb.AbstractLangString_choice()
        abstract_lang_string_to_pb_choice(
            abstract_lang_string,
            abstract_lang_string_choice_pb
        )

        some_bytes = abstract_lang_string_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _ABSTRACT_LANG_STRING_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def lang_string_name_type_to_pb(
    that: types.LangStringNameType,
    target: types_pb.LangStringNameType
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_name_type_to_pb

        lang_string_name_type = types.LangStringNameType(
            ... # some constructor arguments
        )

        lang_string_name_type_pb = types_pb.LangStringNameType()
        lang_string_name_type_to_pb(
            lang_string_name_type,
            lang_string_name_type_pb
        )

        some_bytes = lang_string_name_type_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.language = that.language

    target.text = that.text


def lang_string_text_type_to_pb(
    that: types.LangStringTextType,
    target: types_pb.LangStringTextType
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_text_type_to_pb

        lang_string_text_type = types.LangStringTextType(
            ... # some constructor arguments
        )

        lang_string_text_type_pb = types_pb.LangStringTextType()
        lang_string_text_type_to_pb(
            lang_string_text_type,
            lang_string_text_type_pb
        )

        some_bytes = lang_string_text_type_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.language = that.language

    target.text = that.text


def environment_to_pb(
    that: types.Environment,
    target: types_pb.Environment
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import environment_to_pb

        environment = types.Environment(
            ... # some constructor arguments
        )

        environment_pb = types_pb.Environment()
        environment_to_pb(
            environment,
            environment_pb
        )

        some_bytes = environment_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    if that.asset_administration_shells is not None:
        for asset_administration_shells_item in that.asset_administration_shells:
            asset_administration_shells_item_pb = target.asset_administration_shells.add()
            asset_administration_shell_to_pb(
                asset_administration_shells_item,
                asset_administration_shells_item_pb)

    if that.submodels is not None:
        for submodels_item in that.submodels:
            submodels_item_pb = target.submodels.add()
            submodel_to_pb(
                submodels_item,
                submodels_item_pb)

    if that.concept_descriptions is not None:
        for concept_descriptions_item in that.concept_descriptions:
            concept_descriptions_item_pb = target.concept_descriptions.add()
            concept_description_to_pb(
                concept_descriptions_item,
                concept_descriptions_item_pb)


class _DataSpecificationContentToPbChoice(
    _PartialVisitorWithContext[
        types_pb.DataSpecificationContent_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_data_specification_iec_61360_with_context(
        self,
        that: types.DataSpecificationIEC61360,
        context: types_pb.DataSpecificationContent_choice
    ) -> None:
        """
        Set the fields of ``context.data_specification_iec_61360``
        according to ``that`` instance.
        """
        data_specification_iec_61360_to_pb(
            that,
            context.data_specification_iec_61360
        )


_DATA_SPECIFICATION_CONTENT_TO_PB_CHOICE = _DataSpecificationContentToPbChoice()


def data_specification_content_to_pb_choice(
    that: types.DataSpecificationContent,
    target: types_pb.DataSpecificationContent_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import data_specification_content_to_pb_choice

        data_specification_content = types.DataSpecificationIEC61360(
            ... # some constructor arguments
        )

        data_specification_content_choice_pb = types_pb.DataSpecificationContent_choice()
        data_specification_content_to_pb_choice(
            data_specification_content,
            data_specification_content_choice_pb
        )

        some_bytes = data_specification_content_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _DATA_SPECIFICATION_CONTENT_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def embedded_data_specification_to_pb(
    that: types.EmbeddedDataSpecification,
    target: types_pb.EmbeddedDataSpecification
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import embedded_data_specification_to_pb

        embedded_data_specification = types.EmbeddedDataSpecification(
            ... # some constructor arguments
        )

        embedded_data_specification_pb = types_pb.EmbeddedDataSpecification()
        embedded_data_specification_to_pb(
            embedded_data_specification,
            embedded_data_specification_pb
        )

        some_bytes = embedded_data_specification_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    # We clear so that the field is set even if all the properties are None.
    target.data_specification.Clear()

    reference_to_pb(
        that.data_specification,
        target.data_specification
    )

    data_specification_content_to_pb_choice(
        that.data_specification_content,
        target.data_specification_content
    )


# fmt: off
_DATA_TYPE_IEC_61360_TO_PB_MAP = {
    types.DataTypeIEC61360.DATE:
        types_pb.DataTypeIec61360.Datatypeiec61360_DATE,
    types.DataTypeIEC61360.STRING:
        types_pb.DataTypeIec61360.Datatypeiec61360_STRING,
    types.DataTypeIEC61360.STRING_TRANSLATABLE:
        types_pb.DataTypeIec61360.Datatypeiec61360_STRING_TRANSLATABLE,
    types.DataTypeIEC61360.INTEGER_MEASURE:
        types_pb.DataTypeIec61360.Datatypeiec61360_INTEGER_MEASURE,
    types.DataTypeIEC61360.INTEGER_COUNT:
        types_pb.DataTypeIec61360.Datatypeiec61360_INTEGER_COUNT,
    types.DataTypeIEC61360.INTEGER_CURRENCY:
        types_pb.DataTypeIec61360.Datatypeiec61360_INTEGER_CURRENCY,
    types.DataTypeIEC61360.REAL_MEASURE:
        types_pb.DataTypeIec61360.Datatypeiec61360_REAL_MEASURE,
    types.DataTypeIEC61360.REAL_COUNT:
        types_pb.DataTypeIec61360.Datatypeiec61360_REAL_COUNT,
    types.DataTypeIEC61360.REAL_CURRENCY:
        types_pb.DataTypeIec61360.Datatypeiec61360_REAL_CURRENCY,
    types.DataTypeIEC61360.BOOLEAN:
        types_pb.DataTypeIec61360.Datatypeiec61360_BOOLEAN,
    types.DataTypeIEC61360.IRI:
        types_pb.DataTypeIec61360.Datatypeiec61360_IRI,
    types.DataTypeIEC61360.IRDI:
        types_pb.DataTypeIec61360.Datatypeiec61360_IRDI,
    types.DataTypeIEC61360.RATIONAL:
        types_pb.DataTypeIec61360.Datatypeiec61360_RATIONAL,
    types.DataTypeIEC61360.RATIONAL_MEASURE:
        types_pb.DataTypeIec61360.Datatypeiec61360_RATIONAL_MEASURE,
    types.DataTypeIEC61360.TIME:
        types_pb.DataTypeIec61360.Datatypeiec61360_TIME,
    types.DataTypeIEC61360.TIMESTAMP:
        types_pb.DataTypeIec61360.Datatypeiec61360_TIMESTAMP,
    types.DataTypeIEC61360.FILE:
        types_pb.DataTypeIec61360.Datatypeiec61360_FILE,
    types.DataTypeIEC61360.HTML:
        types_pb.DataTypeIec61360.Datatypeiec61360_HTML,
    types.DataTypeIEC61360.BLOB:
        types_pb.DataTypeIec61360.Datatypeiec61360_BLOB
}  # type: Mapping[types.DataTypeIEC61360, types_pb.DataTypeIec61360]
# fmt: on


def data_type_iec_61360_to_pb(
    that: types.DataTypeIEC61360
) -> types_pb.DataTypeIec61360:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import data_type_iec_61360_to_pb
    >>> import aas_core3.types as types
    >>> data_type_iec_61360_to_pb(
    ...     types.DataTypeIEC61360.DATE
    ... )
    1
    """
    return _DATA_TYPE_IEC_61360_TO_PB_MAP[that]


def level_type_to_pb(
    that: types.LevelType,
    target: types_pb.LevelType
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import level_type_to_pb

        level_type = types.LevelType(
            ... # some constructor arguments
        )

        level_type_pb = types_pb.LevelType()
        level_type_to_pb(
            level_type,
            level_type_pb
        )

        some_bytes = level_type_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.min = that.min

    target.nom = that.nom

    target.typ = that.typ

    target.max = that.max


def value_reference_pair_to_pb(
    that: types.ValueReferencePair,
    target: types_pb.ValueReferencePair
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import value_reference_pair_to_pb

        value_reference_pair = types.ValueReferencePair(
            ... # some constructor arguments
        )

        value_reference_pair_pb = types_pb.ValueReferencePair()
        value_reference_pair_to_pb(
            value_reference_pair,
            value_reference_pair_pb
        )

        some_bytes = value_reference_pair_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.value = that.value

    # We clear so that the field is set even if all the properties are None.
    target.value_id.Clear()

    reference_to_pb(
        that.value_id,
        target.value_id
    )


def value_list_to_pb(
    that: types.ValueList,
    target: types_pb.ValueList
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import value_list_to_pb

        value_list = types.ValueList(
            ... # some constructor arguments
        )

        value_list_pb = types_pb.ValueList()
        value_list_to_pb(
            value_list,
            value_list_pb
        )

        some_bytes = value_list_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    for value_reference_pairs_item in that.value_reference_pairs:
        value_reference_pairs_item_pb = target.value_reference_pairs.add()
        value_reference_pair_to_pb(
            value_reference_pairs_item,
            value_reference_pairs_item_pb)


def lang_string_preferred_name_type_iec_61360_to_pb(
    that: types.LangStringPreferredNameTypeIEC61360,
    target: types_pb.LangStringPreferredNameTypeIec61360
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_preferred_name_type_iec_61360_to_pb

        lang_string_preferred_name_type_iec_61360 = types.LangStringPreferredNameTypeIEC61360(
            ... # some constructor arguments
        )

        lang_string_preferred_name_type_iec_61360_pb = types_pb.LangStringPreferredNameTypeIec61360()
        lang_string_preferred_name_type_iec_61360_to_pb(
            lang_string_preferred_name_type_iec_61360,
            lang_string_preferred_name_type_iec_61360_pb
        )

        some_bytes = lang_string_preferred_name_type_iec_61360_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.language = that.language

    target.text = that.text


def lang_string_short_name_type_iec_61360_to_pb(
    that: types.LangStringShortNameTypeIEC61360,
    target: types_pb.LangStringShortNameTypeIec61360
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_short_name_type_iec_61360_to_pb

        lang_string_short_name_type_iec_61360 = types.LangStringShortNameTypeIEC61360(
            ... # some constructor arguments
        )

        lang_string_short_name_type_iec_61360_pb = types_pb.LangStringShortNameTypeIec61360()
        lang_string_short_name_type_iec_61360_to_pb(
            lang_string_short_name_type_iec_61360,
            lang_string_short_name_type_iec_61360_pb
        )

        some_bytes = lang_string_short_name_type_iec_61360_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.language = that.language

    target.text = that.text


def lang_string_definition_type_iec_61360_to_pb(
    that: types.LangStringDefinitionTypeIEC61360,
    target: types_pb.LangStringDefinitionTypeIec61360
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import lang_string_definition_type_iec_61360_to_pb

        lang_string_definition_type_iec_61360 = types.LangStringDefinitionTypeIEC61360(
            ... # some constructor arguments
        )

        lang_string_definition_type_iec_61360_pb = types_pb.LangStringDefinitionTypeIec61360()
        lang_string_definition_type_iec_61360_to_pb(
            lang_string_definition_type_iec_61360,
            lang_string_definition_type_iec_61360_pb
        )

        some_bytes = lang_string_definition_type_iec_61360_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.language = that.language

    target.text = that.text


def data_specification_iec_61360_to_pb(
    that: types.DataSpecificationIEC61360,
    target: types_pb.DataSpecificationIec61360
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import data_specification_iec_61360_to_pb

        data_specification_iec_61360 = types.DataSpecificationIEC61360(
            ... # some constructor arguments
        )

        data_specification_iec_61360_pb = types_pb.DataSpecificationIec61360()
        data_specification_iec_61360_to_pb(
            data_specification_iec_61360,
            data_specification_iec_61360_pb
        )

        some_bytes = data_specification_iec_61360_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    for preferred_name_item in that.preferred_name:
        preferred_name_item_pb = target.preferred_name.add()
        lang_string_preferred_name_type_iec_61360_to_pb(
            preferred_name_item,
            preferred_name_item_pb)

    if that.short_name is not None:
        for short_name_item in that.short_name:
            short_name_item_pb = target.short_name.add()
            lang_string_short_name_type_iec_61360_to_pb(
                short_name_item,
                short_name_item_pb)

    if that.unit is not None:
        target.unit = that.unit

    if that.unit_id is not None:
        # We clear so that the field is set even if all the properties are None.
        target.unit_id.Clear()

        reference_to_pb(
            that.unit_id,
            target.unit_id
        )

    if that.source_of_definition is not None:
        target.source_of_definition = that.source_of_definition

    if that.symbol is not None:
        target.symbol = that.symbol

    if that.data_type is not None:
        target.data_type = data_type_iec_61360_to_pb(
            that.data_type
        )

    if that.definition is not None:
        for definition_item in that.definition:
            definition_item_pb = target.definition.add()
            lang_string_definition_type_iec_61360_to_pb(
                definition_item,
                definition_item_pb)

    if that.value_format is not None:
        target.value_format = that.value_format

    if that.value_list is not None:
        # We clear so that the field is set even if all the properties are None.
        target.value_list.Clear()

        value_list_to_pb(
            that.value_list,
            target.value_list
        )

    if that.value is not None:
        target.value = that.value

    if that.level_type is not None:
        # We clear so that the field is set even if all the properties are None.
        target.level_type.Clear()

        level_type_to_pb(
            that.level_type,
            target.level_type
        )


class _ToPbTransformer(
    types.AbstractTransformer[google.protobuf.message.Message]
):
    """
    Dispatch to-pb conversion to the concrete functions.

    The classes with descendants (i.e., subtypes) are always going to be converted
    to their concrete Protocol Buffer instead of the choice (union) Protocol Buffer
    class. We made this decision with the compactness of messages in mind.
    """
    def transform_extension(
        self,
        that: types.Extension
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Extension`.
        """
        result = types_pb.Extension()
        extension_to_pb(that, result)
        return result

    def transform_administrative_information(
        self,
        that: types.AdministrativeInformation
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.AdministrativeInformation`.
        """
        result = types_pb.AdministrativeInformation()
        administrative_information_to_pb(that, result)
        return result

    def transform_qualifier(
        self,
        that: types.Qualifier
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Qualifier`.
        """
        result = types_pb.Qualifier()
        qualifier_to_pb(that, result)
        return result

    def transform_asset_administration_shell(
        self,
        that: types.AssetAdministrationShell
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.AssetAdministrationShell`.
        """
        result = types_pb.AssetAdministrationShell()
        asset_administration_shell_to_pb(that, result)
        return result

    def transform_asset_information(
        self,
        that: types.AssetInformation
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.AssetInformation`.
        """
        result = types_pb.AssetInformation()
        asset_information_to_pb(that, result)
        return result

    def transform_resource(
        self,
        that: types.Resource
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Resource`.
        """
        result = types_pb.Resource()
        resource_to_pb(that, result)
        return result

    def transform_specific_asset_id(
        self,
        that: types.SpecificAssetID
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.SpecificAssetId`.
        """
        result = types_pb.SpecificAssetId()
        specific_asset_id_to_pb(that, result)
        return result

    def transform_submodel(
        self,
        that: types.Submodel
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Submodel`.
        """
        result = types_pb.Submodel()
        submodel_to_pb(that, result)
        return result

    def transform_relationship_element(
        self,
        that: types.RelationshipElement
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.RelationshipElement_choice`.
        """
        result = types_pb.RelationshipElement_choice()
        relationship_element_to_pb_choice(that, result)
        return result

    def transform_submodel_element_list(
        self,
        that: types.SubmodelElementList
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.SubmodelElementList`.
        """
        result = types_pb.SubmodelElementList()
        submodel_element_list_to_pb(that, result)
        return result

    def transform_submodel_element_collection(
        self,
        that: types.SubmodelElementCollection
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.SubmodelElementCollection`.
        """
        result = types_pb.SubmodelElementCollection()
        submodel_element_collection_to_pb(that, result)
        return result

    def transform_property(
        self,
        that: types.Property
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Property`.
        """
        result = types_pb.Property()
        property_to_pb(that, result)
        return result

    def transform_multi_language_property(
        self,
        that: types.MultiLanguageProperty
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.MultiLanguageProperty`.
        """
        result = types_pb.MultiLanguageProperty()
        multi_language_property_to_pb(that, result)
        return result

    def transform_range(
        self,
        that: types.Range
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Range`.
        """
        result = types_pb.Range()
        range_to_pb(that, result)
        return result

    def transform_reference_element(
        self,
        that: types.ReferenceElement
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.ReferenceElement`.
        """
        result = types_pb.ReferenceElement()
        reference_element_to_pb(that, result)
        return result

    def transform_blob(
        self,
        that: types.Blob
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Blob`.
        """
        result = types_pb.Blob()
        blob_to_pb(that, result)
        return result

    def transform_file(
        self,
        that: types.File
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.File`.
        """
        result = types_pb.File()
        file_to_pb(that, result)
        return result

    def transform_annotated_relationship_element(
        self,
        that: types.AnnotatedRelationshipElement
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.AnnotatedRelationshipElement`.
        """
        result = types_pb.AnnotatedRelationshipElement()
        annotated_relationship_element_to_pb(that, result)
        return result

    def transform_entity(
        self,
        that: types.Entity
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Entity`.
        """
        result = types_pb.Entity()
        entity_to_pb(that, result)
        return result

    def transform_event_payload(
        self,
        that: types.EventPayload
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.EventPayload`.
        """
        result = types_pb.EventPayload()
        event_payload_to_pb(that, result)
        return result

    def transform_basic_event_element(
        self,
        that: types.BasicEventElement
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.BasicEventElement`.
        """
        result = types_pb.BasicEventElement()
        basic_event_element_to_pb(that, result)
        return result

    def transform_operation(
        self,
        that: types.Operation
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Operation`.
        """
        result = types_pb.Operation()
        operation_to_pb(that, result)
        return result

    def transform_operation_variable(
        self,
        that: types.OperationVariable
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.OperationVariable`.
        """
        result = types_pb.OperationVariable()
        operation_variable_to_pb(that, result)
        return result

    def transform_capability(
        self,
        that: types.Capability
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Capability`.
        """
        result = types_pb.Capability()
        capability_to_pb(that, result)
        return result

    def transform_concept_description(
        self,
        that: types.ConceptDescription
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.ConceptDescription`.
        """
        result = types_pb.ConceptDescription()
        concept_description_to_pb(that, result)
        return result

    def transform_reference(
        self,
        that: types.Reference
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Reference`.
        """
        result = types_pb.Reference()
        reference_to_pb(that, result)
        return result

    def transform_key(
        self,
        that: types.Key
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Key`.
        """
        result = types_pb.Key()
        key_to_pb(that, result)
        return result

    def transform_lang_string_name_type(
        self,
        that: types.LangStringNameType
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.LangStringNameType`.
        """
        result = types_pb.LangStringNameType()
        lang_string_name_type_to_pb(that, result)
        return result

    def transform_lang_string_text_type(
        self,
        that: types.LangStringTextType
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.LangStringTextType`.
        """
        result = types_pb.LangStringTextType()
        lang_string_text_type_to_pb(that, result)
        return result

    def transform_environment(
        self,
        that: types.Environment
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Environment`.
        """
        result = types_pb.Environment()
        environment_to_pb(that, result)
        return result

    def transform_embedded_data_specification(
        self,
        that: types.EmbeddedDataSpecification
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.EmbeddedDataSpecification`.
        """
        result = types_pb.EmbeddedDataSpecification()
        embedded_data_specification_to_pb(that, result)
        return result

    def transform_level_type(
        self,
        that: types.LevelType
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.LevelType`.
        """
        result = types_pb.LevelType()
        level_type_to_pb(that, result)
        return result

    def transform_value_reference_pair(
        self,
        that: types.ValueReferencePair
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.ValueReferencePair`.
        """
        result = types_pb.ValueReferencePair()
        value_reference_pair_to_pb(that, result)
        return result

    def transform_value_list(
        self,
        that: types.ValueList
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.ValueList`.
        """
        result = types_pb.ValueList()
        value_list_to_pb(that, result)
        return result

    def transform_lang_string_preferred_name_type_iec_61360(
        self,
        that: types.LangStringPreferredNameTypeIEC61360
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.LangStringPreferredNameTypeIec61360`.
        """
        result = types_pb.LangStringPreferredNameTypeIec61360()
        lang_string_preferred_name_type_iec_61360_to_pb(that, result)
        return result

    def transform_lang_string_short_name_type_iec_61360(
        self,
        that: types.LangStringShortNameTypeIEC61360
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.LangStringShortNameTypeIec61360`.
        """
        result = types_pb.LangStringShortNameTypeIec61360()
        lang_string_short_name_type_iec_61360_to_pb(that, result)
        return result

    def transform_lang_string_definition_type_iec_61360(
        self,
        that: types.LangStringDefinitionTypeIEC61360
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.LangStringDefinitionTypeIec61360`.
        """
        result = types_pb.LangStringDefinitionTypeIec61360()
        lang_string_definition_type_iec_61360_to_pb(that, result)
        return result

    def transform_data_specification_iec_61360(
        self,
        that: types.DataSpecificationIEC61360
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.DataSpecificationIec61360`.
        """
        result = types_pb.DataSpecificationIec61360()
        data_specification_iec_61360_to_pb(that, result)
        return result


_TO_PB_TRANSFORMER = _ToPbTransformer()


def to_pb(
    that: types.Class,
) -> google.protobuf.message.Message:
    """
    Dispatch to-pb conversion to the concrete functions.

    The classes with descendants (i.e., subtypes) are always going to be converted
    to their concrete Protocol Buffer message type instead of the choice (union) type.
    We made this decision with the compactness of messages in mind as choice types
    would occupy a tiny bit more space.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        from aas_core3_protobuf.pbization import to_pb

        instance = types.Extension(
            ... # some constructor arguments
        )

        instance_pb = to_pb(
            instance
        )

        some_bytes = instance_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    return _TO_PB_TRANSFORMER.transform(that)


# endregion To Protocol Buffers


# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.
