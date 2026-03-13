# fmt: off
_AAS_SUBMODEL_ELEMENTS_TO_TYPE: Mapping[
    aas_types.AASSubmodelElements,
    type
] = {
    aas_types.AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT:
        aas_types.AnnotatedRelationshipElement,

    aas_types.AASSubmodelElements.BASIC_EVENT_ELEMENT:
        aas_types.BasicEventElement,

    aas_types.AASSubmodelElements.BLOB:
        aas_types.Blob,

    aas_types.AASSubmodelElements.CAPABILITY:
        aas_types.Capability,

    aas_types.AASSubmodelElements.DATA_ELEMENT:
        aas_types.DataElement,

    aas_types.AASSubmodelElements.ENTITY:
        aas_types.Entity,

    aas_types.AASSubmodelElements.EVENT_ELEMENT:
        aas_types.EventElement,

    aas_types.AASSubmodelElements.FILE:
        aas_types.File,

    aas_types.AASSubmodelElements.MULTI_LANGUAGE_PROPERTY:
        aas_types.MultiLanguageProperty,

    aas_types.AASSubmodelElements.OPERATION:
        aas_types.Operation,

    aas_types.AASSubmodelElements.PROPERTY:
        aas_types.Property,

    aas_types.AASSubmodelElements.RANGE:
        aas_types.Range,

    aas_types.AASSubmodelElements.REFERENCE_ELEMENT:
        aas_types.ReferenceElement,

    aas_types.AASSubmodelElements.RELATIONSHIP_ELEMENT:
        aas_types.RelationshipElement,

    aas_types.AASSubmodelElements.SUBMODEL_ELEMENT:
        aas_types.SubmodelElement,

    aas_types.AASSubmodelElements.SUBMODEL_ELEMENT_LIST:
        aas_types.SubmodelElementList,

    aas_types.AASSubmodelElements.SUBMODEL_ELEMENT_COLLECTION:
        aas_types.SubmodelElementCollection,
}
# fmt: on


def _assert_all_types_covered_in_aas_submodel_elements_to_type() -> None:
    """
    Assert that we did not miss a type in :py:attr:`_AAS_SUBMODEL_ELEMENTS_TO_TYPE`.
    """
    missing_literals = [
        literal
        for literal in aas_types.AASSubmodelElements
        if literal not in _AAS_SUBMODEL_ELEMENTS_TO_TYPE
    ]

    assert len(missing_literals) == 0, (
        f"Some literals were missed in "
        f"_AAS_SUBMODEL_ELEMENTS_TO_TYPE: {missing_literals!r}"
    )


_assert_all_types_covered_in_aas_submodel_elements_to_type()


def submodel_element_is_of_type(
    element: aas_types.SubmodelElement, expected_type: aas_types.AASSubmodelElements
) -> bool:
    """
    Check that :paramref:`element` is an instance of class corresponding
    to :paramref:`expected_type`.
    """
    # noinspection PyTypeHints
    return isinstance(element, _AAS_SUBMODEL_ELEMENTS_TO_TYPE[expected_type])
