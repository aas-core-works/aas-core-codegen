"""Generate JSON schema corresponding to the meta-model."""
import collections
import json
from typing import (
    TextIO,
    Any,
    MutableMapping,
    Optional,
    Tuple,
    List,
    Sequence,
    Mapping,
    Set,
)

from icontract import ensure

from aas_core_codegen import (
    naming,
    specific_implementations,
    intermediate,
    run,
    infer_for_schema,
)
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier


def _define_for_enumeration(
    enumeration: intermediate.Enumeration,
) -> MutableMapping[str, Any]:
    """
    Generate the definition for an ``enumeration``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    definition["type"] = "string"
    definition["enum"] = [literal.value for literal in enumeration.literals]

    model_type = naming.json_model_type(enumeration.name)

    return collections.OrderedDict([(model_type, definition)])


_PRIMITIVE_MAP = {
    intermediate.PrimitiveType.BOOL: "boolean",
    intermediate.PrimitiveType.INT: "integer",
    intermediate.PrimitiveType.FLOAT: "number",
    intermediate.PrimitiveType.STR: "string",
    intermediate.PrimitiveType.BYTEARRAY: "string",
}
assert all(literal in _PRIMITIVE_MAP for literal in intermediate.PrimitiveType)


def _define_primitive_type(
    primitive_type: intermediate.PrimitiveType,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
) -> MutableMapping[str, Any]:
    """
    Generate the type definition for the ``primitive_type``.

    The associated constraints are included in the definition, if specified.
    """
    type_definition = collections.OrderedDict(
        [("type", _PRIMITIVE_MAP[primitive_type])]
    )  # type: MutableMapping[str, Any]

    if (
        primitive_type
        in (intermediate.PrimitiveType.STR, intermediate.PrimitiveType.BYTEARRAY)
        and len_constraint is not None
    ):
        if len_constraint.min_value is not None:
            type_definition["minLength"] = len_constraint.min_value

        if len_constraint.max_value is not None:
            type_definition["maxLength"] = len_constraint.max_value

    if (
        primitive_type == intermediate.PrimitiveType.STR
        and pattern_constraints is not None
        and len(pattern_constraints) > 0
    ):
        if len(pattern_constraints) == 1:
            type_definition["pattern"] = pattern_constraints[0].pattern
        else:
            all_of = [type_definition]  # type: List[MutableMapping[str, Any]]

            for pattern_constraint in pattern_constraints:
                all_of.append(
                    collections.OrderedDict([("pattern", pattern_constraint.pattern)])
                )

            type_definition = collections.OrderedDict([("allOf", all_of)])

    return type_definition


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_type(
    type_annotation: intermediate.TypeAnnotation,
    ref_association: intermediate.ClassUnion,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[Error]]:
    """
    Generate the type definition for ``type_annotation``.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        type_definition = _define_primitive_type(
            primitive_type=type_annotation.a_type,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
        )

        return type_definition, None

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        model_type = naming.json_model_type(type_annotation.symbol.name)

        if isinstance(type_annotation.symbol, intermediate.Enumeration):
            return (
                collections.OrderedDict([("$ref", f"#/definitions/{model_type}")]),
                None,
            )

        elif isinstance(type_annotation.symbol, intermediate.ConstrainedPrimitive):
            type_definition = collections.OrderedDict(
                [("$ref", f"#/definitions/{model_type}")]
            )

            if (
                type_annotation.symbol.constrainee
                in (
                    intermediate.PrimitiveType.STR,
                    intermediate.PrimitiveType.BYTEARRAY,
                )
                and len_constraint is not None
            ):
                if len_constraint.min_value is not None:
                    type_definition["minLength"] = len_constraint.min_value

                if len_constraint.max_value is not None:
                    type_definition["maxLength"] = len_constraint.max_value

            if (
                type_annotation.symbol.constrainee is intermediate.PrimitiveType.STR
                and pattern_constraints is not None
                and len(pattern_constraints) > 0
            ):
                if len(pattern_constraints) == 1:
                    type_definition["pattern"] = pattern_constraints[0].pattern
                else:
                    all_of = [type_definition]  # type: List[MutableMapping[str, Any]]

                    for pattern_constraint in pattern_constraints:
                        all_of.append(
                            collections.OrderedDict(
                                [("pattern", pattern_constraint.pattern)]
                            )
                        )

                    type_definition = collections.OrderedDict([("allOf", all_of)])

            return type_definition, None

        elif isinstance(type_annotation.symbol, intermediate.Class):
            if type_annotation.symbol.interface is not None:
                return (
                    collections.OrderedDict(
                        [("$ref", f"#/definitions/{model_type}_abstract")]
                    ),
                    None,
                )
            else:
                return (
                    collections.OrderedDict([("$ref", f"#/definitions/{model_type}")]),
                    None,
                )

        else:
            assert_never(type_annotation.symbol)

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        # NOTE (mristin, 2021-12-02):
        # We do not propagate the inference of constraints to sub-lists
        # so in this case we set all the constraint on the ``items`` to ``None``.
        # This behavior might change in the future when we encounter such
        # constraints and have more context available.

        items_type_definition, items_error = _define_type(
            type_annotation=type_annotation.items,
            ref_association=ref_association,
            len_constraint=None,
            pattern_constraints=None,
        )

        if items_error is not None:
            return None, items_error

        assert items_type_definition is not None

        type_definition = collections.OrderedDict(
            [("type", "array"), ("items", items_type_definition)]
        )

        if len_constraint is not None:
            if len_constraint.min_value is not None:
                assert (
                    "minItems" not in type_definition
                ), "Unexpected property 'minItems' in the JSON type definition"

                type_definition["minItems"] = len_constraint.min_value

            if len_constraint.max_value is not None:
                assert (
                    "maxItems" not in type_definition
                ), "Unexpected property 'maxItems' in the JSON type definition"

                type_definition["maxItems"] = len_constraint.max_value

        return type_definition, None

    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        raise NotImplementedError(
            f"(mristin, 2021-11-10):\n"
            f"Nested optional values are unexpected in the JSON schema. "
            f"We did not implement them at the moment since we need more information "
            f"about the context.\n\n"
            f"This feature needs yet to be implemented.\n\n"
            f"{type_annotation=}"
        )

    elif isinstance(type_annotation, intermediate.RefTypeAnnotation):
        model_type = naming.json_model_type(ref_association.name)

        return collections.OrderedDict([("$ref", f"#/definitions/{model_type}")]), None

    else:
        raise NotImplementedError(
            f"(mristin, 2021-11-10):\n"
            f"We implemented only a subset of possible type annotations "
            f"to be represented in a JSON schema since we lacked more information "
            f"about the context.\n\n"
            f"This feature needs yet to be implemented.\n\n"
            f"{type_annotation=}"
        )


def _define_for_constrained_primitive(
    constrained_primitive: intermediate.ConstrainedPrimitive,
    pattern_verifications_by_name: infer_for_schema.PatternVerificationsByName,
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[List[Error]]]:
    """
    Generate the JSON definitions based on the ``constrained_primitive``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    all_of = []  # type: List[MutableMapping[str, Any]]

    # region Inheritance

    for inheritance in constrained_primitive.inheritances:
        all_of.append(
            {"$ref": f"#/definitions/{naming.json_model_type(inheritance.name)}"}
        )

    # endregion

    # region Constraints

    errors = []  # type: List[Error]

    (
        len_constraint,
        len_constraint_errors,
    ) = infer_for_schema.infer_len_constraint_of_self(
        constrained_primitive=constrained_primitive
    )

    if len_constraint_errors is not None:
        errors.extend(len_constraint_errors)

    if len(errors) > 0:
        return None, errors

    assert len_constraint is not None

    pattern_constraints = infer_for_schema.infer_patterns_on_self(
        constrained_primitive=constrained_primitive,
        pattern_verifications_by_name=pattern_verifications_by_name,
    )

    type_definition = _define_primitive_type(
        primitive_type=constrained_primitive.constrainee,
        len_constraint=len_constraint,
        pattern_constraints=pattern_constraints,
    )

    all_of.append(type_definition)

    # endregion

    model_type = naming.json_model_type(constrained_primitive.name)

    result = collections.OrderedDict()  # type: MutableMapping[str, Any]
    assert (
        len(all_of) >= 1
    ), "At least the type definition for the primitive type expected"
    result[model_type] = {"allOf": all_of} if len(all_of) > 1 else all_of[0]

    return result, None


# fmt: off
@ensure(
    lambda result:
    (result[0] is not None and result[1] is not None) ^ (result[2] is not None)
)
# fmt: on
def _define_properties_and_required(
    cls: intermediate.Class,
    ref_association: intermediate.ClassUnion,
    pattern_verifications_by_name: infer_for_schema.PatternVerificationsByName,
) -> Tuple[
    Optional[MutableMapping[str, Any]],
    Optional[List[Identifier]],
    Optional[List[Error]],
]:
    """
    Define the ``properties`` and ``required`` part for the given class ``cls``.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    errors = []  # type: List[Error]

    (
        len_constraints_by_property,
        len_constraints_errors,
    ) = infer_for_schema.infer_len_constraints_by_class_properties(cls=cls)

    if len_constraints_errors is not None:
        errors.extend(len_constraints_errors)

    if len(errors) > 0:
        return None, None, errors

    assert len_constraints_by_property is not None

    pattern_constraints_by_property = (
        infer_for_schema.infer_patterns_by_class_properties(
            cls=cls, pattern_verifications_by_name=pattern_verifications_by_name
        )
    )

    properties = collections.OrderedDict()  # type: MutableMapping[str, Any]
    required = []  # type: List[Identifier]

    for prop in cls.properties:
        if prop.specified_for is not cls:
            continue

        prop_name = naming.json_property(prop.name)

        len_constraint = len_constraints_by_property.get(prop, None)
        pattern_constraints = pattern_constraints_by_property.get(prop, None)

        # noinspection PyUnusedLocal
        type_anno = None  # type: Optional[intermediate.TypeAnnotation]
        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            type_anno = prop.type_annotation.value
        else:
            type_anno = prop.type_annotation

            required.append(prop_name)

        assert type_anno is not None
        type_definition, error = _define_type(
            type_annotation=type_anno,
            ref_association=ref_association,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
        )

        if error is not None:
            errors.append(error)
        else:
            assert type_definition is not None
            properties[prop_name] = type_definition

    if len(errors) > 0:
        return None, None, errors

    return properties, required, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_for_class(
    cls: intermediate.Class,
    ref_association: intermediate.ClassUnion,
    ids_of_classes_in_properties: Set[int],
    pattern_verifications_by_name: infer_for_schema.PatternVerificationsByName,
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[List[Error]]]:
    """
    Generate the JSON definitions based on the class ``cls``.

    The list of definitions is to be *extended* with the resulting mapping.

    The ``ref_association`` indicates which symbol to use for representing references
    within an AAS.
    """
    all_of = []  # type: List[MutableMapping[str, Any]]

    # region Inheritance

    for inheritance in cls.inheritances:
        all_of.append(
            {"$ref": f"#/definitions/{naming.json_model_type(inheritance.name)}"}
        )

    # endregion

    # region Properties

    errors = []  # type: List[Error]

    properties, required, properties_error = _define_properties_and_required(
        cls=cls,
        ref_association=ref_association,
        pattern_verifications_by_name=pattern_verifications_by_name,
    )

    if properties_error is not None:
        errors.extend(properties_error)

    if len(errors) > 0:
        return None, errors

    assert properties is not None
    assert required is not None

    if len(properties) > 0:
        definition = collections.OrderedDict(
            [("type", "object"), ("properties", properties)]
        )

        if len(required) > 0:
            definition["required"] = required

        all_of.append(definition)

    # endregion

    model_type = naming.json_model_type(cls.name)

    result = collections.OrderedDict()  # type: MutableMapping[str, Any]
    result[model_type] = {"allOf": all_of} if len(all_of) > 0 else {"type": "object"}

    # region Define the abstract part

    # NOTE (mristin, 2022-01-02):
    # We generate the "*_abstract" definition of a class only if it is used to specify
    # the type of one or more properties in the meta-model. Otherwise, we can ignore
    # the abstract definition as it wouldn't be used during the validation.

    if len(cls.concrete_descendants) > 0 and id(cls) in ids_of_classes_in_properties:
        model_type_abstract = f"{model_type}_abstract"

        any_of = [
            {"$ref": f"#/definitions/{naming.json_model_type(descendant.name)}"}
            for descendant in cls.concrete_descendants
        ]  # type: List[MutableMapping[str, Any]]

        result[model_type_abstract] = {"anyOf": any_of}

    # endregion

    return result, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the JSON schema based on the ``symbol_table."""
    schema_base_key = specific_implementations.ImplementationKey("schema_base.json")

    schema_base_json = spec_impls.get(schema_base_key, None)
    if schema_base_json is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the base schema "
                f"is missing: {schema_base_key}",
            )
        ]

    # noinspection PyUnusedLocal
    schema = None  # type: Optional[MutableMapping[str, Any]]

    try:
        # noinspection PyTypeChecker
        schema = json.loads(schema_base_json, object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as err:
        return None, [
            Error(
                None, f"Failed to parse the base schema from {schema_base_key}: {err}"
            )
        ]

    assert schema is not None

    if "definitions" in schema:
        return None, [
            Error(
                None, "The property ``definitions`` unexpected in the base JSON schema"
            )
        ]

    errors = []  # type: List[Error]

    definitions = collections.OrderedDict()

    pattern_verifications_by_name = infer_for_schema.map_pattern_verifications_by_name(
        verifications=symbol_table.verification_functions
    )

    ids_of_classes_in_properties = intermediate.collect_ids_of_classes_in_properties(
        symbol_table=symbol_table
    )

    for symbol in symbol_table.symbols:
        # Key-value pairs to extend the definitions
        extension = None  # type: Optional[Mapping[str, Any]]

        if isinstance(symbol, intermediate.Class) and symbol.is_implementation_specific:
            implementation_key = specific_implementations.ImplementationKey(
                f"{symbol.name}.json"
            )

            code = spec_impls.get(implementation_key, None)
            if code is None:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"The implementation is missing "
                        f"for the implementation-specific class: {implementation_key}",
                    )
                )
                continue

            try:
                # noinspection PyTypeChecker
                extension = json.loads(code, object_pairs_hook=collections.OrderedDict)
            except Exception as err:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"Failed to parse the JSON out of "
                        f"the specific implementation {implementation_key}: {err}",
                    )
                )
                continue

            if not isinstance(extension, dict):
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"Expected the implementation-specific snippet "
                        f"at {implementation_key} to be a JSON object, "
                        f"but got: {type(extension)}",
                    )
                )
                continue
        else:
            if isinstance(symbol, intermediate.Enumeration):
                extension = _define_for_enumeration(enumeration=symbol)

            elif isinstance(symbol, intermediate.ConstrainedPrimitive):
                extension, definition_errors = _define_for_constrained_primitive(
                    constrained_primitive=symbol,
                    pattern_verifications_by_name=pattern_verifications_by_name,
                )

                if definition_errors is not None:
                    errors.extend(definition_errors)
                    continue

            elif isinstance(symbol, intermediate.Class):
                extension, definition_errors = _define_for_class(
                    cls=symbol,
                    ref_association=symbol_table.ref_association,
                    ids_of_classes_in_properties=ids_of_classes_in_properties,
                    pattern_verifications_by_name=pattern_verifications_by_name,
                )

                if definition_errors is not None:
                    errors.extend(definition_errors)
                    continue

            else:
                assert_never(symbol)

        assert extension is not None
        for identifier, definition in extension.items():
            if identifier in definitions:
                errors.append(
                    Error(
                        symbol.parsed.node,
                        f"One of the JSON definitions, {identifier}, "
                        f"for the symbol {symbol.name} has been "
                        f"already provided in the definitions; "
                        f"did you already define it in another implementation-specific "
                        f"snippet?",
                    )
                )
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
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )

    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the JSON Schema "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "schema.json"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the JSON schema to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")
    return 0
