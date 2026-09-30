def properties_or_ranges_have_value_type(
    elements: Iterable[our_types.SubmodelElement], value_type: our_types.DataTypeDefXSD
) -> bool:
    """
    Check that :paramref:`elements` which are
    :py:class:`.types.Property` or :py:class:`.types.Range`
    have the given :paramref:`value_type`.
    """
    range_or_property = (our_types.Property, our_types.Range)
    for element in elements:
        if isinstance(element, range_or_property):
            if element.value_type is not value_type:
                return False

    return True
