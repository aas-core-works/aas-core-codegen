def data_specification_iec_61360s_for_property_or_value_have_appropriate_data_type(
    embedded_data_specifications: Iterable[aas_types.EmbeddedDataSpecification],
) -> bool:
    """
    Check that :py:attr:`.types.DataSpecificationIEC61360.data_type`
    is defined appropriately for all data specifications whose content is given
    as IEC 61360.
    """
    for embedded_data_specification in embedded_data_specifications:
        if isinstance(
            embedded_data_specification.data_specification_content,
            aas_types.DataSpecificationIEC61360,
        ):
            iec61360 = embedded_data_specification.data_specification_content
            if (
                iec61360.data_type is None
                or iec61360.data_type
                not in aas_constants.DATA_TYPE_IEC_61360_FOR_PROPERTY_OR_VALUE
            ):
                return False

    return True
