def qualifier_types_are_unique(qualifiers: Iterable[aas_types.Qualifier]) -> bool:
    """
    Check that there are no duplicate
    :py:attr:`.types.Qualifier.type`'s
    in the :paramref:`qualifiers`.
    """
    type_set = set()  # type: Set[str]
    for qualifier in qualifiers:
        if qualifier.type in type_set:
            return False

        type_set.add(qualifier.type)

    return True
