def id_shorts_are_unique(referables: Iterable[aas_types.Referable]) -> bool:
    """
    Check that all :py:attr:`.types.Referable.id_short` are unique
    among :paramref:`referables`.
    """
    id_short_set = set()  # type: Set[str]
    for referable in referables:
        if referable.id_short in id_short_set:
            return False

        if referable.id_short is not None:
            id_short_set.add(referable.id_short)

    return True
