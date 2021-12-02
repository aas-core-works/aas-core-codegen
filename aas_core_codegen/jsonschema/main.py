"""Generate JSON schema corresponding to the meta-model."""
import collections
import json
from typing import TextIO, Any, MutableMapping, Optional, Tuple, List, Sequence, \
    Mapping, Set

from icontract import ensure

from aas_core_codegen import naming, specific_implementations, intermediate, run, \
    infer_for_schema
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier


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
        type_annotation: intermediate.TypeAnnotation,
        ref_association: intermediate.Symbol,
        len_constraint: Optional[infer_for_schema.LenConstraint]
) -> MutableMapping[str, Any]:
    """Generate the type definition for ``type_annotation``."""
    if isinstance(type_annotation, intermediate.BuiltinAtomicTypeAnnotation):
        return collections.OrderedDict(
            [('type', _BUILTIN_MAP[type_annotation.a_type])]
        )

    elif isinstance(type_annotation, intermediate.OurAtomicTypeAnnotation):
        model_type = naming.json_model_type(type_annotation.symbol.name)

        if isinstance(
                type_annotation.symbol, (intermediate.Enumeration, intermediate.Class)):
            return collections.OrderedDict([('$ref', f"#/definitions/{model_type}")])

        elif isinstance(type_annotation.symbol, intermediate.Interface):
            return collections.OrderedDict(
                [('$ref', f"#/definitions/{model_type}_abstract")])

        else:
            assert_never(type_annotation.symbol)

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        # TODO: continue here, finish this
        if len_constraint is not None:
            if len_constraint.min_value is not None:
                if 'minItems' in type_definition:
                    errors.append(Error(

                    ))

                assert 'minItems' not in type_definition, (
                    f"Unexpected property 'minItems' in the JSON type definition of the property {prop_name} for the symbol {symbol.name}"
                )

        # NOTE (mristin, 2021-12-02):
        # We do not propagate the inference of constraints on the length to sub-lists
        # so in this case we set the length constraint on the ``items`` to ``None``.
        # This behavior might change in the future if we ever encounter such
        # constraints.

        return collections.OrderedDict(
            [
                ('type', 'array'),
                (
                    'items',
                    _define_type(
                        type_annotation=type_annotation.items,
                        ref_association=ref_association,
                        len_constraint=None)
                )
            ]
        )

    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        raise NotImplementedError(
            f'(mristin, 2021-11-10):\n'
            f'Nested optional values are unexpected in the JSON schema. '
            f'We did not implement them at the moment since we need more information '
            f'about the context.\n\n'
            f'This feature needs yet to be implemented.\n\n'
            f'{type_annotation=}')

    elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
        model_type = naming.json_model_type(ref_association.name)

        return collections.OrderedDict([('$ref', f"#/definitions/{model_type}")])

    else:
        raise NotImplementedError(
            f'(mristin, 2021-11-10):\n'
            f'We implemented only a subset of possible type annotations '
            f'to be represented in a JSON schema since we lacked more information '
            f'about the context.\n\n'
            f'This feature needs yet to be implemented.\n\n'
            f'{type_annotation=}')


def _define_for_interface(
        interface: intermediate.Interface,
        implementers: Sequence[intermediate.Class],
        ids_of_used_interfaces: Set[int],
        ref_association: intermediate.Symbol
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[List[Error]]]:
    """
    Generate the definitions resulting from the ``interface``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    all_of = []  # type: List[MutableMapping[str, Any]]

    # region Inheritance

    for inheritance in interface.inheritances:
        all_of.append(
            {
                "$ref": f"#/definitions/{naming.json_model_type(inheritance.name)}"
            })

    # endregion

    # region Properties

    errors = []  # type: List[Error]

    len_constraints, len_constraints_errors = (
        infer_for_schema.infer_len_constraints(symbol=interface))

    if len_constraints_errors is not None:
        errors.extend(len_constraints_errors)

    # TODO: add constraint on patterns here as well

    if len(errors) > 0:
        return None, errors

    properties = collections.OrderedDict()
    required = []  # type: List[Identifier]

    for prop in interface.properties:
        if prop.implemented_for is not interface:
            continue

        prop_name = naming.json_property(prop.name)

        len_constraint = len_constraints.get(prop, None)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            type_definition = _define_type(
                type_annotation=prop.type_annotation.value,
                ref_association=ref_association,
                len_constraint=len_constraint)
        else:
            type_definition = _define_type(
                type_annotation=prop.type_annotation,
                ref_association=ref_association,
                len_constraint=len_constraint)
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

    model_type = naming.json_model_type(interface.name)
    model_type_abstract = f'{model_type}_abstract'

    result = collections.OrderedDict()  # type: MutableMapping[str, Any]
    result[model_type] = (
        {'allOf': all_of}
        if len(all_of) > 0
        else {'type': 'object'}
    )

    if id(interface) in ids_of_used_interfaces:
        any_of = [
            {
                "$ref": f"#/definitions/{naming.json_model_type(implementer.name)}"
            }
            for implementer in implementers
        ]  # type: List[MutableMapping[str, Any]]

        result[model_type_abstract] = {'anyOf': any_of}

    return result


def _define_for_class(
        cls: intermediate.Class,
        ref_association: intermediate.Symbol
) -> MutableMapping[str, Any]:
    """
    Generate the definition for the intermediate class ``cls``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    all_of = []  # type: List[MutableMapping[str, Any]]

    for interface in cls.interfaces:
        # Please mind the difference to ``{interface name}`` which is
        # the full ``anyOf`` list of class implementers.
        all_of.append(
            {
                "$ref": f"#/definitions/{naming.json_model_type(interface.name)}"
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
                type_annotation=prop.type_annotation.value,
                ref_association=ref_association)
        else:
            type_definition = _define_type(
                type_annotation=prop.type_annotation,
                ref_association=ref_association)
            required.append(prop_name)

        properties[prop_name] = type_definition

    if cls.serialization.with_model_type:
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

    # noinspection PyUnusedLocal
    schema = None  # type: Optional[MutableMapping[str, Any]]

    try:
        # noinspection PyTypeChecker
        schema = json.loads(
            schema_base_json,
            object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as err:
        return None, [Error(
            None,
            f"Failed to parse the base schema from {schema_base_key}: {err}")]

    assert schema is not None

    if 'definitions' in schema:
        return None, [Error(
            None,
            "The property ``definitions`` unexpected in the base JSON schema")]

    errors = []  # type: List[Error]

    definitions = collections.OrderedDict()

    ids_of_used_interfaces = intermediate.collect_ids_of_interfaces_in_properties(
        symbol_table=symbol_table)

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
                    implementers=interface_implementers.get(symbol, []),
                    ids_of_used_interfaces=ids_of_used_interfaces,
                    ref_association=symbol_table.ref_association)

            elif isinstance(symbol, intermediate.Class):
                extension = _define_for_class(
                    cls=symbol,
                    ref_association=symbol_table.ref_association)

            else:
                assert_never(symbol)

        assert extension is not None
        for identifier, definition in extension.items():
            if identifier in definitions:
                errors.append(Error(
                    symbol.parsed.node,
                    f"One of the JSON definitions, {identifier}, "
                    f"for the symbol {symbol.name} has been "
                    f"already provided in the definitions ; did you already define it "
                    f"in another implementation-specific snippet?"
                ))
                continue
            else:
                definitions[identifier] = definition

    if len(errors) > 0:
        return None, errors

    schema["definitions"] = definitions

    return Stripped(json.dumps(schema, indent=2)), None


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    code, errors = _generate(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        interface_implementers=context.interface_implementers)

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the JSON Schema "
                    f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr)
        return 1

    assert code is not None

    pth = context.output_dir / "schema.json"
    try:
        pth.write_text(code)
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the JSON schema to {pth}",
            errors=[str(exception)],
            stderr=stderr)
        return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
