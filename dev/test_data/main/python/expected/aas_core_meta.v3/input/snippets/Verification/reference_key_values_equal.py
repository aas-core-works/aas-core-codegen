def reference_key_values_equal(
    that: our_types.Reference, other: our_types.Reference
) -> bool:
    """
    Check that the two references, :paramref:`that` and :paramref:`other`,
    are equal by comparing their :py:attr:`.types.Reference.keys`
    by :py:attr:`.types.Key.value`'s.
    """
    if len(that.keys) != len(other.keys):
        return False

    for that_key, other_key in zip(that.keys, other.keys):
        if that_key.value != other_key.value:
            return False

    return True
