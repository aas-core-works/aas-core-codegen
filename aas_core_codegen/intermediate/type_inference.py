"""
Infer the types of the tree nodes.

Note that these types roughly follow the type annotations in
:py:mod:`aas_core_codegen.intermediate._types`, but are not identical. For example,
the ``LENGTH`` primitive exists only in type inference. Another example, we do not
track ``parsed`` as the types are inferred in the intermediate stage, but can not
be traced back to the parse stage.
"""

import abc
import ast
import contextlib
import enum
from typing import (
    FrozenSet,
    Mapping,
    MutableMapping,
    Set,
    Optional,
    List,
    Final,
    Sequence,
    Union,
    get_args,
    Tuple,
)

from icontract import DBC, ensure

from aas_core_codegen.common import (
    Identifier,
    Error,
    assert_never,
    assert_union_of_descendants_exhaustive,
    assert_union_without_excluded,
)
from aas_core_codegen.intermediate import _types
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


# NOTE (mristin):
# The types in _types module provide a different set of primitive types,
# so we have to map here.
_PRIMITIVE_TYPES_TO_OUR_PRIMITIVE_TYPES: Final[
    Mapping[_types.PrimitiveType, PrimitiveType]
] = {
    _types.PrimitiveType.BOOL: PrimitiveType.BOOL,
    _types.PrimitiveType.INT: PrimitiveType.INT,
    _types.PrimitiveType.FLOAT: PrimitiveType.FLOAT,
    _types.PrimitiveType.STR: PrimitiveType.STR,
    _types.PrimitiveType.BYTEARRAY: PrimitiveType.BYTEARRAY,
}
assert all(
    literal in _PRIMITIVE_TYPES_TO_OUR_PRIMITIVE_TYPES
    for literal in _types.PrimitiveType
)


class OurTypeAnnotation(AtomicTypeAnnotation):
    """
    Represent an atomic annotation defined by our type in the meta-model.

     For example, ``Asset``.
    """

    def __init__(self, our_type: _types.OurType) -> None:
        """Initialize with the given values."""
        self.our_type = our_type

    def __str__(self) -> str:
        return self.our_type.name


class Downcast:
    """
    Represent a value whose type has been narrowed down by an ``isinstance`` guard.

    The implementation targets need to down-cast such values. The class or
    the named union of the value before the narrowing determines how the value
    is represented, and hence how it needs to be down-cast.
    """

    #: Type of the value before the narrowing, a class or a named union
    source: Final[OurTypeAnnotation]

    #: Class which the value has been narrowed down to
    target: Final[OurTypeAnnotation]

    def __init__(self, source: OurTypeAnnotation, target: OurTypeAnnotation) -> None:
        """Initialize with the given values."""
        self.source = source
        self.target = target

    def __str__(self) -> str:
        return f"{self.source} as {self.target}"


def try_primitive_type(
    type_annotation: "TypeAnnotationUnion",
) -> Optional[PrimitiveType]:
    """
    Try to get the underlying primitive type of the type annotation.

    If it is neither a primitive type annotation nor a constrained primitive,
    return None.
    """
    if isinstance(type_annotation, PrimitiveTypeAnnotation):
        return type_annotation.a_type

    elif isinstance(type_annotation, OurTypeAnnotation) and isinstance(
        type_annotation.our_type, _types.ConstrainedPrimitive
    ):
        return _PRIMITIVE_TYPES_TO_OUR_PRIMITIVE_TYPES[
            type_annotation.our_type.constrainee
        ]
    else:
        return None


class FunctionTypeAnnotation(AtomicTypeAnnotation):
    """Represent a function as a type."""

    @abc.abstractmethod
    def __str__(self) -> str:
        # Signal that this is a purely abstract class
        raise NotImplementedError()


class VerificationTypeAnnotation(FunctionTypeAnnotation):
    """Represent a type of verification function."""

    def __init__(self, func: _types.Verification):
        """Initialize with the given values."""
        self.func = func

    def __str__(self) -> str:
        return self.func.name


@enum.unique
class BuiltinFunctionKind(enum.Enum):
    """
    Enumerate the built-in functions which we understand.

    The value is the name of the function in the meta-model.

    We dispatch on the kind, not on the name, so that mypy can check that
    the dispatch is exhaustive. For example:

    .. code-block:: python

        if func.kind is BuiltinFunctionKind.LEN:
            ...
        elif func.kind is BuiltinFunctionKind.ABS:
            ...
        elif func.kind is BuiltinFunctionKind.INT:
            ...
        elif func.kind is BuiltinFunctionKind.SET:
            ...
        else:
            assert_never(func.kind)
    """

    LEN = "len"
    ABS = "abs"
    INT = "int"
    SET = "set"


class BuiltinFunction:
    """Represent a built-in function."""

    #: Kind of the built-in function, which we dispatch on
    kind: Final[BuiltinFunctionKind]

    #: Name of the built-in function
    name: Final[Identifier]

    #: Type of the returned value.
    #:
    #: If None, the function either returns nothing, or the returned type depends
    #: on the arguments and is inferred at the call site (*e.g.*, ``abs``).
    returns: Final[Optional["TypeAnnotationUnion"]]

    def __init__(
        self, kind: BuiltinFunctionKind, returns: Optional["TypeAnnotationUnion"]
    ):
        """Initialize with the given values."""
        self.kind = kind
        self.name = Identifier(kind.value)
        self.returns = returns


class BuiltinFunctionTypeAnnotation(FunctionTypeAnnotation):
    """Represent a type of built-in function."""

    def __init__(self, func: BuiltinFunction):
        """Initialize with the given values."""
        self.func = func

    def __str__(self) -> str:
        return self.func.name


class BuiltinMethod:
    """
    Represent a built-in method of a primitive type such as ``str.find``.

    Unlike our methods, which the meta-model defines on its classes, the built-in
    methods come with the language of the meta-model, Python, and each target
    needs to transpile them explicitly.
    """

    def __init__(
        self,
        name: Identifier,
        returns: Optional["TypeAnnotationUnion"],
        min_arg_count: int,
        max_arg_count: int,
    ) -> None:
        """
        Initialize with the given values.

        If ``returns`` is None, the returned type depends on the instance, and is
        inferred at the call site (*e.g.*, ``set.intersection``).
        """
        self.name = name
        self.returns = returns
        self.min_arg_count = min_arg_count
        self.max_arg_count = max_arg_count


class BuiltinMethodTypeAnnotation(AtomicTypeAnnotation):
    """Represent a type of built-in method bound to an instance of a primitive."""

    def __init__(self, method: BuiltinMethod) -> None:
        """Initialize with the given values."""
        self.method = method

    def __str__(self) -> str:
        return self.method.name


#: Represent ``str.find(sub)`` and ``str.find(sub, start)``.
#:
#: The result is the position of the first occurrence of ``sub``, or -1 if there
#: is none.
#:
#: The transpiled code follows the Python implementation of ``str.find``, since
#: Python is the language of the meta-model specifications. Hence, the positions
#: count the characters (code points), a negative ``start`` counts from the end
#: of the string, and a ``start`` beyond the end of the string gives -1.
STR_FIND = BuiltinMethod(
    name=Identifier("find"),
    returns=PrimitiveTypeAnnotation(PrimitiveType.INT),
    min_arg_count=1,
    max_arg_count=2,
)


#: Represent ``str.lstrip(chars)``.
#:
#: The result is the string without the longest prefix of the characters listed
#: in ``chars``.
#:
#: The transpiled code follows the Python implementation of ``str.lstrip``, and
#: strips the characters (code points). We do not support ``lstrip`` without
#: an argument, since what counts as a white space differs among the target
#: languages.
STR_LSTRIP = BuiltinMethod(
    name=Identifier("lstrip"),
    returns=PrimitiveTypeAnnotation(PrimitiveType.STR),
    min_arg_count=1,
    max_arg_count=1,
)


#: Map the names of the built-in methods on strings to their definitions
STR_METHODS_BY_NAME: Mapping[Identifier, BuiltinMethod] = {
    STR_FIND.name: STR_FIND,
    STR_LSTRIP.name: STR_LSTRIP,
}


#: Represent ``set.add(item)``.
#:
#: The item has to be assignable to the items of the set, and the set has to be
#: mutable. The call returns nothing, so it can only be a statement on its own.
SET_ADD = BuiltinMethod(
    name=Identifier("add"),
    returns=PrimitiveTypeAnnotation(PrimitiveType.NONE),
    min_arg_count=1,
    max_arg_count=1,
)


#: Represent ``set.intersection(other)``.
#:
#: The result is a new set with the items which are in both sets. The other set
#: has to hold the items of the same type.
SET_INTERSECTION = BuiltinMethod(
    name=Identifier("intersection"),
    returns=None,
    min_arg_count=1,
    max_arg_count=1,
)


#: Represent ``set.difference(other)``.
#:
#: The result is a new set with the items which are not in the other set.
#: The other set has to hold the items of the same type.
SET_DIFFERENCE = BuiltinMethod(
    name=Identifier("difference"),
    returns=None,
    min_arg_count=1,
    max_arg_count=1,
)


#: Map the names of the built-in methods on sets to their definitions
SET_METHODS_BY_NAME: Mapping[Identifier, BuiltinMethod] = {
    SET_ADD.name: SET_ADD,
    SET_INTERSECTION.name: SET_INTERSECTION,
    SET_DIFFERENCE.name: SET_DIFFERENCE,
}


class MethodTypeAnnotation(AtomicTypeAnnotation):
    """Represent a type of class method."""

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


class SetTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a ``Set[...]``."""

    def __init__(self, items: "TypeAnnotationUnion"):
        self.items = items

    def __str__(self) -> str:
        return f"Set[{self.items}]"


class TupleTypeAnnotation(SubscriptedTypeAnnotation):
    """
    Represent a type annotation involving a ``Tuple[...]`` of fixed length.

    Unlike :class:`ListTypeAnnotation`, the items are heterogeneous and their
    number is fixed.
    """

    def __init__(self, items: Sequence["TypeAnnotationUnion"]):
        self.items = items

    def __str__(self) -> str:
        items_joined = ", ".join(str(item) for item in self.items)
        return f"Tuple[{items_joined}]"


class OptionalTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving an ``Optional[...]``."""

    def __init__(self, value: "TypeAnnotationUnion"):
        self.value = value

    def __str__(self) -> str:
        return f"Optional[{self.value}]"


class JsonValueTypeAnnotation(AtomicTypeAnnotation):
    """
    Represent the type of an arbitrary, open JSON-able value.

    Since neither its shape nor any further operation on it can be determined
    statically, we treat it analogous to ``Unknown`` -- no member access,
    indexing or other operation is allowed on a value of this type.
    """

    def __str__(self) -> str:
        return "JSONValue"


class JsonArrayTypeAnnotation(AtomicTypeAnnotation):
    """Represent the type of an open, JSON-able array."""

    def __str__(self) -> str:
        return "JSONArray"


class JsonObjectTypeAnnotation(AtomicTypeAnnotation):
    """
    Represent the type of an open, JSON-object-shaped value.

    The value is always a :class:`JsonValueTypeAnnotation` and can not be
    customized, so we only track the ``key`` here.
    """

    def __init__(self, key: "TypeAnnotationUnion") -> None:
        """Initialize with the given values."""
        self.key = key

    def __str__(self) -> str:
        return f"JSONObject[{self.key}]"


class EnumerationAsTypeTypeAnnotation(TypeAnnotation):
    """
    Represent an enum class as a type.

    Note that this is not the enum as a type of that enum class, but
    rather the type-as-a-type. We write``Type[T]`` in Python to describe this.
    """

    # NOTE (mristin):
    # The name of this class is admittedly clumsy. Please feel free to change if you
    # come up with a better idea.

    def __init__(self, enumeration: _types.Enumeration) -> None:
        """Initialize with the given values."""
        self.enumeration = enumeration

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[{self.enumeration}]"


def beneath_optional(
    type_annotation: "TypeAnnotationUnion",
) -> "TypeAnnotationExceptOptional":
    """Recurse over optionals until we reach a non-optional."""
    while isinstance(type_annotation, OptionalTypeAnnotation):
        type_annotation = type_annotation.value

    return type_annotation


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
            return that.our_type is other.our_type

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

    elif isinstance(that, BuiltinMethodTypeAnnotation):
        if not isinstance(other, BuiltinMethodTypeAnnotation):
            return False
        else:
            return that.method is other.method

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

    elif isinstance(that, SetTypeAnnotation):
        if not isinstance(other, SetTypeAnnotation):
            return False
        else:
            return _type_annotations_equal(that.items, other.items)

    elif isinstance(that, TupleTypeAnnotation):
        if not isinstance(other, TupleTypeAnnotation):
            return False
        else:
            return len(that.items) == len(other.items) and all(
                _type_annotations_equal(that_item, other_item)
                for that_item, other_item in zip(that.items, other.items)
            )

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

    elif isinstance(that, JsonValueTypeAnnotation):
        return isinstance(other, JsonValueTypeAnnotation)

    elif isinstance(that, JsonArrayTypeAnnotation):
        return isinstance(other, JsonArrayTypeAnnotation)

    elif isinstance(that, JsonObjectTypeAnnotation):
        if not isinstance(other, JsonObjectTypeAnnotation):
            return False
        else:
            return _type_annotations_equal(that.key, other.key)

    else:
        assert_never(that)

    raise AssertionError("Should not have gotten here")


PRIMITIVE_TYPE_MAP = {
    _types.PrimitiveType.BOOL: PrimitiveType.BOOL,
    _types.PrimitiveType.INT: PrimitiveType.INT,
    _types.PrimitiveType.FLOAT: PrimitiveType.FLOAT,
    _types.PrimitiveType.STR: PrimitiveType.STR,
    _types.PrimitiveType.BYTEARRAY: PrimitiveType.BYTEARRAY,
}


def _primitive_assignable(
    target_type: PrimitiveType, value_type: PrimitiveType
) -> bool:
    """
    Check whether the primitive value can be assigned to the primitive target.

    A length can be assigned to an integer, as it only widens. The opposite would
    narrow the integer in the targets which represent the lengths with narrower
    types, such as ``int`` in C#, Java and Go.
    """
    return target_type == value_type or (
        target_type is PrimitiveType.INT and value_type is PrimitiveType.LENGTH
    )


def _assignable(
    target_type: "TypeAnnotationUnion", value_type: "TypeAnnotationUnion"
) -> bool:
    """Check whether the value can be assigned to the target."""
    if isinstance(target_type, PrimitiveTypeAnnotation):
        if isinstance(value_type, PrimitiveTypeAnnotation):
            return _primitive_assignable(
                target_type=target_type.a_type, value_type=value_type.a_type
            )

        # NOTE (mristin):
        # We have to be careful about the constrained primitives,
        # since we can always assign a constrained primitive to a primitive, if they
        # primitive types match.
        elif isinstance(value_type, OurTypeAnnotation) and isinstance(
            value_type.our_type, _types.ConstrainedPrimitive
        ):
            return (
                target_type.a_type
                == PRIMITIVE_TYPE_MAP[value_type.our_type.constrainee]
            )

        else:
            return False

    elif isinstance(target_type, OurTypeAnnotation):
        if isinstance(target_type.our_type, _types.Enumeration):
            # NOTE (mristin):
            # The enumerations are invariant.
            return (
                isinstance(value_type, OurTypeAnnotation)
                and isinstance(value_type.our_type, _types.Enumeration)
                and target_type.our_type is value_type.our_type
            )

        elif isinstance(target_type.our_type, _types.ConstrainedPrimitive):
            # NOTE (mristin):
            # If it is a constrained primitive with no constraints, allow the assignment
            # if the target and the value match on the primitive type.
            if len(target_type.our_type.invariants) == 0 and isinstance(
                value_type, PrimitiveTypeAnnotation
            ):
                return _primitive_assignable(
                    target_type=PRIMITIVE_TYPE_MAP[target_type.our_type.constrainee],
                    value_type=value_type.a_type,
                )
            else:
                # NOTE (mristin):
                # We assume the assignments of constrained primitives to be co-variant.
                if (
                    isinstance(value_type, OurTypeAnnotation)
                    and isinstance(value_type.our_type, _types.ConstrainedPrimitive)
                    and target_type.our_type.constrainee
                    == value_type.our_type.constrainee
                ):
                    return (
                        target_type.our_type is value_type.our_type
                        or _types.runtime_id(value_type.our_type)
                        in target_type.our_type.descendant_id_set
                    )

            return False

        elif isinstance(target_type.our_type, _types.Class):
            if not (
                isinstance(value_type, OurTypeAnnotation)
                and isinstance(value_type.our_type, _types.Class)
            ):
                return False

            # NOTE (mristin):
            # We assume the assignment to be co-variant. Either the target type and
            # the value type are equal *or* the value type is a descendant of the
            # target type.

            return target_type.our_type is value_type.our_type or (
                _types.runtime_id(value_type.our_type)
                in target_type.our_type.descendant_id_set
            )

        elif isinstance(target_type.our_type, _types.NamedUnion):
            if not isinstance(value_type, OurTypeAnnotation):
                return False

            # NOTE (mristin):
            # We assume the named unions to be invariant among themselves, as
            # the targets would need to re-wrap the value of one named union into
            # another. On the other hand, an instance of a class can be wrapped
            # into the named union if the class is a root of the union, or
            # a descendant of a root.
            if isinstance(value_type.our_type, _types.NamedUnion):
                return value_type.our_type is target_type.our_type

            if isinstance(value_type.our_type, _types.ClassUnionAsTuple):
                value_cls = value_type.our_type
                return any(
                    value_cls.is_subclass_of(root)
                    for root in target_type.our_type.roots
                )

            return False

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

    elif isinstance(target_type, BuiltinMethodTypeAnnotation):
        if not isinstance(value_type, BuiltinMethodTypeAnnotation):
            return False
        else:
            return target_type.method is value_type.method

    elif isinstance(target_type, MethodTypeAnnotation):
        if not isinstance(value_type, MethodTypeAnnotation):
            return False
        else:
            return target_type.method is value_type.method

    elif isinstance(target_type, ListTypeAnnotation):
        if not isinstance(value_type, ListTypeAnnotation):
            return False
        else:
            # NOTE (mristin):
            # We assume the lists to be invariant. This is necessary for code generation
            # in implementation targets such as C++ and Golang.
            return _type_annotations_equal(target_type.items, value_type.items)

    elif isinstance(target_type, SetTypeAnnotation):
        if not isinstance(value_type, SetTypeAnnotation):
            return False
        else:
            # NOTE (mristin):
            # We assume the sets to be invariant. This is necessary for code generation
            # in implementation targets such as C++ and Golang.
            return _type_annotations_equal(target_type.items, value_type.items)

    elif isinstance(target_type, TupleTypeAnnotation):
        if not isinstance(value_type, TupleTypeAnnotation):
            return False
        else:
            # NOTE (mristin):
            # We assume the tuples to be invariant, analogous to the lists and sets
            # above.
            return len(target_type.items) == len(value_type.items) and all(
                _type_annotations_equal(target_item, value_item)
                for target_item, value_item in zip(target_type.items, value_type.items)
            )

    elif isinstance(target_type, OptionalTypeAnnotation):
        # NOTE (mristin):
        # We can always assign ``None`` to an optional.
        if (
            isinstance(value_type, PrimitiveTypeAnnotation)
            and value_type.a_type is PrimitiveType.NONE
        ):
            return True

        # NOTE (mristin):
        # We can always assign a non-optional to an optional.
        if not isinstance(value_type, OptionalTypeAnnotation):
            return _assignable(target_type=target_type.value, value_type=value_type)
        else:
            # NOTE (mristin):
            # We assume the optionals to be co-variant.
            return _assignable(
                target_type=target_type.value, value_type=value_type.value
            )

    elif isinstance(target_type, JsonValueTypeAnnotation):
        # NOTE (mristin):
        # ``JSONValue`` denotes an arbitrary, open JSON-able value, so any
        # JSON-able value -- a JSON-able primitive or a JSON-able collection --
        # can be assigned to it.
        #
        # We deliberately exclude ``PrimitiveType.INT`` here. JSON itself has
        # no separate integer type, only a single "number" type, which we
        # model as ``PrimitiveType.FLOAT``. Accepting an ``int`` here would be
        # ambiguous -- it is unclear whether it should be rendered as, say,
        # ``1`` or ``1.0`` -- so we require the value to already be a
        # ``float`` (or another JSON-able type) before it can flow into
        # a ``JSONValue``.
        return isinstance(
            value_type,
            (
                JsonValueTypeAnnotation,
                JsonArrayTypeAnnotation,
                JsonObjectTypeAnnotation,
            ),
        ) or (
            isinstance(value_type, PrimitiveTypeAnnotation)
            and value_type.a_type
            in (
                PrimitiveType.BOOL,
                PrimitiveType.FLOAT,
                PrimitiveType.STR,
            )
        )

    elif isinstance(target_type, JsonArrayTypeAnnotation):
        return isinstance(value_type, JsonArrayTypeAnnotation)

    elif isinstance(target_type, JsonObjectTypeAnnotation):
        if not isinstance(value_type, JsonObjectTypeAnnotation):
            return False
        else:
            return _type_annotations_equal(target_type.key, value_type.key)

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


def needs_wrapping_into_named_union(
    target_type: "TypeAnnotationUnion", value_type: "TypeAnnotationUnion"
) -> bool:
    """
    Check whether the value needs to be wrapped into the named union of the target.

    This is the case if we assign an instance of a class to a named union, possibly
    optional, since some targets represent the named unions as wrappers or variants.
    """
    target_type_beneath = beneath_optional(target_type)
    return (
        isinstance(target_type_beneath, OurTypeAnnotation)
        and isinstance(target_type_beneath.our_type, _types.NamedUnion)
        and isinstance(value_type, OurTypeAnnotation)
        and isinstance(value_type.our_type, _types.ClassUnionAsTuple)
    )


for _types_primitive_type in _types.PrimitiveType:
    assert (
        _types_primitive_type in PRIMITIVE_TYPE_MAP
    ), f"All primitive types from _types covered, but: {_types_primitive_type=}"


def convert_type_annotation(
    type_annotation: _types.TypeAnnotationUnion,
) -> "TypeAnnotationUnion":
    """
    Convert from the :py:mod:`aas_core_codegen.intermediate._types`.

    We can not use the same type annotations as type inference uses a wider set of
    type annotations such as ``LENGTH`` in primitives or enumeration-as-type.
    """
    if isinstance(type_annotation, _types.PrimitiveTypeAnnotation):
        return PrimitiveTypeAnnotation(
            a_type=PRIMITIVE_TYPE_MAP[type_annotation.a_type]
        )

    elif isinstance(type_annotation, _types.OurTypeAnnotation):
        return OurTypeAnnotation(our_type=type_annotation.our_type)

    elif isinstance(type_annotation, _types.ListTypeAnnotation):
        return ListTypeAnnotation(items=convert_type_annotation(type_annotation.items))

    elif isinstance(type_annotation, _types.SetTypeAnnotation):
        return SetTypeAnnotation(items=convert_type_annotation(type_annotation.items))

    elif isinstance(type_annotation, _types.TupleTypeAnnotation):
        return TupleTypeAnnotation(
            items=[convert_type_annotation(item) for item in type_annotation.items]
        )

    elif isinstance(type_annotation, _types.OptionalTypeAnnotation):
        return OptionalTypeAnnotation(
            value=convert_type_annotation(type_annotation.value)
        )

    elif isinstance(type_annotation, _types.JsonValueTypeAnnotation):
        return JsonValueTypeAnnotation()

    elif isinstance(type_annotation, _types.JsonArrayTypeAnnotation):
        return JsonArrayTypeAnnotation()

    elif isinstance(type_annotation, _types.JsonObjectTypeAnnotation):
        return JsonObjectTypeAnnotation(
            key=convert_type_annotation(type_annotation.key)
        )

    else:
        assert_never(type_annotation)

    raise AssertionError("Should not have gotten here")


def refusal_of_set_items(items: "TypeAnnotationUnion") -> Optional[str]:
    """
    Explain why the ``items`` can not be the items of a set.

    We support only the sets of booleans, integers, strings, the constrained
    primitives of them, and the enumeration literals.

    :return: the explanation, or None if the ``items`` are supported
    """
    a_type = try_primitive_type(items)

    if a_type is PrimitiveType.FLOAT:
        return (
            f"We do not support the sets of floating-point numbers, "
            f"but got the items of type {items}. The targets disagree on "
            f"the equality of floating-point numbers in a set: Python finds "
            f"a NaN only if it is the very same object, C++ and Go never find "
            f"a NaN, while C#, Java and TypeScript always do. Moreover, Java "
            f"tells 0.0 and -0.0 apart, while the other targets do not."
        )

    if a_type is PrimitiveType.BYTEARRAY:
        return (
            f"We do not support the sets of byte arrays, but got the items "
            f"of type {items}. A bytearray is mutable and hence unhashable in "
            f"Python, so ``set().add(bytearray(...))`` raises a ``TypeError``."
        )

    if a_type is not None:
        return None

    if isinstance(items, OurTypeAnnotation):
        if isinstance(items.our_type, _types.Enumeration):
            return None

        return (
            f"We support only the sets of primitive values and enumeration "
            f"literals, but got the items of type {items}, which is "
            f"a {'named union' if isinstance(items.our_type, _types.NamedUnion) else 'class'}. "
            f"Please contact the developers if you need the sets of instances."
        )

    if isinstance(items, OptionalTypeAnnotation):
        return (
            f"We do not support None as an item of a set, but got the items "
            f"of type {items}. Some targets can not hold a null item in a set, "
            f"*e.g.*, a string key of a map in Go can not be nil. If the whole "
            f"set is optional, please declare it as ``Optional[Set[...]]``."
        )

    if isinstance(items, (ListTypeAnnotation, SetTypeAnnotation)):
        return (
            f"We do not support the sets of lists or sets, but got the items "
            f"of type {items}. The lists and the sets are mutable and hence "
            f"unhashable in Python, so they can not be items of a set."
        )

    if isinstance(items, TupleTypeAnnotation):
        return (
            f"We do not support the sets of tuples, but got the items "
            f"of type {items}. Only some of the targets can hash a tuple "
            f"out of the box. Please contact the developers if you need "
            f"this feature."
        )

    if isinstance(
        items,
        (JsonValueTypeAnnotation, JsonArrayTypeAnnotation, JsonObjectTypeAnnotation),
    ):
        return (
            f"We do not support the sets of JSON-able values, but got the items "
            f"of type {items}. The JSON-able arrays and objects are mutable and "
            f"hence unhashable in Python, so they can not be items of a set."
        )

    return (
        f"We support only the sets of booleans, integers, strings, "
        f"the constrained primitives of them, and the enumeration literals, "
        f"but got the items of type {items}."
    )


class Environment(DBC):
    """
    Map names to type annotations for a given scope.

    We first search in the given scope and then iterate over the ancestor scopes.
    See, for example: https://craftinginterpreters.com/resolving-and-binding.html.

    The most outer, global, scope is parentless.
    """

    def __init__(self, parent: Optional["Environment"]) -> None:
        """Initialize with the given values."""
        self.parent = parent

    @property
    @abc.abstractmethod
    def mapping(self) -> Mapping[Identifier, "TypeAnnotationUnion"]:
        """Retrieve the underlying mapping."""
        raise NotImplementedError()

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

    def find_our_type(self, identifier: Identifier) -> Optional[_types.OurType]:
        """
        Search for our type with the given ``identifier``.

        Unlike :py:meth:`find`, this method resolves the names which refer to our
        types, and not to values. For example, we need to resolve the classes
        in ``isinstance(something, Some_class)``.

        We search all the way to the most outer scope.
        """
        if self.parent is not None:
            return self.parent.find_our_type(identifier)

        return None


class ImmutableEnvironment(Environment):
    """
    Map immutably names to type annotations for a given scope.

    Optionally, the environment also resolves the names of our types. This is
    usually the case only for the most outer, global scope.
    """

    def __init__(
        self,
        mapping: Mapping[Identifier, "TypeAnnotationUnion"],
        parent: Optional["Environment"] = None,
        our_types_by_name: Optional[Mapping[Identifier, _types.OurType]] = None,
    ) -> None:
        self._mapping = mapping
        self._our_types_by_name = our_types_by_name

        Environment.__init__(self, parent)

    @property
    def mapping(self) -> Mapping[Identifier, "TypeAnnotationUnion"]:
        """Retrieve the underlying mapping."""
        return self._mapping

    def find_our_type(self, identifier: Identifier) -> Optional[_types.OurType]:
        if self._our_types_by_name is not None:
            our_type = self._our_types_by_name.get(identifier, None)
            if our_type is not None:
                return our_type

        return Environment.find_our_type(self, identifier)


class MutableEnvironment(Environment):
    """
    Map names to type annotations for a given scope and allow mutations.
    """

    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self._mapping = (
            dict()
        )  # type: MutableMapping[Identifier, "TypeAnnotationUnion"]

        Environment.__init__(self, parent)

    @property
    def mapping(self) -> Mapping[Identifier, "TypeAnnotationUnion"]:
        """Retrieve the underlying mapping."""
        return self._mapping

    def set(
        self, identifier: Identifier, type_annotation: "TypeAnnotationUnion"
    ) -> None:
        """Set the ``type_annotation`` for the given ``identifier``."""
        self._mapping[identifier] = type_annotation

    def remove(self, identifier: Identifier) -> None:
        """
        Remove the entry in the environment for the ``identifier``.

        For example, you need to do this if you have temporary scopes such as generator
        expressions where a long linked list of environments would be neither
        performant nor readable during the debugging.
        """
        del self._mapping[identifier]


class _Canonicalizer(parse_tree.RestrictedTransformer[str]):
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

        While we could always put brackets, they harm readability in later debugging, so
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
                parse_tree.Tuple,
            ),
        )

    def transform_member(self, node: parse_tree.Member) -> str:
        instance_repr = self.transform(node.instance)

        if _Canonicalizer._needs_no_brackets(node.instance):
            result = f"{instance_repr}.{node.name}"
        else:
            result = f"({instance_repr}).{node.name}"

        self.representation_map[node] = result
        return result

    @staticmethod
    def index_representation(
        collection: parse_tree.Node, collection_repr: str, index_repr: str
    ) -> str:
        """
        Render the canonical representation of ``collection[index]``.

        This is a static method so that the callers which know the parts of an index,
        but have no index node at hand, can render exactly the same representation.
        """
        if _Canonicalizer._needs_no_brackets(collection):
            return f"{collection_repr}[{index_repr}]"

        return f"({collection_repr})[{index_repr}]"

    def transform_index(self, node: parse_tree.Index) -> str:
        collection_repr = self.transform(node.collection)
        index_repr = self.transform(node.index)

        result = _Canonicalizer.index_representation(
            collection=node.collection,
            collection_repr=collection_repr,
            index_repr=index_repr,
        )

        self.representation_map[node] = result
        return result

    def transform_slice(self, node: parse_tree.Slice) -> str:
        collection_repr = self.transform(node.collection)
        if not _Canonicalizer._needs_no_brackets(node.collection):
            collection_repr = f"({collection_repr})"

        start_repr = self.transform(node.start) if node.start is not None else ""
        end_repr = self.transform(node.end) if node.end is not None else ""

        result = f"{collection_repr}[{start_repr}:{end_repr}]"
        self.representation_map[node] = result
        return result

    def transform_comparison(self, node: parse_tree.Comparison) -> str:
        left = self.transform(node.left)
        if not _Canonicalizer._needs_no_brackets(node.left):
            left = f"({left})"

        right = self.transform(node.right)
        if not _Canonicalizer._needs_no_brackets(node.right):
            right = f"({right})"

        result = f"{left} {node.op.value} {right}"
        self.representation_map[node] = result
        return result

    def transform_is_in(self, node: parse_tree.IsIn) -> str:
        member = self.transform(node.member)
        if not _Canonicalizer._needs_no_brackets(node.member):
            member = f"({member})"

        container = self.transform(node.container)
        if not _Canonicalizer._needs_no_brackets(node.container):
            container = f"({container})"

        result = f"{member} in {container}"
        self.representation_map[node] = result
        return result

    def transform_is_instance(self, node: parse_tree.IsInstance) -> str:
        value = self.transform(node.value)

        classes = [self.transform(cls) for cls in node.classes]

        if len(classes) == 1:
            result = f"isinstance({value}, {classes[0]})"
        else:
            classes_joined = ", ".join(classes)
            result = f"isinstance({value}, ({classes_joined}))"

        self.representation_map[node] = result
        return result

    def transform_implication(self, node: parse_tree.Implication) -> str:
        antecedent = self.transform(node.antecedent)
        if not _Canonicalizer._needs_no_brackets(node.antecedent):
            antecedent = f"({antecedent})"

        consequent = self.transform(node.consequent)
        if not _Canonicalizer._needs_no_brackets(node.consequent):
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

    def transform_tuple(self, node: parse_tree.Tuple) -> str:
        values = [self.transform(value) for value in node.values]

        values_joined = ", ".join(values)
        if len(values) == 1:
            result = f"({values_joined},)"
        else:
            result = f"({values_joined})"

        self.representation_map[node] = result
        return result

    def transform_is_none(self, node: parse_tree.IsNone) -> str:
        value = self.transform(node.value)
        if not _Canonicalizer._needs_no_brackets(node.value):
            value = f"({value})"

        result = f"{value} is None"
        self.representation_map[node] = result
        return result

    def transform_is_not_none(self, node: parse_tree.IsNotNone) -> str:
        value = self.transform(node.value)
        if not _Canonicalizer._needs_no_brackets(node.value):
            value = f"({value})"

        result = f"{value} is not None"
        self.representation_map[node] = result
        return result

    def transform_name(self, node: parse_tree.Name) -> str:
        result = node.identifier
        self.representation_map[node] = result
        return result

    def transform_not(self, node: parse_tree.Not) -> str:
        operand_repr = self.transform(node.operand)

        if not _Canonicalizer._needs_no_brackets(node):
            operand_repr = f"({operand_repr})"

        result = f"not {operand_repr}"
        self.representation_map[node] = result
        return result

    def transform_and(self, node: parse_tree.And) -> str:
        values = []  # type: List[str]

        for value_node in node.values:
            value = self.transform(value_node)
            if not _Canonicalizer._needs_no_brackets(value_node):
                value = f"({value})"

            values.append(value)

        result = " and ".join(values)
        self.representation_map[node] = result
        return result

    def transform_or(self, node: parse_tree.Or) -> str:
        values = []  # type: List[str]
        for value_node in node.values:
            value = self.transform(value_node)
            if not _Canonicalizer._needs_no_brackets(value_node):
                value = f"({value})"

            values.append(value)

        result = " or ".join(values)
        self.representation_map[node] = result
        return result

    def _transform_binary_arithmetic(
        self, node: Union[parse_tree.Add, parse_tree.Sub, parse_tree.Mod]
    ) -> str:
        left_repr = self.transform(node.left)
        if not _Canonicalizer._needs_no_brackets(node.left):
            left_repr = f"({left_repr})"

        right_repr = self.transform(node.right)
        if not _Canonicalizer._needs_no_brackets(node.right):
            right_repr = f"({right_repr})"

        result: str
        if isinstance(node, parse_tree.Add):
            result = f"{left_repr} + {right_repr}"
        elif isinstance(node, parse_tree.Sub):
            result = f"{left_repr} - {right_repr}"
        elif isinstance(node, parse_tree.Mod):
            result = f"{left_repr} % {right_repr}"
        else:
            assert_never(node)

        self.representation_map[node] = result
        return result

    def transform_add(self, node: parse_tree.Add) -> str:
        return self._transform_binary_arithmetic(node)

    def transform_sub(self, node: parse_tree.Sub) -> str:
        return self._transform_binary_arithmetic(node)

    def transform_mod(self, node: parse_tree.Mod) -> str:
        return self._transform_binary_arithmetic(node)

    def transform_neg(self, node: parse_tree.Neg) -> str:
        operand_repr = self.transform(node.operand)

        # NOTE (mristin):
        # We put a negative constant in brackets as well so that we render
        # ``-(-1)`` instead of the confusing ``--1``.
        if not _Canonicalizer._needs_no_brackets(node.operand) or (
            isinstance(node.operand, parse_tree.Constant)
            and isinstance(node.operand.value, (int, float))
            and node.operand.value < 0
        ):
            operand_repr = f"({operand_repr})"

        result = f"-{operand_repr}"
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
        if not _Canonicalizer._needs_no_brackets(node.iteration):
            iteration = f"({iteration})"

        result = f"for {variable} in {iteration}"
        self.representation_map[node] = result
        return result

    def transform_for_range(self, node: parse_tree.ForRange) -> str:
        variable = self.transform(node.variable)
        start = self.transform(node.start)
        end = self.transform(node.end)

        result = f"for {variable} in range({start}, {end})"
        self.representation_map[node] = result
        return result

    def _transform_any_or_all(self, node: Union[parse_tree.Any, parse_tree.All]) -> str:
        generator = self.transform(node.generator)

        condition = self.transform(node.condition)
        if not _Canonicalizer._needs_no_brackets(node.condition):
            condition = f"({condition})"

        result: str

        if isinstance(node, parse_tree.Any):
            result = f"any({condition} {generator})"
        elif isinstance(node, parse_tree.All):
            result = f"all({condition} {generator})"
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
        if not _Canonicalizer._needs_no_brackets(node.target):
            target = f"({target})"

        # NOTE (mristin):
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

            # NOTE (mristin):
            # Nested returns are not possible in Python, but who knows where our
            # intermediate representation will take us. Therefore, we handle
            # this edge case even though it seems nonsensical at the moment.
            if isinstance(node.value, parse_tree.Return):
                value = f"({value})"

            result = f"return {value}"
        else:
            result = "return"

        self.representation_map[node] = result
        return result

    def transform_switch(self, node: parse_tree.Switch) -> str:
        parts = [f"switch {self.transform(node.subject)}:"]  # type: List[str]

        for case in node.cases:
            labels = ", ".join(self.transform(label) for label in case.labels)
            stmts = "; ".join(self.transform(stmt) for stmt in case.body)
            parts.append(f"case {labels}: {{{stmts}}}")

        if node.default is not None:
            stmts = "; ".join(self.transform(stmt) for stmt in node.default)
            parts.append(f"default: {{{stmts}}}")

        result = " ".join(parts)

        self.representation_map[node] = result
        return result

    def transform_for(self, node: parse_tree.For) -> str:
        generator = self.transform(node.generator)
        stmts = "; ".join(self.transform(stmt) for stmt in node.body)

        result = f"{generator}: {{{stmts}}}"

        self.representation_map[node] = result
        return result

    def transform_continue(self, node: parse_tree.Continue) -> str:
        result = "continue"

        self.representation_map[node] = result
        return result

    def transform_break(self, node: parse_tree.Break) -> str:
        result = "break"

        self.representation_map[node] = result
        return result

    def transform_if(self, node: parse_tree.If) -> str:
        parts = []  # type: List[str]

        for i, branch in enumerate(node.branches):
            keyword = "if" if i == 0 else "elif"
            condition = self.transform(branch.condition)
            stmts = "; ".join(self.transform(stmt) for stmt in branch.body)
            parts.append(f"{keyword} {condition}: {{{stmts}}}")

        if node.default is not None:
            stmts = "; ".join(self.transform(stmt) for stmt in node.default)
            parts.append(f"else: {{{stmts}}}")

        result = " ".join(parts)

        self.representation_map[node] = result
        return result

    def transform_expression_statement(
        self, node: parse_tree.ExpressionStatement
    ) -> str:
        result = self.transform(node.expression)

        self.representation_map[node] = result
        return result


#: Map a comparator to the comparator which says the same about the flipped operands
_FLIPPED_COMPARATOR = {
    parse_tree.Comparator.LT: parse_tree.Comparator.GT,
    parse_tree.Comparator.LE: parse_tree.Comparator.GE,
    parse_tree.Comparator.GT: parse_tree.Comparator.LT,
    parse_tree.Comparator.GE: parse_tree.Comparator.LE,
    parse_tree.Comparator.EQ: parse_tree.Comparator.EQ,
    parse_tree.Comparator.NE: parse_tree.Comparator.NE,
}  # type: Mapping[parse_tree.Comparator, parse_tree.Comparator]


def _is_int_literal(node: parse_tree.Node) -> bool:
    """Check whether the ``node`` is a literal integer."""
    return (
        isinstance(node, parse_tree.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _combines_to_length(
    left: parse_tree.Node,
    left_a_type: Optional[PrimitiveType],
    right: parse_tree.Node,
    right_a_type: Optional[PrimitiveType],
) -> bool:
    """
    Check whether the integer operands combine to a length.

    The lengths are represented with narrower types than the integers in some
    targets, *e.g.*, ``int`` in C#, Java and Go, while the integers are 64-bit.
    Hence, we keep the result a length only if at least one operand is a length and
    the other one is a length or an integer literal, *e.g.*, ``len(xs) - 1``.
    Otherwise, the length is widened to an integer, and the result is an integer,
    so that we narrow only where the targets require it, *e.g.*, at an index.
    """
    return (
        left_a_type is PrimitiveType.LENGTH or right_a_type is PrimitiveType.LENGTH
    ) and all(
        a_type is PrimitiveType.LENGTH or _is_int_literal(operand)
        for operand, a_type in ((left, left_a_type), (right, right_a_type))
    )


# region Facts for the narrowing

# NOTE (mristin):
# This region implements the narrowing of the types, *i.e.*, it keeps track of what
# we know about the values beyond their declared types at every point of the code.
# Please read the docstring of :py:class:`_Fact` first. It explains the whole model,
# while the functions and the classes below only document their own part.


class _NonNull:
    """
    Tell that the value is not ``None``.

    For example, ``x is not None`` tells us this about ``x``.
    """


class _MinLength:
    """
    Tell that the JSON-able array has at least :attr:`length` items.

    For example, ``len(self.values) > 1`` tells us that ``self.values`` has at least
    two items, so that ``self.values[0]``, ``self.values[1]``, ``self.values[-1]``
    and ``self.values[-2]`` are all there.
    """

    def __init__(self, length: int) -> None:
        """Initialize with the given values."""
        self.length = length


class _Narrowing:
    """
    Tell that the value is an instance of :attr:`target`.

    For example, ``isinstance(x, Child_a)`` tells us that ``x`` is an instance of
    ``Child_a``, though its declared type is ``Parent``.
    """

    def __init__(self, target: "OurTypeAnnotation") -> None:
        """Initialize with the given values."""
        self.target = target


class _IndexSegment:
    """
    Represent an index in an access path.

    For example, the access path ``items[i].x`` consists of the segments ``items``,
    ``[i]`` and ``x``, where ``[i]`` is an index segment.

    The :attr:`literal` holds the literal index, such as ``0``, ``-1`` or ``"key"``.
    It is ``None`` if the index is not a literal, *e.g.*, ``[i]``, and we then have to
    assume that the index can denote any item, see :py:func:`_segments_may_alias`.
    """

    def __init__(self, literal: Optional[Union[int, str]]) -> None:
        """Initialize with the given values."""
        self.literal = literal


#: Segment of an access path: a variable (at the start), a member or an index
_PathSegment = Union[Identifier, _IndexSegment]


class _Fact:
    """
    Represent what we know about the value of an expression at a point of the code.

    **Why we need the facts.** The meta-model is written in Python, where
    the narrowing is implicit. The targets are statically typed, and they need to
    know where a value is non-null, and to which class a value has been narrowed,
    so that they can de-reference and down-cast it. They read this from
    :py:attr:`_Inferrer.type_map` and :py:attr:`_Inferrer.downcast_map`.
    Consider the following verification function in the meta-model:

    .. code-block:: python

        @verification
        def narrowing_after_early_return(parent: Optional[Parent]) -> bool:
            # Passes: ``parent is None`` accepts an optional value, and
            # ``isinstance`` sees ``parent`` as non-null in the remainder of
            # the disjunction.
            if parent is None or not isinstance(parent, Child_b):
                return True

            # Passes: ``parent`` is a non-null ``Child_b`` here, since the only
            # branch returns. Without the facts, this would fail with
            # "The member 'b_only' could not be found in the class 'Parent'".
            return parent.b_only < 50

    For example, we generate the following C++ code, which de-references
    the ``std::optional`` and down-casts the pointer based on the facts:

    .. code-block:: cpp

        if (
          (
            (!(parent.has_value()))
            || (!types::IsChildB(*(*parent)))
          )
        ) {
          return true;
        }
        return (
          std::dynamic_pointer_cast<types::IChildB>(*parent)->b_only() < 50
        );

    Analogously, we generate ``((Aas.IChildB)parent).BOnly < 50`` in C#,
    ``parent.(aastypes.IChildB).BOnly() < 50`` in Go and
    ``((IChildB) parent.get()).getBOnly() < 50`` in Java.

    **What a fact is.** A fact tells :attr:`what` we know about the value of
    the expression identified by its canonical representation, :attr:`key`
    (see :py:class:`_Canonicalizer`). The keys are textual, so that the two
    occurrences of ``self.parent`` in ``self.parent is not None and
    self.parent.x > 0`` share the facts. We know three kinds of facts:
    :py:class:`_NonNull`, :py:class:`_MinLength` and :py:class:`_Narrowing`.

    **Where the facts come from.** The facts come from three sources:

    1. *The guards in the expressions* hold only for the remainder of
       the expression. For example, ``x`` is non-null in the second value of
       ``x is not None and len(x) > 0``, and in the second value of
       ``x is None or len(x) > 0``, but not after the expression.
       See :py:meth:`_Inferrer.transform_and`, :py:meth:`_Inferrer.transform_or`
       and :py:meth:`_Inferrer.transform_implication`.

    2. *The conditions of the if-statements* hold in their branches, and their
       negations hold in the subsequent branches and, possibly, after
       the if-statement. See :py:meth:`_Inferrer.transform_if`.

    3. *The assignments* tell us about the assigned value. For example,
       ``text = "default"`` tells us that ``text`` is non-null even though it has
       been defined as ``Optional[str]``. See
       :py:meth:`_Inferrer.transform_assignment`.

    **How the facts flow through the statements.** The following annotated example
    shows all the rules at once:

    .. code-block:: python

        @verification
        def some_func(
            x: Optional[Parent], y: Optional[Parent], flag: bool
        ) -> bool:
            if x is None:
                # Fails: x is None here, "Expected an instance type to be
                # a non-None, ..., but inferred an Optional: Optional[Parent]".
                return x.optional_text is None
            elif flag:
                # Facts: x is non-null, by the negation of ``x is None``.
                # Passes.
                return x.optional_text is None
            else:
                # Facts: x is non-null, by the negation of ``x is None``;
                # nothing about ``flag``, as we do not track booleans.
                x = y
                # Facts: none, the assignment removed "x is non-null",
                # and ``y`` is optional.

            # Facts: none. The ``if`` and the ``elif`` return, so they do not
            # count. The ``else`` ends without ``x`` being non-null.
            # Fails: x is optional here.
            return x.optional_text is None

    * A statement sees the facts left by the previous statement of the block.
    * The branch ``i`` of an if-statement sees the facts before the if-statement,
      the negations of the conditions ``0, …, i - 1``, and its own condition.
      The ``else`` sees the negations of all the conditions. A branch never sees
      the effects of its siblings, since only one branch executes. Hence, we reset
      the facts at the start of each branch.
    * After an if-statement or a switch, we keep only the facts which hold at
      the end of *every* branch which can complete normally. The branches which
      end in ``return``, ``continue`` or ``break`` never reach the code after
      the if-statement, so they do not count. An absent ``else`` counts as
      a branch which completes normally with the negations of all
      the conditions. This is how we narrow after the early exits:

      .. code-block:: python

          if x is None or not isinstance(x, Child_a):
              return False

          # The only branch returns, so only the absent ``else`` counts.
          # Facts: x is non-null and an instance of Child_a,
          # by De Morgan: not (a or b) == (not a) and (not b).
          # Passes.
          return x.a_only > 0

      Analogously, only the ``if`` counts in ``if c: pass else: return False``, so
      ``c`` holds after the if-statement. See :py:meth:`_Inferrer._join`.
    * The body of a for-loop can execute zero or more times. Before the body, we
      remove all the facts which any assignment in the body could invalidate,
      since the next iteration sees the effects of the previous one. After
      the loop, we are back to the facts before the body, since the body might
      not have executed at all. See :py:meth:`_Inferrer.transform_for`.
    * The facts about the variables of a block are removed when we leave
      the block, since a sibling block can define a different variable of
      the same name. See :py:meth:`_Inferrer._transform_in_new_scope`.

    **How the assignments invalidate the facts.** An assignment removes all
    the facts which it can falsify. To that end, a fact records the :attr:`path`
    and the :attr:`names` which its value depends on, see :py:func:`_dependencies`
    and :py:func:`_invalidates`:

    ========================= ====================== ==============================
    Fact about                Assignment             Result
    ========================= ====================== ==============================
    ``self.x``                ``self.y = 5``         kept, a different property
    ``self.x``                ``self.x = z``         removed, the same path
    ``self.x.y``              ``self.x = z``         removed, ``self.x`` is a prefix
    ``items[i]``              ``items[j] = z``       removed, ``i`` might equal ``j``
    ``items[0]``              ``items[1] = z``       kept, distinct literal indices
    ``items[i]``              ``i = i + 1``          removed, the index changed
    ``items[j]``              ``i = i + 1``          kept, ``j`` did not change
    ``self.items``            ``self.items[0] = z``  kept, the list is the same one
    ========================= ====================== ==============================

    The assignment then adds the facts about the assigned value, see
    :py:meth:`_Inferrer.transform_assignment`.

    **What we do not catch.** Similar to mypy, we are lax about the aliasing and
    the calls. The following code is accepted, though it fails at run-time:

    .. code-block:: python

        if holder.parent is None:
            return False

        # We do not know that ``alias`` and ``holder`` are the same instance.
        alias = holder
        alias.parent = other_optional_parent
        # A method might also set ``holder.parent`` to ``None`` behind our back.
        holder.reset()

        # Passes, though ``holder.parent`` might be ``None`` at run-time.
        return holder.parent.optional_text is None
    """

    #: Canonical representation of the expression, see :py:class:`_Canonicalizer`
    key: Final[str]

    #: What we know about the value of the expression
    what: Final[Union[_NonNull, _MinLength, _Narrowing]]

    #: Access path of the expression, *e.g.*, ``self``, ``items``, ``[]`` and ``x``
    #: for ``self.items[i].x``, or ``None`` if the expression is not an access path,
    #: *e.g.*, ``self.f().x``
    path: Final[Optional[Sequence[_PathSegment]]]

    #: Variables used in the indices of the access path, *e.g.*, ``i`` for
    #: ``self.items[i].x``, or all the variables of the expression if it is not
    #: an access path, *e.g.*, ``self`` for ``self.f().x``
    names: Final[FrozenSet[Identifier]]

    def __init__(
        self,
        key: str,
        what: Union[_NonNull, _MinLength, _Narrowing],
        path: Optional[Sequence[_PathSegment]],
        names: FrozenSet[Identifier],
    ) -> None:
        """Initialize with the given values."""
        self.key = key
        self.what = what
        self.path = path
        self.names = names


def _names_in(node: parse_tree.Node) -> Set[Identifier]:
    """
    Collect the identifiers of all the names in the ``node``.

    For example, we collect ``i`` and ``offset`` from ``i + offset``.
    """
    return {
        some_node.identifier
        for some_node in parse_tree.over_nodes(node)
        if isinstance(some_node, parse_tree.Name)
    }


def _index_segment(index: parse_tree.Node) -> _IndexSegment:
    """
    Represent the ``index`` as a segment of an access path.

    For example, we represent ``0`` as ``_IndexSegment(literal=0)``, ``"key"`` as
    ``_IndexSegment(literal="key")``, and ``i`` or ``i + 1`` as
    ``_IndexSegment(literal=None)``.
    """
    if (
        isinstance(index, parse_tree.Constant)
        and isinstance(index.value, (int, str))
        and not isinstance(index.value, bool)
    ):
        return _IndexSegment(literal=index.value)

    return _IndexSegment(literal=None)


def _dependencies(
    node: parse_tree.Node,
) -> Tuple[Optional[List[_PathSegment]], Set[Identifier]]:
    """
    Determine the access path of the ``node`` and the variables its value depends on.

    An access path is a chain of members and indices on a variable. If the ``node``
    is an access path, we return its segments together with the variables used in
    its indices. For example:

    * ``x`` gives the path ``x`` and no variables,
    * ``self.items[i].x`` gives the path ``self``, ``items``, ``[i]``, ``x`` and
      the variable ``i``, and
    * ``self.items[0]`` gives the path ``self``, ``items``, ``[0]`` and no
      variables.

    Otherwise, we return ``None`` together with all the variables of the ``node``.
    For example, ``self.f(i).x`` gives ``None`` and the variables ``self`` and
    ``i``, see :py:func:`_invalidates` for how we handle such facts.
    """
    reversed_path = []  # type: List[_PathSegment]
    names = set()  # type: Set[Identifier]

    cursor = node
    while True:
        if isinstance(cursor, parse_tree.Member):
            reversed_path.append(cursor.name)
            cursor = cursor.instance

        elif isinstance(cursor, parse_tree.Index):
            reversed_path.append(_index_segment(cursor.index))
            names.update(_names_in(cursor.index))
            cursor = cursor.collection

        elif isinstance(cursor, parse_tree.Name):
            reversed_path.append(cursor.identifier)
            reversed_path.reverse()
            return reversed_path, names

        else:
            return None, _names_in(node)


def _segments_may_alias(that: _PathSegment, other: _PathSegment) -> bool:
    """
    Check whether the two segments of access paths may denote the same thing.

    Two variables or two members alias only if they have the same name.
    A variable or a member never aliases an index. Two indices alias unless we can
    tell from their literals that they denote different items:

    * ``[i]`` and ``[0]`` might alias, as ``i`` might be ``0``,
    * ``[0]`` and ``[1]`` do not alias,
    * ``[0]`` and ``[-1]`` might alias, as they denote the same item of a list with
      a single item, and
    * ``["a"]`` and ``["b"]`` do not alias.
    """
    if isinstance(that, _IndexSegment) and isinstance(other, _IndexSegment):
        if that.literal is None or other.literal is None:
            return True

        if isinstance(that.literal, int) and isinstance(other.literal, int):
            return that.literal == other.literal or (
                (that.literal < 0) != (other.literal < 0)
            )

        return that.literal == other.literal

    if isinstance(that, _IndexSegment) or isinstance(other, _IndexSegment):
        return False

    return that == other


def _invalidates(target_path: Optional[Sequence[_PathSegment]], fact: _Fact) -> bool:
    """
    Check whether an assignment to the ``target_path`` invalidates the ``fact``.

    The ``target_path`` is the access path of the target of the assignment, see
    :py:func:`_dependencies`, or ``None`` if the target is not an access path, in
    which case we conservatively invalidate all the facts.

    The assignment invalidates the fact in the following cases:

    * The target is a prefix of the path of the fact, where the indices might
      alias, see :py:func:`_segments_may_alias`. For example, ``self.x = z``
      invalidates the facts about ``self.x`` and ``self.x.y``, and
      ``items[j] = z`` invalidates the facts about ``items[i]`` and
      ``items[0].x``. However, ``self.y = z`` keeps the facts about ``self.x``,
      and ``items[0] = z`` keeps the facts about ``items`` itself, such as its
      length.

    * The target is a variable used in an index of the fact. For example,
      ``i = i + 1`` invalidates the facts about ``items[i]``, but keeps the facts
      about ``items[j]``.

    * The fact is not about an access path, and the target modifies one of its
      variables. For example, both ``self = z`` and ``self.y = z`` invalidate
      the facts about ``self.f().x``, since we do not know what ``self.f()``
      depends on.

    We are lax, and ignore the aliasing through other variables and the calls,
    as documented in :py:class:`_Fact`.
    """
    if target_path is None:
        return True

    if fact.path is not None and len(target_path) <= len(fact.path):
        if all(
            _segments_may_alias(that, other)
            for that, other in zip(target_path, fact.path)
        ):
            return True

    root = target_path[0]
    assert isinstance(root, str)

    return root in fact.names and (len(target_path) == 1 or fact.path is None)


def _same_facts(that: _Fact, other: _Fact) -> bool:
    """
    Check whether the two facts tell the same about the same expression.

    We compare the facts by value, since the same knowledge can come from
    different sources in different branches, and we need to recognize it when
    we join the branches, see :py:meth:`_Inferrer._join`. For example, ``text`` is
    non-null at the end of both branches below, once by the assignment and once by
    the negation of the condition:

    .. code-block:: python

        text = parent.optional_text
        if text is None:
            text = "default"
            # Facts: text is non-null, by the assignment.

        # Facts at the end of the absent else: text is non-null, by the negation.
        # Hence, text is non-null after the if-statement.
        # Passes.
        return len(text) < 10
    """
    if that.key != other.key:
        return False

    if isinstance(that.what, _NonNull):
        return isinstance(other.what, _NonNull)

    if isinstance(that.what, _MinLength):
        return (
            isinstance(other.what, _MinLength) and that.what.length == other.what.length
        )

    if isinstance(that.what, _Narrowing):
        return (
            isinstance(other.what, _Narrowing)
            and that.what.target.our_type is other.what.target.our_type
        )

    assert_never(that.what)


# endregion Facts for the narrowing


TypeAnnotationUnion = Union[
    PrimitiveTypeAnnotation,
    OurTypeAnnotation,
    VerificationTypeAnnotation,
    BuiltinFunctionTypeAnnotation,
    BuiltinMethodTypeAnnotation,
    MethodTypeAnnotation,
    ListTypeAnnotation,
    SetTypeAnnotation,
    TupleTypeAnnotation,
    OptionalTypeAnnotation,
    EnumerationAsTypeTypeAnnotation,
    JsonValueTypeAnnotation,
    JsonArrayTypeAnnotation,
    JsonObjectTypeAnnotation,
]


def is_final_annotation(annotation: parse_tree.Expression) -> bool:
    """Check that ``annotation`` declares a variable as ``Final[...]``."""
    return (
        isinstance(annotation, parse_tree.Index)
        and isinstance(annotation.collection, parse_tree.Name)
        and annotation.collection.identifier == "Final"
    )


def _can_be_mutated(type_annotation: "TypeAnnotationUnion") -> bool:
    """
    Check whether a value of ``type_annotation`` can be mutated in place.

    Only the lists, the sets and the instances of the classes can be mutated,
    possibly reached through a tuple. The primitive values and the enumerations are
    immutable, and we do not support mutating the JSON-able values.
    """
    type_anno = beneath_optional(type_annotation)

    if isinstance(type_anno, (ListTypeAnnotation, SetTypeAnnotation)):
        return True

    if isinstance(type_anno, OurTypeAnnotation):
        return isinstance(type_anno.our_type, _types.Class)

    if isinstance(type_anno, TupleTypeAnnotation):
        return any(_can_be_mutated(item) for item in type_anno.items)

    return False


def _holds_list(type_annotation: "TypeAnnotationUnion") -> bool:
    """Check whether a value of ``type_annotation`` is or contains a list."""
    type_anno = beneath_optional(type_annotation)

    if isinstance(type_anno, ListTypeAnnotation):
        return True

    if isinstance(type_anno, TupleTypeAnnotation):
        return any(_holds_list(item) for item in type_anno.items)

    return False


def _is_access_path(node: parse_tree.Expression) -> bool:
    """Check that ``node`` is a chain of member and index accesses on a name."""
    while isinstance(node, (parse_tree.Member, parse_tree.Index)):
        node = node.instance if isinstance(node, parse_tree.Member) else node.collection

    return isinstance(node, parse_tree.Name)


def _is_set_call(node: parse_tree.Node) -> bool:
    """Check whether ``node`` is a call to the built-in ``set``."""
    return isinstance(node, parse_tree.FunctionCall) and node.name.identifier == "set"


def _is_new_set(
    node: parse_tree.Node,
    type_map: Mapping[parse_tree.Node, "TypeAnnotationUnion"],
) -> bool:
    """
    Check whether ``node`` gives a new set.

    A new set is created by ``set()``, ``intersection`` or ``difference``, so it
    shares nothing with any other set.
    """
    if _is_set_call(node):
        return True

    if not isinstance(node, parse_tree.MethodCall):
        return False

    member_type = type_map.get(node.member, None)
    return isinstance(member_type, BuiltinMethodTypeAnnotation) and (
        member_type.method is SET_INTERSECTION or member_type.method is SET_DIFFERENCE
    )


class _Inferrer(parse_tree.RestrictedTransformer[Optional["TypeAnnotationUnion"]]):
    """
    Infer the types of the given parse tree.

    Since we also handle non-nullness, you need to pre-compute the canonical
    representation of the nodes that you want to infer the types for. To that end,
    use :class:`~CanonicalRepresenter`.
    """

    #: Track of the inferred types
    type_map: Final[MutableMapping[parse_tree.Node, "TypeAnnotationUnion"]]

    #: Track of the nodes whose type has been narrowed down to a class by
    #: an ``isinstance`` guard. The implementation targets need to down-cast
    #: the value of these nodes to the given class.
    downcast_map: Final[MutableMapping[parse_tree.Node, Downcast]]

    #: Errors encountered during the inference
    errors: Final[List[Error]]

    def __init__(
        self,
        environment: "Environment",
        representation_map: Mapping[parse_tree.Node, str],
        argument_by_name: Mapping[Identifier, _types.Argument],
        enclosing_method: Optional[_types.UnderstoodMethod],
        returns: Optional[_types.TypeAnnotationUnion],
    ) -> None:
        """
        Initialize with the given values.

        The ``argument_by_name`` gives the arguments of the verification function or
        of the method, and is empty for an invariant.

        The ``enclosing_method`` is the method whose body we infer, if any.

        The ``returns`` is the return type of the verification function or
        of the method, and ``None`` for a procedure or an invariant.
        """
        # We need to create our own child environment so that we can introduce new
        # entries without affecting the variables from the outer scopes.
        self._environment = MutableEnvironment(parent=environment)

        self._representation_map = representation_map

        self._argument_by_name = argument_by_name

        self._enclosing_method = enclosing_method

        self._returns = (
            convert_type_annotation(returns)
            if returns is not None
            else PrimitiveTypeAnnotation(PrimitiveType.NONE)
        )  # type: Final[TypeAnnotationUnion]

        # NOTE (mristin):
        # We keep track of the variables whose values can be mutated in place,
        # *i.e.*, the mutable arguments, and the variables defined from a mutable
        # value. The mutability is deep, and flows from the variable, which is
        # the root of an access path, to all the values reached through it.
        #
        # The mutability of a variable is fixed at its definition. The names can
        # not shadow each other, so a set suffices, as long as we remove
        # the variables of a scope when we leave it,
        # see :py:meth:`_transform_in_new_scope`.
        self._mutable_name_set = {
            arg.name for arg in argument_by_name.values() if arg.mutable
        }  # type: Set[Identifier]

        # NOTE (mristin):
        # The instance is mutable only in the methods which are not marked as
        # @non_mutating. In the invariants and the verification functions, ``self``
        # is either read-only or not defined at all.
        if enclosing_method is not None and not enclosing_method.non_mutating:
            self._mutable_name_set.add(Identifier("self"))

        # NOTE (mristin):
        # We keep track of why the read-only variables are read-only so that we can
        # explain the errors. We remove them as we leave their scope, see
        # :py:meth:`_transform_in_new_scope`.
        self._read_only_reason_by_name = dict()  # type: MutableMapping[Identifier, str]

        # NOTE (mristin):
        # We keep track of the variables declared as ``Final[...]``, so that we
        # refuse to re-assign or to mutate them. We remove them as we leave their
        # scope, see :py:meth:`_transform_in_new_scope`.
        self._final_name_set = set()  # type: Set[Identifier]

        # NOTE (mristin):
        # We need to keep track of what we know about the values of the expressions
        # at the current point of the iteration, such as that ``x`` is non-null,
        # that ``x`` is an instance of a class, or that a JSON-able array has at
        # least one item. This member is stateful! It will constantly change,
        # depending on the position of the iteration through the tree. Please see
        # :py:class:`_Fact` for the whole model and the examples.
        #
        # The facts about the same expression are ordered such that the last
        # narrowing is the most specific one.
        #
        # Mind how we change the list, as some code keeps references to it:
        #
        # * The expressions, such as ``x is not None and ...``, append the facts
        #   in place, and remove exactly these facts again as their exit stack
        #   unwinds, see :py:meth:`_assume`. Once an expression has been
        #   transformed, the list is as it was before.
        # * The statements never change the list in place, but always assign
        #   a new list. Hence, :py:meth:`transform_if` and the other statements can
        #   keep the list before a branch, or at the end of a branch, as a snapshot
        #   without copying it.
        self._facts = []  # type: List[_Fact]

        # NOTE (mristin):
        # We keep track of the variables defined in the nested scopes, *i.e.*,
        # the branches of the switches and the if-statements, and the bodies of
        # the for-loops, which have been
        # already closed. The variables themselves are not visible anymore, as
        # their environments have been discarded. We keep their names to refuse
        # the re-declarations of the same names in the enclosing scope, see
        # :py:meth:`_transform_in_new_scope`. We keep their types to refuse
        # the re-definitions of the same names with different types, see
        # :py:meth:`_check_consistent_type_of_definition`.
        #
        # Each entry of the stack belongs to a scope, and the top of the stack
        # belongs to the current scope.
        self._types_of_variables_in_closed_scopes = [
            dict()
        ]  # type: List[MutableMapping[Identifier, TypeAnnotationUnion]]

        # NOTE (mristin):
        # We keep track of the loop variables of the for-loops enclosing the current
        # statement, so that we can refuse the assignments to them in the loop
        # bodies. An assignment to a loop variable behaves differently in Python
        # than in the targets:
        #
        # * Python re-binds the loop variable to the next item or integer on each
        #   iteration, so an assignment does not affect the iteration. In contrast,
        #   the targets loop over ``range(start, end)`` with a counter,
        #   *e.g.*, ``for (i = start; i < end; i++)``, so an assignment to
        #   the counter would skip or repeat the iterations.
        # * The targets define the loop variable over a collection as read-only,
        #   *e.g.*, ``const`` in TypeScript, a ``foreach`` iteration variable in C#,
        #   or a constant reference in C++, so an assignment does not compile.
        #
        # The environment can not tell us whether a variable is a loop variable,
        # since the loop variable is an ordinary entry in the scope of the loop
        # body. We add the loop variable when we enter the body, and remove it
        # when we leave. A set suffices for the nested for-loops, as a loop
        # variable must not shadow any visible variable, including the loop
        # variables of the enclosing for-loops.
        #
        # The set is empty if and only if we are outside of all for-loops, so we
        # also use it to refuse the ``continue`` and ``break`` statements outside
        # of a loop.
        self._loop_variable_set = set()  # type: Set[Identifier]

        self.type_map = dict()
        self.downcast_map = dict()
        self.errors = []

    def _is_copy_of_lists(self, node: parse_tree.Expression) -> bool:
        """
        Check that all the lists held by ``node`` are copies.

        A copy is a slice ``[:]``, possibly as an item of a tuple literal.
        """
        if isinstance(node, parse_tree.Slice):
            return True

        if isinstance(node, parse_tree.Tuple):
            return all(
                not _holds_list(self.type_map[value]) or self._is_copy_of_lists(value)
                for value in node.values
            )

        return False

    def _read_only_reason(self, node: parse_tree.Expression) -> Optional[str]:
        """
        Explain why the value of ``node`` can not be mutated in place.

        :return: the explanation, or None if the value is mutable
        """
        if isinstance(node, parse_tree.Name):
            identifier = node.identifier
            if identifier in self._mutable_name_set:
                return None

            argument = self._argument_by_name.get(identifier, None)
            if argument is not None:
                what = "function" if self._enclosing_method is None else "method"

                if isinstance(
                    beneath_optional(convert_type_annotation(argument.type_annotation)),
                    ListTypeAnnotation,
                ):
                    return (
                        f"the argument {identifier!r} is declared as a Sequence, "
                        f"which is read-only. Please declare it as a List "
                        f"if the {what} mutates it"
                    )

                if isinstance(
                    beneath_optional(convert_type_annotation(argument.type_annotation)),
                    SetTypeAnnotation,
                ):
                    return (
                        f"the argument {identifier!r} is declared as "
                        f"an AbstractSet, which is read-only. Please declare it as "
                        f"a Set if the {what} mutates it"
                    )

                return (
                    f"the argument {identifier!r} is read-only. Please declare it "
                    f"as Mutable[...] if the {what} mutates it"
                )

            if identifier == "self":
                if self._enclosing_method is None:
                    return "an invariant must not change the instance it checks"

                return (
                    f"the method {self._enclosing_method.name!r} is marked as "
                    f"@non_mutating, so it must not change its instance"
                )

            if identifier in self._loop_variable_set:
                return (
                    f"the loop variable {identifier!r} iterates over "
                    f"a read-only collection"
                )

            # NOTE (mristin):
            # The constant sets are the only sets defined in the global scope,
            # which is immutable.
            environment = self._environment  # type: Optional[Environment]
            while environment is not None and identifier not in environment.mapping:
                environment = environment.parent

            if isinstance(environment, ImmutableEnvironment) and isinstance(
                environment.mapping[identifier], SetTypeAnnotation
            ):
                return f"the constant set {identifier!r} is immutable"

            if identifier in self._final_name_set:
                return f"the variable {identifier!r} is declared as ``Final[...]``"

            definition_reason = self._read_only_reason_by_name.get(identifier, None)
            if definition_reason is not None:
                return (
                    f"the variable {identifier!r} has been defined from a read-only "
                    f"value, and the mutability of a variable is fixed at its "
                    f"definition; the value was read-only, as {definition_reason}"
                )

            return f"the variable {identifier!r} is read-only"

        if isinstance(node, parse_tree.Member):
            return self._read_only_reason(node.instance)

        if isinstance(node, parse_tree.Index):
            return self._read_only_reason(node.collection)

        if isinstance(node, parse_tree.Tuple):
            for item in node.values:
                item_type = self.type_map.get(item, None)
                if item_type is None or not _can_be_mutated(item_type):
                    continue

                reason = self._read_only_reason(item)
                if reason is not None:
                    return f"the tuple holds a read-only item, as {reason}"

            return None

        if isinstance(node, parse_tree.Slice):
            # NOTE (mristin):
            # A copy of a list is a fresh value, and hence mutable.
            return None

        if _is_new_set(node, self.type_map):
            # NOTE (mristin):
            # A new set is a fresh value, and hence mutable.
            return None

        if isinstance(node, parse_tree.MethodCall):
            return "the result of a method call is read-only"

        return (
            "the value is neither a variable, nor a property, nor an item "
            "of a list or a tuple"
        )

    def _strip_optional_if_non_null(
        self, node: parse_tree.Node, type_annotation: "TypeAnnotationUnion"
    ) -> "TypeAnnotationUnion":
        """
        Remove ``Optional`` from the ``type_annotation`` if the ``node`` is non-null.

        The ``type_annotation`` refers to the type inferred for the ``node``.

        We keep track of the non-nullness over the iteration in :attr:`._facts`.
        Using the canonical representation of the ``node``, we can check whether
        the type of the ``node`` is non-null.
        """
        if not isinstance(type_annotation, OptionalTypeAnnotation):
            return type_annotation

        canonical_repr = self._representation_map[node]
        if any(
            fact.key == canonical_repr and isinstance(fact.what, _NonNull)
            for fact in self._facts
        ):
            return type_annotation.value

        return type_annotation

    def _index_within_asserted_length(self, node: parse_tree.Index) -> bool:
        """
        Check whether a guard asserted the position of the ``node`` to be there.

        We keep track of the asserted lengths over the iteration
        in :attr:`._facts`, see :py:meth:`._implied_facts`.
        """
        if not _is_int_literal(node.index):
            return False

        assert isinstance(node.index, parse_tree.Constant)
        assert isinstance(node.index.value, int)

        collection_repr = self._representation_map[node.collection]
        min_length = max(
            (
                fact.what.length
                for fact in self._facts
                if fact.key == collection_repr and isinstance(fact.what, _MinLength)
            ),
            default=0,
        )

        # NOTE (mristin):
        # A negative index is resolved from the back of the array, so both ends
        # of the range are bounded by the asserted length.
        return -min_length <= node.index.value < min_length

    def _is_length_call(self, node: parse_tree.Node) -> bool:
        """Check whether the ``node`` is a call to the built-in ``len``."""
        if not (isinstance(node, parse_tree.FunctionCall) and len(node.args) == 1):
            return False

        func_type = self.type_map.get(node.name, None)

        return (
            isinstance(func_type, BuiltinFunctionTypeAnnotation)
            and func_type.func.kind is BuiltinFunctionKind.LEN
        )

    def _asserted_min_length(
        self, node: parse_tree.Node
    ) -> Optional[Tuple[parse_tree.Expression, int]]:
        """
        Determine which JSON-able array the ``node`` asserts to be how long.

        We understand the length checks such as ``len(self.values) > 0`` and
        ``1 <= len(self.values)``, and return the array together with the asserted
        length.
        """
        if not isinstance(node, parse_tree.Comparison):
            return None

        length_call = None  # type: Optional[parse_tree.FunctionCall]
        literal = None  # type: Optional[int]
        op = node.op

        if self._is_length_call(node.left) and _is_int_literal(node.right):
            assert isinstance(node.left, parse_tree.FunctionCall)
            assert isinstance(node.right, parse_tree.Constant)
            assert isinstance(node.right.value, int)

            length_call, literal = node.left, node.right.value
        elif _is_int_literal(node.left) and self._is_length_call(node.right):
            assert isinstance(node.left, parse_tree.Constant)
            assert isinstance(node.left.value, int)
            assert isinstance(node.right, parse_tree.FunctionCall)

            length_call, literal = node.right, node.left.value

            # NOTE (mristin):
            # ``1 < len(self.values)`` says the same as ``len(self.values) > 1``.
            op = _FLIPPED_COMPARATOR[op]
        else:
            return None

        assert length_call is not None
        assert literal is not None

        if op is parse_tree.Comparator.GT:
            min_length = literal + 1
        elif op is parse_tree.Comparator.GE:
            min_length = literal
        else:
            return None

        if min_length <= 0:
            return None

        collection = length_call.args[0]
        if not isinstance(
            beneath_optional(self.type_map[collection]), JsonArrayTypeAnnotation
        ):
            return None

        return collection, min_length

    def _fact_about(
        self,
        node: parse_tree.Expression,
        what: Union[_NonNull, _MinLength, _Narrowing],
    ) -> _Fact:
        """
        Create the fact that tells ``what`` about the value of the ``node``.

        For example, ``_fact_about(<self.items[i]>, _NonNull())`` gives the fact with
        the key ``self.items[i]``, the path ``self``, ``items``, ``[]``, and
        the names ``i``.
        """
        path, names = _dependencies(node)

        return _Fact(
            key=self._representation_map[node],
            what=what,
            path=path,
            names=frozenset(names),
        )

    def _implied_facts(self, node: parse_tree.Node) -> List[_Fact]:
        """
        Determine what the ``node`` tells us about the values if it holds.

        For example:

        ==================================== =====================================
        ``node``                             Implied facts
        ==================================== =====================================
        ``x is not None``                    ``x`` is non-null
        ``isinstance(x, C)``                 ``x`` is an instance of ``C``
        ``isinstance(x, (A, B))``            none, ``x`` is either ``A`` or ``B``
        ``len(self.values) > 1``             ``self.values`` has at least 2 items
        ``"key" in self.mapping``            ``self.mapping["key"]`` is non-null
        ``x is not None and isinstance(x, C)`` both of the above about ``x``
        ``not (x is None)``                  ``x`` is non-null, see
                                             :py:meth:`_implied_facts_of_negation`
        ``x is not None or y is not None``   none, we do not know which one holds
        ==================================== =====================================

        Mind that the ``node`` must have been already transformed, as we need its type
        and its canonical representation.
        """
        if isinstance(node, parse_tree.And):
            return [
                fact for value in node.values for fact in self._implied_facts(value)
            ]

        if isinstance(node, parse_tree.Not):
            return self._implied_facts_of_negation(node.operand)

        if isinstance(node, parse_tree.IsNotNone):
            return [self._fact_about(node.value, _NonNull())]

        # NOTE (mristin):
        # ``key in obj`` tells us that ``obj[key]`` is there. A JSON-able object is
        # the only container whose membership is a question about the index.
        if isinstance(node, parse_tree.IsIn) and isinstance(
            beneath_optional(self.type_map[node.container]), JsonObjectTypeAnnotation
        ):
            path, names = _dependencies(node.container)
            if path is not None:
                path.append(_index_segment(node.member))
                names.update(_names_in(node.member))
            else:
                names.update(_names_in(node.member))

            return [
                _Fact(
                    key=_Canonicalizer.index_representation(
                        collection=node.container,
                        collection_repr=self._representation_map[node.container],
                        index_repr=self._representation_map[node.member],
                    ),
                    what=_NonNull(),
                    path=path,
                    names=frozenset(names),
                )
            ]

        # NOTE (mristin):
        # ``isinstance(x, C)`` tells us that ``x`` is an instance of ``C``. We can not
        # narrow on multiple classes, ``isinstance(x, (A, B))``, as the value could be
        # an instance of either of them.
        if isinstance(node, parse_tree.IsInstance):
            if len(node.classes) != 1:
                return []

            cls = self._environment.find_our_type(node.classes[0].identifier)
            assert isinstance(cls, _types.ClassUnionAsTuple), (
                f"Expected the class of a successfully inferred isinstance "
                f"to be resolved, but got: {cls}"
            )

            return [
                self._fact_about(
                    node.value, _Narrowing(target=OurTypeAnnotation(our_type=cls))
                )
            ]

        # NOTE (mristin):
        # ``len(arr) > 0`` tells us that ``arr[0]`` and ``arr[-1]`` are there, and
        # so on for the longer arrays.
        asserted = self._asserted_min_length(node)
        if asserted is not None:
            collection, min_length = asserted
            return [self._fact_about(collection, _MinLength(length=min_length))]

        return []

    def _implied_facts_of_negation(self, node: parse_tree.Node) -> List[_Fact]:
        """
        Determine what the ``node`` tells us about the values if it does *not* hold.

        We need the negations for the ``elif`` and ``else`` branches, which execute
        only if the previous conditions do not hold, and for the code after
        an if-statement whose branches exit early. For example:

        ======================================= ==================================
        ``node`` which does not hold            Implied facts
        ======================================= ==================================
        ``x is None``                           ``x`` is non-null
        ``not isinstance(x, C)``                ``x`` is an instance of ``C``
        ``x is None or not isinstance(x, C)``   both of the above about ``x``,
                                                by De Morgan
        ``isinstance(x, C) => x.y is not None`` ``x`` is an instance of ``C``;
                                                nothing about ``x.y``
        ``x is not None and isinstance(x, C)``  none, see below
        ``isinstance(x, C)``                    none, see below
        ``x is not None``                       none, see below
        ======================================= ==================================

        We can not tell anything from the negation of a conjunction, as we do not
        know which of its values does not hold. Analogously, the negation of
        ``isinstance(x, C)`` does not tell us to which class ``x`` belongs, and
        the negation of ``x is not None`` tells us only that ``x`` is ``None``, which
        we do not track.

        Mind that the ``node`` must have been already transformed, as we need its type
        and its canonical representation.
        """
        if isinstance(node, parse_tree.IsNone):
            return [self._fact_about(node.value, _NonNull())]

        if isinstance(node, parse_tree.Not):
            return self._implied_facts(node.operand)

        # NOTE (mristin):
        # The implication ``a => b`` is ``not a or b``, so its negation is
        # ``a and not b``.
        if isinstance(node, parse_tree.Implication):
            return self._implied_facts(
                node.antecedent
            ) + self._implied_facts_of_negation(node.consequent)

        # NOTE (mristin):
        # By De Morgan, ``not (a or b)`` is ``not a and not b``.
        if isinstance(node, parse_tree.Or):
            return [
                fact
                for value in node.values
                for fact in self._implied_facts_of_negation(value)
            ]

        return []

    def _assume(self, facts: List[_Fact], exit_stack: contextlib.ExitStack) -> None:
        """
        Assume the ``facts`` until the ``exit_stack`` unwinds.

        We use this only in the expressions, where the facts hold for the remainder
        of the expression. For example, while we transform ``len(x) > 0`` in
        ``x is not None and len(x) > 0``, ``x`` is non-null.
        """
        self._facts.extend(facts)

        for fact in facts:
            exit_stack.callback(self._facts.remove, fact)

    def _join(
        self,
        facts_before: List[_Fact],
        facts_at_ends: Sequence[List[_Fact]],
    ) -> None:
        """
        Set the facts after the branches of an if-statement or of a switch.

        The ``facts_before`` hold before the branching, while the ``facts_at_ends``
        hold at the ends of the branches which can complete normally.

        We keep only the facts which hold at the end of every such branch. If no branch
        can complete normally, the code after the branching is unreachable, and we
        simply keep the ``facts_before``.

        For example:

        .. code-block:: python

            if x is not None:
                pass
                # Facts at the end: x is non-null.
            elif flag:
                return False
                # Can not complete normally, does not count.
            else:
                pass
                # Facts at the end: none.

            # Facts: none, since the else-branch knows nothing about ``x``.
            # Fails: x is optional here.
            return x.optional_text is None

        We compare the facts by value, see :py:func:`_same_facts`.
        """
        if len(facts_at_ends) == 0:
            self._facts = facts_before
            return

        self._facts = [
            fact
            for fact in facts_at_ends[0]
            if all(
                any(_same_facts(fact, other) for other in facts)
                for facts in facts_at_ends[1:]
            )
        ]

    @ensure(lambda self, result: not (result is None) or len(self.errors) > 0)
    def transform(self, node: parse_tree.Node) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin):
        # We can not write the following as the pre-condition as it would break
        # behavioral subtyping since the parent class expects no pre-conditions.
        #
        # However, in this case, we check that the supplied dependency,
        # ``representation_map``, is correct.
        assert node in self._representation_map, (
            f"The node {parse_tree.dump(node)} at 0x{id(node):x} could not be found "
            f"in the supplied representation_map."
        )

        result = super().transform(node)

        # NOTE (mristin):
        # We narrow the type of the value if we know it to be an instance of
        # a more specific class, *e.g.*, after ``isinstance(x, C)`` or after
        # ``x = c`` where ``c`` is a ``C``, see :py:class:`_Fact`. The transpilers
        # down-cast the value based on :py:attr:`downcast_map`.
        if isinstance(result, OurTypeAnnotation):
            canonical_repr = self._representation_map[node]
            narrowing = next(
                (
                    fact.what
                    for fact in reversed(self._facts)
                    if fact.key == canonical_repr and isinstance(fact.what, _Narrowing)
                ),
                None,
            )
            if narrowing is not None:
                self.downcast_map[node] = Downcast(
                    source=result, target=narrowing.target
                )

                result = narrowing.target
                self.type_map[node] = result

        return result

    def transform_member(
        self, node: parse_tree.Member
    ) -> Optional["TypeAnnotationUnion"]:
        instance_type = self.transform(node.instance)

        if instance_type is None:
            return None

        if isinstance(instance_type, SetTypeAnnotation):
            set_method = SET_METHODS_BY_NAME.get(node.name, None)
            if set_method is None:
                supported = ", ".join(
                    repr(name) for name in sorted(SET_METHODS_BY_NAME.keys())
                )
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The member {node.name!r} is not supported on sets; "
                        f"we support only the following methods: {supported}",
                    )
                )
                return None

            set_method_type = BuiltinMethodTypeAnnotation(method=set_method)
            self.type_map[node] = set_method_type
            return set_method_type

        if try_primitive_type(instance_type) is PrimitiveType.STR:
            builtin_method = STR_METHODS_BY_NAME.get(node.name, None)
            if builtin_method is None:
                supported = ", ".join(
                    repr(name) for name in sorted(STR_METHODS_BY_NAME.keys())
                )
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The member {node.name!r} is not supported on strings; "
                        f"we support only the following methods: {supported}",
                    )
                )
                return None

            builtin_method_type = BuiltinMethodTypeAnnotation(method=builtin_method)
            self.type_map[node] = builtin_method_type
            return builtin_method_type

        if isinstance(instance_type, OurTypeAnnotation):
            if not isinstance(instance_type.our_type, _types.Class):
                self.errors.append(
                    Error(
                        node.instance.original_node,
                        f"Expected an instance type as our type to be a class, "
                        f"but got: {instance_type.our_type}",
                    )
                )
                return None

            cls = instance_type.our_type
            assert isinstance(cls, _types.Class)

            prop = cls.properties_by_name.get(node.name, None)
            if prop is not None:
                result = convert_type_annotation(prop.type_annotation)

                result = self._strip_optional_if_non_null(
                    node=node, type_annotation=result
                )
                self.type_map[node] = result
                return result

            method = cls.methods_by_name.get(node.name, None)
            if method is not None:
                # NOTE (mristin):
                # The invariants and the verification functions are generated
                # outside the class in most targets (*e.g.*, in a separate package in
                # Go and Java). Hence, the non-public methods can not be called from
                # there, and serve only as helpers to the methods of the class.
                # A protected method can be called on ``self`` from the methods of
                # the class and its descendants, while a private method only from
                # the methods of the class which specified it.
                if method.visibility is not _types.Visibility.PUBLIC and not (
                    self._enclosing_method is not None
                    and isinstance(node.instance, parse_tree.Name)
                    and node.instance.identifier == "self"
                    and (
                        method.visibility is _types.Visibility.PROTECTED
                        or method.specified_for is self._enclosing_method.specified_for
                    )
                ):
                    self.errors.append(
                        Error(
                            node.original_node,
                            f"The method {node.name!r} of the class {cls.name!r} "
                            f"is {method.visibility.value}, so it can be only called "
                            f"on self from the methods of the class"
                            + (
                                " and its descendants"
                                if method.visibility is _types.Visibility.PROTECTED
                                else ""
                            ),
                        )
                    )
                    return None

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
                result = OurTypeAnnotation(our_type=enumeration)

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
            if isinstance(instance_type, OptionalTypeAnnotation):
                self.errors.append(
                    Error(
                        node.instance.original_node,
                        f"Expected an instance type to be a non-None, either "
                        f"an enumeration-as-type or our type, "
                        f"but inferred an Optional: {instance_type}",
                    )
                )
            else:
                self.errors.append(
                    Error(
                        node.instance.original_node,
                        f"Expected an instance type to be either "
                        f"an enumeration-as-type or our type, "
                        f"but inferred: {instance_type}",
                    )
                )
            return None

        return None

    def transform_index(
        self, node: parse_tree.Index
    ) -> Optional["TypeAnnotationUnion"]:
        collection_type = self.transform(node.collection)
        if collection_type is None:
            return None

        index_type = self.transform(node.index)
        if index_type is None:
            return None

        success = True

        if isinstance(collection_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.collection.original_node,
                    f"Expected the collection to be a non-None, "
                    f"but got: {collection_type}",
                )
            )
            success = False

        if isinstance(index_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.index.original_node,
                    f"Expected the index to be a non-None, " f"but got: {index_type}",
                )
            )
            success = False

        if not success:
            return None

        if isinstance(collection_type, TupleTypeAnnotation):
            # NOTE (mristin):
            # Tuples are heterogeneous, so, unlike lists, we can only infer the type
            # of the individual item if the index is given as a literal integer.
            if not (
                isinstance(node.index, parse_tree.Constant)
                and isinstance(node.index.value, int)
                and not isinstance(node.index.value, bool)
            ):
                self.errors.append(
                    Error(
                        node.index.original_node,
                        f"Expected a literal integer as the index into a tuple "
                        f"so that the type of the individual tuple item can be "
                        f"statically inferred, but got: {parse_tree.dump(node.index)}",
                    )
                )
                return None

            items = collection_type.items
            index_value = node.index.value
            if not (
                -len(items) <= index_value < len(items)
            ):  # pylint: disable=superfluous-parens
                self.errors.append(
                    Error(
                        node.index.original_node,
                        f"The index {index_value} is out of range "
                        f"for a tuple of {len(items)} item(s): {collection_type}",
                    )
                )
                return None

            result = items[index_value]
            self.type_map[node] = result
            return result

        if isinstance(collection_type, JsonArrayTypeAnnotation):
            if not (
                isinstance(index_type, PrimitiveTypeAnnotation)
                and index_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
            ):
                self.errors.append(
                    Error(
                        node.index.original_node,
                        f"Expected the index into a JSONArray to be an integer, "
                        f"but got: {index_type}",
                    )
                )
                return None

            # NOTE (mristin):
            # The position might lie outside the array, so the item is optional
            # unless a guard, such as ``len(self.values) > 0``, asserted the array
            # to be long enough.
            if self._index_within_asserted_length(node):
                result = JsonValueTypeAnnotation()
            else:
                result = OptionalTypeAnnotation(JsonValueTypeAnnotation())

            self.type_map[node] = result
            return result

        if isinstance(collection_type, JsonObjectTypeAnnotation):
            if try_primitive_type(index_type) != PrimitiveType.STR:
                self.errors.append(
                    Error(
                        node.index.original_node,
                        f"Expected the index into a JSONObject to be a string "
                        f"(or a class constraining ``str``), but got: {index_type}",
                    )
                )
                return None

            # NOTE (mristin):
            # The key might be missing in the object, so the value is optional
            # unless a guard, such as ``"type" in self.mapping``, asserted the key
            # to be there.
            result = OptionalTypeAnnotation(JsonValueTypeAnnotation())
            result = self._strip_optional_if_non_null(node=node, type_annotation=result)
            self.type_map[node] = result
            return result

        if isinstance(collection_type, JsonValueTypeAnnotation):
            self.errors.append(
                Error(
                    node.collection.original_node,
                    "JSONValue represents an arbitrary, open JSON-able value "
                    "whose shape can not be determined statically, so we treat "
                    "it analogous to Unknown -- indexing into it is not "
                    "supported",
                )
            )
            return None

        if not isinstance(collection_type, ListTypeAnnotation):
            self.errors.append(
                Error(
                    node.collection.original_node,
                    f"Expected an index access on a list or a tuple, "
                    f"but got: {collection_type}",
                )
            )
            return None

        if not (
            isinstance(index_type, PrimitiveTypeAnnotation)
            and index_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
        ):
            self.errors.append(
                Error(
                    node.collection.original_node,
                    f"Expected the index to be an integer, but got: {index_type}",
                )
            )
            return None

        result = collection_type.items
        self.type_map[node] = result
        return result

    def _check_position_in_string(
        self,
        node: parse_tree.Expression,
        type_annotation: "TypeAnnotationUnion",
        what: str,
    ) -> bool:
        """
        Check that ``node`` can denote a position in a string.

        A position is an integer. The transpiled code follows the Python
        implementation of the slicing and of ``str.find``, since Python is
        the language of the meta-model specifications. Hence, a position counts
        the characters (code points), a negative position counts from the end of
        the string, and the positions out of range are clamped to the string.

        Return ``False`` and append to :py:attr:`errors` if the check fails.
        """
        if not (
            isinstance(type_annotation, PrimitiveTypeAnnotation)
            and type_annotation.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
        ):
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected {what} to be an integer, but got: {type_annotation}",
                )
            )
            return False

        return True

    def transform_slice(
        self, node: parse_tree.Slice
    ) -> Optional["TypeAnnotationUnion"]:
        success = True

        collection_type = self.transform(node.collection)
        if collection_type is None:
            success = False

        start_type = None  # type: Optional[TypeAnnotationUnion]
        if node.start is not None:
            start_type = self.transform(node.start)
            if start_type is None:
                success = False

        end_type = None  # type: Optional[TypeAnnotationUnion]
        if node.end is not None:
            end_type = self.transform(node.end)
            if end_type is None:
                success = False

        if not success:
            return None

        assert collection_type is not None

        if isinstance(collection_type, ListTypeAnnotation):
            # NOTE (mristin):
            # We support slicing the lists only to copy them, as the lists need
            # to be copied explicitly when they are stored, see
            # :py:meth:`transform_assignment`.
            if node.start is not None or node.end is not None:
                self.errors.append(
                    Error(
                        node.original_node,
                        "We support slicing a list only to copy it as a whole, "
                        "with ``[:]``, but got a slice with a start or an end",
                    )
                )
                return None

            if _holds_list(collection_type.items):
                self.errors.append(
                    Error(
                        node.original_node,
                        f"We can not copy the list of type {collection_type} with "
                        f"``[:]``, since its items hold lists themselves. Python "
                        f"copies the list shallowly, so that the copy shares "
                        f"the inner lists, while C++ copies the inner lists as well.",
                    )
                )
                return None

            list_copy_type = ListTypeAnnotation(items=collection_type.items)
            self.type_map[node] = list_copy_type
            return list_copy_type

        if try_primitive_type(collection_type) is not PrimitiveType.STR:
            self.errors.append(
                Error(
                    node.collection.original_node,
                    f"We support slicing only of non-None strings, and copying of "
                    f"non-None lists with ``[:]``, but got: {collection_type}",
                )
            )
            success = False

        if node.start is not None:
            assert start_type is not None
            if not self._check_position_in_string(
                node=node.start,
                type_annotation=start_type,
                what="the start of a slice",
            ):
                success = False

        if node.end is not None:
            assert end_type is not None
            if not self._check_position_in_string(
                node=node.end, type_annotation=end_type, what="the end of a slice"
            ):
                success = False

        if not success:
            return None

        # NOTE (mristin):
        # A slice of a constrained primitive does not necessarily satisfy
        # the constraints, so we infer a plain string.
        result = PrimitiveTypeAnnotation(PrimitiveType.STR)
        self.type_map[node] = result
        return result

    def transform_tuple(
        self, node: parse_tree.Tuple
    ) -> Optional["TypeAnnotationUnion"]:
        items = []  # type: List[TypeAnnotationUnion]
        failed = False
        for value in node.values:
            value_type = self.transform(value)
            if value_type is None:
                failed = True
            else:
                items.append(value_type)

        if failed:
            return None

        result = TupleTypeAnnotation(items=items)
        self.type_map[node] = result
        return result

    def transform_comparison(
        self, node: parse_tree.Comparison
    ) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``left`` and ``right`` even though we
        # know the type in advance

        left_type = self.transform(node.left)
        if left_type is None:
            return None

        right_type = self.transform(node.right)
        if right_type is None:
            return None

        success = True

        if isinstance(left_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.left.original_node,
                    f"Expected the left operand to be a non-None, "
                    f"but got: {left_type}",
                )
            )
            success = False

        if isinstance(right_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.right.original_node,
                    f"Expected the right operand to be a non-None, "
                    f"but got: {right_type}",
                )
            )
            success = False

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_is_in(self, node: parse_tree.IsIn) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``member`` and ``container`` even though
        # we know the type of the expression in advance.

        member_type = self.transform(node.member)
        container_type = self.transform(node.container)

        if member_type is None or container_type is None:
            return None

        # NOTE (mristin):
        # Check that both the member and the container are non-nullables. We already
        # had bugs related to this, see:
        # https://github.com/aas-core-works/aas-core-meta/pull/272
        success = True

        if isinstance(member_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.member.original_node,
                    f"Expected the member to be a non-None, but got: {member_type}",
                )
            )
            success = False

        if isinstance(container_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.container.original_node,
                    f"Expected the container to be a non-None, "
                    f"but got: {container_type}",
                )
            )
            success = False

        if not success:
            return None

        # NOTE (mristin):
        # The targets look up the member in a hash set, so the member has to be of
        # the same type as the items. We accept the constrained primitives in
        # either direction, as they are represented by their constrainees.
        if isinstance(container_type, SetTypeAnnotation) and not (
            _assignable(target_type=container_type.items, value_type=member_type)
            or _assignable(target_type=member_type, value_type=container_type.items)
        ):
            self.errors.append(
                Error(
                    node.member.original_node,
                    f"Expected the member to be of the type of the items of "
                    f"the set {container_type}, but got: {member_type}",
                )
            )
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_is_instance(
        self, node: parse_tree.IsInstance
    ) -> Optional["TypeAnnotationUnion"]:
        value_type = self.transform(node.value)

        if value_type is None:
            return None

        # NOTE (mristin):
        # We refuse the optional values since ``isinstance`` on ``None`` would
        # panic or be undefined behavior in some implementation targets. Please
        # check for non-nullness first, and only then check the class.
        if isinstance(value_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.value.original_node,
                    f"Expected the value to be a non-None for ``isinstance``, "
                    f"but got: {value_type}. Please check for ``is not None`` first.",
                )
            )
            return None

        if not (
            isinstance(value_type, OurTypeAnnotation)
            and isinstance(
                value_type.our_type,
                (_types.AbstractClass, _types.ConcreteClass, _types.NamedUnion),
            )
        ):
            self.errors.append(
                Error(
                    node.value.original_node,
                    f"Expected the value to be an instance of a class or "
                    f"of a named union for ``isinstance``, but got: {value_type}",
                )
            )
            return None

        value_our_type = value_type.our_type

        success = True

        for cls_name in node.classes:
            cls = self._environment.find_our_type(cls_name.identifier)

            if cls is None:
                self.errors.append(
                    Error(
                        cls_name.original_node,
                        f"The class {cls_name.identifier!r} given to ``isinstance`` "
                        f"could not be found",
                    )
                )
                success = False
                continue

            if not isinstance(cls, _types.ClassUnionAsTuple):
                self.errors.append(
                    Error(
                        cls_name.original_node,
                        f"Expected only classes in ``isinstance``, "
                        f"but got {cls_name.identifier!r}: {cls}",
                    )
                )
                success = False
                continue

            if isinstance(value_our_type, _types.NamedUnion):
                if not any(cls.is_subclass_of(root) for root in value_our_type.roots):
                    roots_joined = ", ".join(root.name for root in value_our_type.roots)

                    self.errors.append(
                        Error(
                            cls_name.original_node,
                            f"Expected the class {cls.name!r} "
                            f"to be a root of the named union "
                            f"{value_our_type.name!r} of the value "
                            f"in ``isinstance``, or a descendant of a root, "
                            f"but it is not. The roots are: {roots_joined}",
                        )
                    )
                    success = False

            elif isinstance(value_our_type, _types.ClassUnionAsTuple):
                if _types.runtime_id(cls) not in value_our_type.descendant_id_set:
                    is_ancestor_or_same = (
                        cls is value_our_type
                        or _types.runtime_id(value_our_type) in cls.descendant_id_set
                    )

                    if is_ancestor_or_same:
                        reason = "so the check always holds"
                    else:
                        reason = "so the check never holds"

                    self.errors.append(
                        Error(
                            cls_name.original_node,
                            f"Expected the class {cls.name!r} to be a strict "
                            f"descendant of the class {value_our_type.name!r} "
                            f"of the value in ``isinstance``, but it is not, "
                            f"{reason}",
                        )
                    )
                    success = False

            else:
                assert_never(value_our_type)

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_implication(
        self, node: parse_tree.Implication
    ) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin):
        # Just recurse to fill ``type_map`` on ``antecedent`` even though we know the
        # type in advance

        antecedent_type = self.transform(node.antecedent)
        if antecedent_type is None:
            return None

        success = True

        if isinstance(antecedent_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.antecedent.original_node,
                    f"Expected the antecedent to be a non-None, "
                    f"but got: {antecedent_type}",
                )
            )
            success = False

        # region Recurse into consequent while considering any non-nullness

        # NOTE (mristin):
        # We are very lax here and ignore the fact that calls to methods and functions
        # can actually alter the value assumed to be non-null, and actually violate
        # its non-nullness by setting it to null.
        #
        # This lack of conservatism works for now. If the bugs related to nullness
        # start to surface, we should re-think our approach here.

        with contextlib.ExitStack() as exit_stack:
            self._assume(self._implied_facts(node.antecedent), exit_stack)

            success = (self.transform(node.consequent) is not None) and success

            if not success:
                return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def _transform_builtin_method_call(
        self,
        node: parse_tree.MethodCall,
        method: BuiltinMethod,
        arg_types: Sequence["TypeAnnotationUnion"],
    ) -> Optional["TypeAnnotationUnion"]:
        """Check the arguments of a call to a built-in method, and infer the result."""
        if not method.min_arg_count <= len(node.args) <= method.max_arg_count:
            if method.min_arg_count == method.max_arg_count:
                expected = f"{method.min_arg_count}"
            else:
                expected = f"between {method.min_arg_count} and {method.max_arg_count}"

            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected {expected} argument(s) to the built-in method "
                    f"{method.name!r}, but got {len(node.args)}",
                )
            )
            return None

        if method is STR_FIND:
            success = True

            if try_primitive_type(arg_types[0]) is not PrimitiveType.STR:
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the searched value of ``find`` to be a string, "
                        f"but got: {arg_types[0]}",
                    )
                )
                success = False

            if len(arg_types) == 2:
                if not self._check_position_in_string(
                    node=node.args[1],
                    type_annotation=arg_types[1],
                    what="the start of ``find``",
                ):
                    success = False

            if not success:
                return None

        elif method is STR_LSTRIP:
            if try_primitive_type(arg_types[0]) is not PrimitiveType.STR:
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the stripped characters of ``lstrip`` to be "
                        f"a string, but got: {arg_types[0]}",
                    )
                )
                return None

        elif method is SET_ADD:
            set_type = self.type_map[node.member.instance]
            assert isinstance(set_type, SetTypeAnnotation)

            if not _assignable(target_type=set_type.items, value_type=arg_types[0]):
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the item added to {set_type} to be "
                        f"assignable to {set_type.items}, but got: {arg_types[0]}",
                    )
                )
                return None

            reason = self._read_only_reason(node.member.instance)
            if reason is not None:
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The ``add`` mutates the set, but {reason}.",
                    )
                )
                return None

        elif method is SET_INTERSECTION or method is SET_DIFFERENCE:
            set_type = self.type_map[node.member.instance]
            assert isinstance(set_type, SetTypeAnnotation)

            if not _assignable(target_type=set_type, value_type=arg_types[0]):
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the argument of ``{method.name}`` to be "
                        f"a set of the same items, {set_type}, "
                        f"but got: {arg_types[0]}",
                    )
                )
                return None

        else:
            raise AssertionError(f"Unexpected built-in method: {method.name!r}")

        result: TypeAnnotationUnion
        if method.returns is not None:
            result = method.returns
        else:
            # NOTE (mristin):
            # The intersection and the difference give a new set of the items
            # of the instance.
            set_type = self.type_map[node.member.instance]
            assert isinstance(set_type, SetTypeAnnotation)
            result = SetTypeAnnotation(items=set_type.items)

        self.type_map[node] = result
        return result

    def _check_arguments(
        self,
        args: Sequence[parse_tree.Expression],
        arguments: Sequence[_types.Argument],
        what: str,
    ) -> bool:
        """
        Check that the ``args`` fit the ``arguments`` beyond their types.

        We check that the ``args`` passed to the mutable ``arguments`` are mutable,
        and that ``None`` is passed only to the optional ``arguments``.

        The ``what`` describes the called function or method in the error messages,
        *e.g.*, ``the verification function 'foo'``.

        :return: True if the check passed
        """
        ok = True
        for arg_node, argument in zip(args, arguments):
            # NOTE (mristin):
            # We do not check the types of the arguments in general. However, we
            # have to check the sets, since the targets represent them with
            # different types which only the checks here make compatible.
            arg_type = self.type_map.get(arg_node, None)
            argument_type = convert_type_annotation(argument.type_annotation)
            if (
                arg_type is not None
                and (
                    isinstance(beneath_optional(arg_type), SetTypeAnnotation)
                    or isinstance(beneath_optional(argument_type), SetTypeAnnotation)
                )
                and not _assignable(target_type=argument_type, value_type=arg_type)
            ):
                self.errors.append(
                    Error(
                        arg_node.original_node,
                        f"The argument {argument.name!r} of {what} is "
                        f"of type {argument_type}, but got: {arg_type}",
                    )
                )
                ok = False
                continue

            if (
                isinstance(arg_node, parse_tree.Constant)
                and arg_node.value is None
                and not isinstance(
                    argument.type_annotation, _types.OptionalTypeAnnotation
                )
            ):
                self.errors.append(
                    Error(
                        arg_node.original_node,
                        f"The argument {argument.name!r} of {what} is not "
                        f"optional, but got None.",
                    )
                )
                ok = False
                continue

            if not argument.mutable:
                continue

            if not _is_access_path(arg_node):
                self.errors.append(
                    Error(
                        arg_node.original_node,
                        f"The argument {argument.name!r} of {what} is mutable, "
                        f"so we expect a variable, a property or an item of a list "
                        f"or a tuple so that the mutation is observable, but "
                        f"got a temporary value.",
                    )
                )
                ok = False
                continue

            reason = self._read_only_reason(arg_node)
            if reason is not None:
                self.errors.append(
                    Error(
                        arg_node.original_node,
                        f"The argument {argument.name!r} of {what} is mutable, "
                        f"but {reason}.",
                    )
                )
                ok = False

        return ok

    def transform_method_call(
        self, node: parse_tree.MethodCall
    ) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin):
        # We recurse to track the types of the arguments. We check their types only
        # for the built-in methods, as we have not implemented the checks against
        # the signatures of our methods. However, we check the mutability of
        # the arguments passed to our methods.
        failed = False
        arg_types = []  # type: List[TypeAnnotationUnion]
        for arg in node.args:
            arg_type = self.transform(arg)
            if arg_type is None:
                failed = True
            else:
                arg_types.append(arg_type)

        member_type = self.transform(node.member)

        if member_type is None:
            failed = True

        elif isinstance(member_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.member.original_node,
                    f"Expected the member to be a non-None, " f"but got: {member_type}",
                )
            )
            failed = True
        else:
            pass

        if failed:
            return None

        if isinstance(member_type, BuiltinMethodTypeAnnotation):
            return self._transform_builtin_method_call(
                node=node, method=member_type.method, arg_types=arg_types
            )

        if not isinstance(member_type, MethodTypeAnnotation):
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected the member in a method call to be a method, "
                    f"but got: {member_type}",
                )
            )
            return None

        if not self._check_arguments(
            args=node.args,
            arguments=member_type.method.arguments,
            what=f"the method {node.member.name!r}",
        ):
            return None

        if not member_type.method.non_mutating:
            reason = self._read_only_reason(node.member.instance)
            if reason is not None:
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The method {node.member.name!r} is not marked "
                        f"as @non_mutating, so it might mutate its instance, "
                        f"but {reason}.",
                    )
                )
                return None

        result: TypeAnnotationUnion

        if member_type.method.returns is None:
            result = PrimitiveTypeAnnotation(a_type=PrimitiveType.NONE)
        else:
            result = convert_type_annotation(member_type.method.returns)

        result = self._strip_optional_if_non_null(node=node, type_annotation=result)
        self.type_map[node] = result
        return result

    def _check_signed_number_operand(
        self,
        operand: parse_tree.Expression,
        operand_type: "TypeAnnotationUnion",
        operation_name_with_capital_the: str,
    ) -> Optional[PrimitiveType]:
        """
        Check that the operand of a sign-related operation is a signed number.

        The sign-related operations are the arithmetic negation and ``abs``.
        Return the primitive type of the operand, or None if the check failed.
        Errors, if any, are appended to :py:attr:`errors`.

        We refuse lengths as they are unsigned in some target languages (*e.g.*,
        ``size_t`` in C++) so that their negation would silently wrap around.
        """
        if isinstance(operand_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    operand.original_node,
                    f"Expected the operand to be a non-None, "
                    f"but got: {operand_type}",
                )
            )
            return None

        # NOTE (mristin):
        # The constrained primitives behave like their constrainees in arithmetic.
        a_type = try_primitive_type(operand_type)

        if a_type not in (PrimitiveType.INT, PrimitiveType.FLOAT):
            self.errors.append(
                Error(
                    operand.original_node,
                    f"{operation_name_with_capital_the} is only defined on "
                    f"integer and floating-point numbers, but got: {operand_type}",
                )
            )
            return None

        return a_type

    def transform_function_call(
        self, node: parse_tree.FunctionCall
    ) -> Optional["TypeAnnotationUnion"]:
        result = None  # type: Optional[TypeAnnotationUnion]
        failed = False

        func_type = self.transform(node.name)
        if func_type is None:
            failed = True
        else:
            # NOTE (mristin):
            # The verification functions use
            # :py:mod:`aas_core_codegen.intermediate._types` while the built-in
            # functions are a construct of
            # :py:mod:`aas_core_codegen.intermediate.type_inference`.

            if isinstance(func_type, VerificationTypeAnnotation):
                if func_type.func.returns is not None:
                    result = convert_type_annotation(func_type.func.returns)
                else:
                    result = PrimitiveTypeAnnotation(PrimitiveType.NONE)

            elif isinstance(func_type, BuiltinFunctionTypeAnnotation):
                if func_type.func.kind is BuiltinFunctionKind.SET:
                    self.errors.append(
                        Error(
                            node.original_node,
                            "We support ``set()`` only as the value assigned to "
                            "a variable declared as a set, *e.g.*, "
                            "``x: Set[str] = set()``, since the targets need to "
                            "know the type of the items of the new set.",
                        )
                    )
                    failed = True

                elif func_type.func.returns is not None:
                    result = func_type.func.returns
                else:
                    result = PrimitiveTypeAnnotation(PrimitiveType.NONE)

            elif isinstance(
                func_type,
                (
                    PrimitiveTypeAnnotation,
                    OurTypeAnnotation,
                    BuiltinMethodTypeAnnotation,
                    MethodTypeAnnotation,
                    ListTypeAnnotation,
                    SetTypeAnnotation,
                    TupleTypeAnnotation,
                    OptionalTypeAnnotation,
                    EnumerationAsTypeTypeAnnotation,
                    JsonValueTypeAnnotation,
                    JsonArrayTypeAnnotation,
                    JsonObjectTypeAnnotation,
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

        # NOTE (mristin):
        # Recurse to track the type of arguments. Even if we failed before, we want to
        # catch the errors in the arguments for better developer experience.
        #
        # Mind that we are sloppy here. Theoretically, we could check that arguments in
        # the call are assignable to the arguments in the function definition and catch
        # errors in the meta-model at this point. However, we prioritize other features
        # and leave this check unimplemented for now.

        arg_types = []  # type: List[Optional[TypeAnnotationUnion]]
        for arg in node.args:
            arg_type = self.transform(arg)
            if arg_type is None:
                failed = True

            arg_types.append(arg_type)

        if failed:
            return None

        if isinstance(
            func_type, VerificationTypeAnnotation
        ) and not self._check_arguments(
            args=node.args,
            arguments=func_type.func.arguments,
            what=f"the verification function {func_type.func.name!r}",
        ):
            return None

        # NOTE (mristin):
        # The length of a JSON-able value is not a question we can answer: its
        # shape is known only at run time, and a boolean and a number have no
        # length at all. This mirrors :py:meth:`_Inferrer.transform_index`,
        # which refuses to index into a JSON-able value for the very same
        # reason. A JSON-able array and a JSON-able object, in contrast, are
        # known to be a sequence and a mapping, respectively.
        if (
            isinstance(func_type, BuiltinFunctionTypeAnnotation)
            and func_type.func.kind is BuiltinFunctionKind.LEN
            and len(arg_types) == 1
        ):
            arg_type = arg_types[0]
            assert arg_type is not None

            if isinstance(arg_type, OptionalTypeAnnotation):
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the argument of ``len`` to be a non-None, "
                        f"but got: {arg_type}. Please check for ``is not None`` "
                        f"first.",
                    )
                )
                return None

            if isinstance(arg_type, JsonValueTypeAnnotation):
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        "JSONValue represents an arbitrary, open JSON-able value "
                        "whose shape can not be determined statically, so we treat "
                        "it analogous to Unknown -- computing its length is not "
                        "supported. Only a JSONArray and a JSONObject have "
                        "a length which we can compute.",
                    )
                )
                return None

            # NOTE (mristin):
            # These are the types whose length all the transpilers know how to
            # compute. The constrained primitives behave like their constrainees.
            # The length of a tuple is fixed by its type, so the transpilers
            # write it as a constant.
            if not (
                try_primitive_type(arg_type)
                in (PrimitiveType.STR, PrimitiveType.BYTEARRAY)
                or isinstance(
                    arg_type,
                    (
                        ListTypeAnnotation,
                        SetTypeAnnotation,
                        TupleTypeAnnotation,
                        JsonArrayTypeAnnotation,
                        JsonObjectTypeAnnotation,
                    ),
                )
            ):
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the argument of ``len`` to be a string, "
                        f"a bytearray, a list, a set, a tuple, a JSONArray or "
                        f"a JSONObject, since we know how to compute the length "
                        f"only of these types in all the target languages, "
                        f"but got: {arg_type}",
                    )
                )
                return None

        if (
            isinstance(func_type, BuiltinFunctionTypeAnnotation)
            and func_type.func.kind is BuiltinFunctionKind.ABS
            and len(arg_types) == 1
        ):
            arg_type = arg_types[0]
            assert arg_type is not None

            a_type = self._check_signed_number_operand(
                operand=node.args[0],
                operand_type=arg_type,
                operation_name_with_capital_the="The absolute value",
            )
            if a_type is None:
                return None

            # NOTE (mristin):
            # The type of the result depends on the argument.
            result = PrimitiveTypeAnnotation(a_type=a_type)

        if (
            isinstance(func_type, BuiltinFunctionTypeAnnotation)
            and func_type.func.kind is BuiltinFunctionKind.INT
            and len(arg_types) == 1
        ):
            arg_type = arg_types[0]
            assert arg_type is not None

            # NOTE (mristin):
            # We parse only strings. The conversions of the other types, such as
            # truncating a floating-point number, differ among the target languages,
            # and we have no use case for them at the moment.
            if try_primitive_type(arg_type) is not PrimitiveType.STR:
                self.errors.append(
                    Error(
                        node.args[0].original_node,
                        f"Expected the argument of ``int`` to be a non-None string, "
                        f"since we support only parsing the integers from "
                        f"the strings, but got: {arg_type}",
                    )
                )
                return None

        assert result is not None

        result = self._strip_optional_if_non_null(node=node, type_annotation=result)
        self.type_map[node] = result
        return result

    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Optional["TypeAnnotationUnion"]:
        result: TypeAnnotationUnion

        if node.value is None:
            result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        elif isinstance(node.value, bool):
            result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        elif isinstance(node.value, int):
            result = PrimitiveTypeAnnotation(PrimitiveType.INT)
        elif isinstance(node.value, float):
            result = PrimitiveTypeAnnotation(PrimitiveType.FLOAT)
        elif isinstance(node.value, str):
            result = PrimitiveTypeAnnotation(PrimitiveType.STR)
        else:
            assert_never(node.value)

        self.type_map[node] = result
        return result

    def _nullness_check_over_json_index_is_refused(
        self, value: parse_tree.Node, check: str
    ) -> bool:
        """
        Record an error if the ``check`` is applied to an index into a JSON-able value.

        The ``value`` must have been already transformed, as we need the type of
        its collection.
        """
        if not isinstance(value, parse_tree.Index):
            return False

        if not isinstance(
            beneath_optional(self.type_map[value.collection]),
            (JsonArrayTypeAnnotation, JsonObjectTypeAnnotation),
        ):
            return False

        self.errors.append(
            Error(
                value.original_node,
                f"A JSON-able value is never null, so {check} over an index into "
                f"a JSON-able object or array really asks whether the key or "
                f"the position is there. Please ask that directly, as "
                f"``<key> in <object>`` and as ``len(<array>) > <position>``, "
                f"which strips the optionality of the index in the guarded "
                f"expression.",
            )
        )
        return True

    def transform_is_none(
        self, node: parse_tree.IsNone
    ) -> Optional["TypeAnnotationUnion"]:
        value_type = self.transform(node.value)

        # NOTE (mristin):
        # Something went wrong if we could not infer the type of the ``value``.
        if value_type is None:
            return None

        if self._nullness_check_over_json_index_is_refused(node.value, "``is None``"):
            return None

        if not isinstance(value_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.value.original_node,
                    f"Expected the value to be of an optional type for "
                    f"a nullness check (``is None``), "
                    f"but got {value_type}",
                )
            )
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_is_not_none(
        self, node: parse_tree.IsNotNone
    ) -> Optional["TypeAnnotationUnion"]:
        value_type = self.transform(node.value)

        # NOTE (mristin):
        # Something went wrong if we could not infer the type of the ``value``.
        if value_type is None:
            return None

        if self._nullness_check_over_json_index_is_refused(
            node.value, "``is not None``"
        ):
            return None

        if not isinstance(value_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.value.original_node,
                    f"Expected the value to be of an optional type "
                    f"for a non-nullness check (``is not None``), "
                    f"but got {value_type}",
                )
            )
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_not(self, node: parse_tree.Not) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``operand`` even though we know the type
        # in advance

        operand_type = self.transform(node.operand)

        if operand_type is None:
            return None

        if isinstance(operand_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.operand.original_node,
                    f"Expected the operand to be a non-None, "
                    f"but got: {operand_type}",
                )
            )
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_name(self, node: parse_tree.Name) -> Optional["TypeAnnotationUnion"]:
        type_in_env = self._environment.find(node.identifier)
        if type_in_env is None:
            if any(
                node.identifier in types
                for types in self._types_of_variables_in_closed_scopes
            ):
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The variable {node.identifier!r} has been defined in "
                        f"a nested block before, such as a for-loop or a branch of "
                        f"a switch or of an if-statement, and is not visible here. "
                        f"While Python keeps the variable after the block, the other "
                        f"targets scope it to the block. Please define the variable "
                        f"before the block.",
                    )
                )
                return None

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
        # NOTE (mristin):
        # We need to iterate and recurse into ``values`` to fill the ``type_map``.
        # In the process, we have to consider the non-nullness and how it applies
        # to the remainder of the conjunction.

        # NOTE (mristin):
        # We are very lax here and ignore the fact that calls to methods and functions
        # can actually alter the value assumed to be non-null, and actually violate
        # its non-nullness by setting it to null.
        #
        # This lack of conservatism works for now. If the bugs related to nullness
        # start to surface, we should re-think our approach here.

        success = True

        with contextlib.ExitStack() as exit_stack:
            for value_node in node.values:
                value_type = self.transform(value_node)
                if value_type is None:
                    return None

                if isinstance(value_type, OptionalTypeAnnotation):
                    self.errors.append(
                        Error(
                            value_node.original_node,
                            f"Expected the value to be a non-None, "
                            f"but got: {value_type}",
                        )
                    )
                    success = False

                self._assume(self._implied_facts(value_node), exit_stack)

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_or(self, node: parse_tree.Or) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance

        success = True

        with contextlib.ExitStack() as exit_stack:
            for value_node in node.values:
                value_type = self.transform(value_node)
                if value_type is None:
                    return None

                if isinstance(value_type, OptionalTypeAnnotation):
                    self.errors.append(
                        Error(
                            value_node.original_node,
                            f"Expected the value to be a non-None, "
                            f"but got: {value_type}",
                        )
                    )
                    success = False

                # NOTE (mristin):
                # The remainder of the disjunction is evaluated only if the value
                # does not hold. For example, ``x`` is non-null in the remainder of
                # ``x is None or ...``, and an instance of ``C`` in the remainder of
                # ``not isinstance(x, C) or ...``.
                if success:
                    self._assume(
                        self._implied_facts_of_negation(value_node), exit_stack
                    )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    @staticmethod
    def _binary_operation_name_with_capital_the(
        node: Union[parse_tree.Add, parse_tree.Sub, parse_tree.Mod]
    ) -> str:
        if isinstance(node, parse_tree.Add):
            return "The addition"

        elif isinstance(node, parse_tree.Sub):
            return "The subtraction"

        elif isinstance(node, parse_tree.Mod):
            return "The modulo operation"

        else:
            assert_never(node)

    def _transform_binary_arithmetic(
        self, node: Union[parse_tree.Add, parse_tree.Sub, parse_tree.Mod]
    ) -> Optional["TypeAnnotationUnion"]:
        left_type = self.transform(node.left)
        if left_type is None:
            return None

        right_type = self.transform(node.right)
        if right_type is None:
            return None

        success = True

        if isinstance(left_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.left.original_node,
                    f"Expected the left operand to be a non-None, "
                    f"but got: {left_type}",
                )
            )
            success = False

        if isinstance(right_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.right.original_node,
                    f"Expected the right operand to be a non-None, "
                    f"but got: {right_type}",
                )
            )
            success = False

        if not success:
            return None

        # NOTE (mristin):
        # We do not support the modulo on floating-point numbers as the native
        # operators and functions differ considerably among the target languages,
        # and we have no use case for it at the moment.
        allowed_operand_types: Tuple[PrimitiveType, ...]
        allowed_operand_description: str
        if isinstance(node, parse_tree.Mod):
            allowed_operand_types = (PrimitiveType.INT, PrimitiveType.LENGTH)
            allowed_operand_description = "integer numbers"
        else:
            allowed_operand_types = (
                PrimitiveType.INT,
                PrimitiveType.FLOAT,
                PrimitiveType.LENGTH,
            )
            allowed_operand_description = "integer and floating-point numbers"

        # NOTE (mristin):
        # The constrained primitives behave like their constrainees in arithmetic.
        left_a_type = try_primitive_type(left_type)
        right_a_type = try_primitive_type(right_type)

        if left_a_type not in allowed_operand_types:
            self.errors.append(
                Error(
                    node.left.original_node,
                    f"{_Inferrer._binary_operation_name_with_capital_the(node)} is "
                    f"only defined on {allowed_operand_description}, "
                    f"but got as a left operand: {left_type}",
                )
            )
            success = False

        if right_a_type not in allowed_operand_types:
            self.errors.append(
                Error(
                    node.right.original_node,
                    f"{_Inferrer._binary_operation_name_with_capital_the(node)} is "
                    f"only defined on {allowed_operand_description}, "
                    f"but got as a right operand: {right_type}",
                )
            )
            success = False

        if not success:
            return None

        assert left_a_type is not None
        assert right_a_type is not None

        # fmt: off
        if (
            (
                left_a_type is PrimitiveType.FLOAT
                and right_a_type is not PrimitiveType.FLOAT
            ) or (
                right_a_type is PrimitiveType.FLOAT
                and left_a_type is not PrimitiveType.FLOAT
            )
        ):
            # fmt: on
            self.errors.append(
                Error(
                    node.original_node,
                    f"You can not mix floating-point and integer numbers, "
                    f"but the left operand was: {left_type}; "
                    f"and the right operand was: {right_type}"
                )
            )
            success = False

        if not success:
            return None

        # fmt: off
        result_type: PrimitiveType
        if _combines_to_length(
            left=node.left,
            left_a_type=left_a_type,
            right=node.right,
            right_a_type=right_a_type,
        ):
            result_type = PrimitiveType.LENGTH

        elif (
                left_a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
                and right_a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
        ):
            result_type = PrimitiveType.INT

        elif (
                left_a_type is PrimitiveType.FLOAT
                and right_a_type is PrimitiveType.FLOAT
        ):
            result_type = PrimitiveType.FLOAT
        else:
            raise AssertionError(
                f"Unhandled execution path: {left_type=}, {right_type=}"
            )
        # fmt: on

        result = PrimitiveTypeAnnotation(a_type=result_type)
        self.type_map[node] = result
        return result

    def transform_add(self, node: parse_tree.Add) -> Optional["TypeAnnotationUnion"]:
        return self._transform_binary_arithmetic(node)

    def transform_sub(self, node: parse_tree.Sub) -> Optional["TypeAnnotationUnion"]:
        return self._transform_binary_arithmetic(node)

    def transform_mod(self, node: parse_tree.Mod) -> Optional["TypeAnnotationUnion"]:
        return self._transform_binary_arithmetic(node)

    def transform_neg(self, node: parse_tree.Neg) -> Optional["TypeAnnotationUnion"]:
        operand_type = self.transform(node.operand)
        if operand_type is None:
            return None

        a_type = self._check_signed_number_operand(
            operand=node.operand,
            operand_type=operand_type,
            operation_name_with_capital_the="The arithmetic negation",
        )
        if a_type is None:
            return None

        result = PrimitiveTypeAnnotation(a_type=a_type)
        self.type_map[node] = result
        return result

    def transform_formatted_value(
        self, node: parse_tree.FormattedValue
    ) -> Optional["TypeAnnotationUnion"]:
        value_type = self.transform(node.value)
        if value_type is None:
            return None

        if isinstance(value_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.value.original_node,
                    f"Expected the value to be a non-None, " f"but got: {value_type}",
                )
            )
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

        if isinstance(iter_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.iteration.original_node,
                    f"Expected the collection which we iterate over to be a non-None, "
                    f"but got: {iter_type}",
                )
            )
            return None

        # NOTE (mristin):
        # The order of the items in a set differs among the targets. The meta-model
        # has to make sure that the result does not depend on it.
        if not isinstance(iter_type, (ListTypeAnnotation, SetTypeAnnotation)):
            self.errors.append(
                Error(
                    node.iteration.original_node,
                    f"Expected an iteration over a list or a set, "
                    f"but got: {iter_type}",
                )
            )
            return None

        loop_variable_type = iter_type.items

        self.type_map[node.variable] = loop_variable_type

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_for_range(
        self, node: parse_tree.ForRange
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

        start_type = self.transform(node.start)
        if start_type is None:
            return None

        end_type = self.transform(node.end)
        if end_type is None:
            return None

        success = True

        if isinstance(start_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.start.original_node,
                    f"Expected the start to be a non-None, " f"but got: {start_type}",
                )
            )
            success = False

        if isinstance(end_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.end.original_node,
                    f"Expected the end to be a non-None, " f"but got: {end_type}",
                )
            )
            success = False

        if not success:
            return None

        if not (
            isinstance(start_type, PrimitiveTypeAnnotation)
            and start_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
        ):
            self.errors.append(
                Error(
                    node.start.original_node,
                    f"Expected the start of a range to be an integer, "
                    f"but got: {start_type}",
                )
            )
            return None

        if not (
            isinstance(end_type, PrimitiveTypeAnnotation)
            and end_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
        ):
            self.errors.append(
                Error(
                    node.end.original_node,
                    f"Expected the end of a range to be an integer, "
                    f"but got: {end_type}",
                )
            )
            return None

        # NOTE (mristin):
        # The loop variable is a length only if both bounds combine to a length,
        # *e.g.*, ``range(0, len(xs))``. Otherwise, it is an integer, so that
        # the bounds which are integers need not be narrowed.
        loop_variable_type = PrimitiveTypeAnnotation(
            a_type=(
                PrimitiveType.LENGTH
                if _combines_to_length(
                    left=node.start,
                    left_a_type=start_type.a_type,
                    right=node.end,
                    right_a_type=end_type.a_type,
                )
                else PrimitiveType.INT
            )
        )

        self.type_map[node.variable] = loop_variable_type

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def _transform_any_or_all(
        self, node: Union[parse_tree.Any, parse_tree.All]
    ) -> Optional["TypeAnnotationUnion"]:
        a_type = self.transform(node.generator)
        if a_type is None:
            return None

        loop_variable_type = self.type_map[node.generator.variable]

        if (
            isinstance(node.generator, parse_tree.ForEach)
            and _can_be_mutated(loop_variable_type)
            and self._read_only_reason(node.generator.iteration) is None
        ):
            self._mutable_name_set.add(node.generator.variable.identifier)

        try:
            self._environment.set(
                identifier=node.generator.variable.identifier,
                type_annotation=loop_variable_type,
            )

            a_type = self.transform(node.condition)
            if a_type is None:
                return None

            if (
                not isinstance(a_type, PrimitiveTypeAnnotation)
                or a_type.a_type is not PrimitiveType.BOOL
            ):
                self.errors.append(
                    Error(
                        node.condition.original_node,
                        f"Expected the condition to be a boolean, "
                        f"but got: {a_type}",
                    )
                )
                return None

        finally:
            self._environment.remove(identifier=node.generator.variable.identifier)
            self._mutable_name_set.discard(node.generator.variable.identifier)

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_any(self, node: parse_tree.Any) -> Optional["TypeAnnotationUnion"]:
        return self._transform_any_or_all(node)

    def transform_all(self, node: parse_tree.All) -> Optional["TypeAnnotationUnion"]:
        return self._transform_any_or_all(node)

    def _check_consistent_type_of_definition(
        self, variable: parse_tree.Name, type_annotation: "TypeAnnotationUnion"
    ) -> bool:
        """
        Check that the ``variable`` is always defined with the same type.

        Python has only function-level scopes, so the static type checkers such as
        mypy refuse two definitions of the same name with different types, even if
        they live in sibling blocks in the target languages, *e.g.*, the loop
        variables of two sibling for-loops.

        A previous definition of the same name can only live in a closed scope.
        If it were still visible, the new definition would be either
        an assignment, which we check against the type of the variable, or
        a loop variable shadowing it, which we refuse.

        Record the error, if any, and return ``True`` if the check passed.
        """
        previous_type = None  # type: Optional[TypeAnnotationUnion]
        for types in reversed(self._types_of_variables_in_closed_scopes):
            previous_type = types.get(variable.identifier, None)
            if previous_type is not None:
                break

        if previous_type is None:
            return True

        # NOTE (mristin):
        # We compare the string representations, since the type annotations do not
        # implement the equality, and the string representations are unique.
        if str(previous_type) != str(type_annotation):
            self.errors.append(
                Error(
                    variable.original_node,
                    f"The variable {variable.identifier!r} has been already "
                    f"defined before with the type {previous_type}, but now we "
                    f"inferred its type to be {type_annotation}. Python has only "
                    f"function-level scopes, and the static type checkers such as "
                    f"mypy refuse such re-definitions. Please use a different name.",
                )
            )
            return False

        return True

    def _transform_as_target(
        self, node: Union[parse_tree.Member, parse_tree.Index]
    ) -> Optional["TypeAnnotationUnion"]:
        """
        Transform the ``node`` as the target of an assignment.

        We infer the declared type of the target instead of its narrowed type, since
        the assignment can set any value of the declared type. For example,
        the following assignment is valid, though ``self.x`` is known to be
        non-null before it:

        .. code-block:: python

            if self.x is None:
                return

            # Passes: the target ``self.x`` is ``Optional[str]``, not ``str``,
            # so that we can assign the optional ``y``.
            self.x = y

            # Fails: the assignment removed "self.x is non-null".
            return len(self.x)

        The transpilers rely on the declared type of the target as well, *e.g.*, to
        decide whether to de-reference it.

        We only ignore the facts about the target itself. The facts about its
        parts still apply, *e.g.*, ``self.parent`` is still narrowed in
        ``self.parent.x = y`` after ``isinstance(self.parent, Child_a)``.
        """
        facts = self._facts
        canonical_repr = self._representation_map[node]

        self._facts = [fact for fact in facts if fact.key != canonical_repr]
        try:
            return self.transform(node)
        finally:
            self._facts = facts

    def _resolve_annotation(
        self, node: parse_tree.Expression, read_only: bool
    ) -> Optional["TypeAnnotationUnion"]:
        """
        Resolve the type annotation of a variable declaration.

        We resolve the primitive types, our types, including the named unions,
        and ``Optional``, ``List``, ``Sequence``, ``Set`` and ``Tuple`` of them. We refuse
        inline ``Union[...]``, as the targets need a named type to represent a union.

        If ``read_only`` is set, the annotation is beneath ``Final[...]``, and we
        require the read-only spelling of the containers, ``Sequence[...]`` and
        ``AbstractSet[...]``, so that mypy also refuses to mutate them.

        Record the error, if any, and return ``None`` on failure.
        """
        if isinstance(node, parse_tree.Constant) and isinstance(node.value, str):
            # NOTE (mristin):
            # We resolve the forward references such as ``"Parent"`` just as
            # the names themselves.
            name = Identifier(node.value)
        elif isinstance(node, parse_tree.Name):
            name = node.identifier
        elif isinstance(node, parse_tree.Index) and isinstance(
            node.collection, parse_tree.Name
        ):
            generic = node.collection.identifier

            if generic == "Final":
                self.errors.append(
                    Error(
                        node.original_node,
                        "We support ``Final[...]`` only as the outermost type "
                        "annotation of a variable, *e.g.*, "
                        "``x: Final[Optional[int]] = ...``.",
                    )
                )
                return None

            if generic == "Union":
                self.errors.append(
                    Error(
                        node.original_node,
                        "We do not support inline unions such as ``Union[A, B]`` "
                        "in the type annotations of the variables. The targets "
                        "need a named type to represent a union, such as "
                        "a variant in C++ or a wrapper class in C#, so only "
                        "the named unions of the meta-model are accepted. Please "
                        "define a named union at the module level, *e.g.*, "
                        "``Some_union = Union[A, B]``, and annotate "
                        "the variable with it, *e.g.*, ``x: Some_union = ...``. "
                        "For an optional value, please use ``Optional[...]``.",
                    )
                )
                return None

            if generic == "Optional":
                value = self._resolve_annotation(node.index, read_only)
                if value is None:
                    return None

                if isinstance(value, OptionalTypeAnnotation):
                    self.errors.append(
                        Error(
                            node.original_node,
                            f"We do not support nested optionals, "
                            f"but got: Optional[{value}]",
                        )
                    )
                    return None

                return OptionalTypeAnnotation(value=value)

            # NOTE (mristin):
            # The ``Sequence`` marks a read-only list in the arguments. The variables
            # are read-only if their values are, so both denote the same list here.
            if read_only and generic in ("List", "Set"):
                read_only_generic = "Sequence" if generic == "List" else "AbstractSet"
                self.errors.append(
                    Error(
                        node.original_node,
                        f"A variable declared as ``Final[...]`` is immutable, "
                        f"but ``{generic}[...]`` is mutable. Please declare it "
                        f"as ``{read_only_generic}[...]`` instead.",
                    )
                )
                return None

            if generic in ("List", "Sequence"):
                items = self._resolve_annotation(node.index, read_only)
                if items is None:
                    return None

                return ListTypeAnnotation(items=items)

            if generic == "AbstractSet" and not read_only:
                self.errors.append(
                    Error(
                        node.original_node,
                        "We do not support declaring a variable as "
                        "an ``AbstractSet[...]``, since it would share a set "
                        "with another variable, and the targets disagree on "
                        "that: C++ copies the set, while the other targets share "
                        "it. Please declare a new set as ``Set[...]`` and "
                        "initialize it with ``set()``.",
                    )
                )
                return None

            if generic in ("Set", "AbstractSet"):
                set_items = self._resolve_annotation(node.index, read_only)
                if set_items is None:
                    return None

                refusal = refusal_of_set_items(set_items)
                if refusal is not None:
                    self.errors.append(Error(node.original_node, refusal))
                    return None

                return SetTypeAnnotation(items=set_items)

            if generic == "Tuple":
                item_nodes = (
                    node.index.values
                    if isinstance(node.index, parse_tree.Tuple)
                    else [node.index]
                )

                tuple_items = []  # type: List[TypeAnnotationUnion]
                for item_node in item_nodes:
                    item = self._resolve_annotation(item_node, read_only)
                    if item is None:
                        return None

                    tuple_items.append(item)

                return TupleTypeAnnotation(items=tuple_items)

            self.errors.append(
                Error(
                    node.original_node,
                    f"We support only ``Optional[...]``, ``List[...]``, "
                    f"``Sequence[...]``, ``Set[...]`` and ``Tuple[...]`` as "
                    f"generic types in the type annotations of the variables, "
                    f"but got: {generic}[...]",
                )
            )
            return None
        else:
            self.errors.append(
                Error(
                    node.original_node,
                    f"We support only the primitive types, our types, and "
                    f"``Optional[...]``, ``List[...]``, ``Sequence[...]``, "
                    f"``Set[...]`` and ``Tuple[...]`` of them in the type "
                    f"annotations of the variables, but got: "
                    f"{ast.unparse(node.original_node)}",
                )
            )
            return None

        primitive_type = _types.STR_TO_PRIMITIVE_TYPE.get(name, None)
        if primitive_type is not None:
            return PrimitiveTypeAnnotation(a_type=PRIMITIVE_TYPE_MAP[primitive_type])

        our_type = self._environment.find_our_type(name)
        if our_type is None:
            self.errors.append(
                Error(
                    node.original_node,
                    f"The type {name!r} in the type annotation is not defined.",
                )
            )
            return None

        return OurTypeAnnotation(our_type=our_type)

    def _transform_new_set(
        self,
        node: parse_tree.FunctionCall,
        target_type: Optional["TypeAnnotationUnion"],
    ) -> Optional["TypeAnnotationUnion"]:
        """
        Infer the type of ``set()`` from the ``target_type`` it is assigned to.

        Python infers the type of the items from the declaration, *e.g.*,
        ``x: Set[str] = set()``, and so do we.
        """
        if self.transform(node.name) is None:
            return None

        if len(node.args) > 0:
            self.errors.append(
                Error(
                    node.original_node,
                    f"We support only ``set()`` without arguments to create "
                    f"a new set, but got {len(node.args)} argument(s). Please "
                    f"add the items one by one with ``add``.",
                )
            )
            return None

        target_type_beneath = (
            beneath_optional(target_type) if target_type is not None else None
        )
        if not isinstance(target_type_beneath, SetTypeAnnotation):
            self.errors.append(
                Error(
                    node.original_node,
                    "We support ``set()`` only as the value assigned to "
                    "a variable declared as a set, *e.g.*, "
                    "``x: Set[str] = set()``, since the targets need to "
                    "know the type of the items of the new set"
                    + (
                        "."
                        if target_type is None
                        else f", but the target is of type {target_type}."
                    ),
                )
            )
            return None

        self.type_map[node] = target_type_beneath
        return target_type_beneath

    def transform_assignment(
        self, node: parse_tree.Assignment
    ) -> Optional["TypeAnnotationUnion"]:
        is_new_variable = False

        is_final = node.annotation is not None and is_final_annotation(node.annotation)

        target_type: Optional[TypeAnnotationUnion]

        if isinstance(node.target, parse_tree.Name):
            if node.target.identifier in self._loop_variable_set:
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The loop variable {node.target.identifier!r} can not be "
                        f"assigned to in the body of the for-loop. Python does not "
                        f"change the iteration on such an assignment, while "
                        f"the targets would skip or repeat the iterations over "
                        f"a range, or refuse to compile the assignment to "
                        f"a read-only loop variable. Please use a different "
                        f"variable.",
                    )
                )
                return None

            target_type = self._environment.find(node.target.identifier)

            if node.annotation is not None:
                if target_type is not None:
                    self.errors.append(
                        Error(
                            node.original_node,
                            f"The variable {node.target.identifier!r} has been "
                            f"already defined before with the type {target_type}, "
                            f"so it can not be declared again with a type "
                            f"annotation. Please assign to it without "
                            f"the annotation, or use a different name.",
                        )
                    )
                    return None

                if (
                    isinstance(node.annotation, parse_tree.Name)
                    and node.annotation.identifier == "Final"
                ):
                    self.errors.append(
                        Error(
                            node.annotation.original_node,
                            f"Please specify the type of the variable "
                            f"{node.target.identifier!r} as a subscript of "
                            f"``Final[...]``, *e.g.*, "
                            f"``{node.target.identifier}: Final[int] = ...``, "
                            f"since the targets need to declare it with the type.",
                        )
                    )
                    return None

                if is_final and len(self._loop_variable_set) > 0:
                    self.errors.append(
                        Error(
                            node.original_node,
                            f"The variable {node.target.identifier!r} can not be "
                            f"declared as ``Final[...]`` in the body of a for-loop, "
                            f"as mypy refuses it. Please declare it without "
                            f"``Final[...]``, or move it out of the loop.",
                        )
                    )
                    return None

                # NOTE (mristin):
                # The declared type is the type of the variable, while the type of
                # the value only needs to be assignable to it. For example,
                # ``x: Optional[Parent] = None`` declares ``x`` as
                # ``Optional[Parent]``, so that we can re-assign it later.
                if is_final:
                    assert isinstance(node.annotation, parse_tree.Index)
                    target_type = self._resolve_annotation(
                        node.annotation.index, read_only=True
                    )
                else:
                    target_type = self._resolve_annotation(
                        node.annotation, read_only=False
                    )

                if target_type is None:
                    return None

                is_new_variable = True

            elif target_type is None:
                is_new_variable = True

            elif node.target.identifier in self._final_name_set:
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The variable {node.target.identifier!r} is declared "
                        f"as ``Final[...]``, so it can not be re-assigned.",
                    )
                )
                return None
        elif isinstance(node.target, parse_tree.Member):
            target_type = self._transform_as_target(node.target)
            if target_type is None:
                return None

            instance_type = self.type_map[node.target.instance]

            message = None  # type: Optional[str]
            if isinstance(instance_type, EnumerationAsTypeTypeAnnotation):
                message = (
                    f"The enumeration literal "
                    f"{instance_type.enumeration.name}.{node.target.name} "
                    f"can not be assigned to."
                )
            elif isinstance(target_type, BuiltinMethodTypeAnnotation):
                message = (
                    f"The method {node.target.name!r} of strings "
                    f"can not be assigned to."
                )
            elif isinstance(target_type, MethodTypeAnnotation):
                message = (
                    f"The method {node.target.name!r} of {instance_type} "
                    f"can not be assigned to."
                )
            elif not (
                isinstance(instance_type, OurTypeAnnotation)
                and isinstance(instance_type.our_type, _types.Class)
                and node.target.name in instance_type.our_type.properties_by_name
            ):
                message = (
                    f"Only a property of a class can be assigned to, "
                    f"but the member {node.target.name!r} of {instance_type} "
                    f"is not a property."
                )

            if message is not None:
                self.errors.append(Error(node.target.original_node, message))
                return None

        elif isinstance(node.target, parse_tree.Index):
            target_type = self._transform_as_target(node.target)
            if target_type is None:
                return None

            collection_type = self.type_map[node.target.collection]

            message = None
            if isinstance(collection_type, TupleTypeAnnotation):
                message = (
                    f"Tuples are immutable in Python, so the item "
                    f"of {collection_type} can not be assigned to."
                )
            elif isinstance(
                collection_type,
                (
                    JsonValueTypeAnnotation,
                    JsonArrayTypeAnnotation,
                    JsonObjectTypeAnnotation,
                ),
            ):
                message = (
                    f"We do not support mutating JSON-able values, so the item "
                    f"of {collection_type} can not be assigned to."
                )
            elif not isinstance(collection_type, ListTypeAnnotation):
                message = (
                    f"Only an item of a list can be assigned to, but "
                    f"the collection is inferred to be {collection_type}."
                )

            if message is not None:
                self.errors.append(Error(node.target.original_node, message))
                return None

        else:
            self.errors.append(
                Error(
                    node.target.original_node,
                    f"Expected the target of an assignment to be a variable, "
                    f"a property of a class or an item of a list, "
                    f"but got: {type(node.target).__name__}",
                )
            )
            return None

        if _is_set_call(node.value):
            assert isinstance(node.value, parse_tree.FunctionCall)
            value_type = self._transform_new_set(
                node=node.value, target_type=target_type
            )
        else:
            value_type = self.transform(node.value)

        if (not is_new_variable and target_type is None) or (value_type is None):
            return None

        if (
            is_new_variable
            and target_type is None
            and try_primitive_type(value_type) is PrimitiveType.NONE
        ):
            assert isinstance(node.target, parse_tree.Name)
            self.errors.append(
                Error(
                    node.original_node,
                    f"We can not infer the type of the variable "
                    f"{node.target.identifier!r} from ``None``. Please declare "
                    f"the variable with a type annotation, *e.g.*, "
                    f"``{node.target.identifier}: Optional[...] = None``.",
                )
            )
            return None

        # NOTE (mristin):
        # The type of a new variable is its declared type, if it has been annotated,
        # and the type of the assigned value otherwise.
        variable_type = target_type if target_type is not None else value_type

        if is_new_variable:
            assert isinstance(node.target, parse_tree.Name)
            if node.target.identifier in self._types_of_variables_in_closed_scopes[-1]:
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The variable {node.target.identifier!r} has been already "
                        f"defined in a nested block before, such as a for-loop or "
                        f"a branch of a switch or of an if-statement. In Python, both "
                        f"definitions denote the same variable, while they denote "
                        f"two different variables in the target languages with "
                        f"block scopes, and some target languages, such as C#, "
                        f"refuse such re-declarations altogether. Please use "
                        f"a different name.",
                    )
                )

                # NOTE (mristin):
                # We still define the variable so that the subsequent statements
                # do not report it as unknown, which would only confuse the user.
                self._environment.set(
                    identifier=node.target.identifier, type_annotation=variable_type
                )
                return None

        # NOTE (mristin):
        # We wrap a class instance into a named union in the targets which represent
        # the named unions as wrappers or variants, such as C# or C++. We can not wrap
        # a null, so we refuse to assign an optional instance to a named union.
        target_type_beneath = (
            beneath_optional(target_type) if target_type is not None else None
        )
        if (
            isinstance(target_type_beneath, OurTypeAnnotation)
            and isinstance(target_type_beneath.our_type, _types.NamedUnion)
            and isinstance(value_type, OptionalTypeAnnotation)
            and isinstance(value_type.value, OurTypeAnnotation)
            and isinstance(value_type.value.our_type, _types.ClassUnionAsTuple)
        ):
            self.errors.append(
                Error(
                    node.value.original_node,
                    f"The value assigned to the named union "
                    f"{target_type_beneath.our_type.name!r} might be None, "
                    f"since it is inferred to be {value_type}. We need to wrap "
                    f"the instance into the named union in some targets, "
                    f"which we can not do for a None. Please check first that "
                    f"the value is not None, *e.g.*, with "
                    f"``if {self._representation_map[node.value]} is not None:``.",
                )
            )
            is_refused = True

        elif target_type is not None and not _assignable(
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
            is_refused = True

        else:
            is_refused = False

        if is_refused:
            if is_new_variable:
                assert isinstance(node.target, parse_tree.Name)

                # NOTE (mristin):
                # We still define the declared variable so that the subsequent
                # statements do not report it as unknown, which would only confuse
                # the user.
                self._environment.set(
                    identifier=node.target.identifier, type_annotation=variable_type
                )

            return None

        if isinstance(node.target, (parse_tree.Member, parse_tree.Index)):
            receiver = (
                node.target.instance
                if isinstance(node.target, parse_tree.Member)
                else node.target.collection
            )

            what = (
                f"the property {node.target.name!r}"
                if isinstance(node.target, parse_tree.Member)
                else "an item of the list"
            )

            reason = self._read_only_reason(receiver)
            if reason is not None:
                self.errors.append(
                    Error(
                        node.target.original_node,
                        f"We can not assign to {what} "
                        f"of {self._representation_map[receiver]}, since {reason}.",
                    )
                )
                return None

            # NOTE (mristin):
            # Python shares a stored list, while C++ copies it, as its lists are
            # values. We can not faithfully transpile the sharing to C++, so we
            # require an explicit copy of every stored list, in all the targets.
            if _holds_list(value_type) and not self._is_copy_of_lists(node.value):
                self.errors.append(
                    Error(
                        node.value.original_node,
                        f"The value assigned to {what} "
                        f"of {self._representation_map[receiver]} holds a list, "
                        f"which Python would share, but C++ would copy. We can not "
                        f"transpile the sharing to C++, so please assign an explicit "
                        f"copy of the list, *e.g.*, "
                        f"``{self._representation_map[node.value]}[:]``.",
                    )
                )
                return None

            # NOTE (mristin):
            # Storing a value in a mutable place makes the value mutable through
            # the place, so the value needs to be mutable itself. Otherwise,
            # a read-only argument could be mutated through the alias.
            if _can_be_mutated(value_type):
                reason = self._read_only_reason(node.value)
                if reason is not None:
                    self.errors.append(
                        Error(
                            node.value.original_node,
                            f"The value assigned to {what} "
                            f"of {self._representation_map[receiver]} would become "
                            f"mutable through it, so it needs to be mutable itself, "
                            f"but {reason}.",
                        )
                    )
                    return None

        elif (
            not is_new_variable
            and isinstance(node.target, parse_tree.Name)
            and node.target.identifier in self._mutable_name_set
            and _can_be_mutated(value_type)
        ):
            reason = self._read_only_reason(node.value)
            if reason is not None:
                self.errors.append(
                    Error(
                        node.original_node,
                        f"The variable {node.target.identifier!r} is mutable, "
                        f"so it can be re-assigned only a mutable value, "
                        f"but {reason}.",
                    )
                )
                return None

        if isinstance(node.target, parse_tree.Name):
            # NOTE (mristin):
            # We record the type of the variable, not narrowed by any facts, so that
            # the targets can declare the variable with it.
            self.type_map[node.target] = variable_type

        if is_new_variable:
            assert isinstance(node.target, parse_tree.Name)

            self._environment.set(
                identifier=node.target.identifier, type_annotation=variable_type
            )

            if not self._check_consistent_type_of_definition(
                variable=node.target, type_annotation=variable_type
            ):
                return None

            if is_final:
                # NOTE (mristin):
                # A final variable is read-only regardless of its value, and
                # the read-only-ness is deep, as for the read-only arguments.
                self._final_name_set.add(node.target.identifier)

            elif _can_be_mutated(variable_type):
                # NOTE (mristin):
                # An optional set declared with ``None`` is mutable, since it can
                # later be assigned only a new set, see :py:func:`_check_sets`.
                reason = (
                    None
                    if (
                        isinstance(beneath_optional(variable_type), SetTypeAnnotation)
                        and isinstance(node.value, parse_tree.Constant)
                        and node.value.value is None
                    )
                    else self._read_only_reason(node.value)
                )
                if reason is None:
                    self._mutable_name_set.add(node.target.identifier)
                else:
                    self._read_only_reason_by_name[node.target.identifier] = reason

        # region Update the facts

        # NOTE (mristin):
        # An assignment falsifies the facts about the target and about everything
        # which depends on it, and tells us new facts about the target. Please see
        # :py:class:`_Fact` for the whole model. For example:
        #
        # .. code-block:: python
        #
        #     if x is None or not isinstance(x, Child_a):
        #         return False
        #     # Facts: x is non-null, x is an instance of Child_a.
        #     # Passes.
        #     result = x.a_only > 0
        #
        #     x = parent
        #     # Facts: x is non-null, since ``parent`` is a non-optional ``Parent``;
        #     # but x is not an instance of Child_a anymore.
        #     # Passes.
        #     result = x.optional_text is None
        #     # Fails: "The member 'a_only' could not be found in the class
        #     # 'Parent'".
        #     result = x.a_only > 0
        #
        #     x = child_b
        #     # Facts: x is non-null, x is an instance of Child_b.
        #     # Passes.
        #     result = x.b_only > 0
        #
        # For the variable ``x`` of the declared type ``Optional[Parent]``, we
        # generate, *e.g.*, ``((Aas.IChildB)x).BOnly`` in C# on ``x.b_only`` after
        # the last assignment.
        #
        # A new variable has no facts yet, so there is nothing to invalidate. Its type
        # is the type of the assigned value, *e.g.*, ``y = child_b`` defines ``y`` as
        # ``Child_b``, not as ``Parent``, or the declared type.
        #
        # We deliberately do not narrow a declared variable by its initial value,
        # as mypy does not do that either. For example, ``y: Parent = child_b``
        # declares ``y`` as ``Parent``, and ``y.b_only`` is refused. Only
        # the subsequent assignments narrow the variable.
        if not is_new_variable:
            assert target_type is not None

            # NOTE (mristin):
            # We derive the new facts from the type of the value, which is itself
            # narrowed by the facts before the assignment. Therefore, we do not need
            # to keep any of the old facts about the target: if an old fact still
            # holds for the new value, the type of the value tells it as well. For
            # example, ``x = y`` keeps ``x`` non-null only if ``y`` is known to be
            # non-null.
            facts_about_value = []  # type: List[_Fact]

            # NOTE (mristin):
            # The ``None`` is not an optional value, but it is certainly not
            # a non-null either.
            if isinstance(target_type, OptionalTypeAnnotation) and not (
                isinstance(value_type, OptionalTypeAnnotation)
                or try_primitive_type(value_type) is PrimitiveType.NONE
            ):
                facts_about_value.append(self._fact_about(node.target, _NonNull()))

            target_type_beneath = beneath_optional(target_type)
            if (
                isinstance(target_type_beneath, OurTypeAnnotation)
                and isinstance(value_type, OurTypeAnnotation)
                and isinstance(value_type.our_type, _types.ClassUnionAsTuple)
                and value_type.our_type is not target_type_beneath.our_type
            ):
                facts_about_value.append(
                    self._fact_about(node.target, _Narrowing(target=value_type))
                )

            target_path, _ = _dependencies(node.target)

            self._facts = [
                fact for fact in self._facts if not _invalidates(target_path, fact)
            ] + facts_about_value

        # endregion Update the facts

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

        # NOTE (mristin):
        # We record the return type of the function on the return statement, so
        # that the targets know whether they need to unwrap or wrap an optional,
        # *e.g.*, when they return a variable narrowed down to non-null.
        self.type_map[node] = self._returns
        return self._returns

    def _transform_in_new_scope(
        self,
        statements: Sequence[parse_tree.StatementUnion],
        variables: Optional[Mapping[Identifier, "TypeAnnotationUnion"]] = None,
    ) -> bool:
        """
        Transform the ``statements`` in a new scope, and return ``True`` on success.

        The ``variables``, such as a loop variable, are defined in the new scope
        before the ``statements``.

        A scope is the region of the code where a variable is visible. Python has
        only function-level scopes, so a variable assigned in a branch of an ``if``
        stays visible after the ``if``. The target languages with C-like syntax
        (C++, C#, Java, TypeScript and Go) scope the variables to the enclosing block,
        and we generate a separate block for each branch of a switch or of
        an if-statement, and for the body of a for-loop, including its loop variable.
        Hence, we model the branches and the loop bodies as block scopes here as well:

        * The statements see the variables of the enclosing scopes, and can assign
          to them.
        * A variable newly defined in the statements is visible only in them, and
          not after the branch. For example, the following is not allowed:

          .. code-block:: python

              if kind == Kind.Something:
                  x = 1
              else:
                  x = 2

              return x > 0

        The meta-model is written in Python, but must behave the same in all
        the targets. Therefore, we refuse all the collisions of variable names where
        Python's function-level scope and the block scopes would diverge:

        * Reading a variable after the branch which defined it is refused, as
          the variable is unknown outside the branch. This also refuses reading
          a variable which has been defined only in a sibling branch.
        * Defining a variable in an enclosing scope after a branch which defined
          a variable of the same name is refused. In Python, both definitions
          would denote the same variable, while they denote two different
          variables with block scopes. Moreover, some target languages, such as
          C#, refuse such re-declarations altogether. To that end, we remember
          the names and the types (but not the variables themselves!) of
          the closed scopes in :attr:`_types_of_variables_in_closed_scopes`.
        * Assigning in a branch to a variable defined before the switch is
          an assignment to that very variable, both in Python and in the block
          scopes, so it is allowed.
        * Sibling branches can define the variables of the same name. In Python,
          they denote the same variable, but since neither of them is visible
          outside its branch, no branch can observe the value set by another
          branch, and the behavior is the same as with block scopes.
        """
        parent_environment = self._environment
        scope_environment = MutableEnvironment(parent=parent_environment)
        if variables is not None:
            for identifier, type_annotation in variables.items():
                scope_environment.set(
                    identifier=identifier, type_annotation=type_annotation
                )

        self._environment = scope_environment
        self._types_of_variables_in_closed_scopes.append(dict())

        success = True
        try:
            for stmt in statements:
                if self.transform(stmt) is None:
                    success = False
        finally:
            # NOTE (mristin):
            # We discard the environment of the scope so that its variables are not
            # visible anymore. However, we pass on the types of its variables, and
            # the types of the variables of its own closed nested scopes, to
            # the enclosing scope so that it can refuse their re-declarations and
            # their re-definitions with different types.
            types_of_variables_in_nested_scopes = (
                self._types_of_variables_in_closed_scopes.pop()
            )
            self._types_of_variables_in_closed_scopes[-1].update(
                types_of_variables_in_nested_scopes
            )
            self._types_of_variables_in_closed_scopes[-1].update(
                scope_environment.mapping
            )

            self._mutable_name_set.difference_update(scope_environment.mapping.keys())
            self._final_name_set.difference_update(scope_environment.mapping.keys())
            for identifier in scope_environment.mapping:
                self._read_only_reason_by_name.pop(identifier, None)

            # NOTE (mristin):
            # The facts about the variables of the scope must not outlive them, as
            # a sibling scope can define a different variable with the same name.
            # For example, the first ``x`` below is a ``Child_a``, but the second
            # one is merely a ``Parent``, and ``x.a_only`` must be refused:
            #
            # .. code-block:: python
            #
            #     if flag:
            #         x = parent
            #         x = child_a
            #     else:
            #         return False
            #
            #     # Without the removal, the fact "x is an instance of Child_a"
            #     # would survive here, as the if-branch is the only one to complete.
            #
            #     if not flag:
            #         x = parent
            #         # Fails: "The member 'a_only' could not be found in the class
            #         # 'Parent'".
            #         return x.a_only > 0
            #
            # We also remove the facts which use the variables of the scope in
            # an index, *e.g.*, ``items[i]`` for the loop variable ``i``.
            self._facts = [
                fact
                for fact in self._facts
                if not (
                    (
                        fact.path is not None
                        and fact.path[0] in scope_environment.mapping
                    )
                    or any(name in scope_environment.mapping for name in fact.names)
                )
            ]

            self._environment = parent_environment

        return success

    def transform_switch(
        self, node: parse_tree.Switch
    ) -> Optional["TypeAnnotationUnion"]:
        subject_type = self.transform(node.subject)
        if subject_type is None:
            return None

        if isinstance(subject_type, OptionalTypeAnnotation):
            self.errors.append(
                Error(
                    node.subject.original_node,
                    f"Expected the subject of the switch to be a non-None, "
                    f"but got: {subject_type}",
                )
            )
            return None

        enumeration = None  # type: Optional[_types.Enumeration]
        primitive_type = None  # type: Optional[PrimitiveType]

        if isinstance(subject_type, OurTypeAnnotation) and isinstance(
            subject_type.our_type, _types.Enumeration
        ):
            enumeration = subject_type.our_type
        else:
            primitive_type = try_primitive_type(subject_type)
            if primitive_type not in (PrimitiveType.STR, PrimitiveType.INT):
                self.errors.append(
                    Error(
                        node.subject.original_node,
                        f"Expected the subject of the switch to be an enumeration, "
                        f"a string or an integer, but got: {subject_type}",
                    )
                )
                return None

        success = True

        # NOTE (mristin):
        # The cases compare the subject against the constants, which tells us
        # nothing we track. However, the assignments in the cases invalidate
        # the facts, so we join the ends of the cases, analogous to
        # :py:meth:`transform_if`. Each case starts from the facts before
        # the switch, since only one case executes.
        facts_before = self._facts
        facts_at_ends = []  # type: List[List[_Fact]]

        for case in node.cases:
            for label in case.labels:
                label_type = self.transform(label)
                if label_type is None:
                    success = False
                    continue

                if enumeration is not None:
                    if not (
                        isinstance(label, parse_tree.Member)
                        and isinstance(
                            self.type_map.get(label.instance, None),
                            EnumerationAsTypeTypeAnnotation,
                        )
                        and isinstance(label_type, OurTypeAnnotation)
                        and label_type.our_type is enumeration
                    ):
                        self.errors.append(
                            Error(
                                label.original_node,
                                f"Expected the label to be a literal of "
                                f"the enumeration {enumeration.name!r}, the type of "
                                f"the subject of the switch, but got: {label_type}",
                            )
                        )
                        success = False

                else:
                    assert primitive_type is not None
                    if not (
                        isinstance(label, parse_tree.Constant)
                        and isinstance(label_type, PrimitiveTypeAnnotation)
                        and label_type.a_type is primitive_type
                    ):
                        self.errors.append(
                            Error(
                                label.original_node,
                                f"Expected the label to be "
                                f"a {primitive_type.value} literal, the type of "
                                f"the subject of the switch, but got: {label_type}",
                            )
                        )
                        success = False

            self._facts = facts_before
            if not self._transform_in_new_scope(case.body):
                success = False

            if parse_tree.can_complete_normally(case.body):
                facts_at_ends.append(self._facts)

        self._facts = facts_before
        if node.default is not None:
            if not self._transform_in_new_scope(node.default):
                success = False

            if parse_tree.can_complete_normally(node.default):
                facts_at_ends.append(self._facts)
        else:
            facts_at_ends.append(facts_before)

        self._join(facts_before, facts_at_ends)

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_for(self, node: parse_tree.For) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin):
        # The generator refuses the loop variables which shadow the variables
        # of the enclosing scopes, and sets the type of the loop variable.
        if self.transform(node.generator) is None:
            return None

        if not self._check_consistent_type_of_definition(
            variable=node.generator.variable,
            type_annotation=self.type_map[node.generator.variable],
        ):
            return None

        loop_variable = node.generator.variable.identifier

        # NOTE (mristin):
        # The generator refused the shadowing, so the loop variable can not be
        # the loop variable of an enclosing for-loop.
        assert loop_variable not in self._loop_variable_set

        # NOTE (mristin):
        # The loop variable inherits the mutability of the collection. The scope
        # removes it from the mutable variables once we leave the loop body.
        if (
            isinstance(node.generator, parse_tree.ForEach)
            and _can_be_mutated(self.type_map[node.generator.variable])
            and self._read_only_reason(node.generator.iteration) is None
        ):
            self._mutable_name_set.add(loop_variable)

        # NOTE (mristin):
        # The body of the loop can be executed many times, so the assignments in
        # the body invalidate the facts already at the start of the body. We do not
        # know the types of the assigned values yet, so we can not narrow by them.
        # For example, ``x.optional_text`` must be refused below, since the second
        # iteration sees ``x = y`` of the first one:
        #
        # .. code-block:: python
        #
        #     if x is None:
        #         return False
        #
        #     for number in numbers:
        #         # Fails: x is optional, as the previous iteration might have
        #         # executed ``x = y``.
        #         if x.optional_text is None:
        #             return False
        #
        #         x = y
        #
        # Mypy analyzes the body repeatedly until the types stabilize. Since
        # the assignments only ever remove the facts here, a single pass over
        # the assignments gives the same result.
        for stmt in node.body:
            for some_node in parse_tree.over_nodes(stmt):
                if isinstance(some_node, parse_tree.Assignment):
                    target_path, _ = _dependencies(some_node.target)
                    self._facts = [
                        fact
                        for fact in self._facts
                        if not _invalidates(target_path, fact)
                    ]

        facts_before = self._facts

        self._loop_variable_set.add(loop_variable)
        try:
            success = self._transform_in_new_scope(
                node.body,
                variables={loop_variable: self.type_map[node.generator.variable]},
            )
        finally:
            self._loop_variable_set.remove(loop_variable)

            # NOTE (mristin):
            # The body might not be executed at all, and we already removed all
            # the facts which the body could invalidate. Hence, the facts before
            # the body are exactly the facts after the loop. We discard the facts
            # gained in the body, since they do not hold if the body has not been
            # executed, or if we exited it early. For example, ``x`` is non-null at
            # the end of the body below, but not after the loop:
            #
            # .. code-block:: python
            #
            #     for number in numbers:
            #         if x is None:
            #             break
            #
            #     # Fails: x is optional, as the loop might not have executed or
            #     # might have been exited by the ``break``.
            #     return x.optional_text is None
            self._facts = facts_before

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_continue(
        self, node: parse_tree.Continue
    ) -> Optional["TypeAnnotationUnion"]:
        if len(self._loop_variable_set) == 0:
            self.errors.append(
                Error(
                    node.original_node,
                    "The ``continue`` statement is not within a for-loop",
                )
            )
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_break(
        self, node: parse_tree.Break
    ) -> Optional["TypeAnnotationUnion"]:
        if len(self._loop_variable_set) == 0:
            self.errors.append(
                Error(
                    node.original_node,
                    "The ``break`` statement is not within a for-loop",
                )
            )
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_if(self, node: parse_tree.If) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin):
        # We narrow the types in the branches by their conditions, and by
        # the negations of the previous conditions. After the if-statement, we keep
        # only the facts common to the ends of the branches which can complete
        # normally. Please see :py:class:`_Fact` for the whole model. For example:
        #
        # .. code-block:: python
        #
        #     if parent is None:
        #         # Facts: none; we do not track that ``parent`` is ``None``.
        #         return True
        #     elif not isinstance(parent, Child_b):
        #         # Facts: parent is non-null, by the negation of the first
        #         # condition. Passes.
        #         return parent.optional_text is None
        #     else:
        #         # Facts: parent is non-null, and an instance of Child_b, by
        #         # the negations of both conditions. Passes.
        #         return parent.b_only > 0
        #
        # We generate, *e.g.*, the following Go code, where the transpiler
        # down-casts ``parent`` in the ``else`` based on the facts:
        #
        # .. code-block:: go
        #
        #     if parent == nil {
        #         return true
        #     } else if !aastypes.IsChildB(parent) {
        #         return parent.OptionalText() == nil
        #     } else {
        #         return parent.(aastypes.IChildB).BOnly() > 0
        #     }
        #
        # In contrast, the narrowing does not leak out of a branch:
        #
        # .. code-block:: python
        #
        #     if flag:
        #         if parent is None:
        #             return False
        #
        #         # Passes: the inner if-statement narrows the rest of the branch.
        #         result = parent.optional_text is None
        #
        #     # Fails: the absent else knows nothing about ``parent``.
        #     return parent.optional_text is None

        success = True

        facts_before = self._facts
        facts_of_negations = []  # type: List[_Fact]
        facts_at_ends = []  # type: List[List[_Fact]]

        for branch in node.branches:
            # NOTE (mristin):
            # The branch is reached only if none of the previous conditions holds.
            self._facts = facts_before + facts_of_negations

            # NOTE (mristin):
            # We stop at the first condition which we could not infer. We could not
            # tell its facts, so checking the subsequent branches would only report
            # spurious errors about the optional values.
            condition_type = self.transform(branch.condition)
            if condition_type is None:
                self._facts = facts_before
                return None

            if try_primitive_type(condition_type) is not PrimitiveType.BOOL:
                # NOTE (mristin):
                # We refuse the conditions which rely on Python's truthiness, such
                # as ``if some_list:``, since the targets do not share it.
                self.errors.append(
                    Error(
                        branch.condition.original_node,
                        f"Expected the condition of the if-statement to be "
                        f"a boolean, but got: {condition_type}",
                    )
                )
                self._facts = facts_before
                return None

            self._facts = self._facts + self._implied_facts(branch.condition)

            if not self._transform_in_new_scope(branch.body):
                success = False

            # NOTE (mristin):
            # A branch which ends in ``return``, ``continue`` or ``break`` never
            # reaches the code after the if-statement, so its facts do not matter
            # there. This is what narrows ``x`` after
            # ``if x is None: return False``.
            if parse_tree.can_complete_normally(branch.body):
                facts_at_ends.append(self._facts)

            facts_of_negations.extend(self._implied_facts_of_negation(branch.condition))

        self._facts = facts_before + facts_of_negations

        if node.default is not None:
            if not self._transform_in_new_scope(node.default):
                success = False

            if parse_tree.can_complete_normally(node.default):
                facts_at_ends.append(self._facts)
        else:
            # NOTE (mristin):
            # An absent ``else`` is an empty branch, which always completes
            # normally with the negations of all the conditions.
            facts_at_ends.append(self._facts)

        self._join(facts_before, facts_at_ends)

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_expression_statement(
        self, node: parse_tree.ExpressionStatement
    ) -> Optional["TypeAnnotationUnion"]:
        if self.transform(node.expression) is None:
            return None

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
                kind=BuiltinFunctionKind.LEN,
                returns=PrimitiveTypeAnnotation(PrimitiveType.LENGTH),
            )
        ),
        # NOTE (mristin):
        # The return type of ``abs`` depends on the argument, so it is inferred
        # at the call site.
        Identifier("abs"): BuiltinFunctionTypeAnnotation(
            func=BuiltinFunction(kind=BuiltinFunctionKind.ABS, returns=None)
        ),
        # NOTE (mristin):
        # We support ``int`` only to parse a string. The transpiled code is
        # stricter than Python: it accepts only an optional sign followed by
        # the ASCII digits, and only the safe integers, *i.e.*, the integers
        # which a double-precision floating-point number represents exactly.
        # Otherwise, it throws. We limit ourselves to the safe integers as
        # TypeScript represents the integers as ``number``. The meta-model has
        # to check the text before it calls ``int``.
        Identifier("int"): BuiltinFunctionTypeAnnotation(
            func=BuiltinFunction(
                kind=BuiltinFunctionKind.INT,
                returns=PrimitiveTypeAnnotation(PrimitiveType.INT),
            )
        ),
    }

    # NOTE (mristin):
    # The type of ``set()`` is given by the declaration of the variable which it
    # initializes, *e.g.*, ``x: Set[str] = set()``, see
    # :py:meth:`_Inferrer.transform_assignment`.
    mapping[Identifier("set")] = BuiltinFunctionTypeAnnotation(
        func=BuiltinFunction(kind=BuiltinFunctionKind.SET, returns=None)
    )

    for constant in symbol_table.constants:
        if isinstance(constant, _types.ConstantPrimitive):
            mapping[constant.name] = PrimitiveTypeAnnotation(
                a_type=PRIMITIVE_TYPE_MAP[constant.a_type]
            )
        elif isinstance(constant, _types.ConstantSetOfPrimitives):
            mapping[constant.name] = SetTypeAnnotation(
                items=PrimitiveTypeAnnotation(PRIMITIVE_TYPE_MAP[constant.a_type])
            )
        elif isinstance(constant, _types.ConstantSetOfEnumerationLiterals):
            mapping[constant.name] = SetTypeAnnotation(
                items=OurTypeAnnotation(our_type=constant.enumeration)
            )
        else:
            assert_never(constant)

    for verification in symbol_table.verification_functions:
        assert verification.name not in mapping
        mapping[verification.name] = VerificationTypeAnnotation(func=verification)

    for our_type in symbol_table.our_types:
        if isinstance(our_type, _types.Enumeration):
            assert our_type.name not in mapping
            mapping[our_type.name] = EnumerationAsTypeTypeAnnotation(
                enumeration=our_type
            )

    return ImmutableEnvironment(
        mapping=mapping,
        parent=None,
        our_types_by_name={
            our_type.name: our_type for our_type in symbol_table.our_types
        },
    )


class InferenceOfFunction:
    """Represent the result of type inference on a function body and arguments."""

    #: Environment inferred after processing a body of statements including
    #: the function arguments
    environment_with_args: Final[Environment]

    #: Map of body nodes to types
    type_map: Final[Mapping[parse_tree.Node, "TypeAnnotationUnion"]]

    #: Map of body nodes narrowed by ``isinstance`` to their down-casts
    downcast_map: Final[Mapping[parse_tree.Node, Downcast]]

    def __init__(
        self,
        environment_with_args: Environment,
        type_map: Mapping[parse_tree.Node, "TypeAnnotationUnion"],
        downcast_map: Mapping[parse_tree.Node, Downcast],
    ) -> None:
        """Initialize with the given values."""
        self.environment_with_args = environment_with_args
        self.type_map = type_map
        self.downcast_map = downcast_map


def _check_nones(
    body: Sequence[parse_tree.Node],
    returns: Optional[_types.TypeAnnotationUnion],
) -> List[Error]:
    """
    Check that the ``None`` literals in the ``body`` can be transpiled.

    We transpile ``None`` as the value of an assignment, as an argument of a call
    and as the returned value, where the optionals are expected, as every target
    represents the ``None`` of an optional. Elsewhere, such as in the comparisons
    or in the tuples, the targets would need a type for the ``None`` on its own.

    The types of the assigned values and of the arguments are checked in
    the inference. Here, we check that the returned ``None`` fits the ``returns``
    of the function, which is ``None`` for the invariants and the procedures.
    """
    allowed_set = set()  # type: Set[parse_tree.Node]
    nones = []  # type: List[parse_tree.Constant]
    returns_of_none = []  # type: List[parse_tree.Return]

    for node_in_body in body:
        for node in parse_tree.over_nodes(node_in_body):
            if isinstance(node, parse_tree.Assignment):
                allowed_set.add(node.value)

            elif isinstance(node, (parse_tree.FunctionCall, parse_tree.MethodCall)):
                allowed_set.update(node.args)

            elif isinstance(node, parse_tree.Return) and node.value is not None:
                allowed_set.add(node.value)

                if (
                    isinstance(node.value, parse_tree.Constant)
                    and node.value.value is None
                ):
                    returns_of_none.append(node)

            elif isinstance(node, parse_tree.Constant) and node.value is None:
                nones.append(node)

    errors = [
        Error(
            none.original_node,
            "We can transpile ``None`` only as the value of an assignment, "
            "as an argument of a call or as the returned value, since the targets "
            "need to know the type of the optional which is ``None``. To check "
            "whether a value is ``None``, please use ``is None`` or "
            "``is not None``.",
        )
        for none in nones
        if none not in allowed_set
    ]  # type: List[Error]

    if not isinstance(returns, _types.OptionalTypeAnnotation):
        for return_of_none in returns_of_none:
            errors.append(
                Error(
                    return_of_none.original_node,
                    (
                        "The function returns nothing, so please use a bare "
                        "``return`` instead of ``return None``."
                        if returns is None
                        else f"The function returns a non-optional {returns}, "
                        f"but got a ``return None``."
                    ),
                )
            )

    return errors


def _check_sets(
    body: Sequence[parse_tree.Node],
    type_map: Mapping[parse_tree.Node, "TypeAnnotationUnion"],
    representation_map: Mapping[parse_tree.Node, str],
) -> List[Error]:
    """
    Check that the sets in the ``body`` are used only where we can transpile them.

    A set can be the container of ``in``, the collection of a for-loop,
    the receiver of its methods, an argument of a call, the target of
    an assignment and the value of a nullness check. A new set, *e.g.*, from
    ``set()`` or ``intersection``, can also be assigned. Elsewhere, *e.g.*, in
    ``b = a``, the targets would need to either copy or share the set, and they
    disagree on that: C++ copies it, while the other targets share it. The type
    inference checks the arguments of the calls with more specific errors, *e.g.*,
    that a set is passed only to a set argument.

    The ``add`` returns nothing, so it can only be a statement on its own.

    A set can not be mutated in a for-loop over it, as the targets disagree on
    that: Python and Java throw, C++ is undefined, while Go and TypeScript carry on.
    """
    allowed_set = set()  # type: Set[parse_tree.Node]
    statement_calls = set()  # type: Set[parse_tree.Node]
    set_nodes = []  # type: List[parse_tree.Node]
    adds = []  # type: List[parse_tree.MethodCall]

    # NOTE (mristin):
    # We collect the sets passed to the mutable arguments together with the calls.
    mutated_set_nodes = []  # type: List[parse_tree.Expression]

    loops_over_sets = []  # type: List[parse_tree.For]

    for node_in_body in body:
        for node in parse_tree.over_nodes(node_in_body):
            if (
                isinstance(node, parse_tree.For)
                and isinstance(node.generator, parse_tree.ForEach)
                and isinstance(
                    type_map.get(node.generator.iteration, None), SetTypeAnnotation
                )
            ):
                loops_over_sets.append(node)

            arguments = None  # type: Optional[Sequence[_types.Argument]]
            call_args = ()  # type: Sequence[parse_tree.Expression]
            if isinstance(node, parse_tree.FunctionCall):
                func_type = type_map.get(node.name, None)
                if isinstance(func_type, VerificationTypeAnnotation):
                    arguments = func_type.func.arguments
                    call_args = node.args
            elif isinstance(node, parse_tree.MethodCall):
                method_type = type_map.get(node.member, None)
                if isinstance(method_type, MethodTypeAnnotation):
                    arguments = method_type.method.arguments
                    call_args = node.args
            else:
                pass

            if arguments is not None:
                for arg_node, argument in zip(call_args, arguments):
                    arg_type = type_map.get(arg_node, None)
                    if (
                        argument.mutable
                        and arg_type is not None
                        and isinstance(beneath_optional(arg_type), SetTypeAnnotation)
                    ):
                        mutated_set_nodes.append(arg_node)

            if isinstance(node, parse_tree.IsIn):
                allowed_set.add(node.container)

            elif isinstance(node, (parse_tree.IsNone, parse_tree.IsNotNone)):
                allowed_set.add(node.value)

            elif isinstance(node, parse_tree.Assignment):
                allowed_set.add(node.target)
                if _is_new_set(node.value, type_map):
                    allowed_set.add(node.value)

            elif isinstance(node, parse_tree.ExpressionStatement):
                statement_calls.add(node.expression)

            elif isinstance(node, parse_tree.MethodCall):
                allowed_set.update(node.args)

                member_type = type_map.get(node.member, None)
                if (
                    isinstance(member_type, BuiltinMethodTypeAnnotation)
                    and member_type.method is SET_ADD
                ):
                    adds.append(node)

            elif isinstance(node, parse_tree.FunctionCall):
                allowed_set.update(node.args)

            elif isinstance(node, parse_tree.Member):
                allowed_set.add(node.instance)

            elif isinstance(node, parse_tree.ForEach):
                allowed_set.add(node.iteration)

            if isinstance(node, parse_tree.Expression):
                type_anno = type_map.get(node, None)
                if type_anno is not None and isinstance(
                    beneath_optional(type_anno), SetTypeAnnotation
                ):
                    set_nodes.append(node)

    errors = [
        Error(
            node.original_node,
            "We support a set only as the container of ``in``, the collection "
            "of a for-loop, the receiver of its methods, an argument of a call, "
            "the target of an assignment, the value of a nullness check, and "
            "a new set as the assigned value. Elsewhere, the targets would need "
            "to either copy or share the set, and they disagree on that: C++ "
            "copies it, while the other targets share it.",
        )
        for node in set_nodes
        if node not in allowed_set
    ]  # type: List[Error]

    errors.extend(
        Error(
            add.original_node,
            "The ``add`` of a set returns nothing, so it can only be called as "
            "a statement on its own.",
        )
        for add in adds
        if add not in statement_calls
    )

    mutated_set_nodes.extend(add.member.instance for add in adds)

    for loop in loops_over_sets:
        assert isinstance(loop.generator, parse_tree.ForEach)
        iterated = representation_map[loop.generator.iteration]

        nodes_in_loop = {
            node for stmt in loop.body for node in parse_tree.over_nodes(stmt)
        }

        errors.extend(
            Error(
                mutated.original_node,
                f"The set {iterated} can not be mutated in the for-loop over it, "
                f"since the targets disagree on that: Python and Java throw "
                f"an exception, the behavior is undefined in C++, while Go and "
                f"TypeScript carry on.",
            )
            for mutated in mutated_set_nodes
            if mutated in nodes_in_loop and representation_map[mutated] == iterated
        )

    return errors


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _infer_for_function(
    body: Sequence[parse_tree.Node],
    arguments: Sequence[_types.Argument],
    returns: Optional[_types.TypeAnnotationUnion],
    environment: MutableEnvironment,
    enclosing_method: Optional[_types.UnderstoodMethod],
    what: str,
    node: ast.AST,
) -> Tuple[Optional[InferenceOfFunction], Optional[Error]]:
    """
    Infer the types in the ``body`` of a verification function or of a method.

    The ``environment`` is expected to hold the arguments already, and ``self``
    in case of a method. The ``what`` describes the function in the error messages,
    *e.g.*, ``the verification function 'foo'``.
    """
    canonicalizer = _Canonicalizer()
    for node_in_body in body:
        _ = canonicalizer.transform(node_in_body)

    type_inferrer = _Inferrer(
        environment=environment,
        representation_map=canonicalizer.representation_map,
        argument_by_name={arg.name: arg for arg in arguments},
        enclosing_method=enclosing_method,
        returns=returns,
    )

    for node_in_body in body:
        _ = type_inferrer.transform(node_in_body)

    type_inferrer.errors.extend(_check_nones(body=body, returns=returns))
    type_inferrer.errors.extend(
        _check_sets(
            body=body,
            type_map=type_inferrer.type_map,
            representation_map=canonicalizer.representation_map,
        )
    )

    # NOTE (mristin):
    # Some targets, such as Go or Java, refuse to compile a function which misses
    # a return statement at the end, so we refuse it here already.
    if returns is not None and parse_tree.can_complete_normally(body):  # type: ignore
        type_inferrer.errors.append(
            Error(
                node,
                f"Expected {what} to end with a return statement, "
                f"since it returns a value",
            )
        )

    if len(type_inferrer.errors):
        return None, Error(
            node,
            f"Failed to infer the types in {what}",
            type_inferrer.errors,
        )

    return (
        InferenceOfFunction(
            environment_with_args=environment,
            type_map=type_inferrer.type_map,
            downcast_map=type_inferrer.downcast_map,
        ),
        None,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_for_verification(
    verification: _types.TranspilableVerification, base_environment: Environment
) -> Tuple[Optional[InferenceOfFunction], Optional[Error]]:
    """Infer the types for the given function and map the body nodes to the types."""
    environment = MutableEnvironment(parent=base_environment)

    for arg in verification.arguments:
        environment.set(
            identifier=arg.name,
            type_annotation=convert_type_annotation(arg.type_annotation),
        )

    return _infer_for_function(
        body=verification.parsed.body,
        arguments=verification.arguments,
        returns=verification.returns,
        environment=environment,
        enclosing_method=None,
        what=f"the verification function {verification.name!r}",
        node=verification.parsed.node,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_for_method(
    method: _types.UnderstoodMethod, base_environment: Environment
) -> Tuple[Optional[InferenceOfFunction], Optional[Error]]:
    """
    Infer the types for the given method and map the body nodes to the types.

    The ``self`` is typed as the class which specified the method, so that
    the inference holds for all the classes which inherit the method.
    """
    specified_for = method.specified_for
    assert isinstance(specified_for, (_types.AbstractClass, _types.ConcreteClass))

    environment = MutableEnvironment(parent=base_environment)

    environment.set(
        identifier=Identifier("self"),
        type_annotation=OurTypeAnnotation(our_type=specified_for),
    )

    for arg in method.arguments:
        environment.set(
            identifier=arg.name,
            type_annotation=convert_type_annotation(arg.type_annotation),
        )

    return _infer_for_function(
        body=method.body,
        arguments=method.arguments,
        returns=method.returns,
        environment=environment,
        enclosing_method=method,
        what=f"the method {method.name!r} of the class {method.specified_for.name!r}",
        node=method.parsed.node,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_for_methods(
    symbol_table: _types.SymbolTable,
) -> Tuple[
    Optional[Mapping[_types.UnderstoodMethod, InferenceOfFunction]],
    Optional[List[Error]],
]:
    """
    Infer the types for all the understood methods of the ``symbol_table``.

    We infer the types of a method only once, in the class which specified it.
    The generators re-use the inference in all the concrete classes which repeat
    the method.
    """
    base_environment = populate_base_environment(symbol_table=symbol_table)

    errors = []  # type: List[Error]
    inference_by_method = (
        dict()
    )  # type: MutableMapping[_types.UnderstoodMethod, InferenceOfFunction]

    for cls in symbol_table.classes:
        for method in cls.methods:
            if method.specified_for is not cls or not isinstance(
                method, _types.UnderstoodMethod
            ):
                continue

            inference, error = infer_for_method(
                method=method, base_environment=base_environment
            )
            if error is not None:
                errors.append(error)
                continue

            assert inference is not None
            inference_by_method[method] = inference

    if len(errors) > 0:
        return None, errors

    return inference_by_method, None


class InferenceOfInvariant:
    """Represent the result of type inference on the body of an invariant."""

    #: Map of body nodes to types
    type_map: Final[Mapping[parse_tree.Node, "TypeAnnotationUnion"]]

    #: Map of body nodes narrowed by ``isinstance`` to their down-casts
    downcast_map: Final[Mapping[parse_tree.Node, Downcast]]

    def __init__(
        self,
        type_map: Mapping[parse_tree.Node, "TypeAnnotationUnion"],
        downcast_map: Mapping[parse_tree.Node, Downcast],
    ) -> None:
        """Initialize with the given values."""
        self.type_map = type_map
        self.downcast_map = downcast_map


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def infer_for_invariant(
    invariant: _types.Invariant, environment: Environment
) -> Tuple[Optional[InferenceOfInvariant], Optional[Error]]:
    """Infer the types of the nodes corresponding to the body of an invariant."""
    canonicalizer = _Canonicalizer()
    _ = canonicalizer.transform(invariant.body)

    type_inferrer = _Inferrer(
        environment=environment,
        representation_map=canonicalizer.representation_map,
        argument_by_name=dict(),
        enclosing_method=None,
        returns=None,
    )

    _ = type_inferrer.transform(invariant.body)

    type_inferrer.errors.extend(_check_nones(body=[invariant.body], returns=None))
    type_inferrer.errors.extend(
        _check_sets(
            body=[invariant.body],
            type_map=type_inferrer.type_map,
            representation_map=canonicalizer.representation_map,
        )
    )

    if len(type_inferrer.errors):
        return None, Error(
            invariant.parsed.node,
            "Failed to infer the types in the invariant",
            type_inferrer.errors,
        )

    return (
        InferenceOfInvariant(
            type_map=type_inferrer.type_map,
            downcast_map=type_inferrer.downcast_map,
        ),
        None,
    )


assert_union_of_descendants_exhaustive(
    union=TypeAnnotationUnion, base_class=TypeAnnotation
)

TypeAnnotationExceptOptional = Union[
    PrimitiveTypeAnnotation,
    OurTypeAnnotation,
    VerificationTypeAnnotation,
    BuiltinFunctionTypeAnnotation,
    BuiltinMethodTypeAnnotation,
    MethodTypeAnnotation,
    ListTypeAnnotation,
    SetTypeAnnotation,
    TupleTypeAnnotation,
    EnumerationAsTypeTypeAnnotation,
    JsonValueTypeAnnotation,
    JsonArrayTypeAnnotation,
    JsonObjectTypeAnnotation,
]
assert_union_without_excluded(
    original_union=TypeAnnotationUnion,
    subset_union=TypeAnnotationExceptOptional,
    excluded=[OptionalTypeAnnotation],
)

FunctionTypeAnnotationUnion = Union[
    VerificationTypeAnnotation, BuiltinFunctionTypeAnnotation
]
assert_union_of_descendants_exhaustive(
    union=FunctionTypeAnnotationUnion, base_class=FunctionTypeAnnotation
)

# NOTE (mristin):
# Mypy is not smart enough to work with ``get_args``, so we have to manually write it
# out.
FunctionTypeAnnotationUnionAsTuple = (
    VerificationTypeAnnotation,
    BuiltinFunctionTypeAnnotation,
)
assert FunctionTypeAnnotationUnionAsTuple == get_args(FunctionTypeAnnotationUnion)
