"""Generate the test code for the JSON de/serialization of concrete classes."""

from typing import List

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.java import common as java_common, naming as java_naming
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


def generate(
    package: java_common.PackageIdentifier,
    symbol_table: intermediate.SymbolTable,
) -> List[java_common.JavaFile]:
    """
    Generate the test code for the JSON de/serialization of concrete classes.
    """
    blocks = [
        Stripped(
            f"""\
private static void assertSerializeDeserializeEqualsOriginal(JsonNode originalNode, IClass instance, Path path)
{I}throws JsonProcessingException {{
{I}final ObjectMapper objectMapper = new ObjectMapper();

{I}JsonNode serialized = null;
{I}try {{
{II}serialized = Jsonization.Serialize.toJsonObject(instance);
{I}}} catch (Exception exception) {{
{II}fail("Expected no exception upon serialization of an instance " +
{III}"de-serialized from " + path + ", but got: " + exception);
{I}}}

{I}if (serialized == null) {{
{II}fail(
{III}"Unexpected null serialization of an instance from " + path);
{I}}}

assertEquals(objectMapper.readTree(originalNode.toString()), objectMapper.readTree(serialized.toString()));
}}"""
        ),
        Stripped(
            f"""\
private static void assertEqualsExpectedOrRerecordDeserializationException(
{I}Jsonization.DeserializeException exception,
{I}Path path) throws FileNotFoundException, IOException{{
{I}if (exception == null) {{
{II}fail("Expected a Jsonization exception when de-serializing " +
{II}path +
{II}", but got none.");
{I}}} else {{
{II}final Path exceptionPath = Paths.get(path + ".exception");
{II}final String got = exception.getMessage();
{II}if (Common.RECORD_MODE) {{
{III}Files.write(exceptionPath, got.getBytes(StandardCharsets.UTF_8));
{II}}} else {{
if (!Files.exists(exceptionPath)) {{
{I}throw new FileNotFoundException(
{II}"The file with the recorded errors does not exist: "
{III}+ exceptionPath
{III}+ "; maybe you want to set the environment variable "
{III}+ Common.RECORD_MODE_ENVIRONMENT_VARIABLE_NAME);
}}
final String expected =
{I}Files.readAllLines(exceptionPath).stream().collect(Collectors.joining("\\n"));
assertEquals(
{I}expected,
{I}got,
{I}"The expected exception does not match the actual one for the file " + path);
{II}}}
{I}}}
}}"""
        ),
    ]  # type: List[Stripped]

    for concrete_cls in symbol_table.concrete_classes:
        cls_name_java = java_naming.class_name(concrete_cls.name)
        cls_name_json = naming.json_model_type(concrete_cls.name)

        blocks.append(
            Stripped(
                f"""\
@Test
public void test{cls_name_java}Ok() throws IOException {{
{I}final ObjectMapper objectMapper = new ObjectMapper();

{I}final Path searchPath = Paths.get(
{II}Common.TEST_DATA_DIR,
{II}"Json",
{II}"Expected",
{II}{java_common.string_literal(cls_name_json)});
{I}final List<Path> paths = Common.findPaths(searchPath, ".json");

{I}for (Path path : paths) {{
{II}final JsonNode node = objectMapper.readTree(path.toFile());
{II}final {cls_name_java} instance = Jsonization.Deserialize.deserialize{cls_name_java}(node);

{II}final Iterable<Reporting.Error> errorIter = Verification.verify(instance);
{II}final List<Reporting.Error> errors = Common.asList(errorIter);
{II}Common.assertNoVerificationErrors(errors, path);
{I}}}
}} // public void test{cls_name_java}Ok"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
@Test
public void test{cls_name_java}DeserializationFromNonObjectFail() throws IOException {{
{I}final JsonNode node = JsonNodeFactory.instance.textNode("INVALID");

{I}Jsonization.DeserializeException exception = null;
{I}try {{
{II}final {cls_name_java} unused = Jsonization.Deserialize.deserialize{cls_name_java}(node);
{I}}} catch (Jsonization.DeserializeException observedException) {{
{II}exception = observedException;
{I}}}

{I}assert exception != null : "Expected an exception, but got none";
{I}assert exception.getMessage().startsWith("Expected a JsonObject, but got ") :
{II}"Unexpected exception message: " + exception.getMessage();
}} // public void test{cls_name_java}DeserializationFromNonObjectFail"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
@Test
public void test{cls_name_java}DeserializationFail() throws IOException {{
{I}for (Path causeDir :
{II}Common.findDirs(
{III}Paths.get(
{IIII}Common.TEST_DATA_DIR,
{IIII}"Json",
{IIII}"Unexpected",
{IIII}"Unserializable"))) {{
{II}final Path clsDir = causeDir.resolve({java_common.string_literal(cls_name_json)});

{II}if (!Files.exists(clsDir)) {{
{III}// No examples of {cls_name_java} for the failure cause.
{III}continue;
{II}}}

{II}final List<Path> paths = Common.findPaths(clsDir, ".json");
{II}for (Path path : paths) {{
{III}final JsonNode node = CommonJson.readFromFile(path);

{III}Jsonization.DeserializeException exception = null;
{III}try {{
{IIII}final {cls_name_java} var = Jsonization.Deserialize.deserialize{cls_name_java}(node);
{III}}} catch (Jsonization.DeserializeException observedException) {{
{IIII}exception = observedException;
{III}}}

{III}assertEqualsExpectedOrRerecordDeserializationException(
{IIII}exception, path);
{II}}}
{I}}}
}} // public void test{cls_name_java}DeserializationFail"""
            )
        )

        blocks.append(
            Stripped(
                f"""\
@Test
public void test{cls_name_java}VerificationFail() throws IOException {{
{I}for (Path causeDir :
{II}Common.findDirs(
{III}Paths.get(
{IIII}Common.TEST_DATA_DIR,
{IIII}"Json",
{IIII}"Unexpected",
{IIII}"Invalid"))) {{
{II}final Path clsDir = causeDir.resolve({java_common.string_literal(cls_name_json)});

{II}if (!Files.exists(clsDir)) {{
{III}// No examples of {cls_name_java} for the failure cause.
{III}continue;
{II}}}

{II}final List<Path> paths = Common.findPaths(clsDir, ".json");
{II}for (Path path : paths) {{
{III}final JsonNode node = CommonJson.readFromFile(path);

{III}final {cls_name_java} instance = Jsonization.Deserialize.deserialize{cls_name_java}(node);

{III}final Iterable<Reporting.Error> errorIter = Verification.verify(instance);
{III}final List<Reporting.Error> errors = Common.asList(errorIter);
{III}Common.assertEqualsExpectedOrRerecordVerificationErrors(errors, path);
{II}}}
{I}}}
}} // public void test{cls_name_java}VerificationFail"""
            )
        )

    blocks_joined = "\n\n".join(blocks)

    return [
        java_common.JavaFile(
            "TestJsonizationOfConcreteClasses.java",
            f"""\
{java_common.WARNING}

package {package}.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.fail;

import {package}.jsonization.Jsonization;
import {package}.reporting.Reporting;
import {package}.types.impl.*;
import {package}.types.model.IClass;
import {package}.verification.Verification;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;

public class TestJsonizationOfConcreteClasses {{
{I}{indent_but_first_line(blocks_joined, I)}
}} // class TestJsonizationOfConcreteClasses

// package {package}.tests

{java_common.WARNING}
""",
        )
    ]


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
