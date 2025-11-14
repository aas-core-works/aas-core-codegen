def lang_strings_have_unique_languages(
    lang_strings: Iterable[aas_types.AbstractLangString],
) -> bool:
    """
    Check that :paramref:`lang_strings` are specified each for a unique
    language.
    """
    language_set = set()  # type: Set[str]
    for lang_string in lang_strings:
        if lang_string.language in language_set:
            return False

        language_set.add(lang_string.language)

    return True
