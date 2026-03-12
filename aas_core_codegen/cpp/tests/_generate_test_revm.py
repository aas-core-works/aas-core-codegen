"""Generate code to test the virtual machine for matching regular expressions."""

import io

from icontract import ensure

from aas_core_codegen.common import (
    Stripped,
)
from aas_core_codegen.cpp import common as cpp_common
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_implementation(library_namespace: Stripped) -> str:
    """Generate implementation to test the virtual machine for matching regular expressions."""
    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            """\
/**
 * Test the virtual machine for matching regular expressions.
 */"""
        ),
        Stripped(
            f'''\
#include "{include_prefix_path}/common.hpp"
#include "{include_prefix_path}/revm.hpp"'''
        ),
        Stripped(
            """\
#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>"""
        ),
        Stripped(
            f"""\
namespace aas = {library_namespace};"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test character in an empty range") {{
{I}std::vector<aas::revm::Range> ranges;

{I}REQUIRE(
{II}!aas::revm::CharacterInRanges(ranges, L'M')
{I});
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test character in a single range") {{
{I}std::vector<aas::revm::Range> ranges = {{
{II}aas::revm::Range(L'A', L'Z')
{I}}};

{I}REQUIRE(CharacterInRanges(ranges, L'M'));
{I}REQUIRE(!CharacterInRanges(ranges, L'a'));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test character in multiple ranges") {{
{I}std::vector<aas::revm::Range> ranges = {{
{II}aas::revm::Range(L'A', L'C'),
{II}aas::revm::Range(L'D', L'F'),
{II}aas::revm::Range(L'G', L'I'),
{II}aas::revm::Range(L'J', L'L'),
{II}aas::revm::Range(L'M', L'N')
{I}}};

{I}for (wchar_t character = L'A'; character < L'Z'; ++character) {{
{II}const std::string message(
{III}aas::common::WstringToUtf8(
{IIII}L"Testing for character: " + std::wstring(1, character)
{III})
{II});

{II}if (character <= L'N') {{
{III}INFO(message)
{III}REQUIRE(
{IIII}CharacterInRanges(ranges, character)
{III});
{II}}} else {{
{III}INFO(message)
{III}REQUIRE(
{IIII}!CharacterInRanges(ranges, character)
{III});
{II}}}
{I}}}
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^a$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'a')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(!aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^a+b+$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'a')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionSplit>(0, 2)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'b')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionSplit>(2, 4)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(!aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(!aas::revm::Match(program, L"b"));
{I}REQUIRE(aas::revm::Match(program, L"ab"));
{I}REQUIRE(aas::revm::Match(program, L"aabb"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^a|b$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionSplit>(1, 3)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'a')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionJump>(4)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'b')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^a?$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionSplit>(1, 2)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'a')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(!aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^a*$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionSplit>(1, 3)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'a')
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionJump>(0)
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(aas::revm::Match(program, L"aa"));
{I}REQUIRE(!aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^[a-b]$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionSet>(
{III}std::vector<aas::revm::Range>{{
{IIII}aas::revm::Range(L'a', L'b')
{III}}}
{II})
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^[^a-b]$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionNotSet>(
{III}std::vector<aas::revm::Range>{{
{IIII}aas::revm::Range(L'a', L'b')
{III}}}
{II})
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionEnd>()
{I});
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{I});

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(!aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(!aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
{I}REQUIRE(aas::revm::Match(program, L"c"));
{I}REQUIRE(!aas::revm::Match(program, L"cc"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern ^.$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(std::make_unique<aas::revm::InstructionAny>());
{I}program.emplace_back(std::make_unique<aas::revm::InstructionEnd>());
{I}program.emplace_back(std::make_unique<aas::revm::InstructionMatch>());

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(!aas::revm::Match(program, L"aa"));
{I}REQUIRE(aas::revm::Match(program, L"b"));
{I}REQUIRE(!aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        Stripped(
            f"""\
TEST_CASE("Test pattern with arbitrary suffix ^a.*$") {{
{I}std::vector<std::unique_ptr<aas::revm::Instruction> > program;

{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionChar>(L'a')
{III});

{I}// NOTE (mristin):
{I}// Usually, the last two instructions would be `end` followed by a `match`.
{I}// However, we can optimize by having a single `match` without an `end` so that
{I}// we return early.
{I}program.emplace_back(
{II}std::make_unique<aas::revm::InstructionMatch>()
{III});

{I}REQUIRE(!aas::revm::Match(program, L""));
{I}REQUIRE(aas::revm::Match(program, L"a"));
{I}REQUIRE(aas::revm::Match(program, L"aa"));
{I}REQUIRE(!aas::revm::Match(program, L"b"));
{I}REQUIRE(aas::revm::Match(program, L"ab"));
{I}REQUIRE(!aas::revm::Match(program, L"ba"));
}}"""
        ),
        cpp_common.WARNING,
    ]

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue()


assert generate_implementation.__doc__ is not None
cpp_common.assert_module_docstring_and_generate_implementation_consistent(
    module_doc=__doc__, generate_implementation_doc=generate_implementation.__doc__
)
