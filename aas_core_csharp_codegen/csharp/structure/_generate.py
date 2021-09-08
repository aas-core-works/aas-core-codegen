"""Generate the C# data structures from the intermediate representation."""
import io
import re
import textwrap
from typing import Optional, Dict, List, Tuple, cast, Mapping

from icontract import ensure, require

from aas_core_csharp_codegen import intermediate
from aas_core_csharp_codegen import specific_implementations
from aas_core_csharp_codegen.common import Error, Identifier, assert_never, \
    TRAILING_WHITESPACE_RE, Code
import aas_core_csharp_codegen.csharp.common as csharp_common

# region Checks
from aas_core_csharp_codegen.csharp import naming


def _verify_structure_name_collisions(
        intermediate_symbol_table: intermediate.SymbolTable
) -> List[Error]:
    """Verify that the C# names of the structures do not collide."""
    observed_structure_names = {}  # type: Dict[Identifier, intermediate.Symbol]

    errors = []  # type: List[Error]

    for symbol in intermediate_symbol_table.symbols:
        name = None  # type: Optional[Identifier]

        if isinstance(symbol, intermediate.Class):
            name = naming.class_name(symbol.name)
        elif isinstance(symbol, intermediate.Enumeration):
            name = naming.enum_name(symbol.name)
        elif isinstance(symbol, intermediate.Interface):
            name = naming.interface_name(symbol.name)
        else:
            assert_never(symbol)

        assert name is not None
        if name in observed_structure_names:
            # TODO: test
            errors.append(
                Error(
                    symbol.parsed.node,
                    f"The C# name {name!r} "
                    f"of the meta-model symbol {symbol.name!r} collides "
                    f"with another meta-model symbol "
                    f"{observed_structure_names[name].name!r}"))
        else:
            observed_structure_names[name] = symbol

    # region Intra-structure collisions

    for symbol in intermediate_symbol_table.symbols:
        collision_error = _verify_intra_structure_collisions(intermediate_symbol=symbol)

        if collision_error is not None:
            errors.append(collision_error)

    return errors


def _verify_intra_structure_collisions(
        intermediate_symbol: intermediate.Symbol
) -> Optional[Error]:
    """Verify that no member names collide in the C# structure of the given symbol."""
    errors = []  # type: List[Error]

    # TODO: add method_name to _naming
    # TODO: include methods in this step

    if isinstance(intermediate_symbol, (intermediate.Class, intermediate.Interface)):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in intermediate_symbol.properties:
            private_prop_name = naming.private_property(prop.name)
            if private_prop_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# private property {private_prop_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[private_prop_name]}"
                    ))
            else:
                observed_member_names[private_prop_name] = (
                    f"C# private property {private_prop_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

            getter_name = naming.getter_name(prop.name)
            if getter_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# getter {getter_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[getter_name]}"
                    ))
            else:
                observed_member_names[getter_name] = (
                    f"C# getter {getter_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

            setter_name = naming.setter_name(prop.name)
            if setter_name in observed_member_names:
                # TODO: test
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C# setter {setter_name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[setter_name]}"
                    ))
            else:
                observed_member_names[setter_name] = (
                    f"C# setter {setter_name!r} corresponding to "
                    f"the meta-model property {prop.name!r}")

    elif isinstance(intermediate_symbol, intermediate.Enumeration):
        pass
    else:
        assert_never(intermediate_symbol)

    if len(errors) > 0:
        errors.append(
            Error(
                intermediate_symbol.parsed.node,
                f"Naming collision(s) in C# code "
                f"for the symbol {intermediate_symbol.name!r}",
                underlying=errors))

    return None


class VerifiedIntermediateSymbolTable(intermediate.SymbolTable):
    """Represent a verified symbol table which can be used for code generation."""

    def __new__(
            cls, intermediate_symbol_table: intermediate.SymbolTable
    ) -> 'VerifiedIntermediateSymbolTable':
        raise AssertionError("Only for type annotation")


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def verify(
        intermediate_symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
) -> Tuple[Optional[VerifiedIntermediateSymbolTable], Optional[List[Error]]]:
    """Verify that C# code can be generated from the ``intermediate_symbol_table``."""
    errors = []  # type: List[Error]

    structure_name_collisions = _verify_structure_name_collisions(
        intermediate_symbol_table=intermediate_symbol_table)

    errors.extend(structure_name_collisions)

    for symbol in intermediate_symbol_table.symbols:
        error = _verify_intra_structure_collisions(intermediate_symbol=symbol)
        if error is not None:
            errors.append(error)

    errors.extend(
        specific_implementations.verify_that_available_for_all_symbols(
            intermediate_symbol_table=intermediate_symbol_table,
            spec_impls=spec_impls))

    if len(errors) > 0:
        return None, errors

    return cast(VerifiedIntermediateSymbolTable, intermediate.SymbolTable), None


# endregion

# region Generation

class Block(str):
    """Represent a block of generated code."""

    @require(lambda code: not TRAILING_WHITESPACE_RE.match(code))
    def __new__(cls, block: str) -> 'Block':
        return cast(Block, block)


@require(lambda enum_symbol: not enum_symbol.is_implementation_specific)
def _generate_enum(enum_symbol: intermediate.Enumeration) -> Code:
    """Generate the C# code for the enum."""
    enum_name = naming.enum_name(enum_symbol.name)
    if len(enum_symbol.literals) == 0:
        return Code(f"public enum {enum_name} {{}}")

    writer = io.StringIO()
    writer.write(f"public enum {enum_name}\n{{")
    for i, literal in enumerate(enum_symbol.literals):
        if i > 0:
            writer.write(",\n\n")

        writer.write(
            f'    [EnumMember(Value = {csharp_common.string_literal(literal.value)})]\n'
            f'    {naming.enum_literal_name(literal.name)}')

    writer.write("\n}}")

    return Code(writer.getvalue())


def _generate_interface(
        intermediate_symbol: intermediate.Symbol,
        spec_impls: specific_implementations.SpecificImplementations
) -> Code:
    """Generate C# code for the given interface."""
    raise NotImplementedError()


# fmt: off
@ensure(
    lambda result:
    result.endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate(
        intermediate_symbol_table: VerifiedIntermediateSymbolTable,
        namespace: Identifier,
        spec_impls: specific_implementations.SpecificImplementations
) -> str:
    """
    Generate the C# code of the structures based on the symbol table.

    The ``namespace`` defines the C# namespace.
    """
    warning = Block(textwrap.dedent("""\
        /*
         * This code has been automatically generated by aas-core-csharp-codegen.
         * Do NOT edit or append.
         */"""))

    blocks = [warning]  # type: List[Block]

    using_directives = []  # type: List[str]
    if any(
            isinstance(symbol, intermediate.Enumeration)
            for symbol in intermediate_symbol_table.symbols
    ):
        using_directives.append(
            "using EnumMemberAttribute = "
            "System.Runtime.Serialization.EnumMemberAttribute;")

    if len(using_directives) > 0:
        blocks.append(Block("\n".join(using_directives)))

    blocks.append(Block(f"namespace {namespace}\n{{"))

    for intermediate_symbol in intermediate_symbol_table.symbols:
        code = None  # type: Optional[Code]

        if intermediate_symbol.is_implementation_specific:
            # TODO: test
            code = spec_impls[
                specific_implementations.ImplementationKey(
                    intermediate_symbol.name)]
        else:
            if isinstance(intermediate_symbol, intermediate.Enumeration):
                # TODO: test
                code = _generate_enum(enum_symbol=intermediate_symbol)
            elif isinstance(intermediate_symbol, intermediate.Interface):
                # TODO: test
                code = _generate_interface(
                    intermediate_symbol=intermediate_symbol,
                    spec_impls=spec_impls)
            elif isinstance(intermediate_symbol, intermediate.Class):
                # TODO: impl
                code = _generate_class(
                    intermediate_symbol=intermediate_symbol,
                    spec_impls=spec_impls)
            else:
                assert_never(intermediate_symbol)

        assert code is not None
        blocks.append(Block(textwrap.indent(code, '    ')))

    blocks.append(Block(f"}}  // namespace {namespace}"))

    blocks.append(warning)

    return '\n\n'.join(blocks)

# endregion

# TODO: implement live_test 🠒 use C# compiler to actually create and compile the code!
