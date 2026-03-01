"""Generate the constants shared across the unit tests."""

import io
import re
import urllib.parse
from typing import List

from icontract import ensure

from aas_core_codegen.common import (
    Stripped,
    Identifier,
)
from aas_core_codegen.golang import common as golang_common
from aas_core_codegen.golang.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


def _repo_url_to_environment_variable(repo_url: Stripped) -> Identifier:
    """
    Convert a repository URL to an environment-variable-style name.

    >>> _repo_url_to_environment_variable(
    ...     Stripped('github.com/aas-core-works/aas-core3.0-golang')
    ... )
    'GITHUB_COM_AAS_CORE_WORKS_AAS_CORE3_0_GOLANG'

    >>> _repo_url_to_environment_variable(
    ...     Stripped('github.com/org/repo/tree/main/sub/dir')
    ... )
    'GITHUB_COM_ORG_REPO_TREE_MAIN_SUB_DIR'

    >>> _repo_url_to_environment_variable(
    ...     Stripped('gitlab.com/group/subgroup/repo')
    ... )
    'GITLAB_COM_GROUP_SUBGROUP_REPO'

    >>> _repo_url_to_environment_variable(
    ...     Stripped('github.com/some owner/repo')
    ... )
    'GITHUB_COM_SOME_OWNER_REPO'

    >>> _repo_url_to_environment_variable(
    ...     Stripped('https://github.com/owner/repo')
    ... )
    'GITHUB_COM_OWNER_REPO'

    >>> _repo_url_to_environment_variable(Stripped(''))
    Traceback (most recent call last):
    ...
    ValueError: Repo URL must be a non-empty string.
    """
    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError("Repo URL must be a non-empty string.")

    # NOTE (mristin):
    # If scheme missing, we add one so urlsplit parses netloc correctly.
    parsed = urllib.parse.urlsplit(
        repo_url if "://" in repo_url else f"https://{repo_url}"
    )

    host = parsed.netloc or ""
    path = parsed.path or ""

    path = path.strip()
    path = path.strip("/")

    # Compose a canonical identifier string.
    canonical = host
    if len(path):
        canonical = f"{host}/{path}"

    # Convert to ENV_VAR format: uppercase, non-alnum -> underscore, collapse.
    env = re.sub(r"[^0-9A-Za-z]+", "_", canonical).upper()
    env = re.sub(r"_+", "_", env).strip("_")

    return Identifier(env)


# fmt: off
@ensure(
    lambda result: result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(repo_url: Stripped) -> str:
    """Generate the constants shared across the unit tests."""
    environment_variable = _repo_url_to_environment_variable(repo_url)

    blocks = [
        Stripped(
            """\
package aastesting"""
        ),
        golang_common.WARNING,
        Stripped(
            f"""\
import (
{I}"fmt"
{I}"os"
{I}"strings"
)"""
        ),
        Stripped(
            f"""\
const RecordModeEnvironmentVariableName string = (
{I}"{environment_variable}_TEST_RECORD_MODE")"""
        ),
        Stripped(
            '''\
// NOTE (mristin):
// It is tedious to record manually all the expected error messages. Therefore we
// include this variable to steer the automatic recording. We intentionally
// intertwine the recording code with the test code to keep them close to each other
// so that they are easier to maintain.
var rM = os.Getenv(RecordModeEnvironmentVariableName)
var RecordMode = rM == "1" || strings.ToLower(rM) == "true" || strings.ToLower(rM) == "on"'''
        ),
        Stripped(
            f"""\
const TestDataDirEnvironmentVariableName string = (
{I}"{environment_variable}_TEST_DATA_DIR")"""
        ),
        Stripped(
            f"""\
func getTestDataDir() string {{
{I}variable := TestDataDirEnvironmentVariableName
{I}val, ok := os.LookupEnv(variable)
{I}if !ok {{
{II}panic(
{III}fmt.Sprintf(
{IIII}"Expected the environment variable to be set, but it was not: %s",
{IIII}variable,
{III}),
{II})
{I}}}
{I}return val
}}"""
        ),
        Stripped(
            """\
var TestDataDir = getTestDataDir()"""
        ),
        golang_common.WARNING,
    ]  # type: List[Stripped]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
