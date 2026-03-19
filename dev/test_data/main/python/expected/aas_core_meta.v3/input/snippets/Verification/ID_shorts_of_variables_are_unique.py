def id_shorts_of_variables_are_unique(
    input_variables: Optional[List[aas_types.OperationVariable]],
    output_variables: Optional[List[aas_types.OperationVariable]],
    inoutput_variables: Optional[List[aas_types.OperationVariable]],
) -> bool:
    """
    Check that the :py:attr:`.types.Referable.id_short`'s among all the
    :paramref:`input_variables`, :paramref:`output_variables`
    and :paramref:`inoutput_variables` are unique.
    """
    id_short_set = set()
    if input_variables is not None:
        for variable in input_variables:
            if variable.value.id_short is not None:
                if variable.value.id_short in id_short_set:
                    return False

                id_short_set.add(variable.value.id_short)
    if output_variables is not None:
        for variable in output_variables:
            if variable.value.id_short is not None:
                if variable.value.id_short in id_short_set:
                    return False

                id_short_set.add(variable.value.id_short)
    if inoutput_variables is not None:
        for variable in inoutput_variables:
            if variable.value.id_short is not None:
                if variable.value.id_short in id_short_set:
                    return False

                id_short_set.add(variable.value.id_short)
    return True
