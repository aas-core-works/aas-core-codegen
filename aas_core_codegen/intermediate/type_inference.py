"""
Infer the types of the tree nodes.

Note that these types roughly follow the type annotations in
:py:mod:`aas_core_codegen.intermediate._types`, but are not identical. For example,
the ``LENGTH`` primitive exists only in type inference. Another example, we do not
track ``parsed`` as the types are inferred in the intermediate stage, but can not
be traced back to the parse stage.
"""
import abc
import enum
from typing import Mapping, MutableMapping, Dict, Optional, List, Final

from aas_core_codegen.common import Identifier, Error, assert_never
from icontract import DBC

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


class VerificationTypeAnnotation(AtomicTypeAnnotation):
    """Represent a type of a verification function."""

    def __init__(self, func: _types.Verification):
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

    def __init__(self, items: "TypeAnnotation"):
        self.items = items

    def __str__(self) -> str:
        return f"List[{self.items}]"


class OptionalTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving an ``Optional[...]``."""

    def __init__(self, value: "TypeAnnotation"):
        self.value = value

    def __str__(self) -> str:
        return f"Optional[{self.value}]"


class RefTypeAnnotation(SubscriptedTypeAnnotation):
    """Represent a type annotation involving a reference ``Ref[...]``."""

    def __init__(self, value: "TypeAnnotation"):
        self.value = value

    def __str__(self) -> str:
        return f"Ref[{self.value}]"


_PRIMITIVE_TYPE_MAP = {
    _types.PrimitiveType.BOOL: PrimitiveType.BOOL,
    _types.PrimitiveType.INT: PrimitiveType.INT,
    _types.PrimitiveType.FLOAT: PrimitiveType.FLOAT,
    _types.PrimitiveType.STR: PrimitiveType.STR,
    _types.PrimitiveType.BYTEARRAY: PrimitiveType.BYTEARRAY,
}

for _types_primitive_type in _types.PrimitiveType:
    assert _types_primitive_type in _PRIMITIVE_TYPE_MAP, (
        f"All primitive types from _types covered, but: {_types_primitive_type=}"
    )


def _type_annotation_to_inferred_type_annotation(
        type_annotation: _types.TypeAnnotation
) -> TypeAnnotation:
    """Convert from the :py:mod:`aas_core_codegen.intermediate._types`."""
    if isinstance(type_annotation, _types.PrimitiveTypeAnnotation):
        return PrimitiveTypeAnnotation(
            a_type=_PRIMITIVE_TYPE_MAP.get(type_annotation.a_type))

    elif isinstance(type_annotation, _types.OurTypeAnnotation):
        return OurTypeAnnotation(symbol=type_annotation.symbol)

    elif isinstance(type_annotation, _types.ListTypeAnnotation):
        return ListTypeAnnotation(
            items=_type_annotation_to_inferred_type_annotation(type_annotation.items))

    elif isinstance(type_annotation, _types.OptionalTypeAnnotation):
        return OptionalTypeAnnotation(
            value=_type_annotation_to_inferred_type_annotation(type_annotation.value))

    else:
        assert_never(type_annotation)


class Inferrer(
    parse_tree.RestrictedTransformer[Optional[TypeAnnotation]]):
    """Infer the types of the given parse tree."""

    #: Track of the inferred types
    type_map: Final[MutableMapping[parse_tree.Node, TypeAnnotation]]

    #: Errors encountered during the inference
    errors: Final[List[Error]]

    def __init__(
            self,
            symbol_table: _types.SymbolTable,
            environment: Dict[Identifier, TypeAnnotation]
    ) -> None:
        """Initialize with the given values."""
        self._symbol_table = symbol_table
        self._environment = environment.copy()

        self.type_map = dict()
        self.errors = []

    # TODO: override transform with ensure: if None, then errors not empty

    def transform_member(self, node: parse_tree.Member) -> Optional[TypeAnnotation]:
        instance_type = self.transform(node.instance)

        if instance_type is None:
            return None

        if not (
                isinstance(instance_type, OurTypeAnnotation)
                and isinstance(instance_type.symbol, _types.Class)
        ):
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected an instance to be of type class, "
                    f"but got: {instance_type}"
                )
            )
            return None

        cls = instance_type.symbol
        assert isinstance(cls, _types.Class)

        prop = cls.properties_by_name.get(node.name, None)
        if prop is not None:
            result = _type_annotation_to_inferred_type_annotation(
                prop.type_annotation
            )
            self.type_map[node] = result
            return result

        method = cls.methods_by_name.get(node.name, None)
        if method is not None:
            result = MethodTypeAnnotation(method=method)
            self.type_map[node] = result
            return result

        self.errors.append(
            Error(
                node.original_node,
                f"The member {node.name!r} could not be found in the class {cls.name!r}"
            )
        )

        return None

    def transform_comparison(
            self, node: parse_tree.Comparison
    ) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit left and right!
        raise NotImplementedError()

    def transform_implication(
            self,
            node: parse_tree.Implication
    ) -> Optional[TypeAnnotation]:
        result = PrimitiveTypeAnnotation(a_type=PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_method_call(
            self,
            node: parse_tree.MethodCall
    ) -> Optional[TypeAnnotation]:
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
                    f"but got: {member_type}"
                )
            )
            return None

        result = None  # type: Optional[TypeAnnotation]

        if member_type.method.returns is None:
            result = PrimitiveTypeAnnotation(a_type=PrimitiveType.NONE)
        else:
            result = _type_annotation_to_inferred_type_annotation(
                member_type.method.returns
            )

        assert result is not None
        self.type_map[node] = result
        return result

    def transform_function_call(
            self,
            node: parse_tree.FunctionCall
    ) -> Optional[TypeAnnotation]:
        # Simply recurse to track the type, but we don't care about the arguments
        failed = False
        for arg in node.args:
            arg_type = self.transform(arg)
            if arg_type is None:
                failed = True

        type_in_env = self._environment.get(node.name, None)
        if type_in_env is None:
            self.errors.append(
                Error(
                    node.original_node,
                    f"The function {node.name!r} has not been defined."
                )
            )
            failed = True

        if failed:
            return None

        if not isinstance(type_in_env, VerificationTypeAnnotation):
            self.errors.append(
                Error(
                    node.original_node,
                    f"Expected the name {node.name!r} to denote "
                    f"a verification function, but got: {type_in_env}"
                )
            )
            return None

        result = None  # type: Optional[TypeAnnotation]

        if type_in_env.func.returns is not None:
            result = _type_annotation_to_inferred_type_annotation(
                type_in_env.func.returns
            )
        else:
            result = PrimitiveTypeAnnotation(a_type=PrimitiveType.NONE)

        assert result is not None

        self.type_map[node] = result
        return result

    def transform_constant(self, node: parse_tree.Constant) -> Optional[TypeAnnotation]:
        result = None  # type: Optional[TypeAnnotation]

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

    def transform_is_none(self, node: parse_tree.IsNone) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit value
        raise NotImplementedError()

    def transform_is_not_none(
            self, node: parse_tree.IsNotNone) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit value
        raise NotImplementedError()

    def transform_name(self, node: parse_tree.Name) -> Optional[TypeAnnotation]:
        # TODO: implement
        raise NotImplementedError()

    def transform_and(self, node: parse_tree.And) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit values
        raise NotImplementedError()

    def transform_or(self, node: parse_tree.Or) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit values
        raise NotImplementedError()

    def transform_joined_str(
            self, node: parse_tree.JoinedStr
    ) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit parts
        raise NotImplementedError()

    def transform_assignment(
            self, node: parse_tree.Assignment
    ) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit parts
        raise NotImplementedError()

    def transform_return(
            self, node: parse_tree.Return
    ) -> Optional[TypeAnnotation]:
        # TODO: implement, continue here, needs to visit value
        raise NotImplementedError()
