"""Generate JSON schema corresponding to the meta-model."""
import argparse
import collections
import json
import pathlib
import sys
from typing import TextIO, Any, MutableMapping, Optional, Tuple, List, Union

import asttokens
from icontract import ensure

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
    """Generate the definition for an ``enumeration``."""
    result = collections.OrderedDict()  # type: MutableMapping[str, Any]
    result["type"] = "string"
    result["enum"] = [
        literal.value
        for literal in enumeration.literals
    ]

    return result


_BUILTIN_MAP = {
    intermediate.BuiltinAtomicType.BOOL: "boolean",
    intermediate.BuiltinAtomicType.INT: "integer",
    intermediate.BuiltinAtomicType.FLOAT: "number",
    intermediate.BuiltinAtomicType.STR: "string"
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
        return collections.OrderedDict(
            [('$ref',
              f"#/definitions/{naming.json_model_type(type_annotation.symbol.name)}")])
    elif isinstance(
            type_annotation, (
                    intermediate.ListTypeAnnotation,
                    intermediate.SequenceTypeAnnotation,
                    intermediate.SetTypeAnnotation)):
        return collections.OrderedDict(
            [('type', 'array'), ('items', _define_type(type_annotation.items))])
    elif isinstance(
            type_annotation, (
                    intermediate.MutableMappingTypeAnnotation,
                    intermediate.MappingTypeAnnotation)
    ):
        return collections.OrderedDict([
            ('type', 'object'),
            ('additionalProperties', _define_type(type_annotation.values))
        ])
    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        raise NotImplementedError(
            f'(mristin, 2021-11-10):\n'
            f'Nested optional values are unexpected in the JSON schema. '
            f'We did not implement them at the moment since we need more information '
            f'about the context.\n\n'
            f'This feature needs yet to be implemented.\n\n'
            f'{type_annotation.value=}')


def _define_for_class_or_interface(
        symbol: Union[intermediate.Interface, intermediate.Class]
) -> MutableMapping[str, Any]:
    """Generate the definition for the intermediate ``symbol``."""
    all_of = []  # type: List[MutableMapping[str, Any]]

    if isinstance(symbol, intermediate.Interface):
        for inheritance in symbol.inheritances:
            all_of.append(
                {
                    "$ref": f"#/definitions/{naming.json_model_type(inheritance.name)}"
                })
    elif isinstance(symbol, intermediate.Class):
        for interface in symbol.interfaces:
            all_of.append(
                {
                    "$ref": f"#/definitions/{naming.json_model_type(interface.name)}"
                })
    else:
        assert_never(symbol)

    properties = collections.OrderedDict()
    required = []  # type: List[Identifier]

    for prop in symbol.properties:
        if prop.implemented_for is not symbol:
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

    if (
            symbol.json_serialization is not None
            and symbol.json_serialization.with_model_type
    ):
        properties['modelType'] = collections.OrderedDict(
            [('$ref', '#/definitions/ModelType')])

    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    definition["type"] = "object"
    definition['properties'] = properties

    if len(required) > 0:
        definition['required'] = required

    if len(all_of) == 0 and len(properties) == 0:
        return collections.OrderedDict([('type', 'object')])

    elif len(all_of) > 0 and len(properties) == 0:
        return collections.OrderedDict([('allOf', all_of)])

    elif len(all_of) == 0 and len(properties) > 0:
        return definition

    elif len(all_of) > 0 and len(properties) > 0:
        return collections.OrderedDict([
            ('allOf', all_of + [definition])
        ])


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
        symbol_table: intermediate.SymbolTable,
        spec_impls: specific_implementations.SpecificImplementations
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
        definition = None  # type: Optional[MutableMapping[str, Any]]

        if isinstance(symbol, intermediate.Enumeration):
            definition = _define_for_enumeration(enumeration=symbol)
        elif isinstance(symbol, (intermediate.Interface, intermediate.Class)):
            definition = _define_for_class_or_interface(symbol=symbol)
        else:
            assert_never(symbol)

        definitions[naming.json_model_type(symbol.name)] = definition

    model_type = definitions.get(Identifier('ModelType'), None)
    if model_type is not None:
        errors.append(Error(
            None,
            f"Unexpected definition of ``modelType`` "
            f"in the definitions: {json.dumps(model_type)}"))

    schema["definitions"] = definitions

    if len(errors) > 0:
        return None, errors

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

    text = params.model_path.read_text()

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

    # endregion

    # region Schema

    code, errors = _generate(
        symbol_table=ir_symbol_table,
        spec_impls=spec_impls)

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
