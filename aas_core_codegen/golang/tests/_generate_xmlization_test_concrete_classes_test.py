"""Generate code to test the XML de/serialization of concrete classes."""

import io
from typing import List

from icontract import ensure

from aas_core_codegen import intermediate, naming
from aas_core_codegen.common import (
    Stripped,
    Identifier,
)
from aas_core_codegen.golang import common as golang_common, naming as golang_naming
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)


def _generate_for_cls(cls: intermediate.ConcreteClass) -> List[Stripped]:
    """Generate the tests for a self-contained class."""
    xml_class_name_literal = golang_common.string_literal(
        naming.xml_class_name(cls.name)
    )

    unmarshal_function = golang_naming.function_name(Identifier("unmarshal"))

    blocks = []  # type: List[Stripped]

    interface_name = golang_naming.interface_name(cls.name)

    test_name = golang_naming.function_name(
        Identifier(f"Test_{cls.name}_round_trip_OK")
    )

    blocks.append(
        Stripped(
            f"""\
func {test_name}(t *testing.T) {{
{I}pths := aastesting.FindFilesBySuffixRecursively(
{II}filepath.Join(
{III}aastesting.TestDataDir,
{III}"Xml",
{III}"Expected",
{III}{xml_class_name_literal},
{II}),
{II}".xml",
{I})
{I}sort.Strings(pths)

{I}for _, pth := range pths {{
{II}bb, err := os.ReadFile(pth)
{II}if err != nil {{
{III}t.Fatalf("Failed to read the file %s: %s", pth, err.Error())
{III}return
{II}}}
{II}text := string(bb)

{II}decoder := xml.NewDecoder(strings.NewReader(text))

{II}deserialized, deseriaErr := aasxmlization.{unmarshal_function}(decoder)
{II}ok := assertNoDeserializationError(t, deseriaErr, pth)
{II}if !ok {{
{III}return
{II}}}

{II}if _, ok := deserialized.(aastypes.{interface_name}); !ok {{
{III}t.Fatalf(
{IIII}"Expected an instance of {interface_name}, "+
{IIIII}"but got %T: %v",
{IIII}deserialized, deserialized,
{III})
{III}return
{II}}}

{II}buf := &bytes.Buffer{{}}
{II}encoder := xml.NewEncoder(buf)
{II}encoder.Indent("", "\\t")

{II}seriaErr := aasxmlization.Marshal(encoder, deserialized, true)
{II}ok = assertNoSerializationError(t, seriaErr, pth)
{II}if !ok {{
{III}return
{II}}}

{II}roundTrip := string(buf.Bytes())

{II}ok = assertSerializationEqualsDeserialization(
{III}t,
{III}text,
{III}roundTrip,
{III}pth,
{II})
{II}if !ok {{
{III}return
{II}}}
{I}}}
}}"""
        )
    )

    test_name = golang_naming.function_name(
        Identifier(f"Test_{cls.name}_deserialization_fail")
    )

    blocks.append(
        Stripped(
            f"""\
func {test_name}(t *testing.T) {{
{I}pattern := filepath.Join(
{II}aastesting.TestDataDir,
{II}"Xml",
{II}"Unexpected",
{II}"Unserializable",
{II}"*",  // This asterisk represents the cause.
{II}{xml_class_name_literal},
{I})

{I}causeDirs, err := filepath.Glob(pattern)
{I}if err != nil {{
{II}panic(
{III}fmt.Sprintf(
{IIII}"Failed to find cause directories matching %s: %s",
{IIII}pattern, err.Error(),
{III}),
{II})
{I}}}

{I}for _, causeDir := range causeDirs {{
{II}pths := aastesting.FindFilesBySuffixRecursively(
{III}causeDir,
{III}".xml",
{II})
{II}sort.Strings(pths)

{II}for _, pth := range pths {{
{III}relPth, err := filepath.Rel(aastesting.TestDataDir, pth)
{III}if err != nil {{
{IIII}panic(
{IIIII}fmt.Sprintf(
{IIIII}{I}"Failed to compute the relative path of %s to %s: %s",
{IIIII}{I}aastesting.TestDataDir, pth, err.Error(),
{IIIII}),
{IIII})
{III}}}

{III}expectedPth := filepath.Join(
{IIII}aastesting.TestDataDir,
{IIII}"DeserializationError",
{IIII}filepath.Dir(relPth),
{IIII}filepath.Base(relPth)+".error",
{III})

{III}bb, err := os.ReadFile(pth)
{III}if err != nil {{
{IIII}t.Fatalf("Failed to read the file %s: %s", pth, err.Error())
{IIII}return
{III}}}
{III}text := string(bb)

{III}decoder := xml.NewDecoder(strings.NewReader(text))

{III}_, deseriaErr := aasxmlization.Unmarshal(decoder)
{III}ok := assertIsDeserializationErrorAndEqualsExpectedOrRecord(
{IIII}t, deseriaErr, pth, expectedPth,
{III})
{III}if !ok {{
{IIII}return
{III}}}
{II}}}
{I}}}
}}"""
        )
    )

    return blocks


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(symbol_table: intermediate.SymbolTable, repo_url: Stripped) -> str:
    """Generate code to test the XML de/serialization of concrete classes."""
    blocks = [
        Stripped("package xmlization_test"),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}"bytes"
{I}"path/filepath"
{I}"fmt"
{I}"os"
{I}"sort"
{I}"strings"
{I}"testing"
{I}"encoding/xml"
{I}aastesting "{repo_url}/aastesting"
{I}aastypes "{repo_url}/types"
{I}aasxmlization "{repo_url}/xmlization"
)"""
        ),
    ]  # type: List[Stripped]

    for concrete_cls in symbol_table.concrete_classes:
        blocks.extend(_generate_for_cls(cls=concrete_cls))

    blocks.append(golang_common.WARNING)

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
