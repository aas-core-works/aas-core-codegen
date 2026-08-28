"""Generate code to test the ``Descend`` methods and ``VisitorThrough``."""

from typing import List

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Identifier, Stripped, indent_but_first_line
from aas_core_codegen.java import common as java_common, naming as java_naming
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)


def generate(
    package: java_common.PackageIdentifier,
    symbol_table: intermediate.SymbolTable,
) -> List[java_common.JavaFile]:
    """
    Generate code to test the ``Descend`` methods and ``VisitorThrough``.
    """
    # NOTE (mristin):
    # ``Identifiable`` and ``Referable`` are not universally defined in every
    # meta-model (they stem from the Asset Administration Shell meta-model), so
    # we only refer to their corresponding Java interfaces, ``IIdentifiable``
    # and ``IReferable``, if they are actually defined. Otherwise, the import
    # would not resolve and the generated code would not compile.
    has_identifiable = symbol_table.find_our_type(Identifier("Identifiable")) is not None
    has_referable = symbol_table.find_our_type(Identifier("Referable")) is not None

    trace_branches = []  # type: List[str]
    if has_identifiable:
        trace_branches.append(
            f"""\
if (instance instanceof IIdentifiable) {{
{I}return instance.getClass().getSimpleName() + " with ID " + (((IIdentifiable) instance).getId());
}}"""
        )
    if has_referable:
        trace_branches.append(
            f"""\
if (instance instanceof IReferable) {{
{I}return instance.getClass().getSimpleName() + " with ID-short " + (((IReferable) instance).getIdShort());
}}"""
        )

    if len(trace_branches) == 0:
        trace_body = f"{I}return instance.getClass().getSimpleName();"
    else:
        trace_body = (
            " else ".join(trace_branches)
            + f""" else {{
{I}return instance.getClass().getSimpleName();
}}"""
        )
        trace_body = indent_but_first_line(trace_body, I)

    blocks = [
        Stripped(
            f"""\
private class TracingVisitorThrough extends VisitorThrough {{
{I}public final List<String> log = new ArrayList<>();

{I}@Override
{I}public void visit(IClass that) {{
{II}log.add(trace(that));
{II}super.visit(that);
{I}}}
}}"""
        ),
        Stripped(
            f"""\
private String trace(IClass instance) {{
{trace_body}
}}"""
        ),
        Stripped(
            f"""\
private void assertDescendAndVisitorThroughSame(IClass instance)
{{
{I}final List<String> logFromDescend = new ArrayList<>();

{I}for (IClass subInstance : instance.descend()) {{
{II}logFromDescend.add(trace(subInstance));
{I}}}

{I}final TracingVisitorThrough visitor = new TracingVisitorThrough();
{I}visitor.visit(instance);
{I}final List<String> traceFromVisitor = visitor.log;

{I}assertFalse(traceFromVisitor.isEmpty());

{I}assertEquals(trace(instance), traceFromVisitor.get(0));

{I}traceFromVisitor.remove(0);

{I}assertTrue(traceFromVisitor.equals(logFromDescend));
}}"""
        ),
        Stripped(
            f"""\
private void compareOrRerecordTrace(IClass instance, Path expectedPath) throws IOException {{
{I}final StringBuilder stringBuilder = new StringBuilder();
{I}for (IClass descendant : instance.descend()) {{
{II}stringBuilder.append(Common.trace(descendant));
{I}}}

{I}final String got = stringBuilder.toString();
{I}if (Common.RECORD_MODE) {{
{II}Files.createDirectories(expectedPath.getParent());
{II}Files.write(expectedPath, got.getBytes());
{I}}} else {{
{II}if (!Files.exists(expectedPath)) {{
{III}throw new FileNotFoundException(
{IIIII}"The file with the recorded value does not exist: " + expectedPath);
{II}}}
{II}final String expected =
{IIII}Files.readAllLines(expectedPath).stream().collect(Collectors.joining("\\n"));
{II}assertEquals(expected.replace("\\n", ""), got.replace("\\n", ""));
{I}}}
}}"""
        ),
    ]  # type: List[str]

    for concrete_cls in symbol_table.concrete_classes:
        cls_name_java = java_naming.class_name(concrete_cls.name)
        cls_name_json = naming.json_model_type(concrete_cls.name)

        blocks.append(
            Stripped(
                f"""\
@Test
public void testDescendOf{cls_name_java}() throws IOException {{
{I}final {cls_name_java} instance = CommonJsonization.loadMaximal{cls_name_java}();

{I}compareOrRerecordTrace(
{II}instance,
{II}Paths.get(
{III}Common.TEST_DATA_DIR,
{III}"Descend",
{III}{java_common.string_literal(cls_name_json)},
{III}"maximal.json.trace"));
}} // public void testDescendOf{cls_name_java}

@Test
public void testDescendAgainstVisitorThroughFor{cls_name_java}() throws IOException {{
{I}{cls_name_java} instance = (
{II}CommonJsonization.loadMaximal{cls_name_java}());

{I}assertDescendAndVisitorThroughSame(instance);
}} // public void testDescendAgainstVisitorThroughFor{cls_name_java}"""
            )
        )

    blocks_joined = "\n\n".join(blocks)

    optional_imports = []  # type: List[str]
    if has_identifiable:
        optional_imports.append(f"import {package}.types.model.IIdentifiable;")
    if has_referable:
        optional_imports.append(f"import {package}.types.model.IReferable;")
    optional_imports_joined = (
        "\n" + "\n".join(optional_imports) if len(optional_imports) > 0 else ""
    )

    return [
        java_common.JavaFile(
            "TestDescendAndVisitorThrough.java",
            f"""\
{java_common.WARNING}

package {package}.tests;

import static org.junit.jupiter.api.Assertions.*;

import {package}.types.impl.*;
import {package}.types.model.IClass;{optional_imports_joined}
import {package}.visitation.VisitorThrough;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;

public class TestDescendAndVisitorThrough {{
{I}{indent_but_first_line(blocks_joined, II)}
}} // class TestDescendAndVisitorThrough

// package {package}.tests

{java_common.WARNING}
""",
        )
    ]


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
