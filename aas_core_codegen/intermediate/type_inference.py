"""
Infer the types of the tree nodes.

Note that these types roughly follow the type annotations in
:py:mod:`aas_core_codegen.intermediate._types`, but are not identical. For example,
the ``LENGTH`` primitive exists only in type inference. Another example, we do not
track ``parsed`` as the types are inferred in the intermediate stage, but can not
be traced back to the parse stage.
"""
import abc
import contextlib
import enum
from typing import Mapping, MutableMapping, Optional, List, Final, Union, get_args

from icontract import DBC, ensure, require

from aas_core_codegen.common import (
    Identifier,
    Error,
    assert_never,
    assert_union_of_descendants_exhaustive,
)
from aas_core_codegen.intermediate import _types
from aas_core_codegen.intermediate._types import Enumeration
from aas_core_codegen.parse import tree as parse_tree


class PrimitiveType(enum.Enum):
    """List primitive types."""

    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BYTEARRAY = "bytearray"

    #: Denote the language-agnostic type returned from ``len(.)``.
    #: Depending on the language, this is not the same as ``INT``.
    LENGTH = "length"

    #: Denote that the node is a statement and that there is no type
    NONE = "None"


class TypeAnnotation(DBC):
    """Represent an inferred type annotation."""

    @abc.abstractmethod
    def __str__(self) -> str:
        # Signal that this is a purely abstract class
        raise NotImplementedError()


class AtomicTypeAnnotation(TypeAnnotation):
    """
    Represent an atomic type annotation.

    Atomic, in this context, means a non-generic type annotation.

    For example, ``int``.
    """

    @abc.abstractmethod
    def __str__(self) -> str:
        # Signal that this is a purely abstract class
        raise NotImplementedError()


class PrimitiveTypeAnnotation(AtomicTypeAnnotation):
    """Represent a primitive type such as ``int``."""

    def __init__(self, a_type: PrimitiveType) -> None:
        """Initialize with the given values."""
        self.a_type = a_type

    def __str__(self) -> str:
        return str(self.a_type.value)


class OurTypeAnnotation(AtomicTypeAnnotation):
    """
    Represent an atomic annotation defined by a symbol in the meta-model.

     For example, ``Asset``.
    """

    def __init__(self, symbol: _types.Symbol) -> None:
        """Initialize with the given values."""
        self.symbol = symbol

    def __str__(self) -> str:
        return self.symbol.name


class FunctionTypeAnnotation(AtomicTypeAnnotation):
    """Represent a function as a type."""

    @abc.abstractmethod
    def __str__(self) -> str:
        # Signal that this is a purely abstract class
        raise NotImplementedError()


class VerificationTypeAnnotation(FunctionTypeAnnotation):
    """Represent a type of a verification function."""

    def __init__(self, func: _types.Verification):
        """Initialize with the given values."""
        self.func = func

    def __str__(self) -> str:
        return self.func.name


class BuiltinFunction:
    """Represent a built-in function."""

    def __init__(self, name: Identifier, returns: Optional["TypeAnnotationUnion"]):
        """Initialize with the given values."""
        self.name = name
        self.returns = returns


class BuiltinFunctionTypeAnnotation(FunctionTypeAnnotation):
    """Represent a type of a built-in function."""

    def __init__(self, func: BuiltinFunction):
        """Initialize with the given values."""
        self.func = func

    def __str__(self) -> str:
        return self.func.name


class MethodTypeAnnotation(AtomicTypeAnnotation):
    """Represent a type of a class method."""

    def __init__(self, method: _types.Method):
        """Initialize with the given values."""
        self.method = method

    def __str__(self) -> str:
        return self.method.name


class SubscriptedTypeAnnotation(TypeAnnotation):
    """Represent a subscripted (i.e. generic) type annotation.

    The subscripted type annotations are, for example, ``List[...]`` (or
    ``Mapping[..., ...]``, *etc.*).
    """

    @abc.abstractmethod
    def __str__(self) -> str:
        # Signal that this is a purely abstract class
        raise NotImplementedError()


class ListTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``List[...]``."""

    def __init__(self, items: "TypeAnnotationUnion"):
        self.items = items

    def __str__(self) -> str:
        return f"List[{self.items}]"


class OptionalTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving an ``Optional[...]``."""

    def __init__(self, value: "TypeAnnotationUnion"):
        self.value = value

    def __str__(self) -> str:
        return f"Optional[{self.value}]"


class EnumerationAsTypeTypeAnnotation(TypeAnnotation):
    """
    Represent an enum class as a type.

    Note that this is not the enum as a type of that enum class, but
    rather the type-as-a-type. We write``Type[T]`` in Python to describe this.
    """

    # NOTE (mristin, 2022-02-04):
    # The name of this class is admittedly clumsy. Please feel free to change if you
    # come up with a better idea.

    def __init__(self, enumeration: Enumeration) -> None:
        """Initialize with the given values."""
        self.enumeration = enumeration

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[{self.enumeration}]"


def _type_annotations_equal(
    that: "TypeAnnotationUnion", other: "TypeAnnotationUnion"
) -> bool:
    """Check whether the ``that`` and ``other`` type annotations are identical."""
    if isinstance(that, PrimitiveTypeAnnotation):
        if not isinstance(other, PrimitiveTypeAnnotation):
            return False
        else:
            return that.a_type == other.a_type

    elif isinstance(that, OurTypeAnnotation):
        if not isinstance(other, OurTypeAnnotation):
            return False
        else:
            return that.symbol is other.symbol

    elif isinstance(that, VerificationTypeAnnotation):
        if not isinstance(other, VerificationTypeAnnotation):
            return False
        else:
            return that.func is other.func

    elif isinstance(that, BuiltinFunctionTypeAnnotation):
        if not isinstance(other, BuiltinFunctionTypeAnnotation):
            return False
        else:
            return that.func is other.func

    elif isinstance(that, MethodTypeAnnotation):
        if not isinstance(other, MethodTypeAnnotation):
            return False
        else:
            return that.method is other.method

    elif isinstance(that, ListTypeAnnotation):
        if not isinstance(other, ListTypeAnnotation):
            return False
        else:
            return _type_annotations_equal(that.items, other.items)

    elif isinstance(that, OptionalTypeAnnotation):
        if not isinstance(other, OptionalTypeAnnotation):
            return False
        else:
            return _type_annotations_equal(that.value, other.value)

    elif isinstance(that, EnumerationAsTypeTypeAnnotation):
        if not isinstance(other, EnumerationAsTypeTypeAnnotation):
            return False
        else:
            return that.enumeration is other.enumeration

    else:
        assert_never(that)

    raise AssertionError("Should not have gotten here")


def _assignable(
    target_type: "TypeAnnotationUnion", value_type: "TypeAnnotationUnion"
) -> bool:
    """Check whether the value can be assigned to the target."""
    if isinstance(target_type, PrimitiveTypeAnnotation):
        if isinstance(value_type, PrimitiveTypeAnnotation):
            return target_type.a_type == value_type.a_type

        # NOTE (mristin, 2021-12-25):
        # We have to be careful about the constrained primitives,
        # since we can always assign a constrained primitive to a primitive, if they
        # primitive types match.
        elif isinstance(value_type, OurTypeAnnotation) and isinstance(
            value_type.symbol, _types.ConstrainedPrimitive
        ):
            return (
                target_type.a_type == PRIMITIVE_TYPE_MAP[value_type.symbol.constrainee]
            )

        else:
            return False

    elif isinstance(target_type, OurTypeAnnotation):
        if isinstance(target_type.symbol, _types.Enumeration):
            # NOTE (mristin, 2021-12-25):
            # The enumerations are invariant.
            return (
                isinstance(value_type, OurTypeAnnotation)
                and isinstance(value_type.symbol, _types.Enumeration)
                and target_type.symbol is value_type.symbol
            )

        elif isinstance(target_type.symbol, _types.ConstrainedPrimitive):
            # NOTE (mristin, 2021-12-25):
            # If it is a constrained primitive with no constraints, allow the assignment
            # if the target and the value match on the primitive type.
            if len(target_type.symbol.invariants) == 0 and isinstance(
                value_type, PrimitiveTypeAnnotation
            ):
                return (
                    PRIMITIVE_TYPE_MAP[target_type.symbol.constrainee]
                    == value_type.a_type
                )
            else:
                # NOTE (mristin, 2021-12-25):
                # We assume the assignments of constrained primitives to be co-variant.
                if (
                    isinstance(value_type, OurTypeAnnotation)
                    and isinstance(value_type.symbol, _types.ConstrainedPrimitive)
                    and target_type.symbol.constrainee == value_type.symbol.constrainee
                ):
                    return (
                        target_type.symbol is value_type.symbol
                        or id(value_type.symbol) in target_type.symbol.descendant_id_set
                    )

            return False

        elif isinstance(target_type.symbol, _types.Class):
            if not (
                isinstance(value_type, OurTypeAnnotation)
                and isinstance(value_type.symbol, _types.Class)
            ):
                return False

            # NOTE (mristin, 2021-12-25):
            # We assume the assignment to be co-variant. Either the target type and
            # the value type are equal *or* the value symbol is a descendant of the
            # target symbol.

            return target_type.symbol is value_type.symbol or (
                id(value_type.symbol) in target_type.symbol.descendant_id_set
            )

    elif isinstance(target_type, VerificationTypeAnnotation):
        if not isinstance(value_type, VerificationTypeAnnotation):
            return False
        else:
            return target_type.func is value_type.func

    elif isinstance(target_type, BuiltinFunctionTypeAnnotation):
        if not isinstance(value_type, BuiltinFunctionTypeAnnotation):
            return False
        else:
            return target_type.func is value_type.func

    elif isinstance(target_type, MethodTypeAnnotation):
        if not isinstance(value_type, MethodTypeAnnotation):
            return False
        else:
            return target_type.method is value_type.method

    elif isinstance(target_type, ListTypeAnnotation):
        if not isinstance(value_type, ListTypeAnnotation):
            return False
        else:
            # NOTE (mristin, 2021-12-25):
            # We assume the lists to be invariant. This is necessary for code generation
            # in implementation targets such as C++ and Golang.
            return _type_annotations_equal(target_type.items, value_type.items)

    elif isinstance(target_type, OptionalTypeAnnotation):
        # NOTE (mristin, 2021-12-25):
        # We can always assign a non-optional to an optional.
        if not isinstance(value_type, OptionalTypeAnnotation):
            return _assignable(target_type=target_type.value, value_type=value_type)
        else:
            # NOTE (mristin, 2021-12-25):
            # We assume the optionals to be co-variant.
            return _assignable(
                target_type=target_type.value, value_type=value_type.value
            )

    elif isinstance(target_type, EnumerationAsTypeTypeAnnotation):
        raise NotImplementedError(
            "(mristin, 2022-02-04): Assigning enumeration-as-type to another "
            "enumeration-as-type is a very niche program logic. As we do not have "
            "a concrete example of such an assignment, we currently ignore this case "
            "in determining whether the assignment makes sense. When you have "
            "a concrete example, please revisit this part of the code."
        )

    else:
        assert_never(target_type)

    return False


PRIMITIVE_TYPE_MAP = {
    _types.PrimitiveType.BOOL: PrimitiveType.BOOL,
    _types.PrimitiveType.INT: PrimitiveType.INT,
    _types.PrimitiveType.FLOAT: PrimitiveType.FLOAT,
    _types.PrimitiveType.STR: PrimitiveType.STR,
    _types.PrimitiveType.BYTEARRAY: PrimitiveType.BYTEARRAY,
}

for _types_primitive_type in _types.PrimitiveType:
    assert (
        _types_primitive_type in PRIMITIVE_TYPE_MAP
    ), f"All primitive types from _types covered, but: {_types_primitive_type=}"


def _type_annotation_to_inferred_type_annotation(
    type_annotation: _types.TypeAnnotationUnion,
) -> "TypeAnnotationUnion":
    """Convert from the :py:mod:`aas_core_codegen.intermediate._types`."""
    if isinstance(type_annotation, _types.PrimitiveTypeAnnotation):
        return PrimitiveTypeAnnotation(
            a_type=PRIMITIVE_TYPE_MAP[type_annotation.a_type]
        )

    elif isinstance(type_annotation, _types.OurTypeAnnotation):
        return OurTypeAnnotation(symbol=type_annotation.symbol)

    elif isinstance(type_annotation, _types.ListTypeAnnotation):
        return ListTypeAnnotation(
            items=_type_annotation_to_inferred_type_annotation(type_annotation.items)
        )

    elif isinstance(type_annotation, _types.OptionalTypeAnnotation):
        return OptionalTypeAnnotation(
            value=_type_annotation_to_inferred_type_annotation(type_annotation.value)
        )

    else:
        assert_never(type_annotation)

    raise AssertionError("Should not have gotten here")


class Environment(DBC):
    """
    Map names to type annotations for a given scope.

    We first search in the given scope and then iterate over the ancestor scopes.
    See, for example: https://craftinginterpreters.com/resolving-and-binding.html.

    The most outer, global, scope is parentless.
    """

    @property
    @abc.abstractmethod
    def mapping(self) -> Mapping[Identifier, "TypeAnnotationUnion"]:
        """Retrieve the underlying mapping."""
        raise NotImplementedError()

    def __init__(self, parent: Optional["Environment"]) -> None:
        """Initialize with the given values."""
        self.parent = parent

    def find(self, identifier: Identifier) -> Optional["TypeAnnotationUnion"]:
        """
        Search for the type annotation of the given ``identifier``.

        We search all the way to the most outer scope.
        """
        type_anno = self.mapping.get(identifier, None)
        if type_anno is not None:
            return type_anno

        if self.parent is not None:
            return self.parent.find(identifier)

        return None


class ImmutableEnvironment(Environment):
    """
    Map immutably names to type annotations for a given scope.
    """

    @property
    def mapping(self) -> Mapping[Identifier, "TypeAnnotationUnion"]:
        """Retrieve the underlying mapping."""
        return self._mapping

    def __init__(
        self,
        mapping: Mapping[Identifier, "TypeAnnotationUnion"],
        parent: Optional["Environment"] = None,
    ) -> None:
        self._mapping = mapping

        Environment.__init__(self, parent)


class MutableEnvironment(Environment):
    """
    Map names to type annotations for a given scope and allow mutations.
    """

    @property
    def mapping(self) -> Mapping[Identifier, "TypeAnnotationUnion"]:
        """Retrieve the underlying mapping."""
        return self._mapping

    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self._mapping = (
            dict()
        )  # type: MutableMapping[Identifier, "TypeAnnotationUnion"]

        Environment.__init__(self, parent)

    def set(
        self, identifier: Identifier, type_annotation: "TypeAnnotationUnion"
    ) -> None:
        """Set the ``type_annotation`` for the given ``identifier``."""
        self._mapping[identifier] = type_annotation


class Canonicalizer(parse_tree.RestrictedTransformer[str]):
    """Represent the nodes as canonical strings so that they can be used in look-ups."""

    #: Track of the canonical representations
    representation_map: Final[MutableMapping[parse_tree.Node, str]]

    def __init__(self) -> None:
        """Initialize with the given values."""
        self.representation_map = dict()

    @ensure(lambda self, node: node in self.representation_map)
    def transform(self, node: parse_tree.Node) -> str:
        return super().transform(node)

    @staticmethod
    def _needs_no_brackets(node: parse_tree.Node) -> bool:
        """
        Check if the representation needs brackets for unambiguity.

        While we could always put brackets, they harm readability in later debugging so
        we try to make the representation as readable as possible.
        """
        return isinstance(
            node,
            (
                parse_tree.Member,
                parse_tree.MethodCall,
                parse_tree.Name,
                parse_tree.FunctionCall,
                parse_tree.Constant,
                parse_tree.JoinedStr,
                parse_tree.Any,
                parse_tree.All,
            ),
        )

    def transform_member(self, node: parse_tree.Member) -> str:
        instance_repr = self.transform(node.instance)

        if Canonicalizer._needs_no_brackets(node.instance):
            result = f"{instance_repr}.{node.name}"
        else:
            result = f"({instance_repr}).{node.name}"

        self.representation_map[node] = result
        return result

    def transform_comparison(self, node: parse_tree.Comparison) -> str:
        left = self.transform(node.left)
        if not Canonicalizer._needs_no_brackets(node.left):
            left = f"({left})"

        right = self.transform(node.right)
        if not Canonicalizer._needs_no_brackets(node.right):
            right = f"({right})"

        result = f"{left} {node.op.value} {right}"
        self.representation_map[node] = result
        return result

    def transform_implication(self, node: parse_tree.Implication) -> str:
        antecedent = self.transform(node.antecedent)
        if not Canonicalizer._needs_no_brackets(node.antecedent):
            antecedent = f"({antecedent})"

        consequent = self.transform(node.consequent)
        if not Canonicalizer._needs_no_brackets(node.consequent):
            consequent = f"({consequent})"

        result = f"{antecedent} ⇒ {consequent}"
        self.representation_map[node] = result
        return result

    def transform_method_call(self, node: parse_tree.MethodCall) -> str:
        member = self.transform(node.member)

        args = [self.transform(arg) for arg in node.args]

        args_joined = ", ".join(args)
        result = f"{member}({args_joined})"
        self.representation_map[node] = result
        return result

    def transform_function_call(self, node: parse_tree.FunctionCall) -> str:
        name = self.transform(node.name)

        args = [self.transform(arg) for arg in node.args]

        args_joined = ", ".join(args)
        result = f"{name}({args_joined})"
        self.representation_map[node] = result
        return result

    def transform_constant(self, node: parse_tree.Constant) -> str:
        result = repr(node.value)
        self.representation_map[node] = result
        return result

    def transform_is_none(self, node: parse_tree.IsNone) -> str:
        value = self.transform(node.value)
        if not Canonicalizer._needs_no_brackets(node.value):
            value = f"({value})"

        result = f"{value} is None"
        self.representation_map[node] = result
        return result

    def transform_is_not_none(self, node: parse_tree.IsNotNone) -> str:
        value = self.transform(node.value)
        if not Canonicalizer._needs_no_brackets(node.value):
            value = f"({value})"

        result = f"{value} is not None"
        self.representation_map[node] = result
        return result

    def transform_name(self, node: parse_tree.Name) -> str:
        result = node.identifier
        self.representation_map[node] = result
        return result

    def transform_and(self, node: parse_tree.And) -> str:
        values = []  # type: List[str]
        for value_node in node.values:
            value = self.transform(value_node)
            if not Canonicalizer._needs_no_brackets(value_node):
                value = f"({value})"

            values.append(value)

        result = " and ".join(values)
        self.representation_map[node] = result
        return result

    def transform_or(self, node: parse_tree.Or) -> str:
        values = []  # type: List[str]
        for value_node in node.values:
            value = self.transform(value_node)
            if not Canonicalizer._needs_no_brackets(value_node):
                value = f"({value})"

            values.append(value)

        result = " or ".join(values)
        self.representation_map[node] = result
        return result

    def transform_formatted_value(self, node: parse_tree.FormattedValue) -> str:
        result = self.transform(node.value)
        self.representation_map[node] = result
        return result

    def transform_joined_str(self, node: parse_tree.JoinedStr) -> str:
        parts = []  # type: List[str]
        for value in node.values:
            if isinstance(value, str):
                parts.append(repr(value))
            elif isinstance(value, parse_tree.FormattedValue):
                transformed_value = self.transform(value)
                parts.append(f"{{{transformed_value}}}")
            else:
                assert_never(value)

        result = "".join(parts)
        self.representation_map[node] = result
        return result

    def transform_for_each(self, node: parse_tree.ForEach) -> str:
        variable = self.transform(node.variable)
        iteration = self.transform(node.iteration)
        if not Canonicalizer._needs_no_brackets(node.iteration):
            iteration = f"({iteration})"

        result = f"for {variable} in {iteration}"
        self.representation_map[node] = result
        return result

    def _transform_any_or_all(self, node: Union[parse_tree.Any, parse_tree.All]) -> str:
        for_each = self.transform(node.for_each)

        condition = self.transform(node.condition)
        if not Canonicalizer._needs_no_brackets(node.condition):
            condition = f"({condition})"

        if isinstance(node, parse_tree.Any):
            result = f"any({condition} {for_each})"
        elif isinstance(node, parse_tree.All):
            result = f"all({condition} {for_each})"
        else:
            assert_never(node)

        self.representation_map[node] = result
        return result

    def transform_any(self, node: parse_tree.Any) -> str:
        return self._transform_any_or_all(node)

    def transform_all(self, node: parse_tree.All) -> str:
        return self._transform_any_or_all(node)

    def transform_assignment(self, node: parse_tree.Assignment) -> str:
        target = self.transform(node.target)
        if not Canonicalizer._needs_no_brackets(node.target):
            target = f"({target})"

        # NOTE (mristin, 2022-06-17):
        # Nested assignments are not possible in Python, but who knows where our
        # intermediate representation will take us. Therefore, we handle this edge case
        # even though it seems nonsensical at the moment.
        value = self.transform(node.value)
        if isinstance(node.value, parse_tree.Assignment):
            value = f"({value})"

        result = f"{target} = {value}"

        self.representation_map[node] = result
        return result

    def transform_return(self, node: parse_tree.Return) -> str:
        if node.value is not None:
            value = self.transform(node.value)

            # NOTE (mristin, 2022-06-17):
            # Nested returns are not possible in Python, but who knows where our
            # intermediate representation will take us. Therefore, we handle this edge case
            # even though it seems nonsensical at the moment.
            if isinstance(node.value, parse_tree.Return):
                value = f"({value})"

            result = f"return {value}"
        else:
            result = "return"

        self.representation_map[node] = result
        return result


class _CountingMap:
    """Provide a map to track multiple counters."""

    def __init__(self) -> None:
        self._counts = dict()  # type: MutableMapping[str, int]

    def increment(self, key: str) -> None:
        """Increment the counter for the ``key``."""
        count = self._counts.get(key, None)
        if count is None:
            self._counts[key] = 1
        else:
            self._counts[key] = count + 1

    @ensure(lambda self, key, result: not result or self.count(key) > 0)
    @ensure(lambda self, key, result: result or self.count(key) == 0)
    def at_least_once(self, key: str) -> bool:
        """Return ``True`` if the ``key`` is tracked and the count is at least 1."""
        count = self.count(key)
        return count >= 1

    @ensure(lambda result: result >= 0)
    def count(self, key: str) -> int:
        """Return the number of stacked ``key``'s."""
        result = self._counts.get(key, None)
        return 0 if result is None else result

    # fmt: off
    @require(
        lambda self, key:
        self.at_least_once(key),
        "Can not decrement past 1"
    )
    # fmt: on
    def decrement(self, key: str) -> None:
        """Decrement the counter for the ``key``."""
        count = self._counts.get(key, None)

        if count is None or count == 0:
            raise AssertionError(f"Unexpected count == 0 for key {key!r}")
        elif count < 0:
            raise AssertionError(f"Unexpected count < 0 for key {key!r}")
        elif count == 1:
            del self._counts[key]
        else:
            self._counts[key] = count - 1


class Inferrer(parse_tree.RestrictedTransformer[Optional["TypeAnnotationUnion"]]):
    """
    Infer the types of the given parse tree.

    Since we also handle non-nullness, you need to pre-compute the canonical
    representation of the nodes that you want to infer the types for. To that end,
    use :class:`~CanonicalRepresenter`.
    """

    #: Track of the inferred types
    type_map: Final[MutableMapping[parse_tree.Node, "TypeAnnotationUnion"]]

    #: Errors encountered during the inference
    errors: Final[List[Error]]

    def __init__(
        self,
        symbol_table: _types.SymbolTable,
        environment: "Environment",
        representation_map: Mapping[parse_tree.Node, str],
    ) -> None:
        """Initialize with the given values."""
        self._symbol_table = symbol_table

        # We need to create our own child environment so that we can introduce new
        # entries without affecting the variables from the outer scopes.
        self._environment = MutableEnvironment(parent=environment)

        self._representation_map = representation_map

        # NOTE (mristin, 2022-06-17):
        # We need to keep track of the expressions that can be assumed to be non-null.
        # This member is stateful! It will constantly change, depending on the position
        # of the iteration through the tree.
        #
        # We use canonical representation from ``representation_map`` to associate
        # non-null assumptions with the expressions.
        self._non_null = _CountingMap()

        self.type_map = dict()
        self.errors = []

    def _strip_optional_if_non_null(
        self, node: parse_tree.Node, type_annotation: "TypeAnnotationUnion"
    ) -> "TypeAnnotationUnion":
        """
        Remove ``Optional`` from the ``type_annotation`` if the ``node`` is non-null.

        The ``type_annotation`` refers to the type inferred for the ``node``.

        We keep track of the non-nullness over the iteration in :attr:`._non_null`.
        Using the canonical representation of the ``node``, we can check whether
        the type of the ``node`` is non-null.
        """
        if not isinstance(type_annotation, OptionalTypeAnnotation):
            return type_annotation

        canonical_repr = self._representation_map[node]
        if self._non_null.at_least_once(canonical_repr):
            return type_annotation.value

        return type_annotation

    @ensure(lambda self, result: not (result is None) or len(self.errors) > 0)
    def transform(self, node: parse_tree.Node) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin, 2022-06-17):
        # We can not write the following as the pre-condition as it would break
        # behavioral subtyping since the parent class expects no pre-conditions.
        #
        # However, in this case, we check that the supplied dependency,
        # ``representation_map``, is correct.
        assert node in self._representation_map, (
            f"The node {parse_tree.dump(node)} at 0x{id(node):x} could not be found "
            f"in the supplied representation_map."
        )

        return super().transform(node)

    def transform_member(
        self, node: parse_tree.Member
    ) -> Optional["TypeAnnotationUnion"]:
        instance_type = self.transform(node.instance)

        if instance_type is None:
            return None

        if isinstance(instance_type, OurTypeAnnotation) and isinstance(
            instance_type.symbol, _types.Class
        ):
            cls = instance_type.symbol
            assert isinstance(cls, _types.Class)

            prop = cls.properties_by_name.get(node.name, None)
            if prop is not None:
                result = _type_annotation_to_inferred_type_annotation(
                    prop.type_annotation
                )

                result = self._strip_optional_if_non_null(
                    node=node, type_annotation=result
                )
                self.type_map[node] = result
                return result

            method = cls.methods_by_name.get(node.name, None)
            if method is not None:
                result = MethodTypeAnnotation(method=method)

                result = self._strip_optional_if_non_null(
                    node=node, type_annotation=result
                )
                self.type_map[node] = result
                return result

            self.errors.append(
                Error(
                    node.original_node,
                    f"The member {node.name!r} could not be found "
                    f"in the class {cls.name!r}",
                )
            )

        elif isinstance(instance_type, EnumerationAsTypeTypeAnnotation):
            enumeration = instance_type.enumeration
            literal = enumeration.literals_by_name.get(node.name, None)
            if literal is not None:
                result = OurTypeAnnotation(symbol=enumeration)

                result = self._strip_optional_if_non_null(
                    node=node, type_annotation=result
                )
                self.type_map[node] = result
                return result

            self.errors.append(
                Error(
                    node.original_node,
                    f"The literal {node.name!r} could not be found "
                    f"in the enumeration {enumeration.name!r}",
                )
            )
        else:
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected an instance type to be either an enumeration-as-type or "
                    f"a class, but got: {instance_type}",
                )
            )
            return None

        return None

    def transform_comparison(
        self, node: parse_tree.Comparison
    ) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``left`` and ``right`` even though we
        # know the type in advance
        success = (self.transform(node.left) is not None) and (
            self.transform(node.right) is not None
        )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_implication(
        self, node: parse_tree.Implication
    ) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin, 2022-06-17):
        # Just recurse to fill ``type_map`` on ``antecedent`` even though we know the
        # type in advance
        if self.transform(node.antecedent) is None:
            return None

        # region Recurse into consequent while considering any non-nullness

        # NOTE (mristin, 2022-06-17):
        # We are very lax here and ignore the fact that calls to methods and functions
        # can actually alter the value assumed to be non-null, and actually violate
        # its non-nullness by setting it to null.
        #
        # This lack of conservatism works for now. If the bugs related to nullness
        # start to surface, we should re-think our approach here.

        with contextlib.ExitStack() as exit_stack:
            if isinstance(node.antecedent, parse_tree.IsNotNone):
                canonical_repr = self._representation_map[node.antecedent.value]
                self._non_null.increment(canonical_repr)

                exit_stack.callback(
                    lambda a_canonical_repr=canonical_repr: self._non_null.decrement(
                        a_canonical_repr
                    )
                )

            elif isinstance(node.antecedent, parse_tree.And):
                for value in node.antecedent.values:
                    if isinstance(value, parse_tree.IsNotNone):
                        canonical_repr = self._representation_map[value.value]
                        self._non_null.increment(canonical_repr)

                        exit_stack.callback(
                            lambda a_canonical_repr=canonical_repr: self._non_null.decrement(
                                a_canonical_repr
                            )
                        )
            else:
                # NOTE (mristin, 2022-06-17):
                # We do not know how to infer any non-nullness in this case.
                pass

            success = self.transform(node.consequent) is not None

            if not success:
                return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_method_call(
        self, node: parse_tree.MethodCall
    ) -> Optional["TypeAnnotationUnion"]:
        # Simply recurse to track the type, but we don't care about the arguments
        failed = False
        for arg in node.args:
            arg_type = self.transform(arg)
            if arg_type is None:
                failed = True

        member_type = self.transform(node.member)

        if member_type is None:
            failed = True

        if failed:
            return None

        if not isinstance(member_type, MethodTypeAnnotation):
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected the member in a method call to be a method, "
                    f"but got: {member_type}",
                )
            )
            return None

        # noinspection PyUnusedLocal
        result = None  # type: Optional[TypeAnnotationUnion]

        if member_type.method.returns is None:
            result = PrimitiveTypeAnnotation(a_type=PrimitiveType.NONE)
        else:
            result = _type_annotation_to_inferred_type_annotation(
                member_type.method.returns
            )

        assert result is not None

        result = self._strip_optional_if_non_null(node=node, type_annotation=result)
        self.type_map[node] = result
        return result

    def transform_function_call(
        self, node: parse_tree.FunctionCall
    ) -> Optional["TypeAnnotationUnion"]:
        result = None  # type: Optional[TypeAnnotationUnion]
        failed = False

        func_type = self.transform(node.name)
        if func_type is None:
            failed = True
        else:
            # NOTE (mristin, 2021-12-26):
            # The verification functions use
            # :py:mod:`aas_core_codegen.intermediate._types` while the built-in
            # functions are a construct of
            # :py:mod:`aas_core_codegen.intermediate.type_inference`.

            if isinstance(func_type, VerificationTypeAnnotation):
                if func_type.func.returns is not None:
                    result = _type_annotation_to_inferred_type_annotation(
                        func_type.func.returns
                    )
                else:
                    result = PrimitiveTypeAnnotation(PrimitiveType.NONE)

            elif isinstance(func_type, BuiltinFunctionTypeAnnotation):
                if func_type.func.returns is not None:
                    result = func_type.func.returns
                else:
                    result = PrimitiveTypeAnnotation(PrimitiveType.NONE)

            elif isinstance(
                func_type,
                (
                    PrimitiveTypeAnnotation,
                    OurTypeAnnotation,
                    MethodTypeAnnotation,
                    ListTypeAnnotation,
                    OptionalTypeAnnotation,
                    EnumerationAsTypeTypeAnnotation,
                ),
            ):
                self.errors.append(
                    Error(
                        node.name.original_node,
                        f"Expected the variable {node.name.identifier!r} to be "
                        f"a function, but got {func_type}",
                    )
                )

            else:
                assert_never(func_type)

        # NOTE (mristin, 2021-12-26):
        # Recurse to track the type of arguments. Even if we failed before, we want to
        # catch the errors in the arguments for better developer experience.
        #
        # Mind that we are sloppy here. Theoretically, we could check that arguments in
        # the call are assignable to the arguments in the function definition and catch
        # errors in the meta-model at this point. However, we prioritize other features
        # and leave this check unimplemented for now.

        for arg in node.args:
            arg_type = self.transform(arg)
            if arg_type is None:
                failed = True

        if failed:
            return None

        assert result is not None

        result = self._strip_optional_if_non_null(node=node, type_annotation=result)
        self.type_map[node] = result
        return result

    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Optional["TypeAnnotationUnion"]:
        result = None  # type: Optional[TypeAnnotationUnion]

        if isinstance(node.value, bool):
            result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        elif isinstance(node.value, int):
            result = PrimitiveTypeAnnotation(PrimitiveType.INT)
        elif isinstance(node.value, float):
            result = PrimitiveTypeAnnotation(PrimitiveType.FLOAT)
        elif isinstance(node.value, str):
            result = PrimitiveTypeAnnotation(PrimitiveType.STR)
        else:
            assert_never(node.value)

        assert result is not None

        self.type_map[node] = result
        return result

    def transform_is_none(
        self, node: parse_tree.IsNone
    ) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``value`` even though we know the type in
        # advance
        success = self.transform(node.value) is not None

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_is_not_none(
        self, node: parse_tree.IsNotNone
    ) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``value`` even though we know the type in
        # advance
        success = self.transform(node.value) is not None

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_name(self, node: parse_tree.Name) -> Optional["TypeAnnotationUnion"]:
        type_in_env = self._environment.find(node.identifier)
        if type_in_env is None:
            self.errors.append(
                Error(
                    node.original_node,
                    f"We do not know how to infer the type of "
                    f"the variable with the identifier {node.identifier!r} from the "
                    f"given environment. Mind that we do not consider the module "
                    f"scope nor handle all built-in functions due to simplicity! If "
                    f"you believe this needs to work, please notify the developers.",
                )
            )
            return None

        result = type_in_env

        result = self._strip_optional_if_non_null(node=node, type_annotation=result)
        self.type_map[node] = result
        return result

    def transform_and(self, node: parse_tree.And) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin, 2022-06-17):
        # We need to iterate and recurse into ``values`` to fill the ``type_map``.
        # In the process, we have to consider the non-nullness and how it applies
        # to the remainder of the conjunction.

        # NOTE (mristin, 2022-06-17):
        # We are very lax here and ignore the fact that calls to methods and functions
        # can actually alter the value assumed to be non-null, and actually violate
        # its non-nullness by setting it to null.
        #
        # This lack of conservatism works for now. If the bugs related to nullness
        # start to surface, we should re-think our approach here.

        with contextlib.ExitStack() as exit_stack:
            for value in node.values:
                success = self.transform(value) is not None
                if not success:
                    return None

                if isinstance(value, parse_tree.IsNotNone):
                    canonical_repr = self._representation_map[value.value]
                    self._non_null.increment(canonical_repr)

                    exit_stack.callback(
                        lambda a_canonical_repr=canonical_repr: self._non_null.decrement(
                            a_canonical_repr
                        )
                    )

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_or(self, node: parse_tree.Or) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance
        success = all(
            self.transform(value_node) is not None for value_node in node.values
        )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_formatted_value(
        self, node: parse_tree.FormattedValue
    ) -> Optional["TypeAnnotationUnion"]:
        value_type = self.transform(node.value)
        if value_type is None:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.STR)
        self.type_map[node] = result
        return result

    def transform_joined_str(
        self, node: parse_tree.JoinedStr
    ) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance
        success = True
        for value in node.values:
            if isinstance(value, str):
                continue
            elif isinstance(value, parse_tree.FormattedValue):
                formatted_value_type = self.transform(value)
                if formatted_value_type is None:
                    success = False
            else:
                assert_never(value)

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.STR)
        self.type_map[node] = result
        return result

    def transform_for_each(
        self, node: parse_tree.ForEach
    ) -> Optional["TypeAnnotationUnion"]:
        variable_type_in_env = self._environment.find(node.variable.identifier)
        if variable_type_in_env is not None:
            self.errors.append(
                Error(
                    node.variable.original_node,
                    f"The variable {node.variable.identifier} "
                    f"has been already defined before",
                )
            )
            return None

        iter_type = self.transform(node.iteration)
        if iter_type is None:
            return None

        while isinstance(iter_type, OptionalTypeAnnotation):
            iter_type = iter_type.value

        if not isinstance(iter_type, ListTypeAnnotation):
            self.errors.append(
                Error(
                    node.iteration.original_node,
                    f"Expected an iteration over a list, but got: {iter_type}",
                )
            )
            return None

        self._environment.set(
            identifier=node.variable.identifier, type_annotation=iter_type.items
        )

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def _transform_any_or_all(
        self, node: Union[parse_tree.Any, parse_tree.All]
    ) -> Optional["TypeAnnotationUnion"]:
        a_type = self.transform(node.for_each)
        if a_type is None:
            return None

        a_type = self.transform(node.condition)
        if a_type is None:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_any(self, node: parse_tree.Any) -> Optional["TypeAnnotationUnion"]:
        return self._transform_any_or_all(node)

    def transform_all(self, node: parse_tree.All) -> Optional["TypeAnnotationUnion"]:
        return self._transform_any_or_all(node)

    def transform_assignment(
        self, node: parse_tree.Assignment
    ) -> Optional["TypeAnnotationUnion"]:
        is_new_variable = False

        # noinspection PyUnusedLocal
        target_type = None  # type: Optional[TypeAnnotationUnion]

        if isinstance(node.target, parse_tree.Name):
            target_type = self._environment.find(node.target.identifier)
            if target_type is None:
                is_new_variable = True
        else:
            target_type = self.transform(node.target)

        value_type = self.transform(node.value)

        if (not is_new_variable and target_type is None) or (value_type is None):
            return None

        if target_type is not None and not _assignable(
            target_type=target_type, value_type=value_type
        ):
            self.errors.append(
                Error(
                    node.original_node,
                    f"We inferred the target type of the assignment to "
                    f"be {target_type}, while the value type is inferred to "
                    f"be {value_type}. We do not know how to model this assignment.",
                )
            )
            return None

        if is_new_variable:
            assert isinstance(node.target, parse_tree.Name)

            self._environment.set(
                identifier=node.target.identifier, type_annotation=value_type
            )

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_return(
        self, node: parse_tree.Return
    ) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``value`` even though we know the type
        # in advance
        if node.value is not None:
            success = self.transform(node.value) is not None
            if not success:
                return None

        # Treat ``return`` as a statement
        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result


def populate_base_environment(symbol_table: _types.SymbolTable) -> Environment:
    """Create a basic mapping name 🠒 type annotation from the global scope.

    The global scope, in this context, refers to the level of symbol table.
    """
    # Build up the environment;
    # see https://craftinginterpreters.com/resolving-and-binding.html
    mapping: MutableMapping[Identifier, "TypeAnnotationUnion"] = {
        Identifier("len"): BuiltinFunctionTypeAnnotation(
            func=BuiltinFunction(
                name=Identifier("len"),
                returns=PrimitiveTypeAnnotation(PrimitiveType.LENGTH),
            )
        )
    }

    for verification in symbol_table.verification_functions:
        assert verification.name not in mapping
        mapping[verification.name] = VerificationTypeAnnotation(func=verification)

    for symbol in symbol_table.symbols:
        if isinstance(symbol, _types.Enumeration):
            assert symbol.name not in mapping
            mapping[symbol.name] = EnumerationAsTypeTypeAnnotation(enumeration=symbol)

    return ImmutableEnvironment(mapping=mapping, parent=None)


TypeAnnotationUnion = Union[
    PrimitiveTypeAnnotation,
    OurTypeAnnotation,
    VerificationTypeAnnotation,
    BuiltinFunctionTypeAnnotation,
    MethodTypeAnnotation,
    ListTypeAnnotation,
    OptionalTypeAnnotation,
    EnumerationAsTypeTypeAnnotation,
]
assert_union_of_descendants_exhaustive(
    union=TypeAnnotationUnion, base_class=TypeAnnotation
)

FunctionTypeAnnotationUnion = Union[
    VerificationTypeAnnotation, BuiltinFunctionTypeAnnotation
]
assert_union_of_descendants_exhaustive(
    union=FunctionTypeAnnotationUnion, base_class=FunctionTypeAnnotation
)

# NOTE (mristin, 2021-12-27):
# Mypy is not smart enough to work with ``get_args``, so we have to manually write it
# out.
FunctionTypeAnnotationUnionAsTuple = (
    VerificationTypeAnnotation,
    BuiltinFunctionTypeAnnotation,
)
assert FunctionTypeAnnotationUnionAsTuple == get_args(FunctionTypeAnnotationUnion)
