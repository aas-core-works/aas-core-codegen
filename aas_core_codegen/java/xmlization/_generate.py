"""Generate Java code for XML-ization based on the intermediate representation."""
from typing import (
    Tuple,
    Optional,
    List
)

from icontract import ensure

from aas_core_codegen.common import (
    Error,
    Stripped,
)
from aas_core_codegen import (
    intermediate,
    specific_implementations,
)
from aas_core_codegen.java import (
    common as java_common,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
)

# region Generate


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
    symbol_table: intermediate.SymbolTable,
    package: java_common.PackageIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the Java code for the general serialization.

    The ``package`` defines the root Java package.
    """
    errors = []  # type: List[Error]

    imports = [
        Stripped("import java.util.Optional;")
    ]  # type: List[Stripped]

    xml_namespace_literal = java_common.string_literal(
        symbol_table.meta_model.xml_namespace
    )

    xmlization_blocks = [
        Stripped(f"""\
/**
 * Represent a critical error during the deserialization.
 */
class DeserializeException extends RuntimeException{{
{I}private final String path;
{I}private final String reason;

{I}public DeserializeException(String path, String reason) {{
{II}super(reason + " at: " + ("".equals(path) ? "the beginning" : path));
{II}this.path = path;
{II}this.reason = reason;
{I}}}

{I}public Optional<String> getPath() {{
{II}return Optional.ofNullable(path);
{I}}}

{I}public Optional<String> getReason() {{
{II}return Optional.ofNullable(reason);
{I}}}
}}"""
        ),
        Stripped(f"""\
/**
 * Provide de/serialization of meta-model classes to/from XML.
 */
public class Xmlization
{{
{I}/**
{I} * The XML namespace of the meta-model
{I} */
{I}public static final String AAS_NAME_SPACE =
{II}{xml_namespace_literal};
}}"""
        )
    ]  # type: List[Stripped]

    if len(errors) > 0:
        return None, errors

    blocks = [
        java_common.WARNING,
        Stripped(f"package {package}.xmlization;"),
        Stripped("\n".join(imports)),
        Stripped("\n\n".join(xmlization_blocks)),
        java_common.WARNING,
    ]  # type: List[Stripped]

    code = "\n\n".join(blocks)

    return f"{code}\n", None


# endregion
