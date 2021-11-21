"""Generate JSON schema corresponding to the meta-model."""
import argparse
import collections
import json
import pathlib
import sys
from typing import TextIO, Any, MutableMapping, Optional, Tuple, List, Union, Sequence, \
    Mapping

from icontract import ensure, require

import aas_core_csharp_codegen
from aas_core_csharp_codegen import cli, parse, naming, specific_implementations, \
    intermediate
from aas_core_csharp_codegen.common import LinenoColumner, Stripped, Error, \
    assert_never, Identifier

# TODO: this needs to be moved to a separate package once we are done with
#  the development.

assert aas_core_csharp_codegen.jsonschema.__doc__ == __doc__


def _define_for_enumeration(
        enumeration: intermediate.Enumeration
) -> MutableMapping[str, Any]:
    """
    Generate the definition for an ``enumeration``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    definition["type"] = "string"
    definition["enum"] = [
        literal.value
        for literal in enumeration.literals
    ]

    model_type = naming.json_model_type(enumeration.name)

    return collections.OrderedDict([(model_type, definition)])


_BUILTIN_MAP = {
    intermediate.BuiltinAtomicType.BOOL: "boolean",
    intermediate.BuiltinAtomicType.INT: "integer",
    intermediate.BuiltinAtomicType.FLOAT: "number",
    intermediate.BuiltinAtomicType.STR: "string",
    intermediate.BuiltinAtomicType.BYTEARRAY: "string"
}
assert all(literal in _BUILTIN_MAP for literal in intermediate.BuiltinAtomicType)


def _define_type(
        type_annotation: intermediate.TypeAnnotation) -> MutableMapping[str, Any]:
    """Generate the type definition for ``type_annotation``."""
    if isinstance(type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
        return collections.OrderedDict(
            [('type', _BUILTIN_MAP[type_annotation.a_type])]
        )

    elif isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
        model_type = naming.json_model_type(type_annotation.symbol.name)
        return collections.OrderedDict([('$ref', f"#/definitions/{model_type}")])

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        return collections.OrderedDict(
            [('type', 'array'), ('items', _define_type(type_annotation.items))])

    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        raise NotImplementedError(
            f'(mristin, 2021-11-10):\n'
            f'Nested optional values are unexpected in the JSON schema. '
            f'We did not implement them at the moment since we need more information '
            f'about the context.\n\n'
            f'This feature needs yet to be implemented.\n\n'
            f'{type_annotation=}')


def _define_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class]
) -> MutableMapping[str, Any]:
    """
    Generate the definitions resulting from the ``interface``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    all_of = []  # type: List[MutableMapping[str, Any]]

    # region Inheritance

    for inheritance in interface.inheritances:
        all_of.append(
            {
                "$ref": f"#/definitions/Part_{naming.json_model_type(inheritance.name)}"
            })

    # endregion

    # region Properties

    properties = collections.OrderedDict()
    required = []  # type: List[Identifier]

    for prop in interface.properties:
        if prop.implemented_for is not interface:
            continue

        prop_name = naming.json_property(prop.name)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            type_definition = _define_type(
                type_annotation=prop.type_annotation.value)
        else:
            type_definition = _define_type(
                type_annotation=prop.type_annotation)
            required.append(prop_name)

        properties[prop_name] = type_definition

    if len(properties) > 0:
        definition = collections.OrderedDict([
            ('type', 'object'),
            ('properties', properties)
        ])

        if len(required) > 0:
            definition['required'] = required

        all_of.append(
            definition
        )

    # endregion

    # region Constrain to implementers

    any_of = [
        {
            "$ref": f"#/definitions/{naming.json_model_type(implementer.name)}"
        }
        for implementer in implementers
    ]  # type: List[MutableMapping[str, Any]]

    # endregion

    model_type = naming.json_model_type(interface.name)
    part_model_type = f'Part_{model_type}'

    return collections.OrderedDict(
        [
            (part_model_type, {'allOf': all_of})
            if len(all_of) > 0
            else (part_model_type, {'type': 'object'}),
            (model_type, {'anyOf': any_of}),
        ])


def _define_for_class(cls: intermediate.Class) -> MutableMapping[str, Any]:
    """
    Generate the definition for the intermediate class ``cls``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    all_of = []  # type: List[MutableMapping[str, Any]]

    for interface in cls.interfaces:
        # Please mind the difference to ``I{interface name}`` which is
        # the full ``anyOf`` list of class implementers.
        all_of.append(
            {
                "$ref": f"#/definitions/Part_{naming.json_model_type(interface.name)}"
            })

    properties = collections.OrderedDict()
    required = []  # type: List[Identifier]

    model_type = naming.json_model_type(cls.name)

    for prop in cls.properties:
        if prop.implemented_for is not cls:
            continue

        prop_name = naming.json_property(prop.name)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            type_definition = _define_type(
                type_annotation=prop.type_annotation.value)
        else:
            type_definition = _define_type(
                type_annotation=prop.type_annotation)
            required.append(prop_name)

        properties[prop_name] = type_definition

    if cls.json_serialization.with_model_type:
        assert 'modelType' not in properties, (
            f"Unexpected JSON property ``modelType`` to be present in "
            f"the JSON properties of the class {cls.name}. This should have been "
            f"caught before (hence the assertion violation)."
        )

        properties['modelType'] = collections.OrderedDict(
            [
                ('type', 'string'),
                ('const', model_type)
            ])

    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    definition["type"] = "object"
    definition['properties'] = properties

    if len(required) > 0:
        definition['required'] = required

    all_of.append(definition)

    if len(all_of) == 0:
        return {model_type: {'type', 'object'}}
    else:
        return {model_type: {"allOf": all_of}}


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations,
        interface_implementers: intermediate.InterfaceImplementers
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the JSON schema based on the ``symbol_table."""
    schema_base_key = specific_implementations.ImplementationKey(
        "schema_base.json"
    )

    schema_base_json = spec_impls.get(schema_base_key, None)
    if schema_base_json is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the base schema "
                f"is missing: {schema_base_key}")]

    # noinspection PyTypeChecker
    schema = json.loads(
        schema_base_json,
        object_pairs_hook=collections.OrderedDict)

    errors = []  # type: List[Error]

    if 'definitions' in schema:
        errors.append(Error(
            None,
            "The property ``definitions`` unexpected in the base JSON schema"))

    if len(errors) > 0:
        return None, errors

    definitions = collections.OrderedDict()

    for symbol in symbol_table.symbols:
        # Key-value-pairs to extend the definitions
        extension = None  # type: Optional[Mapping[str, Any]]

        if (
                isinstance(symbol, intermediate.Class)
                and symbol.is_implementation_specific
        ):
            implementation_key = specific_implementations.ImplementationKey(
                f"{symbol.name}.json")

            code = spec_impls.get(implementation_key, None)
            if code is None:
                errors.append(Error(
                    symbol.parsed.node,
                    f"The implementation is missing "
                    f"for the implementation-specific class: {implementation_key}"))
                continue

            try:
                # noinspection PyTypeChecker
                extension = json.loads(code, object_pairs_hook=collections.OrderedDict)
            except Exception as err:
                errors.append(Error(
                    symbol.parsed.node,
                    f"Failed to parse the JSON out of "
                    f"the specific implementation {implementation_key}: {err}"
                ))
                continue

            if not isinstance(extension, dict):
                errors.append(Error(
                    symbol.parsed.node,
                    f"Expected the implementation-specific snippet "
                    f"at {implementation_key} to be a JSON object, "
                    f"but got: {type(extension)}"
                ))
                continue
        else:
            if isinstance(symbol, intermediate.Enumeration):
                extension = _define_for_enumeration(enumeration=symbol)
            elif isinstance(symbol, intermediate.Interface):
                extension = _define_for_interface(
                    interface=symbol,
                    implementers=interface_implementers.get(symbol, []))
            elif isinstance(symbol, intermediate.Class):
                extension = _define_for_class(cls=symbol)
            else:
                assert_never(symbol)

        assert extension is not None
        for identifier, definition in extension.items():
            if identifier in definitions:
                errors.append(Error(
                    symbol.parsed.node,
                    f"A JSON definition for the symbol {symbol.name} has been "
                    f"already provided in the definitions under "
                    f"the name: {identifier}; did you already define it in an "
                    f"implementation-specific snippet?"
                ))
                continue
            else:
                definitions[identifier] = definition

    if len(errors) > 0:
        return None, errors

    schema["definitions"] = definitions

    return Stripped(json.dumps(schema, indent=2)), None


class Parameters:
    """Represent the program parameters."""

    def __init__(
            self,
            model_path: pathlib.Path,
            snippets_dir: pathlib.Path,
            output_dir: pathlib.Path
    ) -> None:
        """Initialize with the given values."""
        self.model_path = model_path
        self.snippets_dir = snippets_dir
        self.output_dir = output_dir


def run(params: Parameters, stdout: TextIO, stderr: TextIO) -> int:
    """Run the program."""
    # region Basic checks
    # TODO: test this failure case
    if not params.model_path.exists():
        stderr.write(f"The --model_path does not exist: {params.model_path}\n")
        return 1

    # TODO: test this failure case
    if not params.model_path.is_file():
        stderr.write(
            f"The --model_path does not point to a file: {params.model_path}\n")
        return 1

    # TODO: test this failure case
    if not params.snippets_dir.exists():
        stderr.write(f"The --snippets_dir does not exist: {params.snippets_dir}\n")
        return 1

    # TODO: test this failure case
    if not params.snippets_dir.is_dir():
        stderr.write(
            f"The --snippets_dir does not point to a directory: "
            f"{params.snippets_dir}\n")
        return 1

    # TODO: test the happy path
    if not params.output_dir.exists():
        params.output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # TODO: test this failure case
        if not params.snippets_dir.is_dir():
            stderr.write(
                f"The --output_dir does not point to a directory: "
                f"{params.output_dir}\n")
            return 1

    # endregion

    # region Parse

    spec_impls, spec_impls_errors = (
        specific_implementations.read_from_directory(
            snippets_dir=params.snippets_dir))

    if spec_impls_errors:
        cli.write_error_report(
            message="Failed to resolve the implementation-specific "
                    "JSON schema snippets",
            errors=spec_impls_errors,
            stderr=stderr)
        return 1

    text = params.model_path.read_text(encoding='utf-8')

    # TODO: test all the following individual failure cases
    atok, parse_exception = parse.source_to_atok(source=text)
    if parse_exception:
        if isinstance(parse_exception, SyntaxError):
            stderr.write(
                f"Failed to parse the meta-model {params.model_path}: "
                f"invalid syntax at line {parse_exception.lineno}\n"
            )
        else:
            stderr.write(
                f"Failed to parse the meta-model {params.model_path}: "
                f"{parse_exception}\n"
            )

        return 1

    import_errors = parse.check_expected_imports(atok=atok)
    if import_errors:
        cli.write_error_report(
            message="One or more unexpected imports in the meta-model",
            errors=import_errors,
            stderr=stderr,
        )

        return 1

    lineno_columner = LinenoColumner(atok=atok)

    parsed_symbol_table, error = parse.atok_to_symbol_table(atok=atok)
    if error is not None:
        cli.write_error_report(
            message=f"Failed to construct the symbol table from {params.model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    assert parsed_symbol_table is not None

    ir_symbol_table, error = intermediate.translate(
        parsed_symbol_table=parsed_symbol_table,
        atok=atok,
    )
    if error is not None:
        cli.write_error_report(
            message=f"Failed to translate the parsed symbol table "
                    f"to intermediate symbol table "
                    f"based on {params.model_path}",
            errors=[lineno_columner.error_message(error)],
            stderr=stderr,
        )

        return 1

    interface_implementers = intermediate.map_interface_implementers(
        symbol_table=ir_symbol_table)

    # endregion

    # region Schema

    code, errors = _generate(
        symbol_table=ir_symbol_table,
        spec_impls=spec_impls,
        interface_implementers=interface_implementers)

    if errors is not None:
        cli.write_error_report(
            message=f"Failed to generate the JSON Schema "
                    f"based on {params.model_path}",
            errors=[lineno_columner.error_message(error) for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = params.output_dir / "schema.json"
    try:
        pth.write_text(code)
    except Exception as exception:
        cli.write_error_report(
            message=f"Failed to write the JSON schema to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    # endregion

    stdout.write(f"Code generated to: {params.output_dir}\n")
    return 0


def main(prog: str) -> int:
    """
    Execute the main routine.

    :param prog: name of the program to be displayed in the help
    :return: exit code
    """
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("--model_path", help="path to the meta-model", required=True)
    parser.add_argument(
        "--snippets_dir",
        help="path to the directory containing implementation-specific code snippets",
        required=True)
    parser.add_argument(
        "--output_dir", help="path to the generated code", required=True
    )
    args = parser.parse_args()

    params = Parameters(
        model_path=pathlib.Path(args.model_path),
        snippets_dir=pathlib.Path(args.snippets_dir),
        output_dir=pathlib.Path(args.output_dir),
    )

    run(params=params, stdout=sys.stdout, stderr=sys.stderr)

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="aas-core-csharp-codegen")


if __name__ == "__main__":
    sys.exit(main("aas-core-csharp-codegen"))
