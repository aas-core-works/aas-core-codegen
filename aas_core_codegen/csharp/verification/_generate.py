"""Generate the invariant verifiers from the intermediate representation."""
import io
import textwrap
from typing import (
    Tuple,
    Optional,
    List,
    Sequence,
    Set,
    Mapping,
    Union,
)

from icontract import ensure, require

from aas_core_codegen import intermediate, specific_implementations, naming
from aas_core_codegen.common import (
    Error,
    Stripped,
    assert_never,
    Identifier,
    indent_but_first_line,
)
from aas_core_codegen.csharp import (
    common as csharp_common,
    naming as csharp_naming,
    description as csharp_description,
    transpilation as csharp_transpilation,
)
from aas_core_codegen.csharp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference
from aas_core_codegen.parse import tree as parse_tree, retree as parse_retree


# region Verify


def verify(
    spec_impls: specific_implementations.SpecificImplementations,
    verification_functions: Sequence[intermediate.Verification],
) -> Optional[List[str]]:
    """Verify all the implementation snippets related to verification."""
    errors = []  # type: List[str]

    expected_keys = []  # type: List[specific_implementations.ImplementationKey]

    for func in verification_functions:
        if isinstance(func, intermediate.ImplementationSpecificVerification):
            expected_keys.append(
                specific_implementations.ImplementationKey(
                    f"Verification/{func.name}.cs"
                ),
            )

    for key in expected_keys:
        if key not in spec_impls:
            errors.append(f"The implementation snippet is missing for: {key}")

    if len(errors) == 0:
        return None

    return errors


# endregion

# region Generate


class _FixForUTF16Regex(parse_retree.BaseVisitor):
    """
    Modify the pattern in-place such that UTF-32 can be dealt by C# regex engine.

    Specifically, we need to split UTF-32 characters in the two surrogates since
    C# regex engine only works with UTF-16.

    The characters in the range ``\\uD800`` to ``\\uDFFF`` are reserved, so they can
    be used as high surrogates. However, it is still valid to use them as standalone
    characters. Hence, if you use them in your pattern, and the pattern also involves
    UTF-32 characters, the transformed pattern might be more permissive than
    the original one.

    For the problem, see:

    * https://stackoverflow.com/questions/364009/c-sharp-regular-expressions-with-uxxxxxxxx-characters-in-the-pattern
    * https://stackoverflow.com/questions/47605037/unicode-character-range-not-being-consumed-by-regex

    For the UTF-16 specs, ranges and computation of low/high surrogates, see:

    * https://en.wikipedia.org/wiki/UTF-16#Description
    * http://www.russellcottrell.com/greek/utilities/surrogatepaircalculator.htm
    """

    _SUPPLEMENTARY_PLANE_START = 0x00010000
    _SUPPLEMENTARY_PLANE_END = 0x0010FFFF

    # fmt: off
    @staticmethod
    @require(
        lambda code:
        _FixForUTF16Regex._SUPPLEMENTARY_PLANE_START
        <= code <=
        _FixForUTF16Regex._SUPPLEMENTARY_PLANE_END

    )
    @ensure(
        lambda result:
        0xD800 <= result[0] <= 0xDBFF
        and 0xDC00 <= result[1] <= 0xDFFF,
        "High and low surrogates in the expected range"
    )
    # fmt: on
    def _convert_to_surrogates(code: int) -> Tuple[int, int]:
        """Convert a UTF-32 character into its surrogates."""
        high_surrogate = (code - 0x10000) // 0x400 + 0xD800
        low_surrogate = (code - 0x10000) % 0x400 + 0xDC00

        return high_surrogate, low_surrogate

    @staticmethod
    @require(lambda term: isinstance(term.value, parse_retree.Char))
    def _character_literal_to_surrogates_if_necessary(
        term: parse_retree.Term,
    ) -> List[parse_retree.Term]:
        """Expand the character literal to two surrogate characters if necessary."""
        # NOTE (mristin, 2022-06-10):
        # This assertion is needed for mypy.
        assert isinstance(term.value, parse_retree.Char)

        if ord(term.value.character) < _FixForUTF16Regex._SUPPLEMENTARY_PLANE_START:
            return [term]

        high_surrogate, low_surrogate = _FixForUTF16Regex._convert_to_surrogates(
            code=ord(term.value.character)
        )

        # NOTE (mristin, 2022-06-10):
        # We explicitly encode the character since otherwise this split can not be
        # traced back meaningfully.
        high_surrogate_char = parse_retree.Char(
            character=chr(high_surrogate), explicitly_encoded=True
        )
        low_surrogate_char = parse_retree.Char(
            character=chr(low_surrogate), explicitly_encoded=True
        )

        output = []  # type: List[parse_retree.Term]

        if term.quantifier is not None:
            # NOTE (mristin, 2022-06-10):
            # We need to put the surrogates in a group so that the quantifier
            # applies to both.
            value = parse_retree.Group(
                union=parse_retree.UnionExpr(
                    uniates=[
                        parse_retree.Concatenation(
                            concatenants=[
                                parse_retree.Term(
                                    value=high_surrogate_char, quantifier=None
                                ),
                                parse_retree.Term(
                                    value=low_surrogate_char, quantifier=None
                                ),
                            ]
                        )
                    ]
                )
            )

            output.append(parse_retree.Term(value=value, quantifier=term.quantifier))
        else:
            # NOTE (mristin, 2022-06-10):
            # When there is no quantifier, we can simply inject the surrogates
            # as character literals.
            output.append(parse_retree.Term(value=high_surrogate_char, quantifier=None))
            output.append(parse_retree.Term(value=low_surrogate_char, quantifier=None))

        return output

    @staticmethod
    def _produce_char_char(
        first_code: int, second_code: int
    ) -> parse_retree.Concatenation:
        """
        Produce a concatenation as ``{u(code)}{u(code)}``.

        This method helped us to make
        :method:`~_expand_char_set_to_surrogates_if_necessary` somewhat manageable since
        we struggled with the complexity of its code.
        """
        return parse_retree.Concatenation(
            concatenants=[
                parse_retree.Term(
                    value=parse_retree.Char(
                        character=chr(first_code), explicitly_encoded=True
                    ),
                    quantifier=None,
                ),
                parse_retree.Term(
                    value=parse_retree.Char(
                        character=chr(second_code), explicitly_encoded=True
                    ),
                    quantifier=None,
                ),
            ]
        )

    @staticmethod
    def _produce_char_char_set(
        code: int, range_start: int, range_end: int
    ) -> parse_retree.Concatenation:
        """
        Produce a concatenation as ``{u(code)}[{u(range_start)-u(range_end)}]``.

        This method helped us to make
        :method:`~_expand_char_set_to_surrogates_if_necessary` somewhat manageable since
        we struggled with the complexity of its code.
        """
        return parse_retree.Concatenation(
            concatenants=[
                parse_retree.Term(
                    value=parse_retree.Char(
                        character=chr(code), explicitly_encoded=True
                    ),
                    quantifier=None,
                ),
                parse_retree.Term(
                    value=parse_retree.CharSet(
                        complementing=False,
                        ranges=[
                            parse_retree.Range(
                                start=parse_retree.Char(
                                    character=chr(range_start), explicitly_encoded=True
                                ),
                                end=parse_retree.Char(
                                    character=chr(range_end), explicitly_encoded=True
                                ),
                            )
                        ],
                    ),
                    quantifier=None,
                ),
            ]
        )

    @staticmethod
    def _produce_char_set_char_set(
        first_range_start: int,
        first_range_end: int,
        second_range_start: int,
        second_range_end: int,
    ) -> parse_retree.Concatenation:
        """
        Produce a concatenation of the character sets.

        This method helped us to make
        :method:`~_expand_char_set_to_surrogates_if_necessary` somewhat manageable since
        we struggled with the complexity of its code.
        """
        return parse_retree.Concatenation(
            concatenants=[
                parse_retree.Term(
                    value=parse_retree.CharSet(
                        complementing=False,
                        ranges=[
                            parse_retree.Range(
                                start=parse_retree.Char(
                                    character=chr(first_range_start),
                                    explicitly_encoded=True,
                                ),
                                end=parse_retree.Char(
                                    character=chr(first_range_end),
                                    explicitly_encoded=True,
                                ),
                            )
                        ],
                    ),
                    quantifier=None,
                ),
                parse_retree.Term(
                    value=parse_retree.CharSet(
                        complementing=False,
                        ranges=[
                            parse_retree.Range(
                                start=parse_retree.Char(
                                    character=chr(second_range_start),
                                    explicitly_encoded=True,
                                ),
                                end=parse_retree.Char(
                                    character=chr(second_range_end),
                                    explicitly_encoded=True,
                                ),
                            )
                        ],
                    ),
                    quantifier=None,
                ),
            ]
        )

    @staticmethod
    @require(lambda term: isinstance(term.value, parse_retree.CharSet))
    def _expand_char_set_to_surrogates_if_necessary(
        term: parse_retree.Term,
    ) -> List[parse_retree.Term]:
        """Extend the set with surrogates or expand it to a union, if necessary."""
        ranges_wo_utf32 = []  # type: List[parse_retree.Range]
        ranges_w_utf32 = []  # type: List[parse_retree.Range]

        # Needed for mypy
        assert isinstance(term.value, parse_retree.CharSet)

        for a_range in term.value.ranges:
            if (
                ord(a_range.start.character)
                < _FixForUTF16Regex._SUPPLEMENTARY_PLANE_START
            ) and (
                a_range.end is None
                or (
                    ord(a_range.end.character)
                    < _FixForUTF16Regex._SUPPLEMENTARY_PLANE_START
                )
            ):
                ranges_wo_utf32.append(a_range)
            else:
                ranges_w_utf32.append(a_range)

        if len(ranges_w_utf32) == 0:
            return [term]

        assert not term.value.complementing, (
            "Complementing character sets with one or more ranges "
            "involving UTF-32 characters can not be supported, "
            "since we can not represent them relying "
            "on an UTF-16-only regex engine.\n"
            "\n"
            "This should have been detected before and returned as an error.",
        )

        # NOTE (mristin, 2022-06-11):
        # Expand the character set into a union of:
        # 1) A character set without any UTF-32 characters
        # 2) One or more character sets representing the ranges involving
        #    UTF-32 characters.

        # noinspection PyListCreation
        uniates = []  # type: List[parse_retree.Concatenation]

        if len(ranges_wo_utf32) > 0:
            uniates.append(
                parse_retree.Concatenation(
                    concatenants=[
                        parse_retree.Term(
                            value=parse_retree.CharSet(
                                complementing=False, ranges=ranges_wo_utf32
                            ),
                            quantifier=None,
                        )
                    ]
                )
            )

        for a_range in ranges_w_utf32:
            high_start, low_start = _FixForUTF16Regex._convert_to_surrogates(
                code=ord(a_range.start.character)
            )

            if (a_range.end is None) or (
                a_range.start.character == a_range.end.character
            ):
                uniates.append(
                    _FixForUTF16Regex._produce_char_char(
                        first_code=high_start, second_code=low_start
                    )
                )
            else:
                assert ord(a_range.start.character) < ord(a_range.end.character), (
                    "Start of a range must be smaller than its end.\n"
                    "\n"
                    "This is expected to be detected at the parse stage."
                )

                high_end, low_end = _FixForUTF16Regex._convert_to_surrogates(
                    code=ord(a_range.end.character)
                )

                # noinspection SpellCheckingInspection
                if high_start == high_end:
                    # {high start}[{low start}-{low end}]
                    uniates.append(
                        _FixForUTF16Regex._produce_char_char_set(
                            code=high_start, range_start=low_start, range_end=low_end
                        )
                    )
                else:
                    # {high start}[{low start}-\uDFFF]
                    uniates.append(
                        _FixForUTF16Regex._produce_char_char_set(
                            code=high_start, range_start=low_start, range_end=0xDFFF
                        )
                    )

                    if high_end - high_start > 1:
                        # noinspection SpellCheckingInspection
                        if high_start + 1 == high_end - 1:
                            # {high start + 1}[\uDC00-\uDFFF]
                            uniates.append(
                                _FixForUTF16Regex._produce_char_char_set(
                                    code=high_start + 1,
                                    range_start=0xDC00,
                                    range_end=0xDFFF,
                                )
                            )
                        else:
                            # [{high start + 1}-{high end - 1}][\uDC00-\uDFFF]
                            uniates.append(
                                _FixForUTF16Regex._produce_char_set_char_set(
                                    first_range_start=high_start + 1,
                                    first_range_end=high_end - 1,
                                    second_range_start=0xDC00,
                                    second_range_end=0xDFFF,
                                )
                            )

                    uniates.append(
                        _FixForUTF16Regex._produce_char_char_set(
                            code=high_end, range_start=0xDC00, range_end=low_end
                        )
                    )

        return [
            parse_retree.Term(
                value=parse_retree.Group(union=parse_retree.UnionExpr(uniates=uniates)),
                quantifier=term.quantifier,
            )
        ]

    def visit_concatenation(self, node: parse_retree.Concatenation) -> None:
        """Convert character literals to UTF-16, where appropriate."""
        new_concatenants = []  # type: List[parse_retree.Term]

        for concatenant in node.concatenants:
            if isinstance(concatenant.value, parse_retree.Char):
                new_concatenants.extend(
                    _FixForUTF16Regex._character_literal_to_surrogates_if_necessary(
                        term=concatenant
                    )
                )
            elif isinstance(concatenant.value, parse_retree.CharSet):
                new_concatenants.extend(
                    _FixForUTF16Regex._expand_char_set_to_surrogates_if_necessary(
                        term=concatenant
                    )
                )
            else:
                new_concatenants.append(concatenant)

        node.concatenants = new_concatenants
        for concatenant in new_concatenants:
            self.visit(concatenant)


_FIX_FOR_UTF16_REGEX = _FixForUTF16Regex()


class _PatternVerificationTranspiler(
    parse_tree.RestrictedTransformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile a statement of a pattern verification into C#."""

    def __init__(self, defined_variables: Set[Identifier]) -> None:
        """
        Initialize with the given values.

        The ``initialized_variables`` are shared between different statement
        transpilations. It is also mutated when assignments are transpiled. We need to
        keep track of variables so that we know when we have to define them, and when
        we can simply assign them a value, if they have been already defined.
        """
        self.defined_variables = defined_variables

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if isinstance(node.value, str):
            # NOTE (mristin, 2022-06-11):
            # We assume that all the string constants are valid regular expressions.

            regex, parse_error = parse_retree.parse(values=[node.value])
            if parse_error is not None:
                regex_line, pointer_line = parse_retree.render_pointer(
                    parse_error.cursor
                )

                return (
                    None,
                    Error(
                        node.original_node,
                        f"The string constant could not be parsed "
                        f"as a regular expression: \n"
                        f"{parse_error.message}\n"
                        f"{regex_line}\n"
                        f"{pointer_line}",
                    ),
                )

            assert regex is not None
            _FIX_FOR_UTF16_REGEX.visit(regex)

            # NOTE (mristin, 2022-06-11):
            # Strictly speaking, this is a joined string with a single value, a string
            # literal.
            return self._transform_joined_str_values(
                values=parse_retree.render(regex=regex)
            )
        else:
            raise AssertionError(f"Unexpected {node=}")

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def _transform_joined_str_values(
        self, values: Sequence[Union[str, parse_tree.FormattedValue]]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        """Transform the values of a joined string to a C# string literal."""
        if all(isinstance(value, str) for value in values):
            return (
                Stripped(csharp_common.string_literal("".join(values))),  # type: ignore
                None,
            )

        needs_interpolation = False

        parts = []  # type: List[str]
        for value in values:
            if isinstance(value, str):
                string_literal = csharp_common.string_literal(
                    value.replace("{", "{{").replace("}", "}}")
                )

                # We need to remove double-quotes since we are joining everything
                # ourselves later.

                assert string_literal.startswith('"') and string_literal.endswith('"')

                string_literal_wo_quotes = string_literal[1:-1]
                parts.append(string_literal_wo_quotes)

            elif isinstance(value, parse_tree.FormattedValue):
                code, error = self.transform(value.value)
                if error is not None:
                    return None, error
                assert code is not None

                assert (
                    "\n" not in code
                ), f"New-lines are not expected in formatted values, but got: {code}"

                needs_interpolation = True
                parts.append(f"{{{code}}}")
            else:
                assert_never(value)

        writer = io.StringIO()

        if needs_interpolation:
            writer.write('$"')
        else:
            writer.write('"')

        for part in parts:
            writer.write(part)

        writer.write('"')

        return Stripped(writer.getvalue()), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return Stripped(csharp_naming.variable_name(node.identifier)), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_joined_str(
        self, node: parse_tree.JoinedStr
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        regex, parse_error = parse_retree.parse(values=node.values)
        if parse_error is not None:
            regex_line, pointer_line = parse_retree.render_pointer(parse_error.cursor)

            return (
                None,
                Error(
                    node.original_node,
                    f"The joined string could not be parsed "
                    f"as a regular expression: \n"
                    f"{parse_error.message}\n"
                    f"{regex_line}\n"
                    f"{pointer_line}",
                ),
            )

        assert regex is not None
        _FIX_FOR_UTF16_REGEX.visit(regex)

        return self._transform_joined_str_values(
            values=parse_retree.render(regex=regex)
        )

    def transform_assignment(
        self, node: parse_tree.Assignment
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        assert isinstance(node.target, parse_tree.Name)
        variable = csharp_naming.variable_name(node.target.identifier)
        code, error = self.transform(node.value)
        if error is not None:
            return None, error
        assert code is not None

        if node.target.identifier in self.defined_variables:
            return Stripped(f"{variable} = {code};"), None

        else:
            self.defined_variables.add(node.target.identifier)
            return Stripped(f"var {variable} = {code};"), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_pattern_verification(
    verification: intermediate.PatternVerification,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the verification function that checks the regular expressions."""
    # NOTE (mristin, 2021-12-19):
    # We assume that we performed all the checks at the intermediate stage.

    construct_name = csharp_naming.private_method_name(
        Identifier(f"construct_{verification.name}")
    )

    blocks = []  # type: List[Stripped]

    # region Construct block

    writer = io.StringIO()
    writer.write(
        f"""\
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
[CodeAnalysis.SuppressMessageAttribute("ReSharper", "IdentifierTypo")]
[CodeAnalysis.SuppressMessage("ReSharper", "StringLiteralTypo")]
private static Regex {construct_name}()
{{
"""
    )

    defined_variables = set()  # type: Set[Identifier]
    transpiler = _PatternVerificationTranspiler(defined_variables=defined_variables)

    for i, stmt in enumerate(verification.parsed.body):
        if i == len(verification.parsed.body) - 1:
            break

        code, error = transpiler.transform(stmt)
        if error is not None:
            return None, error
        assert code is not None

        writer.write(textwrap.indent(code, I))
        writer.write("\n")

    if len(verification.parsed.body) >= 2:
        writer.write("\n")

    assert len(verification.parsed.body) >= 1

    assert isinstance(verification.parsed.body[-1], parse_tree.Return)
    # noinspection PyUnresolvedReferences
    assert isinstance(verification.parsed.body[-1].value, parse_tree.IsNotNone)
    # noinspection PyUnresolvedReferences
    assert isinstance(verification.parsed.body[-1].value.value, parse_tree.FunctionCall)
    # noinspection PyUnresolvedReferences
    assert verification.parsed.body[-1].value.value.name.identifier == "match"

    # noinspection PyUnresolvedReferences
    match_call = verification.parsed.body[-1].value.value

    assert isinstance(
        match_call, parse_tree.FunctionCall
    ), f"{parse_tree.dump(match_call)}"
    assert match_call.name.identifier == "match"

    assert isinstance(match_call.args[0], parse_tree.Expression)
    pattern_expr, error = transpiler.transform(match_call.args[0])
    if error is not None:
        return None, error
    assert pattern_expr is not None

    # A pragmatic heuristics for breaking lines
    if len(pattern_expr) < 50:
        writer.write(textwrap.indent(f"return new Regex({pattern_expr});\n", I))
    else:
        writer.write(textwrap.indent(f"return new Regex(\n{I}{pattern_expr});\n", I))

    writer.write("}")

    blocks.append(Stripped(writer.getvalue()))

    # endregion

    # region Initialize the regex

    # NOTE (mristin, 2022-05-05):
    # We make this property look "public" since it is static and read-only.
    regex_name = csharp_naming.property_name(Identifier(f"regex_{verification.name}"))

    blocks.append(
        Stripped(f"private static readonly Regex {regex_name} = {construct_name}();")
    )

    assert len(verification.arguments) == 1
    assert isinstance(
        verification.arguments[0].type_annotation, intermediate.PrimitiveTypeAnnotation
    )
    # noinspection PyUnresolvedReferences
    assert (
        verification.arguments[0].type_annotation.a_type
        == intermediate.PrimitiveType.STR
    )

    arg_name = csharp_naming.argument_name(verification.arguments[0].name)

    writer = io.StringIO()
    if verification.description is not None:
        comment, comment_errors = csharp_description.generate_comment_for_signature(
            verification.description
        )
        if comment_errors is not None:
            return None, Error(
                verification.description.parsed.node,
                "Failed to generate the documentation comment",
                comment_errors,
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    method_name = csharp_naming.method_name(verification.name)

    writer.write(
        f"""\
public static bool {method_name}(string {arg_name})
{{
{I}return {regex_name}.IsMatch({arg_name});
}}"""
    )

    blocks.append(Stripped(writer.getvalue()))

    # endregion

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    return Stripped(writer.getvalue()), None


class _TranspilableVerificationTranspiler(csharp_transpilation.Transpiler):
    """Transpile the body of a :class:`.TranspilableVerification`."""

    # fmt: off
    @require(
        lambda environment, verification:
        all(
            environment.find(arg.name) is not None
            for arg in verification.arguments
        ),
        "All arguments defined in the environment"
    )
    # fmt: on
    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
        verification: intermediate.TranspilableVerification,
    ) -> None:
        """Initialize with the given values."""
        csharp_transpilation.Transpiler.__init__(
            self, type_map=type_map, environment=environment
        )

        self._symbol_table = symbol_table

        self._argument_name_set = frozenset(arg.name for arg in verification.arguments)

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            return Stripped(csharp_naming.variable_name(node.identifier)), None

        if node.identifier in self._argument_name_set:
            return Stripped(csharp_naming.variable_name(node.identifier)), None

        if node.identifier in self._symbol_table.constants_by_name:
            constant_as_prop = csharp_naming.property_name(node.identifier)
            return Stripped(f"Aas.Constants.{constant_as_prop}"), None

        if node.identifier in self._symbol_table.verification_functions_by_name:
            return Stripped(csharp_naming.method_name(node.identifier)), None

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            return Stripped(csharp_naming.enum_name(node.identifier)), None

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to C#. We could not find it neither in the constants, nor in "
            f"verification functions, nor as an enumeration. "
            f"If you expect this name to be transpilable, please contact "
            f"the developers.",
        )


def _transpile_transpilable_verification(
    verification: intermediate.TranspilableVerification,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Transpile a verification function."""
    canonicalizer = intermediate_type_inference.Canonicalizer()
    for node in verification.parsed.body:
        _ = canonicalizer.transform(node)

    environment_with_args = intermediate_type_inference.MutableEnvironment(
        parent=environment
    )
    for arg in verification.arguments:
        environment_with_args.set(
            identifier=arg.name,
            type_annotation=intermediate_type_inference.convert_type_annotation(
                arg.type_annotation
            ),
        )

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment_with_args,
        representation_map=canonicalizer.representation_map,
    )

    for node in verification.parsed.body:
        _ = type_inferrer.transform(node)

    if len(type_inferrer.errors):
        return None, Error(
            verification.parsed.node,
            f"Failed to infer the types "
            f"in the verification function {verification.name!r}",
            type_inferrer.errors,
        )

    transpiler = _TranspilableVerificationTranspiler(
        type_map=type_inferrer.type_map,
        environment=environment_with_args,
        symbol_table=symbol_table,
        verification=verification,
    )

    body = []  # type: List[Stripped]
    for node in verification.parsed.body:
        stmt, error = transpiler.transform(node)
        if error is not None:
            return None, Error(
                verification.parsed.node,
                f"Failed to transpile the verification function {verification.name!r}",
                [error],
            )

        assert stmt is not None
        body.append(stmt)

    writer = io.StringIO()
    if verification.description is not None:
        comment, comment_errors = csharp_description.generate_comment_for_signature(
            verification.description
        )
        if comment_errors is not None:
            return None, Error(
                verification.description.parsed.node,
                "Failed to generate the documentation comment",
                comment_errors,
            )

        assert comment is not None

        writer.write(comment)
        writer.write("\n")

    method_name = csharp_naming.method_name(verification.name)

    if verification.returns is None:
        return_type = "void"
    else:
        return_type = csharp_common.generate_type(type_annotation=verification.returns)

    arg_defs = []  # type: List[Stripped]
    for arg in verification.arguments:
        arg_type = csharp_common.generate_type(arg.type_annotation)
        arg_name = csharp_naming.argument_name(arg.name)
        arg_defs.append(Stripped(f"{arg_type} {arg_name}"))

    if len(arg_defs) == 0:
        writer.write(
            f"""\
public static {return_type} {method_name}()
{{"""
        )
    else:
        writer.write(
            f"""\
public static {return_type} {method_name}(
"""
        )

        for i, arg_def in enumerate(arg_defs):
            if i > 0:
                writer.write(",\n")
            writer.write(textwrap.indent(arg_def, I))

        writer.write("\n)\n{")

    for stmt in body:
        writer.write("\n")
        writer.write(textwrap.indent(stmt, I))

    if len(body) > 0:
        writer.write("\n")

    writer.write(f"}}  // public static {return_type} {method_name}")

    return Stripped(writer.getvalue()), None


@ensure(lambda text, result: text == "".join(result))
def _wrap_invariant_description(text: str) -> List[str]:
    """
    Wrap the invariant description as ``text`` into multiple tokens.

    The tokens are split based on the whitespace. We make sure the articles are not
    left hanging between the lines. A line should observe a pre-defined line limit,
    if possible.

    No new lines are added ??? the description should be given to the user in the original
    formatting. We merely split it in string literals for better code readability.
    """
    parts = text.split(" ")
    if len(parts) == 1:
        return [text]

    # NOTE (mristin, 2022-04-08):
    # We do not want to cut out "the", "a" and "an" on separate lines, so we split
    # the text once more in tokens where the articles are kept in the same token as
    # the word.
    tokens = []  # type: List[str]

    article = None  # type: Optional[str]
    for part in parts:
        if article is None:
            if part in ("a", "an", "the"):
                article = part
                continue
            else:
                tokens.append(part)
        else:
            if part in ("a", "an", "the"):
                # Append the previously observed ``article``;
                # the ``part`` becomes a new article.
                tokens.append(article)
                article = part
                continue

            tokens.append(f"{article} {part}")
            article = None

    if article is not None:
        tokens.append(article)

    # NOTE (mristin, 2022-04-08):
    # We add space to the tokens so that it is easier to re-flow them.
    tokens = [
        f"{token} " if i < len(tokens) - 1 else token for i, token in enumerate(tokens)
    ]
    assert "".join(tokens) == text

    # NOTE (mristin, 2022-04-08):
    # The line width of 60 characters is an arbitrary, but plausible limit. Please
    # consider that the text will be indented, so you have to add some slack.
    line_width = 60

    segments = []  # type: List[str]

    accumulation_len = 0
    accumulation = []  # type: List[str]

    for token in tokens:
        if len(token) > line_width:
            segments.append("".join(accumulation))
            segments.append(token)
            accumulation_len = 0
            accumulation = []

        elif accumulation_len + len(token) > line_width:
            segments.append("".join(accumulation))
            accumulation_len = len(token)
            accumulation = [token]
        else:
            accumulation_len += len(token)
            accumulation.append(token)

    if accumulation_len > 0:
        segments.append("".join(accumulation))

    return segments


class _InvariantTranspiler(csharp_transpilation.Transpiler):
    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
    ) -> None:
        """Initialize with the given values."""
        csharp_transpilation.Transpiler.__init__(
            self, type_map=type_map, environment=environment
        )

        self._symbol_table = symbol_table

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            return Stripped(csharp_naming.variable_name(node.identifier)), None

        if node.identifier == "self":
            # The ``that`` refers to the argument of the verification function.
            return Stripped("that"), None

        if node.identifier in self._symbol_table.constants_by_name:
            constant_as_prop = csharp_naming.property_name(node.identifier)
            return Stripped(f"Aas.Constants.{constant_as_prop}"), None

        if node.identifier in self._symbol_table.verification_functions_by_name:
            return Stripped(csharp_naming.method_name(node.identifier)), None

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            return Stripped(csharp_naming.enum_name(node.identifier)), None

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to C#. We could not find it "
            f"neither in the local variables, "
            f"nor in the global constants, "
            f"nor in verification functions, "
            f"nor as an enumeration. "
            f"If you expect this name to be transpilable, please contact "
            f"the developers.",
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_invariant(
    invariant: intermediate.Invariant,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Translate the invariant from the meta-model into C# code."""
    # NOTE (mristin, 2021-10-24):
    # We manually transpile the invariant from our custom syntax without additional
    # semantic analysis in the :py:mod:`aas_core_codegen.intermediate` layer.
    #
    # While this might seem repetitive ("unDRY"), we are still not sure about
    # the appropriate abstraction. After we implement the code generation for a couple
    # of languages, we hope to have a much better understanding about the necessary
    # abstractions.

    canonicalizer = intermediate_type_inference.Canonicalizer()
    _ = canonicalizer.transform(invariant.body)

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment,
        representation_map=canonicalizer.representation_map,
    )

    _ = type_inferrer.transform(invariant.body)

    if len(type_inferrer.errors):
        return None, Error(
            invariant.parsed.node,
            "Failed to infer the types in the invariant",
            type_inferrer.errors,
        )

    transpiler = _InvariantTranspiler(
        type_map=type_inferrer.type_map,
        environment=environment,
        symbol_table=symbol_table,
    )

    expr, error = transpiler.transform(invariant.parsed.body)
    if error is not None:
        return None, error

    assert expr is not None

    writer = io.StringIO()
    if len(expr) > 50 or "\n" in expr:
        writer.write("if (!(\n")
        writer.write(textwrap.indent(expr, I))
        writer.write("))\n{\n")
    else:
        no_parenthesis_type_in_this_context = (
            parse_tree.Name,
            parse_tree.Member,
            parse_tree.MethodCall,
            parse_tree.FunctionCall,
        )

        if isinstance(invariant.parsed.body, no_parenthesis_type_in_this_context):
            not_expr = f"!{expr}"
        else:
            not_expr = f"!({expr})"

        writer.write(f"if ({not_expr})\n{{\n")

    writer.write(
        textwrap.indent(
            f"""\
yield return new Reporting.Error(
{I}"Invariant violated:\\n" +
""",
            I,
        )
    )

    message_literals = []  # type: List[Stripped]
    if invariant.description is not None:
        # NOTE (mristin, 2022-04-08):
        # We need to wrap the description in multiple literals as a single long
        # string literal is often too much for the readability.
        invariant_description_lines = _wrap_invariant_description(invariant.description)
        for i, line in enumerate(invariant_description_lines):
            if i < len(invariant_description_lines) - 1:
                message_literals.append(csharp_common.string_literal(line))
            else:
                message_literals.append(csharp_common.string_literal(f"{line}\n"))

    expr_lines = expr.splitlines()
    for i, line in enumerate(expr_lines):
        if i < len(expr_lines) - 1:
            literal = csharp_common.string_literal(line + "\n")
        else:
            literal = csharp_common.string_literal(line)

        message_literals.append(literal)

    for i, literal in enumerate(message_literals):
        if i < len(message_literals) - 1:
            writer.write(f"{II}{literal} +\n")
        else:
            writer.write(f"{II}{literal});")

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_enum_value_sets(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate a class that pre-computes the sets of allowed enumeration literals."""
    blocks = []  # type: List[Stripped]

    for our_type in symbol_table.our_types:
        if not isinstance(our_type, intermediate.Enumeration):
            continue

        enum_name = csharp_naming.enum_name(our_type.name)

        if len(our_type.literals) == 0:
            blocks.append(
                Stripped(
                    f"""\
internal static readonly HashSet<int> For{enum_name} = new HashSet<int>();"""
                )
            )
        else:
            hash_set_writer = io.StringIO()
            hash_set_writer.write(
                f"""\
internal static readonly HashSet<int> For{enum_name} = new HashSet<int>\n{{\n
"""
            )

            for i, literal in enumerate(our_type.literals):
                literal_name = csharp_naming.enum_literal_name(literal.name)
                hash_set_writer.write(f"{I}(int)Aas.{enum_name}.{literal_name}")
                if i < len(our_type.literals) - 1:
                    hash_set_writer.write(",\n")
                else:
                    hash_set_writer.write("\n")

            hash_set_writer.write("};")

            blocks.append(Stripped(hash_set_writer.getvalue()))

    writer = io.StringIO()
    writer.write(
        """\
/// <summary>
/// Hash allowed enum values for efficient validation of enums.
/// </summary>
internal static class EnumValueSet
{
"""
    )
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // internal static class EnumValueSet")

    return Stripped(writer.getvalue())


def _generate_verify_method(our_type: intermediate.OurType) -> Stripped:
    """Generate the name of the ``Verification.Verify*`` method."""
    if isinstance(our_type, intermediate.Enumeration):
        name = csharp_naming.enum_name(our_type.name)
        return Stripped(f"Verification.Verify{name}")

    elif isinstance(our_type, intermediate.ConstrainedPrimitive):
        name = csharp_naming.class_name(our_type.name)
        return Stripped(f"Verification.Verify{name}")

    elif isinstance(our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)):
        return Stripped("Verification.Verify")
    else:
        assert_never(our_type)

    raise AssertionError("Unexpected execution path")


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transform_property(
    prop: intermediate.Property,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the snippet to transform a property to errors."""
    # NOTE (mristin, 2022-03-10):
    # Instead of writing here a complex but general solution with unrolling we choose
    # to provide a simple, but limited, solution. First, the meta-model is quite
    # limited itself at the moment, so the complexity of the general solution is not
    # warranted. Second, we hope that there will be fewer bugs in the simple solution
    # which is particularly important at this early adoption stage.
    #
    # We anticipate that in the future we will indeed need a general and complex
    # solution. Here are just some thoughts on how to approach it:
    # * Leave the pattern matching to produce more readable code for simple cases,
    # * Unroll only in case of composite types and optional composite types.

    type_anno = (
        prop.type_annotation
        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
        else prop.type_annotation.value
    )

    if isinstance(type_anno, intermediate.OptionalTypeAnnotation):
        return None, Error(
            prop.parsed.node,
            "We currently implemented verification based on a very limited "
            "pattern matching due to code simplicity. We did not handle "
            "the case of nested optional values. Please contact "
            "the developers if you need this functionality.",
        )
    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        if isinstance(type_anno.items, intermediate.OptionalTypeAnnotation):
            return None, Error(
                prop.parsed.node,
                "We currently implemented verification based on a very limited "
                "pattern matching due to code simplicity. We did not handle "
                "the case of lists of optional values. Please contact "
                "the developers if you need this functionality.",
            )
        elif isinstance(type_anno.items, intermediate.ListTypeAnnotation):
            return None, Error(
                prop.parsed.node,
                "We currently implemented verification based on a very limited "
                "pattern matching due to code simplicity. We did not handle "
                "the case of lists of lists. Please contact "
                "the developers if you need this functionality.",
            )
        else:
            pass
    else:
        pass

    stmts = []  # type: List[Stripped]

    prop_name = csharp_naming.property_name(prop.name)
    prop_literal = csharp_common.string_literal(naming.json_property(prop.name))

    # NOTE (mristin, 2022-03-12):
    # For some unexplainable reason, C# compiler can not infer that properties which
    # are enumerations are not null after an ``if (that.someProperty != null)``.
    # Hence, we need to add a null-coalescing for these particular cases.
    # Otherwise, we can just stick to ``that.someProperty``.

    needs_null_coalescing = (
        isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation)
        and isinstance(prop.type_annotation.value, intermediate.OurTypeAnnotation)
        and isinstance(prop.type_annotation.value.our_type, intermediate.Enumeration)
    )
    if needs_null_coalescing:
        source_expr = Stripped("value")
    else:
        source_expr = Stripped(f"that.{prop_name}")

    if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
        # There is nothing that we check for primitive types.
        return Stripped(""), None
    elif isinstance(type_anno, intermediate.OurTypeAnnotation):
        verify_method = _generate_verify_method(our_type=type_anno.our_type)

        foreach_error_in_verify = (
            f"foreach (var error in {verify_method}({source_expr}))"
        )
        # Heuristic to break the lines, very rudimentary
        if len(foreach_error_in_verify) > 80:
            foreach_error_in_verify = textwrap.dedent(
                f"""\
                foreach (
                    {I}var error in {verify_method}(
                    {II}{source_expr}))"""
            )

        # We can't use textwrap.dedent due to foreach_snippet.
        stmts.append(
            Stripped(
                f"""\
{foreach_error_in_verify}
{{
{I}error.PrependSegment(
{II}new Reporting.NameSegment(
{III}{prop_literal}));
{I}yield return error;
}}"""
            )
        )

    elif isinstance(type_anno, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_anno.items,
            (intermediate.OptionalTypeAnnotation, intermediate.ListTypeAnnotation),
        ), (
            "We chose to implement only a very limited pattern matching; "
            "see the note above in the code."
        )

        # NOTE (mristin, 2022-03-16):
        # We only descend into our classes here.
        if not isinstance(type_anno.items, intermediate.OurTypeAnnotation):
            return Stripped(""), None

        index_var = csharp_naming.variable_name(Identifier(f"index_{prop.name}"))
        verify_method = _generate_verify_method(type_anno.items.our_type)

        foreach_item_in_source_expr = f"foreach (var item in {source_expr})"
        # Rudimentary heuristics for line breaking
        if len(foreach_item_in_source_expr) > 80:
            foreach_item_in_source_expr = textwrap.dedent(
                f"""\
                foreach(
                {I}var item in {source_expr})"""
            )

        foreach_error_in_verify_item = f"foreach (var error in {verify_method}(item))"
        if len(foreach_error_in_verify_item) > 70:
            foreach_error_in_verify_item = textwrap.dedent(
                f"""\
                foreach (
                {I}var error in {verify_method}(item))"""
            )

        stmts.append(
            Stripped(
                f"""\
int {index_var} = 0;
{foreach_item_in_source_expr}
{{
{I}{indent_but_first_line(foreach_error_in_verify_item, I)}
{I}{{
{II}error.PrependSegment(
{III}new Reporting.IndexSegment(
{IIII}{index_var}));
{II}error.PrependSegment(
{III}new Reporting.NameSegment(
{IIII}{prop_literal}));
{II}yield return error;
{I}}}
{I}{index_var}++;
}}"""
            )
        )

    else:
        assert_never(type_anno)

    verify_block = Stripped("\n".join(stmts))
    if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
        if needs_null_coalescing:
            value_type = csharp_common.generate_type(prop.type_annotation.value)
            if isinstance(prop.type_annotation.value, intermediate.OurTypeAnnotation):
                our_type = prop.type_annotation.value.our_type
                if isinstance(
                    our_type,
                    (
                        intermediate.Enumeration,
                        intermediate.AbstractClass,
                        intermediate.ConcreteClass,
                    ),
                ):
                    value_type = Stripped(f"Aas.{value_type}")

            return (
                Stripped(
                    f"""\
if (that.{prop_name} != null)
{{
{I}// We need to help the static analyzer with a null coalescing.
{I}{value_type} value = that.{prop_name}
{II}?? throw new System.InvalidOperationException();
{I}{indent_but_first_line(verify_block, I)}
}}"""
                ),
                None,
            )

        else:
            return (
                Stripped(
                    f"""\
if (that.{prop_name} != null)
{{
{I}{indent_but_first_line(verify_block, I)}
}}"""
                ),
                None,
            )
    else:
        return verify_block, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_transform_for_class(
    cls: intermediate.ConcreteClass,
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the transform method to errors for the given concrete class."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    name = csharp_naming.class_name(cls.name)

    environment = intermediate_type_inference.MutableEnvironment(
        parent=base_environment
    )

    assert environment.find(Identifier("self")) is None
    environment.set(
        identifier=Identifier("self"),
        type_annotation=intermediate_type_inference.OurTypeAnnotation(our_type=cls),
    )

    for invariant in cls.invariants:
        invariant_code, error = _transpile_invariant(
            invariant=invariant, symbol_table=symbol_table, environment=environment
        )
        if error is not None:
            errors.append(
                Error(
                    cls.parsed.node,
                    f"Failed to transpile the invariant of the class {cls.name!r}",
                    [error],
                )
            )
            continue

        assert invariant_code is not None

        blocks.append(invariant_code)

    if len(errors) > 0:
        return None, errors

    for prop in cls.properties:
        block, error = _generate_transform_property(prop=prop)
        if error is not None:
            errors.append(error)
        else:
            assert block is not None
            if block != "":
                blocks.append(block)

    if len(errors) > 0:
        return None, errors

    if len(blocks) == 0:
        blocks.append(
            Stripped(
                f"""\
// No verification has been defined for {name}.
yield break;"""
            )
        )

    writer = io.StringIO()
    writer.write(
        f"""\
[CodeAnalysis.SuppressMessage("ReSharper", "NegativeEqualityExpression")]
public override IEnumerable<Reporting.Error> Transform(
{I}Aas.{name} that)
{{
"""
    )

    for i, stmt in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(stmt, I))

    writer.write("\n}")

    return Stripped(writer.getvalue()), None


def _generate_transformer(
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate a transformer to double-dispatch an instance to errors."""
    errors = []  # type: List[Error]

    blocks = []  # type: List[Stripped]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            continue

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            continue

        elif isinstance(our_type, intermediate.AbstractClass):
            # The abstract classes are directly dispatched by the transformer,
            # so we do not need to handle them separately.
            pass

        elif isinstance(our_type, intermediate.ConcreteClass):
            if our_type.is_implementation_specific:
                transform_key = specific_implementations.ImplementationKey(
                    f"Verification/transform_{our_type.name}.cs"
                )

                implementation = spec_impls.get(transform_key, None)
                if implementation is None:
                    errors.append(
                        Error(
                            our_type.parsed.node,
                            f"The transformation snippet is missing "
                            f"for the implementation-specific "
                            f"class {our_type.name}: {transform_key}",
                        )
                    )
                    continue

                blocks.append(spec_impls[transform_key])
            else:
                block, cls_errors = _generate_transform_for_class(
                    cls=our_type,
                    symbol_table=symbol_table,
                    base_environment=base_environment,
                )
                if cls_errors is not None:
                    errors.extend(cls_errors)
                else:
                    assert block is not None
                    blocks.append(block)
        else:
            assert_never(our_type)

    if len(errors) > 0:
        return None, errors

    writer = io.StringIO()
    writer.write(
        f"""\
private class Transformer
{I}: Visitation.AbstractTransformer<IEnumerable<Reporting.Error>>
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}  // private class Transformer")

    return Stripped(writer.getvalue()), None


def _generate_verify_enumeration(enumeration: intermediate.Enumeration) -> Stripped:
    """Generate the verify method to check that an enum is valid."""
    name = csharp_naming.enum_name(enumeration.name)

    return Stripped(
        f"""\
/// <summary>
/// Verify that <paramref name="that" /> is a valid enumeration value.
/// </summary>
public static IEnumerable<Reporting.Error> Verify{name}(
{I}Aas.{name} that)
{{
{I}if (!EnumValueSet.For{name}.Contains(
{II}(int)that))
{I}{{
{II}yield return new Reporting.Error(
{III}$"Invalid {name}: {{that}}");
{I}}}
}}"""
    )


def _generate_verify_constrained_primitive(
    constrained_primitive: intermediate.ConstrainedPrimitive,
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the verify function for the constrained primitives."""
    errors = []  # type: List[Error]
    blocks = []  # type: List[Stripped]

    environment = intermediate_type_inference.MutableEnvironment(
        parent=base_environment
    )

    assert environment.find(Identifier("self")) is None
    environment.set(
        identifier=Identifier("self"),
        type_annotation=intermediate_type_inference.OurTypeAnnotation(
            our_type=constrained_primitive
        ),
    )

    for invariant in constrained_primitive.invariants:
        invariant_code, error = _transpile_invariant(
            invariant=invariant, symbol_table=symbol_table, environment=environment
        )
        if error is not None:
            errors.append(
                Error(
                    constrained_primitive.parsed.node,
                    f"Failed to transpile the invariant of "
                    f"the constrained primitive {constrained_primitive.name!r}",
                    [error],
                )
            )
            continue

        assert invariant_code is not None

        blocks.append(invariant_code)

    if len(errors) > 0:
        return None, errors

    if len(blocks) == 0:
        blocks.append(
            Stripped(
                """\
// There is no verification specified.
yield break;"""
            )
        )

    # NOTE (mristin, 2022-03-16):
    # Constrained primitives are not really classes, but we simply use the naming
    # for classes here since we need to pick *something*.
    name = csharp_naming.class_name(constrained_primitive.name)

    that_type = csharp_common.PRIMITIVE_TYPE_MAP[constrained_primitive.constrainee]

    writer = io.StringIO()
    writer.write(
        f"""\
/// <summary>
/// Verify the constraints of <paramref name="that" />.
/// </summary>
public static IEnumerable<Reporting.Error> Verify{name} (
{I}{that_type} that)
{{
"""
    )

    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")
        writer.write(textwrap.indent(block, I))

    writer.write("\n}")

    assert len(errors) == 0
    return Stripped(writer.getvalue()), None


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
    namespace: csharp_common.NamespaceIdentifier,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the AAS C# namespace.
    """
    blocks = [
        csharp_common.WARNING,
        # Don't use textwrap.dedent since we add a newline in-between.
        Stripped(
            f"""\
using CodeAnalysis = System.Diagnostics.CodeAnalysis;
using Regex = System.Text.RegularExpressions.Regex;
using System.Collections.Generic;  // can't alias
using System.Linq;  // can't alias

using Aas = {namespace};"""
        ),
    ]  # type: List[Stripped]

    verification_blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    base_environment = intermediate_type_inference.populate_base_environment(
        symbol_table=symbol_table
    )

    for verification in symbol_table.verification_functions:
        if isinstance(verification, intermediate.ImplementationSpecificVerification):
            implementation_key = specific_implementations.ImplementationKey(
                f"Verification/{verification.name}.cs"
            )

            implementation = spec_impls.get(implementation_key, None)
            if implementation is None:
                errors.append(
                    Error(
                        None,
                        f"The snippet for the verification function "
                        f"{verification.name!r} is missing: {implementation_key}",
                    )
                )
            else:
                verification_blocks.append(implementation)

        elif isinstance(verification, intermediate.PatternVerification):
            implementation, error = _transpile_pattern_verification(
                verification=verification
            )

            if error is not None:
                errors.append(error)
            else:
                assert implementation is not None
                verification_blocks.append(implementation)

        elif isinstance(verification, intermediate.TranspilableVerification):
            implementation, error = _transpile_transpilable_verification(
                verification=verification,
                symbol_table=symbol_table,
                environment=base_environment,
            )

            if error is not None:
                errors.append(error)
            else:
                assert implementation is not None
                verification_blocks.append(implementation)

        else:
            assert_never(verification)

    verification_blocks.append(_generate_enum_value_sets(symbol_table=symbol_table))

    verification_blocks.append(
        Stripped(
            f"""\
[CodeAnalysis.SuppressMessage("ReSharper", "InconsistentNaming")]
private static readonly Verification.Transformer _transformer = (
{I}new Verification.Transformer());"""
        )
    )

    transformer_block, transformer_errors = _generate_transformer(
        symbol_table=symbol_table,
        base_environment=base_environment,
        spec_impls=spec_impls,
    )
    if transformer_errors is not None:
        errors.extend(transformer_errors)
    else:
        assert transformer_block is not None
        verification_blocks.append(transformer_block)

    verification_blocks.append(
        Stripped(
            f"""\
/// <summary>
/// Verify the constraints of <paramref name="that" /> recursively.
/// </summary>
/// <param name="that">
/// The instance of the meta-model to be verified
/// </param>
public static IEnumerable<Reporting.Error> Verify(Aas.IClass that)
{{
{I}foreach (var error in _transformer.Transform(that))
{I}{{
{II}yield return error;
{I}}}
}}"""
        )
    )

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            verification_blocks.append(
                _generate_verify_enumeration(enumeration=our_type)
            )
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            (
                constrained_primitive_block,
                constrained_primitive_errors,
            ) = _generate_verify_constrained_primitive(
                constrained_primitive=our_type,
                symbol_table=symbol_table,
                base_environment=base_environment,
            )

            if constrained_primitive_errors is not None:
                errors.extend(constrained_primitive_errors)
            else:
                assert constrained_primitive_block is not None
                verification_blocks.append(constrained_primitive_block)

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            # We provide a general dispatch function.
            pass
        else:
            assert_never(our_type)

    if len(errors) > 0:
        return None, errors

    verification_writer = io.StringIO()
    verification_writer.write(
        f"""\
namespace {namespace}
{{
{I}/// <summary>
{I}/// Verify that the instances of the meta-model satisfy the invariants.
{I}/// </summary>
"""
    )

    # region Write an example usage

    first_cls = None  # type: Optional[intermediate.ClassUnion]
    for our_type in symbol_table.our_types:
        if isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            first_cls = our_type
            break

    if first_cls is not None:
        cls_name = None  # type: Optional[str]
        if isinstance(first_cls, intermediate.AbstractClass):
            cls_name = csharp_naming.interface_name(first_cls.name)
        elif isinstance(first_cls, intermediate.ConcreteClass):
            cls_name = csharp_naming.class_name(first_cls.name)
        else:
            assert_never(first_cls)

        an_instance_variable = csharp_naming.variable_name(Identifier("an_instance"))

        verification_writer.write(
            # We can not use textwrap.dedent since we indent everything including the
            # first line.
            f"""\
{I}/// <example>
{I}/// Here is an example how to verify an instance of {cls_name}:
{I}/// <code>
{I}/// var {an_instance_variable} = new Aas.{cls_name}(
{I}///     // ... some constructor arguments ...
{I}/// );
{I}/// foreach (var error in Verification.Verify({an_instance_variable}))
{I}/// {{
{I}/// {I}System.Console.Writeln(
{I}/// {II}$"{{error.Cause}} at: " +
{I}/// {II}Reporting.GenerateJsonPath(error.PathSegments));
{I}/// }}
{I}/// </code>
{I}/// </example>
"""
        )

    # endregion

    verification_writer.write(
        f"""\
{I}public static class Verification
{I}{{
"""
    )

    for i, verification_block in enumerate(verification_blocks):
        if i > 0:
            verification_writer.write("\n\n")

        verification_writer.write(textwrap.indent(verification_block, II))

    verification_writer.write(f"\n{I}}}  // public static class Verification")
    verification_writer.write(f"\n}}  // namespace {namespace}")

    blocks.append(Stripped(verification_writer.getvalue()))

    blocks.append(csharp_common.WARNING)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        assert not block.startswith("\n")
        assert not block.endswith("\n")
        out.write(block)

    out.write("\n")

    return out.getvalue(), None


# endregion
