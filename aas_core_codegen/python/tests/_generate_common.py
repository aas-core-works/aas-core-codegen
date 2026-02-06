"""Generate the shared code used across the unit tests."""
import io

from icontract import ensure

from aas_core_codegen.common import Stripped
from aas_core_codegen.python import (
    common as python_common,
)
from aas_core_codegen.python.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(aas_module: python_common.QualifiedModuleName) -> str:
    """
    Generate the Python code shared across unit tests.

    The ``aas_module`` indicates the fully-qualified name of the base module.
    """
    blocks = [
        Stripped(
            '"""Provide functionality used across the tests."""',
        ),
        python_common.WARNING,
        Stripped(
            """\
import base64
import collections.abc
import difflib
import enum
import io
import os
import pathlib
import textwrap
from typing import Union, Sequence"""
        ),
        Stripped(
            f"""\
import {aas_module}.common as aas_common
import {aas_module}.types as aas_types"""
        ),
        Stripped(
            """\
_REPO_ROOT = pathlib.Path(os.path.realpath(__file__)).parent.parent"""
        ),
        Stripped(
            '''\
#: Path to the directory which contains input and golden files
TEST_DATA_DIR = _REPO_ROOT / "test_data"'''
        ),
        Stripped(
            f"""\
#: If set, the golden files in the tests should be re-recorded instead
#: of checked against.
RECORD_MODE = os.environ.get("AAS_CORE3_1_PYTHON_TESTS_RECORD_MODE", "").lower() in (
{I}"1",
{I}"on",
{I}"true",
)"""
        ),
        Stripped(
            f'''\
def record_or_check(path: pathlib.Path, got: str) -> None:
{I}"""
{I}Re-record or check that :paramref:`got` content matches the content of
{I}:paramref:`path`.

{I}If :py:attr:`~RECORD_MODE` is set, the content of :paramref:`path` will be
{I}simply overwritten with :paramref:`got` content, and no checks are performed.

{I}:param path: to the golden file
{I}:param got: obtained content
{I}:raise: :py:class:`AssertionError` if the contents do not match
{I}"""
{I}if RECORD_MODE:
{II}path.parent.mkdir(exist_ok=True, parents=True)
{II}path.write_text(got, encoding="utf-8")
{I}else:
{II}if not path.exists():
{III}raise FileNotFoundError(
{IIII}f"The golden file could not be found: {{path}}; did you record it?"
{III})

{II}expected = path.read_text(encoding="utf-8")
{II}if expected != got:
{III}writer = io.StringIO()

{III}diff = difflib.ndiff(
{IIII}expected.splitlines(keepends=True), got.splitlines(keepends=True)
{III})

{III}diff_text = "".join(diff)
{III}writer.write(
{IIII}f"""\\
The obtained content and the content of {{path}} do not match:
{{diff_text}}"""
{III})

{III}raise AssertionError(writer.getvalue())'''
        ),
        Stripped(
            f'''\
def trace(
{I}that: Union[
{II}bool,
{II}int,
{II}float,
{II}str,
{II}bytes,
{II}enum.Enum,
{II}aas_types.Class,
{II}Sequence[aas_types.Class],
{I}],
) -> str:
{I}"""
{I}Generate a segment in a trace of an iteration.

{I}:param that: to be traced
{I}:return: segment in the descent trace
{I}"""
{I}if isinstance(that, aas_types.Class):
{II}if isinstance(that, aas_types.Identifiable):
{III}return f"{{that.__class__.__name__}} with ID {{that.id}}"
{II}elif isinstance(that, aas_types.Referable):
{III}return f"{{that.__class__.__name__}} with ID-short {{that.id_short}}"
{II}else:
{III}return that.__class__.__name__
{I}elif isinstance(that, (bool, int, float, str, enum.Enum)):
{II}return str(that)
{I}elif isinstance(that, bytes):
{II}return base64.b64encode(that).decode("ascii")
{I}elif isinstance(that, collections.abc.Sequence):
{II}if len(that) == 0:
{III}return "[]"
{II}writer = io.StringIO()
{II}writer.write("[\\n")
{II}for i, item in enumerate(that):
{III}assert isinstance(item, aas_types.Class)

{III}writer.write(textwrap.indent(trace(item), "  "))

{III}if i < len(that) - 1:
{IIII}writer.write(",\\n")
{III}else:
{IIII}writer.write("\\n")

{II}writer.write("]")
{II}return writer.getvalue()
{I}else:
{II}aas_common.assert_never(that)'''
        ),
        Stripped(
            f'''\
def trace_log_as_text_file_content(log: Sequence[str]) -> str:
{I}"""
{I}Convert the trace log to a text to be stored in a file.

{I}:param log: to be converted to text
{I}:return: content of the file, including the new-line at the end
{I}"""
{I}writer = io.StringIO()
{I}for entry in log:
{II}writer.write(f"{{entry}}\\n")
{I}writer.write("\\n")
{I}return writer.getvalue()'''
        ),
        python_common.WARNING,
    ]

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue()
