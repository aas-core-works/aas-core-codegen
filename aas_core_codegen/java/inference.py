import contextlib
from typing import Mapping, MutableMapping, Optional, List, Final, Union

from icontract import ensure, require

from aas_core_codegen.common import (
    Identifier,
    Error,
    assert_never,
)
from aas_core_codegen.intermediate import _types
from aas_core_codegen.parse import tree as parse_tree
from aas_core_codegen.intermediate.type_inference import (
    _assignable,
    BuiltinFunction,
    BuiltinFunctionTypeAnnotation,
    EnumerationAsTypeTypeAnnotation,
    Environment,
    ImmutableEnvironment,
    ListTypeAnnotation,
    MethodTypeAnnotation,
    MutableEnvironment,
    OptionalTypeAnnotation,
    OurTypeAnnotation,
    PRIMITIVE_TYPE_MAP,
    PrimitiveType,
    PrimitiveTypeAnnotation,
    SetTypeAnnotation,
    TypeAnnotationUnion,
    VerificationTypeAnnotation,
    beneath_optional,
    convert_type_annotation,
)


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
        self._non_null = _CountingMap()

        self.type_map = dict()
        self.errors = []

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

        node_type = beneath_optional(instance_type)

        if isinstance(node_type, OurTypeAnnotation):
            if not isinstance(node_type.our_type, _types.Class):
                self.errors.append(
                    Error(
                        node.instance.original_node,
                        f"Expected an instance type as our type to be a class, "
                        f"but got: {node_type.our_type}",
                    )
                )
                return None

            cls = node_type.our_type
            assert isinstance(cls, _types.Class)

            prop = cls.properties_by_name.get(node.name, None)
            if prop is not None:
                result = convert_type_annotation(prop.type_annotation)

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
                    f"The member {node.name!r} could not be found "
                    f"in the class {cls.name!r}",
                )
            )

        elif isinstance(node_type, (EnumerationAsTypeTypeAnnotation)):
            enumeration = node_type.enumeration
            literal = enumeration.literals_by_name.get(node.name, None)
            if literal is not None:
                result = OurTypeAnnotation(our_type=enumeration)

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

        if not isinstance(collection_type, ListTypeAnnotation):
            self.errors.append(
                Error(
                    node.collection.original_node,
                    f"Expected an index access on a list, but got: {collection_type}",
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

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_implication(
        self, node: parse_tree.Implication
    ) -> Optional["TypeAnnotationUnion"]:
        # NOTE (mristin, 2022-06-17):
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

                        # fmt: off
                        exit_stack.callback(
                            lambda a_canonical_repr=canonical_repr:
                            self._non_null.decrement(a_canonical_repr)
                        )
                        # fmt: on
            else:
                # NOTE (mristin, 2022-06-17):
                # We do not know how to infer any non-nullness in this case.
                pass

            success = (self.transform(node.consequent) is not None) and success

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
            result = convert_type_annotation(member_type.method.returns)

        assert result is not None

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
                    result = convert_type_annotation(func_type.func.returns)
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
                    SetTypeAnnotation,
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
                return None

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

                if isinstance(value_node, parse_tree.IsNotNone):
                    canonical_repr = self._representation_map[value_node.value]
                    self._non_null.increment(canonical_repr)

                    # fmt: off
                    exit_stack.callback(
                        lambda a_canonical_repr=canonical_repr:
                        self._non_null.decrement(a_canonical_repr)
                    )
                    # fmt: on

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    def transform_or(self, node: parse_tree.Or) -> Optional["TypeAnnotationUnion"]:
        # Just recurse to fill ``type_map`` on ``values`` even though we know the type
        # in advance

        success = True

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

        if not success:
            return None

        result = PrimitiveTypeAnnotation(PrimitiveType.BOOL)
        self.type_map[node] = result
        return result

    @staticmethod
    def _binary_operation_name_with_capital_the(
        node: Union[parse_tree.Add, parse_tree.Sub]
    ) -> str:
        if isinstance(node, parse_tree.Add):
            return "The addition"

        elif isinstance(node, parse_tree.Sub):
            return "The subtraction"

        else:
            assert_never(node)

    def _transform_add_or_sub(
        self, node: Union[parse_tree.Add, parse_tree.Sub]
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

        if not (
            isinstance(left_type, PrimitiveTypeAnnotation)
            and left_type.a_type
            in (
                PrimitiveType.INT,
                PrimitiveType.FLOAT,
                PrimitiveType.LENGTH,
            )
        ):
            self.errors.append(
                Error(
                    node.left.original_node,
                    f"{Inferrer._binary_operation_name_with_capital_the(node)} is "
                    f"only defined on integer and floating-point numbers, "
                    f"but got as a left operand: {left_type}",
                )
            )
            success = False

        if not (
            isinstance(right_type, PrimitiveTypeAnnotation)
            and right_type.a_type
            in (
                PrimitiveType.INT,
                PrimitiveType.FLOAT,
                PrimitiveType.LENGTH,
            )
        ):
            self.errors.append(
                Error(
                    node.right.original_node,
                    f"{Inferrer._binary_operation_name_with_capital_the(node)} is "
                    f"only defined on integer and floating-point numbers, "
                    f"but got as a right operand: {right_type}",
                )
            )
            success = False

        if not success:
            return None

        assert isinstance(left_type, PrimitiveTypeAnnotation)
        assert isinstance(right_type, PrimitiveTypeAnnotation)

        # fmt: off
        if (
            (
                left_type.a_type is PrimitiveType.FLOAT
                and right_type.a_type is not PrimitiveType.FLOAT
            ) or (
                right_type.a_type is PrimitiveType.FLOAT
                and left_type.a_type is not PrimitiveType.FLOAT
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
        # noinspection PyUnusedLocal
        result_type = None  # type: Optional[PrimitiveType]
        if (
            (
                left_type.a_type is PrimitiveType.LENGTH
                and right_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
            ) or (
                right_type.a_type is PrimitiveType.LENGTH
                and left_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
            )
        ):
            result_type = PrimitiveType.LENGTH

        elif (
                left_type.a_type is PrimitiveType.INT
                and right_type.a_type is PrimitiveType.INT
        ):
            result_type = PrimitiveType.INT

        elif (
                left_type.a_type is PrimitiveType.FLOAT
                and right_type.a_type is PrimitiveType.FLOAT
        ):
            result_type = PrimitiveType.FLOAT
        else:
            raise AssertionError(
                f"Unhandled execution path: {left_type=}, {right_type=}"
            )
        # fmt: on

        assert result_type is not None

        result = PrimitiveTypeAnnotation(a_type=result_type)
        self.type_map[node] = result
        return result

    def transform_add(self, node: parse_tree.Add) -> Optional["TypeAnnotationUnion"]:
        return self._transform_add_or_sub(node)

    def transform_sub(self, node: parse_tree.Sub) -> Optional["TypeAnnotationUnion"]:
        return self._transform_add_or_sub(node)

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
            iter_type = iter_type.value

        if not isinstance(iter_type, ListTypeAnnotation):
            self.errors.append(
                Error(
                    node.iteration.original_node,
                    f"Expected an iteration over a list, but got: {iter_type}",
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

        # region Pick the larger integer type for the type of the loop variable
        assert isinstance(
            start_type, PrimitiveTypeAnnotation
        ) and start_type.a_type in (PrimitiveType.INT, PrimitiveType.LENGTH)
        assert isinstance(end_type, PrimitiveTypeAnnotation) and end_type.a_type in (
            PrimitiveType.INT,
            PrimitiveType.LENGTH,
        )

        # noinspection PyUnusedLocal
        loop_variable_type = None  # type: Optional[PrimitiveTypeAnnotation]
        if (
            start_type.a_type is PrimitiveType.LENGTH
            or end_type.a_type is PrimitiveType.LENGTH
        ):
            loop_variable_type = PrimitiveTypeAnnotation(a_type=PrimitiveType.LENGTH)
        else:
            assert (
                start_type.a_type is PrimitiveType.INT
                and end_type.a_type is PrimitiveType.INT
            )
            loop_variable_type = PrimitiveTypeAnnotation(a_type=PrimitiveType.INT)

        assert loop_variable_type is not None

        # endregion

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

    return ImmutableEnvironment(mapping=mapping, parent=None)
