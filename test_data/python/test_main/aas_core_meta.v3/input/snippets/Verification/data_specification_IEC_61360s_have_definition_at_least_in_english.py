def data_specification_iec_61360s_have_definition_at_least_in_english(
    embedded_data_specifications: Iterable[aas_types.EmbeddedDataSpecification],
) -> bool:
    """
    Check that :py:attr:`.types.DataSpecificationIEC61360.definition`
    is defined for all data specifications whose content is given as IEC 61360
    at least in English.
    """
    for embedded_data_specification in embedded_data_specifications:
        if isinstance(
            embedded_data_specification.data_specification_content,
            aas_types.DataSpecificationIEC61360,
        ):
            iec61360 = embedded_data_specification.data_specification_content
            if iec61360.definition is None:
                return False

            no_definition_in_english = True
            for lang_string in iec61360.definition:
                if is_bcp_47_for_english(lang_string.language):
                    no_definition_in_english = False
                    break

            if no_definition_in_english:
                return False

    return True
