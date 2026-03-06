"""Provide functions shared across all the generators."""


def assert_module_docstring_and_generate_header_consistent(
    module_doc: str, generate_header_doc: str
) -> None:
    """Check that the two docstrings are consistent and raise an exception otherwise."""
    generate_code_text = "Generate code "
    if not module_doc.startswith(generate_code_text):
        raise ValueError(
            f"Expected the module docstring to start "
            f"with {generate_code_text!r}, but got: {module_doc}"
        )

    generate_header_text = "Generate header "
    if not generate_header_doc.startswith(generate_header_text):
        raise ValueError(
            f"Expected the header generator docstring to start "
            f"with {generate_header_text!r}, "
            f"but got: {generate_header_doc}"
        )

    suffix_module_doc = module_doc[len(generate_code_text) :]
    suffix_generate_header_doc = generate_header_doc[len(generate_header_text) :]

    if not suffix_generate_header_doc.startswith(suffix_module_doc):
        raise ValueError(
            f"Expected the header generator docstring "
            f"to include the part of the module docstring, "
            f"but got: {generate_header_doc!r} and "
            f"the module docstring was {module_doc!r}"
        )


def assert_module_docstring_and_generate_implementation_consistent(
    module_doc: str, generate_implementation_doc: str
) -> None:
    """Check that the two docstrings are consistent and raise an exception otherwise."""
    generate_code_text = "Generate code "
    if not module_doc.startswith(generate_code_text):
        raise ValueError(
            f"Expected the module docstring to start "
            f"with {generate_code_text!r}, but got: {module_doc}"
        )

    generate_implementation_text = "Generate implementation "
    if not generate_implementation_doc.startswith(generate_implementation_text):
        raise ValueError(
            f"Expected the implementation generator docstring to start "
            f"with {generate_implementation_text!r}, "
            f"but got: {generate_implementation_doc}"
        )

    suffix_module_doc = module_doc[len(generate_code_text) :]
    suffix_generate_implementation_doc = generate_implementation_doc[
        len(generate_implementation_text) :
    ]

    if not suffix_generate_implementation_doc.startswith(suffix_module_doc):
        raise ValueError(
            f"Expected the implementation generator docstring "
            f"to include the part of the module docstring, "
            f"but got: {generate_implementation_doc!r} and "
            f"the module docstring was {module_doc!r}"
        )
