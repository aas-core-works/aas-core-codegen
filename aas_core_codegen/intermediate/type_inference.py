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
from typing import Mapping, MutableMapping, Dict, Optional, List, Final, Union

from aas_core_codegen.common import Identifier, Error, assert_never
from icontract import DBC, ensure, require

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


class BuiltinFunction:
    """Represent a built-in function."""

    def __init__(self, name: Identifier, returns: Optional[TypeAnnotation]):
        """Initialize with the given values."""
        self.name = name
        self.returns = returns


class BuiltinFunctionTypeAnnotation(AtomicTypeAnnotation):
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


def _type_annotations_equal(
        that: TypeAnnotation,
        other: TypeAnnotation
):
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
            return id(that.symbol) == id(other.symbol)

    elif isinstance(that, VerificationTypeAnnotation):
        if not isinstance(other, VerificationTypeAnnotation):
            return False
        else:
            return id(that.func) == id(other.func)

    elif isinstance(that, MethodTypeAnnotation):
        if not isinstance(other, MethodTypeAnnotation):
            return False
        else:
            return id(that.method) == id(other.method)

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

    elif isinstance(that, RefTypeAnnotation):
        if not isinstance(other, RefTypeAnnotation):
            return False
        else:
            return _type_annotations_equal(that.value, other.value)

    else:
        assert_never(that)


def _assignable(
        target_type: TypeAnnotation,
        value_type: TypeAnnotation
):
    """Check whether the value can be assigned to the target."""
    if isinstance(target_type, PrimitiveTypeAnnotation):
        if isinstance(value_type, PrimitiveTypeAnnotation):
            return target_type.a_type == value_type.a_type

        # NOTE (mristin, 2021-12-25):
        # We have to be careful about the constrained primitives,
        # since we can always assign a constrained primitive to a primitive, if they
        # primitive types match.
        elif (
                isinstance(value_type, OurTypeAnnotation)
                and isinstance(value_type.symbol, _types.ConstrainedPrimitive)
        ):
            return target_type.a_type == PRIMITIVE_TYPE_MAP.get(
                value_type.symbol.constrainee)

        else:
            return False

    elif isinstance(target_type, OurTypeAnnotation):
        if isinstance(target_type.symbol, _types.Enumeration):
            # NOTE (mristin, 2021-12-25):
            # The enumerations are invariant.
            return (
                    isinstance(value_type, OurTypeAnnotation)
                    and isinstance(value_type.symbol, _types.Enumeration)
                    and id(target_type.symbol) == id(value_type.symbol)
            )

        elif isinstance(target_type.symbol, _types.ConstrainedPrimitive):
            # NOTE (mristin, 2021-12-25):
            # If it is a constrained primitive with no constraints, allow the assignment
            # if the target and the value match on the primitive type.
            if (
                    len(target_type.symbol.invariants) == 0
                    and isinstance(value_type, PrimitiveTypeAnnotation)
            ):
                return PRIMITIVE_TYPE_MAP.get(
                    target_type.symbol.constrainee) == value_type.a_type
            else:
                # NOTE (mristin, 2021-12-25):
                # We assume the assignments of constrained primitives to be co-variant.
                if (
                        isinstance(value_type, OurTypeAnnotation)
                        and isinstance(value_type.symbol, _types.ConstrainedPrimitive)
                        and target_type.symbol.constrainee ==
                        value_type.symbol.constrainee
                ):
                    return (
                            id(target_type.symbol) == id(value_type.symbol)
                            or value_type.symbol in target_type.symbol.descendant_id_set
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

            return (
                    id(target_type.symbol) == id(value_type.symbol)
                    or (
                            id(
                                value_type.symbol) in target_type.symbol.descendant_id_set
                    )
            )

    elif isinstance(target_type, VerificationTypeAnnotation):
        if not isinstance(value_type, VerificationTypeAnnotation):
            return False
        else:
            return id(target_type.func) == id(value_type.func)

    elif isinstance(target_type, MethodTypeAnnotation):
        if not isinstance(value_type, MethodTypeAnnotation):
            return False
        else:
            return id(target_type.method) == id(value_type.method)

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
                target_type=target_type.value, value_type=value_type.value)

    elif isinstance(target_type, RefTypeAnnotation):
        if not isinstance(value_type, RefTypeAnnotation):
            return False
        else:
            # NOTE (mristin, 2021-12-25):
            # We assume the references to be co-variant.
            return _assignable(
                target_type=target_type.value, value_type=value_type.value)

    else:
        assert_never(target_type)


PRIMITIVE_TYPE_MAP = {
    _types.PrimitiveType.BOOL: PrimitiveType.BOOL,
    _types.PrimitiveType.INT: PrimitiveType.INT,
    _types.PrimitiveType.FLOAT: PrimitiveType.FLOAT,
    _types.PrimitiveType.STR: PrimitiveType.STR,
    _types.PrimitiveType.BYTEARRAY: PrimitiveType.BYTEARRAY,
}

for _types_primitive_type in _types.PrimitiveType:
    assert _types_primitive_type in PRIMITIVE_TYPE_MAP, (
        f"All primitive types from _types covered, but: {_types_primitive_type=}"
    )


def _type_annotation_to_inferred_type_annotation(
        type_annotation: _types.TypeAnnotation
) -> TypeAnnotation:
    """Convert from the :py:mod:`aas_core_codegen.intermediate._types`."""
    if isinstance(type_annotation, _types.PrimitiveTypeAnnotation):
        return PrimitiveTypeAnnotation(
            a_type=PRIMITIVE_TYPE_MAP.get(type_annotation.a_type))

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
    type_map: Final[MutableMapping[
        Union[parse_tree.Node, parse_tree.FormattedValue], TypeAnnotation]]

    #: Errors encountered during the inference
    errors: Final[List[Error]]

    def __init__(
            self,
            symbol_table: _types.SymbolTable,
            environment: Mapping[Identifier, TypeAnnotation]
    ) -> None:
        """Initialize with the given values."""
        self._symbol_table = symbol_table

        self._environment = {
            key: value
            for key, value in environment.items()
        }

        self.type_map = dict()
        self.errors = []

    @ensure(lambda self, result: not (result is None) or len(self.errors) > 0)
    def transform(self, node: parse_tree.Node) -> Optional[TypeAnnotation]:
        return super().transform(node)

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
        # Just recurse to fill ``type_map`` on ``left`` and ``right`` even though we
        # know the type in advance
        success = (
                (self.transform(node.left) is not None)
                and (self.transform(node.right) is not None)
        )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_implication(
            self,
            node: parse_tree.Implication
    ) -> Optional[TypeAnnotation]:
        # Just recurse to fill ``type_map`` on ``antecedent`` and ``consequent`` even
        # though we know the type in advance
        success = (
                (self.transform(node.antecedent) is not None)
                and (self.transform(node.consequent) is not None)
        )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
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
        result = None  # type: Optional[TypeAnnotation]
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
        # Just recurse to fill ``type_map`` on ``value`` even though we know the type in
        # advance
        success = self.transform(node.value) is not None

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_is_not_none(
            self, node: parse_tree.IsNotNone) -> Optional[TypeAnnotation]:
        # Just recurse to fill ``type_map`` on ``value`` even though we know the type in
        # advance
        success = self.transform(node.value) is not None

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_name(self, node: parse_tree.Name) -> Optional[TypeAnnotation]:
        type_in_env = self._environment.get(node.identifier, None)
        if type_in_env is None:
            self.errors.append(
                Error(
                    node.original_node,
                    f"We do not know how to infer the type of "
                    f"the variable with the identifier {node.identifier!r} from the "
                    f"given environment. Mind that we do not consider the module "
                    f"scope nor handle all built-in functions due to simplicity! If "
                    f"you believe this needs to work, please notify the developers."
                )
            )
            return None

        self.type_map[node] = type_in_env
        return type_in_env

    def transform_and(self, node: parse_tree.And) -> Optional[TypeAnnotation]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance
        success = all(
            self.transform(value_node) is not None
            for value_node in node.values
        )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_or(self, node: parse_tree.Or) -> Optional[TypeAnnotation]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance
        success = all(
            self.transform(value_node) is not None
            for value_node in node.values
        )

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_joined_str(
            self, node: parse_tree.JoinedStr
    ) -> Optional[TypeAnnotation]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance
        success = True
        for value in node.values:
            if isinstance(value, str):
                continue
            elif isinstance(value, parse_tree.FormattedValue):
                # NOTE (mristin, 2021-12-25):
                # Since ``FormattedValue`` is not a ``Node``, we have to treat it in a
                # special way.
                formatted_value_type = self.transform(value.value)
                if formatted_value_type is None:
                    success = False
                else:
                    self.type_map[value] = formatted_value_type
            else:
                assert_never(value)

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.STR)
        self.type_map[node] = result
        return result

    def transform_assignment(
            self, node: parse_tree.Assignment
    ) -> Optional[TypeAnnotation]:
        is_new_variable = False

        target_type = None  # type: Optional[TypeAnnotation]
        if isinstance(node.target, parse_tree.Name):
            target_type = self._environment.get(node.target.identifier, None)
            if target_type is None:
                is_new_variable = True
        else:
            target_type = self.transform(node.target)

        value_type = self.transform(node.value)

        if (not is_new_variable and target_type is None) or (value_type is None):
            return None

        if (
                target_type is not None
                and not _assignable(target_type=target_type, value_type=value_type)
        ):
            self.errors.append(
                Error(
                    node.original_node,
                    f"We inferred the target type of the assignment to "
                    f"be {target_type}, while the value type is inferred to "
                    f"be {value_type}. We do not know how to model this assignment."
                )
            )
            return None

        if is_new_variable:
            assert isinstance(node.target, parse_tree.Name)
            self._environment[node.target.identifier] = value_type

        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result

    def transform_return(
            self, node: parse_tree.Return
    ) -> Optional[TypeAnnotation]:
        # Just recurse to fill ``type_map`` on ``value`` even though we know the type
        # in advance
        success = self.transform(node.value) is not None
        if not success:
            return None

        # Treat ``return`` as a statement
        result = PrimitiveTypeAnnotation(PrimitiveType.NONE)
        self.type_map[node] = result
        return result
