# fmt: off
_AAS_SUBMODEL_ELEMENTS_TO_TYPE: Mapping[
    aas_types.AasSubmodelElements,
    type
] = {
    aas_types.AasSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT:
        aas_types.AnnotatedRelationshipElement,

    aas_types.AasSubmodelElements.BASIC_EVENT_ELEMENT:
        aas_types.BasicEventElement,

    aas_types.AasSubmodelElements.BLOB:
        aas_types.Blob,

    aas_types.AasSubmodelElements.CAPABILITY:
        aas_types.Capability,

    aas_types.AasSubmodelElements.DATA_ELEMENT:
        aas_types.DataElement,

    aas_types.AasSubmodelElements.ENTITY:
        aas_types.Entity,

    aas_types.AasSubmodelElements.EVENT_ELEMENT:
        aas_types.EventElement,

    aas_types.AasSubmodelElements.FILE:
        aas_types.File,

    aas_types.AasSubmodelElements.MULTI_LANGUAGE_PROPERTY:
        aas_types.MultiLanguageProperty,

    aas_types.AasSubmodelElements.OPERATION:
        aas_types.Operation,

    aas_types.AasSubmodelElements.PROPERTY:
        aas_types.Property,

    aas_types.AasSubmodelElements.RANGE:
        aas_types.Range,

    aas_types.AasSubmodelElements.REFERENCE_ELEMENT:
        aas_types.ReferenceElement,

    aas_types.AasSubmodelElements.RELATIONSHIP_ELEMENT:
        aas_types.RelationshipElement,

    aas_types.AasSubmodelElements.SUBMODEL_ELEMENT:
        aas_types.SubmodelElement,

    aas_types.AasSubmodelElements.SUBMODEL_ELEMENT_LIST:
        aas_types.SubmodelElementList,

    aas_types.AasSubmodelElements.SUBMODEL_ELEMENT_COLLECTION:
        aas_types.SubmodelElementCollection,
}
# fmt: on


def _assert_all_types_covered_in_aas_submodel_elements_to_type() -> None:
    """
    Assert that we did not miss a type in :py:attr:`_AAS_SUBMODEL_ELEMENTS_TO_TYPE`.
    """
    missing_literals = [
        literal
        for literal in aas_types.AasSubmodelElements
        if literal not in _AAS_SUBMODEL_ELEMENTS_TO_TYPE
    ]

    assert len(missing_literals) == 0, (
        f"Some literals were missed in "
        f"_AAS_SUBMODEL_ELEMENTS_TO_TYPE: {missing_literals!r}"
    )


_assert_all_types_covered_in_aas_submodel_elements_to_type()


def submodel_element_is_of_type(
        element: aas_types.SubmodelElement,
        expected_type: aas_types.AasSubmodelElements
) -> bool:
    """
    Check that :paramref:`element` is an instance of class corresponding
    to :paramref:`expected_type`.
    """
    # noinspection PyTypeHints
    return isinstance(
        element,
        _AAS_SUBMODEL_ELEMENTS_TO_TYPE[expected_type]
    )
