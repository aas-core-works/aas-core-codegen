"""Generate the RDF ontology and the SHACL schema corresponding to the meta-model."""

import pathlib
from typing import TextIO

import aas_core_codegen
import aas_core_codegen.rdf_shacl.rdf
import aas_core_codegen.rdf_shacl.shacl
from aas_core_codegen import specific_implementations, run
from aas_core_codegen.rdf_shacl import common as rdf_shacl_common


class Parameters:
    """Represent the program parameters."""

    def __init__(
        self,
        model_path: pathlib.Path,
        snippets_dir: pathlib.Path,
        output_dir: pathlib.Path,
    ) -> None:
        """Initialize with the given values."""
        self.model_path = model_path
        self.snippets_dir = snippets_dir
        self.output_dir = output_dir


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    # region Dependencies

    class_to_rdfs_range, error = rdf_shacl_common.map_class_to_rdfs_range(
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )
    if error:
        run.write_error_report(
            message=f"Failed to determine the mapping symbol 🠒 ``rdfs:range`` "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert class_to_rdfs_range is not None

    url_prefix_key = specific_implementations.ImplementationKey("url_prefix.txt")
    url_prefix = context.spec_impls.get(url_prefix_key, None)
    if url_prefix is None:
        stderr.write(
            f"The implementation snippet for the URL prefix of the ontology "
            f"is missing: {url_prefix_key}\n"
        )
        return 1

    # endregion

    # region RDF ontology

    rdf_code, errors = aas_core_codegen.rdf_shacl.rdf.generate(
        symbol_table=context.symbol_table,
        class_to_rdfs_range=class_to_rdfs_range,
        spec_impls=context.spec_impls,
        url_prefix=url_prefix,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the RDF ontology "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert rdf_code is not None

    pth = context.output_dir / "rdf-ontology.ttl"
    try:
        pth.write_text(rdf_code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the RDF ontology to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    # region SHACL schema

    shacl_code, errors = aas_core_codegen.rdf_shacl.shacl.generate(
        symbol_table=context.symbol_table,
        class_to_rdfs_range=class_to_rdfs_range,
        spec_impls=context.spec_impls,
        url_prefix=url_prefix,
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the SHACL schema "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert shacl_code is not None

    pth = context.output_dir / "shacl-schema.ttl"
    try:
        pth.write_text(shacl_code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the SHACL schema to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    # endregion

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
