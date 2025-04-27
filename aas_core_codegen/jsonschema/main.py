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
    Callable,
)

from icontract import ensure, require

import aas_core_codegen.jsonschema
from aas_core_codegen import (
    naming,
    specific_implementations,
    intermediate,
    run,
    infer_for_schema,
)
from aas_core_codegen.parse import retree as parse_retree
from aas_core_codegen.common import Stripped, Error, assert_never, Identifier

assert aas_core_codegen.jsonschema.__doc__ == __doc__


def _define_for_enumeration(
    enumeration: intermediate.Enumeration,
) -> MutableMapping[str, Any]:
    """
    Generate the definition for an ``enumeration``.

    The list of definitions is to be *extended* with the resulting mapping.
    """
    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    definition["type"] = "string"
    definition["enum"] = sorted(literal.value for literal in enumeration.literals)

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
) -> MutableMapping[str, Any]:
    """Generate the definition for the given ``primitive_type``."""
    definition = collections.OrderedDict([("type", _PRIMITIVE_MAP[primitive_type])])

    if primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        definition["contentEncoding"] = "base64"

    return definition


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_type(
    type_annotation: intermediate.TypeAnnotationExceptOptional,
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[Error]]:
    """Generate the type definition for ``type_annotation``."""
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return _define_primitive_type(type_annotation.a_type), None

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        model_type = naming.json_model_type(type_annotation.our_type.name)

        if isinstance(type_annotation.our_type, intermediate.Enumeration):
            return (
                collections.OrderedDict([("$ref", f"#/definitions/{model_type}")]),
                None,
            )

        elif isinstance(type_annotation.our_type, intermediate.ConstrainedPrimitive):
            return _define_primitive_type(type_annotation.our_type.constrainee), None

        elif isinstance(type_annotation.our_type, intermediate.Class):
            if len(type_annotation.our_type.concrete_descendants) > 0:
                return (
                    collections.OrderedDict(
                        [("$ref", f"#/definitions/{model_type}_choice")]
                    ),
                    None,
                )
            else:
                return (
                    collections.OrderedDict([("$ref", f"#/definitions/{model_type}")]),
                    None,
                )

        else:
            assert_never(type_annotation.our_type)

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        assert not isinstance(
            type_annotation.items, intermediate.OptionalTypeAnnotation
        ), (
            "NOTE (mristin, 2023-02-06): Lists of optional values were not expected "
            "at the time when we implemented this. Please contact the developers "
            "if you need this functionality."
        )

        items_type_definition, items_error = _define_type(
            type_annotation=type_annotation.items
        )

        if items_error is not None:
            return None, items_error

        assert items_type_definition is not None

        return (
            collections.OrderedDict(
                [("type", "array"), ("items", items_type_definition)]
            ),
            None,
        )

    else:
        raise NotImplementedError(
            f"(mristin, 2021-11-10):\n"
            f"We implemented only a subset of possible type annotations "
            f"to be represented in a JSON schema since we lacked more information "
            f"about the context.\n\n"
            f"This feature needs yet to be implemented.\n\n"
            f"{type_annotation=}"
        )


# NOTE (mristin):
# This function is made public so that we can use it in other schema generators such
# as the SHACL generator.
def fix_pattern_for_utf16(pattern: str) -> str:
    """Parse the pattern and re-render it for UTF-16-only regex engines."""
    regex, error = parse_retree.parse([pattern])
    if error is not None:
        raise ValueError(
            f"The pattern could not be parsed: {pattern!r}; error was: {error}"
        )

    assert regex is not None
    parse_retree.fix_for_utf16_regex_in_place(regex)

    parts = parse_retree.render(regex=regex)
    assert all(
        isinstance(part, str) for part in parts
    ), "Only string parts expected, no formatted values"

    # NOTE (mristin, 2023-03-15):
    # We have to make this transformation for mypy.
    parts_str = []  # type: List[str]
    for part in parts:
        assert isinstance(part, str), "Only string parts expected, no formatted values"
        parts_str.append(part)

    return "".join(parts_str)


def _define_constraints_for_primitive_type(
    primitive_type: intermediate.PrimitiveType,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
    fix_pattern: Callable[[str], str],
) -> MutableMapping[str, Any]:
    """
    Generate the constraints, if any, for the ``primitive_type``.

    If there are no constraints, an empty mapping is returned.

    The ``fix_pattern`` determines how the pattern should be translated for
    the regex engine. For example, some JSON schema verification engines expect only
    characters below Basic Multilingual Plane (BMP), and use surrogate pairs to
    represent characters above BMP.
    """
    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]

    if (
        primitive_type
        in (intermediate.PrimitiveType.STR, intermediate.PrimitiveType.BYTEARRAY)
        and len_constraint is not None
    ):
        if len_constraint.min_value is not None:
            definition["minLength"] = len_constraint.min_value

        if len_constraint.max_value is not None:
            definition["maxLength"] = len_constraint.max_value

    if (
        primitive_type == intermediate.PrimitiveType.STR
        and pattern_constraints is not None
        and len(pattern_constraints) > 0
    ):
        if len(pattern_constraints) == 1:
            definition["pattern"] = fix_pattern(pattern_constraints[0].pattern)
        else:
            all_of = [definition]  # type: List[MutableMapping[str, Any]]

            for pattern_constraint in pattern_constraints:
                all_of.append(
                    collections.OrderedDict(
                        [
                            (
                                "pattern",
                                fix_pattern(pattern_constraint.pattern),
                            )
                        ]
                    )
                )

            definition = collections.OrderedDict([("allOf", all_of)])

    return definition


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_constraints(
    type_annotation: intermediate.TypeAnnotation,
    len_constraint: Optional[infer_for_schema.LenConstraint],
    pattern_constraints: Optional[Sequence[infer_for_schema.PatternConstraint]],
    fix_pattern: Callable[[str], str],
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[Error]]:
    """
    Generate only the constraints for the given ``type_annotation``.

    The type is generated in a separated function, `_generate_type`.

    The ``fix_pattern`` determines how the pattern should be translated for
    the regex engine. For example, some JSON schema verification engines expect only
    characters below Basic Multilingual Plane (BMP), and use surrogate pairs to
    represent characters above BMP.

    If there are no constraints, an empty mapping is returned.
    """
    if isinstance(type_annotation, intermediate.PrimitiveTypeAnnotation):
        return (
            _define_constraints_for_primitive_type(
                primitive_type=type_annotation.a_type,
                len_constraint=len_constraint,
                pattern_constraints=pattern_constraints,
                fix_pattern=fix_pattern,
            ),
            None,
        )

    elif isinstance(type_annotation, intermediate.OurTypeAnnotation):
        if isinstance(type_annotation.our_type, intermediate.Enumeration):
            return collections.OrderedDict(), None

        elif isinstance(type_annotation.our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin, 2022-02-11):
            # We in-line the constraints from the constrained primitives directly
            # in the properties. We do not want to introduce separate definitions
            # for them as that would make it more difficult for downstream code
            # generators to generate meaningful code (*e.g.*, code generators for
            # OpenAPI3).
            return (
                _define_constraints_for_primitive_type(
                    primitive_type=type_annotation.our_type.constrainee,
                    len_constraint=len_constraint,
                    pattern_constraints=pattern_constraints,
                    fix_pattern=fix_pattern,
                ),
                None,
            )

        elif isinstance(type_annotation.our_type, intermediate.Class):
            # NOTE (mristin, 2023-02-06):
            # There are no constraints for class itself in JSON schema. We define
            # constraints only per properties at the moment.
            return collections.OrderedDict(), None

        else:
            assert_never(type_annotation.our_type)

    elif isinstance(type_annotation, intermediate.ListTypeAnnotation):
        # NOTE (mristin, 2021-12-02):
        # We do not propagate the inference of constraints to sub-lists
        # so in this case we set all the constraint on the ``items`` to none.
        # This behavior might change in the future when we encounter such
        # constraints and have more context available.

        definition = collections.OrderedDict()

        if len_constraint is not None:
            if len_constraint.min_value is not None:
                assert (
                    "minItems" not in definition
                ), "Unexpected property 'minItems' in the JSON type definition"

                definition["minItems"] = len_constraint.min_value

            if len_constraint.max_value is not None:
                assert (
                    "maxItems" not in definition
                ), "Unexpected property 'maxItems' in the JSON type definition"

                definition["maxItems"] = len_constraint.max_value

        return definition, None

    elif isinstance(type_annotation, intermediate.OptionalTypeAnnotation):
        raise NotImplementedError(
            f"(mristin, 2021-11-10):\n"
            f"Nested optional values are unexpected in the JSON schema. "
            f"We did not implement them at the moment since we need more information "
            f"about the context.\n\n"
            f"This feature needs yet to be implemented.\n\n"
            f"{type_annotation=}"
        )

    else:
        raise NotImplementedError(
            f"(mristin, 2021-11-10):\n"
            f"We implemented only a subset of possible type annotations "
            f"to be represented in a JSON schema since we lacked more information "
            f"about the context.\n\n"
            f"This feature needs yet to be implemented.\n\n"
            f"{type_annotation=}"
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _define_properties(
    cls: intermediate.ClassUnion,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
    fix_pattern: Callable[[str], str],
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[List[Error]]]:
    """
    Generate the definitions of the meta-model properties for the given ``cls``.

    The property ``modelType`` is defined separately as we need to distinguish
    cases where it is set (concrete class) and not (abstract class, or stub of
    a concrete class with descendants).

    The ``fix_pattern`` determines how the pattern should be translated for
    the regex engine. For example, some JSON schema verification engines expect only
    characters below Basic Multilingual Plane (BMP), and use surrogate pairs to
    represent characters above BMP.
    """
    errors = []  # type: List[Error]

    properties = collections.OrderedDict()  # type: MutableMapping[str, Any]

    for prop in cls.properties:
        prop_name = naming.json_property(prop.name)

        len_constraint = constraints_by_property.len_constraints_by_property.get(
            prop, None
        )

        pattern_constraints = constraints_by_property.patterns_by_property.get(
            prop, None
        )

        type_anno = intermediate.beneath_optional(prop.type_annotation)

        definition = collections.OrderedDict()  # type: MutableMapping[str, Any]

        # NOTE (mristin, 2023-02-06):
        # The properties are inherited through ``allOf``. We can not change the type
        # of property in the children as this would result in a conflict and
        # unsatisfiable schema. Therefore, we define the type for a property only
        # at the parent class, where the property is defined for the first time.
        if prop.specified_for is cls:
            property_definition, error = _define_type(type_annotation=type_anno)

            if error is not None:
                errors.append(error)
            else:
                assert property_definition is not None
                definition.update(property_definition)

        constraints_definition, error = _define_constraints(
            type_annotation=type_anno,
            len_constraint=len_constraint,
            pattern_constraints=pattern_constraints,
            fix_pattern=fix_pattern,
        )
        if error is not None:
            errors.append(error)
        else:
            assert constraints_definition is not None
            definition.update(constraints_definition)

        # NOTE (mristin, 2023-02-06):
        # We do not want to pollute the schema with empty definitions. An empty
        # definition results if there are no constraints and the property is inherited
        # from an ancestor class through ``allOf``.
        if len(definition) > 0:
            properties[prop_name] = definition

    if len(errors) > 0:
        return None, errors

    return properties, None


def _list_required_properties(cls: intermediate.ClassUnion) -> List[Identifier]:
    """
    List all the properties which are required.

    Only the meta-model properties are listed, so this list might not be exhaustive.
    For example, the JSON property ``modelType`` is not listed here.
    """
    required = []  # type: List[Identifier]
    for prop in cls.properties:
        # NOTE (mristin, 2023-02-06):
        # We stack the inheritance as ``allOf``. This will impose the stacking
        # of the required fields as well, so whenever you add a field to
        # a child ``required`` constraint, it will *extend* the list of
        # the required fields, *not* replace it.
        if prop.specified_for is not cls:
            continue

        if not isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            prop_name = naming.json_property(prop.name)
            required.append(prop_name)

    return required


def _define_all_of_for_inheritance(
    cls: intermediate.ClassUnion,
) -> List[MutableMapping[str, Any]]:
    """Generate ``allOf`` definition as inheritance."""
    all_of = []  # type: List[MutableMapping[str, Any]]

    for inheritance in cls.inheritances:
        if isinstance(inheritance, intermediate.AbstractClass):
            all_of.append(
                {"$ref": f"#/definitions/{naming.json_model_type(inheritance.name)}"}
            )
        elif isinstance(inheritance, intermediate.ConcreteClass):
            # NOTE (mristin, 2023-03-13):
            # We distinguish between two definitions corresponding to the same concrete
            # class:
            #
            # 1) One definition defines only the class in abstract, so that
            #    it can be inherited. The abstract definition lacks the ``modelType``
            #    constant, as that would conflict in inheritance.
            # 2) The other definition corresponds to the concrete definition of
            #    the class that an instance has to fulfill. This definition includes
            #    the constant ``modelType``.
            #
            # We had to separate these two definitions to avoid conflicts in
            # ``modelType`` constant between a parent concrete class and a child
            # concrete class.
            all_of.append(
                {
                    "$ref": f"#/definitions/"
                    f"{naming.json_model_type(inheritance.name)}_abstract"
                }
            )

    return all_of


@require(lambda cls: len(cls.concrete_descendants) > 0)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_inheritable_definition(
    cls: intermediate.ClassUnion,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
    fix_pattern: Callable[[str], str],
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[List[Error]]]:
    """
    Generate a definition of ``cls`` for inheritance through ``allOf``.

    The ``fix_pattern`` determines how the pattern should be translated for
    the respective JSON schema engine.

    The definitions are to be *extended* with the resulting mapping.
    """
    all_of = _define_all_of_for_inheritance(cls)

    errors = []  # type: List[Error]

    properties, properties_error = _define_properties(
        cls=cls,
        constraints_by_property=constraints_by_property,
        fix_pattern=fix_pattern,
    )
    if properties_error is not None:
        errors.extend(properties_error)

    if len(errors) > 0:
        return None, errors

    assert properties is not None

    required = _list_required_properties(cls)

    if cls.serialization.with_model_type and not any(
        inheritance.serialization.with_model_type for inheritance in cls.inheritances
    ):
        # NOTE (mristin, 2023-03-13):
        # This is going to be an abstract definition for inheritance, so we can not pin
        # the ``modelType`` to a fixed, constant value.
        assert "modelType" not in properties
        properties["modelType"] = {"$ref": "#/definitions/ModelType"}

        required.append(Identifier("modelType"))

    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    if len(cls.inheritances) == 0:
        definition["type"] = "object"

    if len(properties) > 0:
        definition["properties"] = properties

        if len(required) > 0:
            definition["required"] = required

    if len(definition) > 0:
        all_of.append(definition)

    definition_name: str
    if isinstance(cls, intermediate.AbstractClass):
        definition_name = naming.json_model_type(cls.name)
    elif isinstance(cls, intermediate.ConcreteClass):
        definition_name = f"{naming.json_model_type(cls.name)}_abstract"
    else:
        assert_never(cls)

    result = collections.OrderedDict()  # type: MutableMapping[str, Any]

    if len(all_of) == 0:
        result[definition_name] = {"type": "object"}
    elif len(all_of) == 1:
        result[definition_name] = all_of[0]
    else:
        result[definition_name] = {"allOf": all_of}

    return result, None


@require(lambda cls: len(cls.concrete_descendants) > 0)
def _generate_choice_definition(
    cls: intermediate.ClassUnion,
) -> MutableMapping[str, Any]:
    """
    Generate the definition of dispatching through ``oneOf``.

    The definitions are to be *extended* with the resulting mapping.
    """
    one_of = []  # type: List[Mapping[str, Any]]
    if isinstance(cls, intermediate.ConcreteClass):
        one_of.append({"$ref": f"#/definitions/{naming.json_model_type(cls.name)}"})

    for descendant in cls.concrete_descendants:
        one_of.append(
            {"$ref": f"#/definitions/{naming.json_model_type(descendant.name)}"}
        )

    return {f"{naming.json_model_type(cls.name)}_choice": {"oneOf": one_of}}


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_concrete_definition(
    cls: intermediate.ClassUnion,
    constraints_by_property: infer_for_schema.ConstraintsByProperty,
    fix_pattern: Callable[[str], str],
) -> Tuple[Optional[MutableMapping[str, Any]], Optional[List[Error]]]:
    """
    Generate the definition of a concrete class to be matched by an instance.

    The ``fix_pattern`` determines how the pattern should be translated for
    the respective JSON schema engine.
    """
    # NOTE (mristin, 2023-03-13):
    # We distinguish between two definitions corresponding to the same concrete
    # class:
    #
    # 1) One definition defines only the class in abstract, so that
    #    it can be inherited. The abstract definition lacks the ``modelType``
    #    constant, as that would conflict in inheritance.
    # 2) The other definition corresponds to the concrete definition of
    #    the class that an instance has to fulfill. This definition includes
    #    the constant ``modelType``.
    #
    # We had to separate these two definitions to avoid conflicts in
    # ``modelType`` constant between a parent concrete class and a child
    # concrete class.

    model_type = naming.json_model_type(cls.name)

    if len(cls.concrete_descendants) > 0:
        assert cls.serialization.with_model_type, (
            f"Expected model type to be included in a class with concrete descendants "
            f"{cls.name!r}"
        )

        all_of = [
            {"$ref": f"#/definitions/{model_type}_abstract"},
            {"properties": {"modelType": {"const": model_type}}},
        ]  # type: List[MutableMapping[str, Any]]

        return {model_type: {"allOf": all_of}}, None

    all_of = _define_all_of_for_inheritance(cls)

    errors = []  # type: List[Error]

    properties, properties_error = _define_properties(
        cls=cls,
        constraints_by_property=constraints_by_property,
        fix_pattern=fix_pattern,
    )
    if properties_error is not None:
        errors.extend(properties_error)

    if len(errors) > 0:
        return None, errors

    assert properties is not None

    required = _list_required_properties(cls)

    if cls.serialization.with_model_type:
        properties["modelType"] = {"const": model_type}

    definition = collections.OrderedDict()  # type: MutableMapping[str, Any]
    if len(cls.inheritances) == 0:
        definition["type"] = "object"

    if len(properties) > 0:
        definition["properties"] = properties

        if len(required) > 0:
            definition["required"] = required

    all_of.append(definition)

    model_type = naming.json_model_type(cls.name)

    result = collections.OrderedDict()  # type: MutableMapping[str, Any]

    if len(all_of) == 0:
        result[model_type] = {"type": "object"}
    elif len(all_of) == 1:
        result[model_type] = all_of[0]
    else:
        result[model_type] = {"allOf": all_of}

    return result, None


class Definitions:
    """Store definitions of the schema as we go."""

    def __init__(self) -> None:
        """Initialize as empty."""
        self._definitions = collections.OrderedDict()  # type: MutableMapping[str, Any]

    def get(self) -> Mapping[str, Any]:
        """Get the content."""
        return self._definitions

    def update_for(
        self, our_type: intermediate.OurType, extension: Mapping[str, Any]
    ) -> Optional[Error]:
        """Update the definitions with ``extension`` related to ``our_type``."""
        for key, definition in extension.items():
            if key in self._definitions:
                return Error(
                    our_type.parsed.node,
                    f"One of the JSON definitions, {key}, "
                    f"for our type {our_type.name} has been "
                    f"already provided in the definitions; "
                    f"did you already perhaps define it in another "
                    f"implementation-specific snippet?",
                )

            self._definitions[key] = definition

        return None

    def update(self, extension: Mapping[str, Any]) -> Optional[Error]:
        """Update the definitions with ``extension`` unrelated to any of our types."""
        for key, definition in extension.items():
            if key in self._definitions:
                return Error(
                    None,
                    f"One of the JSON definitions, {key}, "
                    f"has been already provided in the definitions; "
                    f"did you already perhaps define it in another "
                    f"implementation-specific snippet?",
                )

            self._definitions[key] = definition

        return None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def generate(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
    fix_pattern: Callable[[str], str],
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """
    Generate the JSON schema based on the symbol table.

    The ``fix_pattern`` determines how the pattern should be translated for
    the respective JSON schema engine.

    This function is intended to be used not only by aas-core-codegen, but also for
    downstream clients. For example, the downstream clients should use this function
    to customize how patterns should be rendered / fixed for the respective regex
    engine.
    """
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

    schema: MutableMapping[str, Any]

    try:
        # noinspection PyTypeChecker
        schema = json.loads(schema_base_json, object_pairs_hook=collections.OrderedDict)
    except json.JSONDecodeError as err:
        return None, [
            Error(
                None, f"Failed to parse the base schema from {schema_base_key}: {err}"
            )
        ]

    if "$id" in schema:
        return None, [
            Error(
                None,
                f"Unexpected property '$id' in the base JSON schema "
                f"from: {schema_base_key}",
            )
        ]

    # NOTE (mristin, 2022-08-25):
    # We use the same namespace in all the schemas for the consistency.
    schema["$id"] = symbol_table.meta_model.xml_namespace

    if "definitions" in schema:
        return None, [
            Error(
                None,
                f"The property ``definitions`` unexpected in the base JSON schema "
                f"from: {schema_base_key}",
            )
        ]

    errors = []  # type: List[Error]

    definitions = Definitions()

    constraints_by_class, some_errors = infer_for_schema.infer_constraints_by_class(
        symbol_table=symbol_table
    )

    if some_errors is not None:
        errors.extend(some_errors)

    if len(errors) > 0:
        return None, errors

    assert constraints_by_class is not None

    ids_of_our_types_in_properties = (
        intermediate.collect_ids_of_our_types_in_properties(symbol_table=symbol_table)
    )

    for our_type in symbol_table.our_types:
        if (
            isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            )
            and our_type.is_implementation_specific
        ):
            implementation_key = specific_implementations.ImplementationKey(
                f"{our_type.name}.json"
            )

            code = spec_impls.get(implementation_key, None)
            if code is None:
                errors.append(
                    Error(
                        our_type.parsed.node,
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
                        our_type.parsed.node,
                        f"Failed to parse the JSON out of "
                        f"the specific implementation {implementation_key}: {err}",
                    )
                )
                continue

            if not isinstance(extension, dict):
                errors.append(
                    Error(
                        our_type.parsed.node,
                        f"Expected the implementation-specific snippet "
                        f"at {implementation_key} to be a JSON object, "
                        f"but got: {type(extension)}",
                    )
                )
                continue

            update_error = definitions.update_for(
                our_type=our_type, extension=extension
            )
            if update_error is not None:
                errors.append(update_error)

        else:
            if isinstance(our_type, intermediate.Enumeration):
                update_error = definitions.update_for(
                    our_type=our_type,
                    extension=_define_for_enumeration(enumeration=our_type),
                )
                if update_error is not None:
                    errors.append(update_error)

            elif isinstance(our_type, intermediate.ConstrainedPrimitive):
                # NOTE (mristin, 2022-02-11):
                # We in-line the constraints from the constrained primitives directly
                # in the properties. We do not want to introduce separate definitions
                # for them as that would make it more difficult for downstream code
                # generators to generate meaningful code (*e.g.*, code generators for
                # OpenAPI3).
                continue

            elif isinstance(
                our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
            ):
                if len(our_type.concrete_descendants) > 0:
                    # region Inheritable
                    inheritable, definition_errors = _generate_inheritable_definition(
                        cls=our_type,
                        constraints_by_property=constraints_by_class[our_type],
                        fix_pattern=fix_pattern,
                    )

                    if definition_errors is not None:
                        errors.extend(definition_errors)
                        continue

                    assert inheritable is not None
                    update_error = definitions.update_for(
                        our_type=our_type, extension=inheritable
                    )
                    if update_error is not None:
                        errors.append(update_error)
                    # endregion

                    # region Choice
                    if isinstance(our_type, intermediate.ConcreteClass) or (
                        isinstance(our_type, intermediate.AbstractClass)
                        and id(our_type) in ids_of_our_types_in_properties
                    ):
                        update_error = definitions.update_for(
                            our_type=our_type,
                            extension=_generate_choice_definition(cls=our_type),
                        )
                        if update_error is not None:
                            errors.append(update_error)
                    # endregion

                if isinstance(our_type, intermediate.ConcreteClass):
                    definition, definition_errors = _generate_concrete_definition(
                        cls=our_type,
                        constraints_by_property=constraints_by_class[our_type],
                        fix_pattern=fix_pattern,
                    )
                    if definition_errors is not None:
                        errors.extend(definition_errors)
                        continue

                    assert definition is not None

                    update_error = definitions.update_for(
                        our_type=our_type, extension=definition
                    )
                    if update_error is not None:
                        errors.append(update_error)
                else:
                    assert isinstance(our_type, intermediate.AbstractClass)

                    # We do not generate any concrete definition for an abstract class.
                    pass
            else:
                assert_never(our_type)

    if len(errors) > 0:
        return None, errors

    model_types = sorted(
        naming.json_model_type(cls.name)
        for cls in symbol_table.concrete_classes
        if cls.serialization.with_model_type
    )  # type: List[Identifier]

    definitions.update(
        {
            "ModelType": collections.OrderedDict(
                [("type", "string"), ("enum", model_types)]
            )
        }
    )

    definitions_mapping = definitions.get()

    schema["definitions"] = collections.OrderedDict(
        [
            (name, definitions_mapping[name])
            for name in sorted(definitions_mapping.keys())
        ]
    )

    return Stripped(json.dumps(schema, indent=2)), None


def execute(context: run.Context, stdout: TextIO, stderr: TextIO) -> int:
    """Generate the code."""
    code, errors = generate(
        symbol_table=context.symbol_table,
        spec_impls=context.spec_impls,
        fix_pattern=fix_pattern_for_utf16,
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
