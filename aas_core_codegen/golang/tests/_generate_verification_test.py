"""Generate the code to test the verification."""

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
    INDENT6 as IIIIII,
)


def _generate_for_cls(cls: intermediate.ConcreteClass) -> List[Stripped]:
    """Generate the tests for a class."""
    model_type_literal = golang_common.string_literal(naming.json_model_type(cls.name))

    deserialization_function = golang_naming.function_name(
        Identifier(f"{cls.name}_from_jsonable")
    )

    blocks = []  # type: List[Stripped]

    test_name = golang_naming.function_name(Identifier(f"Test_{cls.name}_OK"))

    blocks.append(
        Stripped(
            f"""\
func {test_name}(t *testing.T) {{
{I}pths := aastesting.FindFilesBySuffixRecursively(
{II}filepath.Join(
{III}aastesting.TestDataDir,
{III}"Json",
{III}"Expected",
{III}{model_type_literal},
{II}),
{II}".json",
{I})
{I}sort.Strings(pths)

{I}for _, pth := range pths {{
{II}jsonable := aastesting.MustReadJsonable(
{III}pth,
{II})

{II}deserialized, deseriaErr := aasjsonization.{deserialization_function}(
{III}jsonable,
{II})
{II}if deseriaErr != nil {{
{III}t.Fatalf(
{IIII}"Unexpected deserialization error from %s: %s",
{IIII}pth, deseriaErr.Error(),
{III})
{III}return
{II}}}

{II}var errors []*aasverification.VerificationError
{II}aasverification.Verify(
{III}deserialized,
{III}func(veriErr *aasverification.VerificationError) (abort bool) {{
{IIII}errors = append(errors, veriErr)
{IIII}return
{III}}},
{II})

{II}ok := assertNoVerificationErrors(
{III}t,
{III}deserialized,
{III}pth,
{II})
{II}if !ok {{
{III}return
{II}}}
{I}}}
}}"""
        )
    )

    test_name = golang_naming.function_name(Identifier(f"Test_{cls.name}_fail"))

    blocks.append(
        Stripped(
            f"""\
func {test_name}(t *testing.T) {{
{I}pattern := filepath.Join(
{II}aastesting.TestDataDir,
{II}"Json",
{II}"Unexpected",
{II}"Invalid",
{II}"*",  // This asterisk represents the cause.
{II}{model_type_literal},
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
{III}".json",
{II})
{II}sort.Strings(pths)

{II}for _, pth := range pths {{
{III}jsonable := aastesting.MustReadJsonable(
{IIII}pth,
{III})

{III}relPth, err := filepath.Rel(aastesting.TestDataDir, pth)
{III}if err != nil {{
{IIII}panic(
{IIIII}fmt.Sprintf(
{IIIIII}"Failed to compute the relative path of %s to %s: %s",
{IIIIII}aastesting.TestDataDir, pth, err.Error(),
{IIIII}),
{IIII})
{III}}}

{III}expectedPth := filepath.Join(
{IIII}aastesting.TestDataDir,
{IIII}"VerificationError",
{IIII}filepath.Dir(relPth),
{IIII}filepath.Base(relPth)+".errors",
{III})

{III}deserialized, deseriaErr := aasjsonization.{deserialization_function}(
{IIII}jsonable,
{III})
{III}if deseriaErr != nil {{
{IIII}t.Fatalf(
{IIIII}"Unexpected deserialization error from %s: %s",
{IIIII}pth, deseriaErr.Error(),
{IIII})
{IIII}return
{III}}}

{III}var errors []*aasverification.VerificationError
{III}aasverification.Verify(
{IIII}deserialized,
{IIII}func(err *aasverification.VerificationError) (abort bool) {{
{IIIII}errors = append(errors, err)
{IIIII}return
{IIII}}},
{III})

{III}ok := assertEqualsExpectedOrRerecordVerificationErrors(
{IIII}t,
{IIII}errors,
{IIII}pth,
{IIII}expectedPth,
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
    """Generate the code to test the verification."""
    blocks = [
        Stripped("package verification_test"),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}"encoding/json"
{I}"fmt"
{I}"os"
{I}"path/filepath"
{I}"sort"
{I}"strings"
{I}"testing"
{I}aasjsonization "{repo_url}/jsonization"
{I}aastesting "{repo_url}/aastesting"
{I}aastypes "{repo_url}/types"
{I}aasverification "{repo_url}/verification"
)"""
        ),
        Stripped(
            f"""\
// Assert that there are no verification errors in the `instance` de-serialized
// from `source`.
func assertNoVerificationErrors(
{I}t *testing.T,
{I}instance aastypes.IClass,
{I}source string,
) (ok bool) {{
{I}errors := make([]*aasverification.VerificationError, 0)
{I}aasverification.Verify(
{II}instance,
{II}func(err *aasverification.VerificationError) (abort bool) {{
{III}errors = append(errors, err)
{III}return
{II}}},
{I})

{I}ok = true
{I}if len(errors) > 0 {{
{II}ok = false

{II}var sb strings.Builder

{II}sb.WriteString(
{III}fmt.Sprintf(
{IIII}"Expected no errors when verifying the instance de-serialized from "+
{IIIII}"%s, but got %d error(s)\\n",
{IIII}source, len(errors),
{III}),
{II})

{II}for i, err := range errors {{
{III}sb.WriteString(
{IIII}fmt.Sprintf(
{IIIII}"Error %d:\\n%s: %s\\n",
{IIIII}i+1,
{IIIII}err.PathString(),
{IIIII}err.Message,
{IIII}),
{III})
{II}}}

{II}jsonable, seriaErr := aasjsonization.ToJsonable(instance)
{II}if seriaErr != nil {{
{III}panic(
{IIII}fmt.Sprintf(
{IIIII}"Failed to serialize instance to JSON obtained from %s: %s",
{IIIII}source, seriaErr.Error(),
{IIII}),
{III})
{II}}}
{II}jsonableBytes, err := json.Marshal(jsonable)
{II}if err != nil {{
{III}panic(
{IIII}fmt.Sprintf(
{IIIII}"Failed to marshal to JSON an instance serialized from %s: %s",
{IIIII}source, err.Error(),
{IIII}),
{III})
{II}}}

{II}sb.WriteString("Instance:\\n")
{II}sb.WriteString(string(jsonableBytes))

{II}t.Fatal(sb.String())
{I}}}
{I}return
}}"""
        ),
        Stripped(
            f"""\
// Assert that either the verification errors match the recorded ones at `pth`, if
// [aastesting.RecordMode] is set, or re-record the verification errors at `pth`.
func assertEqualsExpectedOrRerecordVerificationErrors(
{I}t *testing.T,
{I}errors []*aasverification.VerificationError,
{I}source string,
{I}expectedPth string,
) (ok bool) {{
{I}ok = true
{I}if len(errors) == 0 {{
{II}ok = false
{II}t.Fatalf(
{III}"Expected at least one verification error, "+
{IIII}"but got none when verifying the model loaded from: %s",
{III}source,
{II})
{I}}}

{I}parts := make([]string, len(errors))
{I}for i, verErr := range errors {{
{II}parts[i] = fmt.Sprintf(
{III}"%s: %s",
{III}verErr.PathString(),
{III}verErr.Message,
{II})
{I}}}

{I}// Add a newline for POSIX systems
{I}got := strings.Replace(strings.Join(parts, ";\\n"), "\\r\\n", "\\n", -1) + "\\n"

{I}if aastesting.RecordMode {{
{II}parent := filepath.Dir(expectedPth)
{II}err := os.MkdirAll(parent, os.ModePerm)
{II}if err != nil {{
{III}panic(
{IIII}fmt.Sprintf(
{IIIII}"Failed to create the directory %s: %s", parent, err.Error(),
{IIII}),
{III})
{II}}}

{II}err = os.WriteFile(expectedPth, []byte(got), 0644)
{II}if err != nil {{
{III}ok = false
{III}t.Fatalf("Failed to write to %s: %s", expectedPth, err.Error())
{III}return
{II}}}
{I}}} else {{
{II}_, err := os.Stat(expectedPth)
{II}if err != nil {{
{III}ok = false
{III}t.Fatalf(
{IIII}"Failed to stat the file %s: %s; if the file does not exist, "+
{IIIII}"you probably want to record the test data by "+
{IIIII}"setting the environment variable %s",
{IIII}expectedPth, err.Error(), aastesting.RecordModeEnvironmentVariableName,
{III})
{III}return
{II}}}

{II}var bb []byte
{II}bb, err = os.ReadFile(expectedPth)
{II}if err != nil {{
{III}ok = false
{III}t.Fatalf("Failed to read from %s: %s", expectedPth, err.Error())
{III}return
{II}}}
{II}expected := strings.ReplaceAll(string(bb), "\\r\\n", "\\n")

{II}if expected != got {{
{III}ok = false
{III}t.Fatalf(
{IIII}"The expected verification errors (read from %s) in the model "+
{IIIII}"de-serialized from %s do not match the obtained ones. "+
{IIIII}"Expected:\\n%s\\nGot:\\n%s",
{IIII}expectedPth, source, expected, got,
{III})
{III}return
{II}}}
{I}}}
{I}return
}}"""
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
