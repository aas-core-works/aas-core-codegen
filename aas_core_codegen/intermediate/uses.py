"""
Check which constructs the meta-model uses.

The generators use these checks to generate the helpers, the includes and
the tests only if the meta-model needs them.

Import this module as ``intermediate_uses`` so that the checks read naturally,
*e.g.*, ``intermediate_uses.modulo(symbol_table)``.
"""

from typing import Iterator, List, Sequence, Set, Union

from aas_core_codegen.intermediate import _types
from aas_core_codegen.parse import tree as parse_tree


def json_types(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any property in the model refers to a JSON-able type.

    This works recursively: a JSON-able type is picked up regardless of how
    deeply it is nested within a property's type annotation (*e.g.*, inside
    a ``List[...]`` or an ``Optional[...]``), not just when the property
    itself is directly annotated as one.
    """
    for cls in symbol_table.classes:
        for prop in cls.properties:
            for type_anno in _types.over_type_annotation_and_nested_type_annotations(
                prop.type_annotation
            ):
                if isinstance(
                    type_anno,
                    (
                        _types.JsonValueTypeAnnotation,
                        _types.JsonArrayTypeAnnotation,
                        _types.JsonObjectTypeAnnotation,
                    ),
                ):
                    return True

    return False


def len_slicing_or_find(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any transpiled code might take ``len`` of, slice or search a string.

    The targets use this check to generate the string helpers only if the meta-model
    needs them. The helpers count the characters (code points) as Python does,
    since Python is the language of the meta-model specifications.

    We check the parse trees of the invariants and of the transpilable
    verification functions. As we do not have the types at hand here, we
    over-approximate and count every call to ``len``, even if it were on a list,
    and every method call named ``find``, even if it were a method of our class.
    In the worst case, we generate unused helpers.
    """
    roots = []  # type: List[parse_tree.Node]

    for our_type in symbol_table.our_types:
        if isinstance(
            our_type,
            (_types.ConstrainedPrimitive, _types.AbstractClass, _types.ConcreteClass),
        ):
            roots.extend(invariant.body for invariant in our_type.invariants)

    for verification in symbol_table.verification_functions:
        if isinstance(verification, _types.TranspilableVerification):
            roots.extend(verification.parsed.body)

    for root in roots:
        for node in parse_tree.over_nodes(root):
            if isinstance(node, parse_tree.Slice):
                return True

            if isinstance(node, parse_tree.MethodCall) and node.member.name == "find":
                return True

            if (
                isinstance(node, parse_tree.FunctionCall)
                and node.name.identifier == "len"
            ):
                return True

    return False


def _over_transpilable_nodes(
    symbol_table: _types.SymbolTable,
) -> Iterator[parse_tree.Node]:
    """
    Iterate recursively over all the nodes which the generators transpile.

    These are the nodes of the invariants, of the transpilable verification
    functions and of the understood methods.
    """
    for our_type in symbol_table.our_types:
        if isinstance(
            our_type,
            (_types.ConstrainedPrimitive, _types.AbstractClass, _types.ConcreteClass),
        ):
            for an_invariant in our_type.invariants:
                # NOTE (mristin):
                # We skip the inherited invariants as they are also listed in
                # the type which specified them.
                if an_invariant.specified_for is not our_type:
                    continue

                yield from parse_tree.over_nodes(an_invariant.body)

        if isinstance(our_type, (_types.AbstractClass, _types.ConcreteClass)):
            for method in our_type.methods:
                if isinstance(method, _types.UnderstoodMethod):
                    for node in method.body:
                        yield from parse_tree.over_nodes(node)

    for verification in symbol_table.verification_functions:
        if isinstance(verification, _types.TranspilableVerification):
            for node in verification.parsed.body:
                yield from parse_tree.over_nodes(node)


def modulo(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model uses the modulo operator in transpilable code.

    The generators use this function to decide whether they need to generate
    the helper functions and the tests for the modulo.
    """
    return any(
        isinstance(node, parse_tree.Mod)
        for node in _over_transpilable_nodes(symbol_table)
    )


def assert_statements_in(
    functions: Sequence[Union[_types.Verification, _types.Method]],
) -> bool:
    """
    Check whether the bodies of the ``functions`` contain ``assert`` statements.

    The C++ generator uses this check to include ``<stdexcept>`` only where
    it is needed.
    """
    for function in functions:
        body = ()  # type: Sequence[parse_tree.Node]
        if isinstance(function, _types.TranspilableVerification):
            body = function.parsed.body
        elif isinstance(function, _types.UnderstoodMethod):
            body = function.body
        else:
            pass

        if any(
            isinstance(node, parse_tree.Assert)
            for stmt in body
            for node in parse_tree.over_nodes(stmt)
        ):
            return True

    return False


def abs_call(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model calls the built-in ``abs`` in transpilable code.

    The generators use this function to decide whether they need to generate
    the helper functions and the tests for ``abs``.
    """
    return any(
        isinstance(node, parse_tree.FunctionCall) and node.name.identifier == "abs"
        for node in _over_transpilable_nodes(symbol_table)
    )


def lstrip_call(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model calls ``str.lstrip`` in transpilable code.

    The generators use this function to decide whether they need to generate
    the helper functions and the tests for ``lstrip``.

    We do not distinguish between ``str.lstrip`` and a method of our class
    named ``lstrip``. In the worst case, we generate unused helpers.
    """
    return any(
        isinstance(node, parse_tree.MethodCall) and node.member.name == "lstrip"
        for node in _over_transpilable_nodes(symbol_table)
    )


def int_call(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model calls the built-in ``int`` in transpilable code.

    The generators use this function to decide whether they need to generate
    the helper functions and the tests for parsing the integers.
    """
    return any(
        isinstance(node, parse_tree.FunctionCall) and node.name.identifier == "int"
        for node in _over_transpilable_nodes(symbol_table)
    )


def _nested_sets(
    type_annotation: _types.TypeAnnotationUnion,
) -> Iterator[_types.SetTypeAnnotation]:
    """Iterate over the sets in ``type_annotation`` at any depth."""
    for type_anno in _types.over_type_annotation_and_nested_type_annotations(
        type_annotation
    ):
        if isinstance(type_anno, _types.SetTypeAnnotation):
            yield type_anno


def sets_in(functions: Sequence[Union[_types.Verification, _types.Method]]) -> bool:
    """
    Check whether the ``functions`` take, return or declare local sets.

    The C++ generator uses this check to include ``<unordered_set>`` only where
    it is needed.
    """
    return any(
        any(
            any(True for _ in _nested_sets(argument.type_annotation))
            for argument in function.arguments
        )
        or (
            function.returns is not None
            and any(True for _ in _nested_sets(function.returns))
        )
        or _types.declares_local_set(function)
        for function in functions
    )


def sets(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model might use the sets in transpilable code.

    The sets are the constant sets, the set arguments, the set return values and
    the local sets.
    The generators use this function to decide whether they need to generate
    the helper functions for the sets.
    """
    if any(
        isinstance(
            constant,
            (
                _types.ConstantSetOfPrimitives,
                _types.ConstantSetOfEnumerationLiterals,
            ),
        )
        for constant in symbol_table.constants
    ):
        return True

    functions = [
        *symbol_table.verification_functions,
        *(method for cls in symbol_table.classes for method in cls.methods),
    ]  # type: List[Union[_types.Verification, _types.Method]]

    return sets_in(functions)


def _nested_dicts(
    type_annotation: _types.TypeAnnotationUnion,
) -> Iterator[_types.DictTypeAnnotation]:
    """Iterate over the dictionaries in ``type_annotation`` at any depth."""
    for type_anno in _types.over_type_annotation_and_nested_type_annotations(
        type_annotation
    ):
        if isinstance(type_anno, _types.DictTypeAnnotation):
            yield type_anno


def dicts_in(functions: Sequence[Union[_types.Verification, _types.Method]]) -> bool:
    """
    Check whether the ``functions`` take, return or declare local dictionaries.

    The C++ generator uses this check to include ``<unordered_map>`` only where
    it is needed.
    """
    return any(
        any(
            any(True for _ in _nested_dicts(argument.type_annotation))
            for argument in function.arguments
        )
        or (
            function.returns is not None
            and any(True for _ in _nested_dicts(function.returns))
        )
        or _types.declares_local_dict(function)
        for function in functions
    )


def dicts(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model might use the dictionaries in transpilable code.

    The dictionaries are the dictionary arguments, the dictionary return values and
    the local dictionaries. The generators use this function to decide whether they
    need to generate the helper functions for the dictionaries.
    """
    functions = [
        *symbol_table.verification_functions,
        *(method for cls in symbol_table.classes for method in cls.methods),
    ]  # type: List[Union[_types.Verification, _types.Method]]

    return dicts_in(functions)


def set_operations(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model computes an intersection or a difference of sets.

    The generators use this function to decide whether they need to generate
    the helper functions for the operations on sets.

    We do not distinguish between the methods of the sets and the methods of our
    classes of the same name. In the worst case, we generate unused helpers.
    """
    return any(
        isinstance(node, parse_tree.MethodCall)
        and node.member.name in ("intersection", "difference")
        for node in _over_transpilable_nodes(symbol_table)
    )


def set_properties(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any class of the ``symbol_table`` has a property holding a set.

    The set can be at any depth of the property's type annotation, *e.g.*,
    ``List[Set[str]]``. The sets are serialized as sorted arrays, so we need to
    generate the helpers for sorting them only if there are any.
    """
    return any(
        any(True for _ in _nested_sets(prop.type_annotation))
        for cls in symbol_table.classes
        for prop in cls.properties
    )


def enumerations_in_set_properties(
    symbol_table: _types.SymbolTable,
) -> List[_types.Enumeration]:
    """
    List the enumerations whose literals are held in the sets of the properties.

    The sets can be at any depth of the properties' type annotations. The targets
    sort such a set by the ranks of its literals when they serialize it, so they
    need the helpers ranking the literals of these enumerations.

    The enumerations are listed in the order of their definition in
    the meta-model, each only once.
    """
    ids_in_sets = set()  # type: Set[int]
    for cls in symbol_table.classes:
        for prop in cls.properties:
            for set_type_anno in _nested_sets(prop.type_annotation):
                if isinstance(
                    set_type_anno.items, _types.OurTypeAnnotation
                ) and isinstance(set_type_anno.items.our_type, _types.Enumeration):
                    ids_in_sets.add(id(set_type_anno.items.our_type))

    return [
        enumeration
        for enumeration in symbol_table.enumerations
        if id(enumeration) in ids_in_sets
    ]


def _items_of(
    type_annotation: _types.TypeAnnotationExceptOptional,
) -> Sequence[_types.TypeAnnotationUnion]:
    """
    Give the items of a list or of a tuple, the keys and the values of
    a dictionary, and nothing for anything else.
    """
    if isinstance(type_annotation, _types.ListTypeAnnotation):
        return [type_annotation.items]

    if isinstance(type_annotation, _types.TupleTypeAnnotation):
        return type_annotation.items

    if isinstance(type_annotation, _types.DictTypeAnnotation):
        return [type_annotation.keys, type_annotation.values]

    return []


def sets_nested_in_properties(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any property holds a set nested in a list, in a tuple or in
    a dictionary.

    The generators need this check to import the type of the set where they
    spell out the types of such lists and tuples, but not those of the sets
    themselves, *e.g.*, in the deep copies.
    """
    return any(
        any(True for _ in _nested_sets(item_type_anno))
        for cls in symbol_table.classes
        for prop in cls.properties
        for item_type_anno in _items_of(_types.beneath_optional(prop.type_annotation))
    )


def dict_properties(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any class of the ``symbol_table`` has a property holding a dictionary.

    The dictionary can be at any depth of the property's type annotation, *e.g.*,
    ``List[Dict[str, int]]``. The keys of the dictionaries are serialized sorted,
    so we need to generate the helpers for sorting them only if there are any.
    """
    return any(
        any(True for _ in _nested_dicts(prop.type_annotation))
        for cls in symbol_table.classes
        for prop in cls.properties
    )


def dicts_nested_in_properties(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any property holds a dictionary nested in a list, in a tuple or
    in another dictionary.

    The generators need this check to import the type of the dictionary where
    they spell out the types of such collections, but not those of
    the dictionaries themselves, *e.g.*, in the deep copies.
    """
    return any(
        any(True for _ in _nested_dicts(item_type_anno))
        for cls in symbol_table.classes
        for prop in cls.properties
        for item_type_anno in _items_of(_types.beneath_optional(prop.type_annotation))
    )


def enumerations_in_dict_property_keys(
    symbol_table: _types.SymbolTable,
) -> List[_types.Enumeration]:
    """
    List the enumerations whose literals are the keys of the dictionaries in
    the properties.

    The dictionaries can be at any depth of the properties' type annotations.
    The targets sort the keys of such a dictionary by the ranks of the literals
    when they serialize it, as for the sets, so they need the helpers ranking
    the literals of these enumerations.

    The enumerations are listed in the order of their definition in
    the meta-model, each only once.
    """
    ids_in_keys = set()  # type: Set[int]
    for cls in symbol_table.classes:
        for prop in cls.properties:
            for dict_type_anno in _nested_dicts(prop.type_annotation):
                if isinstance(
                    dict_type_anno.keys, _types.OurTypeAnnotation
                ) and isinstance(dict_type_anno.keys.our_type, _types.Enumeration):
                    ids_in_keys.add(id(dict_type_anno.keys.our_type))

    return [
        enumeration
        for enumeration in symbol_table.enumerations
        if id(enumeration) in ids_in_keys
    ]


def dicts_with_string_keys_in_properties(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether any property holds a dictionary keyed by strings or by
    constrained strings.

    The targets sort such keys by their code points when they serialize them.
    """
    return any(
        _types.try_primitive_type(dict_type_anno.keys) is _types.PrimitiveType.STR
        for cls in symbol_table.classes
        for prop in cls.properties
        for dict_type_anno in _nested_dicts(prop.type_annotation)
    )


def _holds_set_of_enumeration_literals(
    type_annotation: _types.TypeAnnotationUnion,
) -> bool:
    """Check whether ``type_annotation`` holds a set of enumeration literals at any depth."""
    return any(
        isinstance(set_type_anno.items, _types.OurTypeAnnotation)
        and isinstance(set_type_anno.items.our_type, _types.Enumeration)
        for set_type_anno in _nested_sets(type_annotation)
    )


def sets_of_enumeration_literals(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model uses a set of enumeration literals.

    The sets are the constant sets, the set properties, the set arguments,
    the set return values and the local sets. We do not have the types of
    the local sets at hand here, so we resolve the items of ``Set[...]`` and
    ``AbstractSet[...]`` in the annotations of the local declarations.
    """
    if any(
        isinstance(constant, _types.ConstantSetOfEnumerationLiterals)
        for constant in symbol_table.constants
    ):
        return True

    if any(
        _holds_set_of_enumeration_literals(prop.type_annotation)
        for cls in symbol_table.classes
        for prop in cls.properties
    ):
        return True

    functions = [
        *symbol_table.verification_functions,
        *(method for cls in symbol_table.classes for method in cls.methods),
    ]  # type: List[Union[_types.Verification, _types.Method]]

    for function in functions:
        if any(
            _holds_set_of_enumeration_literals(argument.type_annotation)
            for argument in function.arguments
        ):
            return True

        if function.returns is not None and _holds_set_of_enumeration_literals(
            function.returns
        ):
            return True

        for annotation in _types.local_declaration_annotations(function):
            for node in parse_tree.over_nodes(annotation):
                if (
                    isinstance(node, parse_tree.Index)
                    and isinstance(node.collection, parse_tree.Name)
                    and node.collection.identifier in ("Set", "AbstractSet")
                    and isinstance(node.index, parse_tree.Name)
                    and isinstance(
                        symbol_table.find_our_type(node.index.identifier),
                        _types.Enumeration,
                    )
                ):
                    return True

    return False


def _holds_dict_with_enumeration_keys(
    type_annotation: _types.TypeAnnotationUnion,
) -> bool:
    """
    Check whether ``type_annotation`` holds a dictionary keyed by enumeration
    literals at any depth.
    """
    return any(
        isinstance(dict_type_anno.keys, _types.OurTypeAnnotation)
        and isinstance(dict_type_anno.keys.our_type, _types.Enumeration)
        for dict_type_anno in _nested_dicts(type_annotation)
    )


def dicts_with_enumeration_keys(symbol_table: _types.SymbolTable) -> bool:
    """
    Check whether the meta-model uses a dictionary keyed by enumeration literals.

    The dictionaries are the dictionary properties, the dictionary arguments,
    the dictionary return values and the local dictionaries. We do not have
    the types of the local dictionaries at hand here, so we resolve the keys of
    ``Dict[...]`` and ``Mapping[...]`` in the annotations of the local
    declarations.
    """
    if any(
        _holds_dict_with_enumeration_keys(prop.type_annotation)
        for cls in symbol_table.classes
        for prop in cls.properties
    ):
        return True

    functions = [
        *symbol_table.verification_functions,
        *(method for cls in symbol_table.classes for method in cls.methods),
    ]  # type: List[Union[_types.Verification, _types.Method]]

    for function in functions:
        if any(
            _holds_dict_with_enumeration_keys(argument.type_annotation)
            for argument in function.arguments
        ):
            return True

        if function.returns is not None and _holds_dict_with_enumeration_keys(
            function.returns
        ):
            return True

        for annotation in _types.local_declaration_annotations(function):
            for node in parse_tree.over_nodes(annotation):
                if (
                    isinstance(node, parse_tree.Index)
                    and isinstance(node.collection, parse_tree.Name)
                    and node.collection.identifier in ("Dict", "Mapping")
                    and isinstance(node.index, parse_tree.Tuple)
                    and len(node.index.values) == 2
                    and isinstance(node.index.values[0], parse_tree.Name)
                    and isinstance(
                        symbol_table.find_our_type(node.index.values[0].identifier),
                        _types.Enumeration,
                    )
                ):
                    return True

    return False


def sets_of_strings_in_properties(symbol_table: _types.SymbolTable) -> bool:
    """Check whether any class of the ``symbol_table`` has a property holding a set of strings."""
    return any(
        _types.try_primitive_type(set_type_anno.items) is _types.PrimitiveType.STR
        for cls in symbol_table.classes
        for prop in cls.properties
        for set_type_anno in _nested_sets(prop.type_annotation)
    )
