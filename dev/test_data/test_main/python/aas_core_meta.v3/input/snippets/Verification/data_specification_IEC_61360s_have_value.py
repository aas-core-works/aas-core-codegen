def data_specification_iec_61360s_have_value(
    embedded_data_specifications: Iterable[aas_types.EmbeddedDataSpecification],
) -> bool:
    """
    Check that :py:attr:`.types.DataSpecificationIEC61360.value`
    is defined for all data specifications whose content is given as IEC 61360.
    """
    for embedded_data_specification in embedded_data_specifications:
        if isinstance(
            embedded_data_specification.data_specification_content,
            aas_types.DataSpecificationIEC61360,
        ):
            iec61360 = embedded_data_specification.data_specification_content
            if iec61360.value is None:
                return False

    return True
