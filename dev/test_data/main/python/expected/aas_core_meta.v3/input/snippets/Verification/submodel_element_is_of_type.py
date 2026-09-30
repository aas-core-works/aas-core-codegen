# fmt: off
_AAS_SUBMODEL_ELEMENTS_TO_TYPE: Mapping[
    our_types.AASSubmodelElements,
    type
] = {
    our_types.AASSubmodelElements.ANNOTATED_RELATIONSHIP_ELEMENT:
        our_types.AnnotatedRelationshipElement,

    our_types.AASSubmodelElements.BASIC_EVENT_ELEMENT:
        our_types.BasicEventElement,

    our_types.AASSubmodelElements.BLOB:
        our_types.Blob,

    our_types.AASSubmodelElements.CAPABILITY:
        our_types.Capability,

    our_types.AASSubmodelElements.DATA_ELEMENT:
        our_types.DataElement,

    our_types.AASSubmodelElements.ENTITY:
        our_types.Entity,

    our_types.AASSubmodelElements.EVENT_ELEMENT:
        our_types.EventElement,

    our_types.AASSubmodelElements.FILE:
        our_types.File,

    our_types.AASSubmodelElements.MULTI_LANGUAGE_PROPERTY:
        our_types.MultiLanguageProperty,

    our_types.AASSubmodelElements.OPERATION:
        our_types.Operation,

    our_types.AASSubmodelElements.PROPERTY:
        our_types.Property,

    our_types.AASSubmodelElements.RANGE:
        our_types.Range,

    our_types.AASSubmodelElements.REFERENCE_ELEMENT:
        our_types.ReferenceElement,

    our_types.AASSubmodelElements.RELATIONSHIP_ELEMENT:
        our_types.RelationshipElement,

    our_types.AASSubmodelElements.SUBMODEL_ELEMENT:
        our_types.SubmodelElement,

    our_types.AASSubmodelElements.SUBMODEL_ELEMENT_LIST:
        our_types.SubmodelElementList,

    our_types.AASSubmodelElements.SUBMODEL_ELEMENT_COLLECTION:
        our_types.SubmodelElementCollection,
}
# fmt: on


def _assert_all_types_covered_in_aas_submodel_elements_to_type() -> None:
    """
    Assert that we did not miss a type in :py:attr:`_AAS_SUBMODEL_ELEMENTS_TO_TYPE`.
    """
    missing_literals = [
        literal
        for literal in our_types.AASSubmodelElements
        if literal not in _AAS_SUBMODEL_ELEMENTS_TO_TYPE
    ]

    assert len(missing_literals) == 0, (
        f"Some literals were missed in "
        f"_AAS_SUBMODEL_ELEMENTS_TO_TYPE: {missing_literals!r}"
    )


_assert_all_types_covered_in_aas_submodel_elements_to_type()


def submodel_element_is_of_type(
    element: our_types.SubmodelElement, expected_type: our_types.AASSubmodelElements
) -> bool:
    """
    Check that :paramref:`element` is an instance of class corresponding
    to :paramref:`expected_type`.
    """
    # noinspection PyTypeHints
    return isinstance(element, _AAS_SUBMODEL_ELEMENTS_TO_TYPE[expected_type])
