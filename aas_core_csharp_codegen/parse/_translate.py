"""Translate the abstract syntax tree of the meta-model into parsed structures."""
import ast
import collections
import enum
import io
import textwrap
from typing import List, Any, Optional, cast, Type, Tuple, Union, Mapping

import asttokens
import docutils.io
import docutils.core
import docutils.nodes
import docutils.utils.error_reporting
from icontract import ensure, require

from aas_core_csharp_codegen.common import (
    Error,
    Identifier,
    IDENTIFIER_RE,
    LinenoColumner,
    assert_never,
)
from aas_core_csharp_codegen.parse import tree, _rules
from aas_core_csharp_codegen.parse._types import (
    AbstractClass,
    Argument,
    AtomicTypeAnnotation,
    ConcreteClass,
    Invariant,
    Contract,
    Contracts,
    Default,
    Class,
    Enumeration,
    EnumerationLiteral,
    final_in_type_annotation,
    is_string_expr,
    JsonSerialization,
    Method,
    Property,
    SelfTypeAnnotation,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation,
    UnverifiedSymbolTable, BUILTIN_ATOMIC_TYPES, BUILTIN_COMPOSITE_TYPES, Description,
    XmlSerialization
)


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def source_to_atok(
        source: str,
) -> Tuple[Optional[asttokens.ASTTokens], Optional[Exception]]:
    """
    Parse the Python code.

    :param source: Python code as text
    :return: parsed module or error, if any
    """
    try:
        atok = asttokens.ASTTokens(source, parse=True)
    except Exception as error:
        return None, error

    return atok, None


class _ExpectedImportsVisitor(ast.NodeVisitor):
    # pylint: disable=invalid-name
    # pylint: disable=missing-docstring

    def __init__(self) -> None:
        self.errors = []  # type: List[Error]

    def visit_Import(self, node: ast.Import) -> Any:
        self.errors.append(Error(
            node,
            f"Unexpected ``import ...``. "
            f"Only ``from ... import...`` statements are expected.",
        )
        )

    _EXPECTED_NAME_FROM_MODULE = collections.OrderedDict(
        [
            ("Enum", "enum"),
            ("Final", "typing"),
            ("List", "typing"),
            ("Optional", "typing"),
            ("DBC", "icontract"),
            ("invariant", "icontract"),
            ("ensure", "icontract"),
            ("require", "icontract"),
            ("abstract", "aas_core_meta.marker"),
            ("implementation_specific", "aas_core_meta.marker"),
            ('reference_in_the_book', "aas_core_meta.marker"),
            ("is_superset_of", "aas_core_meta.marker"),
            ("json_serialization", "aas_core_meta.marker"),
            ("xml_serialization", "aas_core_meta.marker"),
            ("are_unique", "aas_core_meta.verification"),
            ("is_IRI", "aas_core_meta.verification"),
            ("is_IRDI", "aas_core_meta.verification"),
            ("is_ID_short", "aas_core_meta.verification"),
        ]
    )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for name in node.names:
            assert isinstance(name, ast.alias)
            if name.asname is not None:
                self.errors.append(Error(
                    name,
                    f"Unexpected ``from ... import ... as ...``. "
                    f"Only ``from ... import...`` statements are expected."))
            else:
                if name.name not in self._EXPECTED_NAME_FROM_MODULE:
                    self.errors.append(Error(
                        name,
                        f"Unexpected import of a name {name.name!r}."))

                else:
                    expected_module = self._EXPECTED_NAME_FROM_MODULE[name.name]
                    if expected_module != node.module:
                        self.errors.append(Error(
                            name,
                            f"Expected to import {name.name!r} "
                            f"from the module {expected_module}, "
                            f"but it is imported from {node.module}."))


def check_expected_imports(atok: asttokens.ASTTokens) -> List[str]:
    """
    Check that only expected imports are stated in the module.

    This is important so that we can parse type annotations and inheritances.

    Return errors, if any.
    """
    visitor = _ExpectedImportsVisitor()
    visitor.visit(atok.tree)

    if len(visitor.errors) == 0:
        return []

    lineno_columner = LinenoColumner(atok=atok)
    return [lineno_columner.error_message(error) for error in visitor.errors]


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _enum_to_symbol(
        node: ast.ClassDef, atok: asttokens.ASTTokens
) -> Tuple[Optional[Enumeration], Optional[Error]]:
    """Interpret a class which defines an enumeration."""
    is_superset_of = None  # type: Optional[List[Identifier]]
    for decorator_node in node.decorator_list:
        if (
                isinstance(decorator_node, ast.Call)
                and isinstance(decorator_node.func, ast.Name)
                and decorator_node.func.id == 'is_superset_of'
        ):
            if is_superset_of is not None:
                return None, Error(
                    decorator_node,
                    "Double definitions of ``is_superset_of`` are not allowed")

            superset_arg_node = None  # type: Optional[ast.AST]
            if len(decorator_node.args) >= 1:
                superset_arg_node = decorator_node.args[0]
            elif len(decorator_node.keywords) > 0:
                for keyword in decorator_node.keywords:
                    if keyword.arg == 'enums':
                        superset_arg_node = keyword.value
            else:
                pass

            if superset_arg_node is None:
                return None, Error(
                    decorator_node,
                    "The ``enums`` argument is missing in the ``is_superset_of`` "
                    "decorator")

            if not isinstance(superset_arg_node, ast.List):
                return None, Error(
                    decorator_node,
                    "Expected the ``enums`` argument of the ``is_superset_of`` "
                    "to be a list literal, but it is not")

            is_superset_of = []

            for elt in superset_arg_node.elts:
                if not isinstance(elt, ast.Name):
                    return None, Error(
                        decorator_node,
                        f"Expected all elements of the ``enums`` argument to "
                        f"the ``is_superset_of`` to be a list literal of enum names, "
                        f"but got: {ast.dump(elt)}")

                is_superset_of.append(Identifier(elt.id))

        elif (
                isinstance(decorator_node, ast.Call)
                and isinstance(decorator_node.func, ast.Name)
                and decorator_node.func.id == 'reference_in_the_book'
        ):
            # NOTE (mristin, 2021-11-17):
            # We ignore references at the moment. At some later point, it might
            # make sense to integrate them in the generated code.
            pass

        else:
            return None, Error(
                decorator_node,
                f"We do not know how to handle this decorator node "
                f"for an Enum: {ast.dump(decorator_node)}")

    if is_superset_of is None:
        is_superset_of = []

    if len(node.body) == 0:
        return (
            Enumeration(
                name=Identifier(node.name),
                is_superset_of=is_superset_of,
                literals=[], description=None, node=node
            ),
            None,
        )

    enumeration_literals = []  # type: List[EnumerationLiteral]

    description = None  # type: Optional[Description]

    cursor = 0
    while cursor < len(node.body):
        old_cursor = cursor

        body_node = node.body[cursor]  # type: ast.AST

        if cursor == 0 and is_string_expr(body_node):
            assert isinstance(body_node, ast.Expr)
            description, error = _string_constant_to_description(body_node.value)
            if error is not None:
                return None, error

            cursor += 1

        elif isinstance(body_node, ast.Pass):
            cursor += 1

        elif isinstance(body_node, ast.Assign):
            assign = body_node

            if len(assign.targets) != 1:
                return (None, Error(
                    assign,
                    f"Expected a single target in the assignment, "
                    f"but got: {len(assign.targets)}"))

            if not isinstance(assign.targets[0], ast.Name):
                return (None, Error(
                    assign.targets[0],
                    f"Expected a name as a target of the assignment, "
                    f"but got: {assign.targets[0]}"))

            if not isinstance(assign.value, ast.Constant):
                return (None, Error(
                    assign.value,
                    f"Expected a constant in the enumeration assignment, "
                    f"but got: {atok.get_text(assign.value)}"))

            if not isinstance(assign.value.value, str):
                return (None, Error(
                    assign.value,
                    f"Expected a string literal in the enumeration, "
                    f"but got: {assign.value.value}"))

            literal_name = Identifier(assign.targets[0].id)
            literal_value = assign.value.value

            literal_description = None  # type: Optional[Description]
            next_expr = node.body[cursor + 1] if cursor < len(node.body) - 1 else None

            if next_expr is not None and is_string_expr(next_expr):
                assert isinstance(next_expr, ast.Expr)
                literal_description, error = _string_constant_to_description(
                    next_expr.value)

                if error is not None:
                    return None, error

                cursor += 1

            enumeration_literals.append(
                EnumerationLiteral(
                    name=literal_name,
                    value=Identifier(literal_value),
                    description=literal_description,
                    node=assign))

            cursor += 1

        else:
            return (None, Error(
                node.body[cursor],
                f"Expected either a docstring or an assignment "
                f"in an enumeration, "
                f"but got: {atok.get_text(node.body[cursor])}"))

        assert cursor > old_cursor, f"Loop invariant: {cursor=}, {old_cursor=}"

    return (
        Enumeration(
            name=Identifier(node.name),
            is_superset_of=is_superset_of,
            literals=enumeration_literals,
            description=description,
            node=node),
        None)


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _type_annotation(
        node: ast.AST, atok: asttokens.ASTTokens
) -> Tuple[Optional[TypeAnnotation], Optional[Error]]:
    """Parse the type annotation."""
    if isinstance(node, ast.Name):
        if node.id == "Final":
            return (
                None,
                Error(
                    node,
                    "The type annotation is expected with subscript(s), "
                    "but got none: Final",
                ),
            )

        return AtomicTypeAnnotation(identifier=Identifier(node.id), node=node), None

    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, str):
            return (None, Error(
                node.value,
                f"Expected a string literal "
                f"if the type annotation is given as a constant, "
                f"but got: "
                f"{node.value!r} (as {type(node.value)})"))

        return AtomicTypeAnnotation(identifier=Identifier(node.value), node=node), None

    elif isinstance(node, ast.Subscript):
        if not isinstance(node.value, ast.Name):
            return (None, Error(
                node.value,
                f"Expected a name to define "
                f"a subscripted type annotation,"
                f"but got: {atok.get_text(node.value)}"))

        if isinstance(node.slice, ast.Index):
            subscripts = []  # type: List[TypeAnnotation]

            if isinstance(node.slice.value, ast.Tuple):
                for elt in node.slice.value.elts:
                    subscript_annotation, error = _type_annotation(node=elt, atok=atok)
                    if error is not None:
                        return None, error

                    assert subscript_annotation is not None

                    subscripts.append(subscript_annotation)

            elif isinstance(node.slice.value, (ast.Name, ast.Subscript, ast.Constant)):
                subscript_annotation, error = _type_annotation(
                    node=node.slice.value, atok=atok
                )
                if error is not None:
                    return None, error

                assert subscript_annotation is not None

                subscripts.append(subscript_annotation)

            else:
                return (
                    None,
                    Error(
                        node.slice.value,
                        f"Expected a tuple, a name, a subscript or a string literal "
                        f"for a subscripted type annotation, "
                        f"but got: {atok.get_text(node.slice.value)}",
                    ),
                )

            return (
                SubscriptedTypeAnnotation(
                    identifier=Identifier(node.value.id), subscripts=subscripts,
                    node=node
                ),
                None,
            )

        else:
            return (None, Error(
                node.slice,
                f"Expected an index to define "
                f"a subscripted type annotation, "
                f"but got: {atok.get_text(node.slice)}"))
    else:
        return (
            None,
            Error(
                node,
                f"Expected either atomic type annotation (as name or string literal) "
                f"or a subscripted one (as a subscript), "
                f"but got: {atok.get_text(node)} (as {type(node)})",
            ),
        )


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _ann_assign_to_property(
        node: ast.AnnAssign, description: Optional[str], atok: asttokens.ASTTokens
) -> Tuple[Optional[Property], Optional[Error]]:
    if not isinstance(node.target, ast.Name):
        return (
            None,
            Error(
                node.target,
                f"Expected property target to be a name, "
                f"but got: {atok.get_text(node.target)}",
            ),
        )

    if not node.simple:
        return (
            None,
            Error(
                node.target,
                f"Expected a property with a simple target " f"(no parentheses!)",
            ),
        )

    if node.annotation is None:
        return (
            None,
            Error(node.target, f"Expected property to be annotated with a type"),
        )

    type_annotation, error = _type_annotation(node=node.annotation, atok=atok)
    if error is not None:
        return None, error

    assert type_annotation is not None

    if node.value is not None:
        return (
            None,
            Error(node.value, f"Unexpected assignment of a value to a property"),
        )

    is_readonly = False
    if (
            isinstance(type_annotation, SubscriptedTypeAnnotation)
            and type_annotation.identifier == "Final"
    ):
        if len(type_annotation.subscripts) != 1:
            return (
                None,
                Error(
                    node.annotation,
                    f"Expected a single subscript for Final type, "
                    f"but got {len(type_annotation.subscripts)}",
                ),
            )

        type_annotation = type_annotation.subscripts[0]
        is_readonly = True

        if final_in_type_annotation(type_annotation=type_annotation):
            return (
                None,
                Error(
                    node.annotation,
                    f"Unexpected nested Final type qualifier: "
                    f"{atok.get_text(node.annotation)}",
                ),
            )

    return (
        Property(
            name=Identifier(node.target.id),
            type_annotation=type_annotation,
            description=description,
            is_readonly=is_readonly,
            node=node,
        ),
        None,
    )


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _args_to_arguments(
        node: ast.arguments, atok: asttokens.ASTTokens
) -> Tuple[Optional[List[Argument]], Optional[Error]]:
    """Parse arguments of a method."""
    if hasattr(node, "posonlyargs") and len(node.posonlyargs) > 0:
        return None, Error(node, f"Unexpected positional-only arguments")

    if node.vararg is not None or node.kwarg is not None:
        return None, Error(node, f"Unexpected variable arguments")

    if len(node.kwonlyargs) > 0:
        return None, Error(node, f"Unexpected keyword-only arguments")

    assert len(node.kw_defaults) == 0, (
        "No keyword-only arguments implies "
        "there should be no defaults "
        "for keyword-only arguments either."
    )

    if len(node.args) == 0:
        return None, Error(node, f"Unexpected no arguments")

    arguments = []  # type: List[Argument]

    # region ``self``

    if node.args[0].arg != "self":
        return None, Error(node, f"Unexpected no ``self`` in arguments")

    if node.args[0].annotation is not None:
        return (
            None,
            Error(
                node.args[0],
                f"Unexpected type annotation for the method argument ``self``",
            ),
        )

    if len(node.defaults) == len(node.args):
        return (
            None,
            Error(
                node.args[0],
                f"Unexpected default value for the method argument ``self``",
            ),
        )

    arguments.append(
        Argument(
            name=Identifier("self"),
            type_annotation=SelfTypeAnnotation(),
            default=None,
            node=node.args[0],
        )
    )

    # endregion

    # region Non-self arguments

    for i in range(1, len(node.args)):
        arg_node = node.args[i]

        # region Type annotation
        if arg_node.annotation is None:
            return (
                None,
                Error(
                    arg_node,
                    f"Unexpected method argument without a type annotation: "
                    f"{arg_node.arg}",
                ),
            )

        type_annotation, error = _type_annotation(node=arg_node.annotation, atok=atok)
        if error is not None:
            return (
                None,
                Error(
                    arg_node,
                    f"Failed to parse the type annotation "
                    f"of the method argument {arg_node.arg}: "
                    f"{atok.get_text(arg_node.annotation)}",
                    underlying=[error],
                ),
            )

        assert type_annotation is not None

        if final_in_type_annotation(type_annotation=type_annotation):
            return (
                None,
                Error(
                    arg_node,
                    f"Unexpected ``Final`` in the type annotation "
                    f"of the method argument {arg_node.arg}: "
                    f"{atok.get_text(arg_node.annotation)}",
                ),
            )

        assert type_annotation is not None
        # endregion

        # region Default
        default = None  # type: Optional[Default]
        offset = len(node.args) - len(node.defaults)
        if i >= offset:
            default = Default(node=node.defaults[i - offset])

        # endregion

        arguments.append(
            Argument(
                name=Identifier(arg_node.arg),
                type_annotation=type_annotation,
                default=default,
                node=arg_node,
            )
        )

    # endregion

    return arguments, None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _parse_contract_condition(
        node: ast.Call, atok: asttokens.ASTTokens
) -> Tuple[Optional[Contract], Optional[Error]]:
    """Parse the contract decorator."""
    condition_node = None  # type: Optional[ast.AST]
    description_node = None  # type: Optional[ast.AST]

    if len(node.args) >= 1:
        condition_node = node.args[0]

    if len(node.args) >= 2:
        description_node = node.args[1]

    for keyword in node.keywords:
        if keyword.arg == "condition":
            condition_node = keyword.value

        elif keyword.arg == "description":
            description_node = keyword.value

        else:
            # We simply ignore to parse the argument.
            pass

    if condition_node is None:
        return (
            None,
            Error(node, "Expected the condition to be defined for a contract"),
        )

    if not isinstance(condition_node, ast.Lambda):
        return (
            None,
            Error(
                condition_node,
                f"Expected a lambda function as a contract condition, "
                f"but got: {atok.get_text(condition_node)}",
            ),
        )

    description = None  # type: Optional[Description]
    if description_node is not None:
        if not (
                isinstance(description_node, ast.Constant)
                and isinstance(description_node.value, str)
        ):
            return (
                None,
                Error(
                    description_node,
                    f"Expected a string literal as a contract description, "
                    f"but got: {atok.get_text(description_node)!r}",
                ))

        description, error = _string_constant_to_description(description_node)
        if error is not None:
            return None, error

    return (
        Contract(
            args=[Identifier(arg.arg) for arg in condition_node.args.args],
            description=description,
            condition=condition_node,
            node=node
        ),
        None)


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _parse_snapshot(
        node: ast.Call, atok: asttokens.ASTTokens
) -> Tuple[Optional[Snapshot], Optional[Error]]:
    """Parse the snapshot decorator."""
    capture_node = None  # type: Optional[ast.AST]
    name_node = None  # type: Optional[ast.AST]

    if len(node.args) >= 1:
        capture_node = node.args[0]

    if len(node.args) >= 2:
        name_node = node.args[1]

    for keyword in node.keywords:
        if keyword.arg == "capture":
            capture_node = keyword.value

        elif keyword.arg == "name":
            name_node = keyword.value

        else:
            # We simply ignore to parse the argument.
            pass

    if capture_node is None:
        return None, Error(node, "Expected the capture to be defined for a snapshot")

    if not isinstance(capture_node, ast.Lambda):
        return (
            None,
            Error(
                capture_node,
                f"Expected a lambda function as a capture of a snapshot, "
                f"but got: {atok.get_text(capture_node)}",
            )
        )

    if name_node is not None and not (
            isinstance(name_node, ast.Constant) and isinstance(name_node.value, str)
    ):
        return (
            None,
            Error(
                name_node,
                f"Expected a string literal as a capture name, "
                f"but got: {atok.get_text(name_node)}",
            ),
        )

    if name_node is not None:
        name = name_node.value
    elif len(capture_node.args.args) == 1 and name_node is None:
        name = capture_node.args.args[0].arg
    else:
        return (
            None,
            Error(
                node,
                f"Expected the name of the snapshot to be defined, "
                f"but there was neither the single argument in the capture "
                f"nor explicit ``name`` given",
            ),
        )

    if not IDENTIFIER_RE.fullmatch(name):
        return (
            None,
            Error(
                name_node if name_node is not None else node,
                f"Expected a capture name to be a valid identifier, but got: {name!r}",
            ),
        )

    return (
        Snapshot(
            args=[Identifier(arg.arg) for arg in capture_node.args.args],
            name=Identifier(name),
            capture=capture_node,
            node=node
        ),
        None,
    )


# TODO: include severity levels for contracts in the meta model and
#  consider them in the imports
# TODO: test for unknown severity level


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _function_def_to_method(
        node: ast.FunctionDef, atok: asttokens.ASTTokens
) -> Tuple[Optional[Method], Optional[Error]]:
    """Parse the function definition into a class method."""
    name = node.name

    if name != "__init__" and name.startswith("__") and name.endswith("__"):
        return (
            None,
            Error(
                node,
                f"Among all dunder methods, only ``__init__`` is expected, "
                f"but got: {name}",
            ),
        )

    preconditions = []  # type: List[Contract]
    postconditions = []  # type: List[Contract]
    snapshots = []  # type: List[Snapshot]

    is_implementation_specific = False

    # region Parse decorators

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                if decorator.func.id == "require":
                    precondition, error = _parse_contract_condition(
                        node=decorator, atok=atok
                    )
                    if error is not None:
                        return None, error

                    assert precondition is not None

                    preconditions.append(precondition)

                elif decorator.func.id == "ensure":
                    postcondition, error = _parse_contract_condition(
                        node=decorator, atok=atok
                    )
                    if error is not None:
                        return None, error

                    assert postcondition is not None

                    postconditions.append(postcondition)

                elif decorator.func.id == "snapshot":
                    snapshot, error = _parse_snapshot(node=decorator, atok=atok)
                    if error is not None:
                        return None, error

                    assert snapshot is not None

                    snapshots.append(snapshot)

                else:
                    return (
                        None,
                        Error(
                            decorator,
                            f"Unexpected decorator of a method: {decorator.func.id}; "
                            f"expected at most "
                            f"``require``, ``ensure`` or ``snapshot``",
                        ),
                    )
            else:
                return (
                    None,
                    Error(
                        decorator,
                        f"Unexpected non-name decorator of a method: "
                        f"{atok.get_text(decorator.func)!r}",
                    ),
                )

        elif isinstance(decorator, ast.Name):
            if decorator.id != "implementation_specific":
                return (
                    None,
                    Error(
                        decorator,
                        f"Unexpected simple decorator of a method: {decorator.id}; "
                        f"expected at most ``implementation_specific``",
                    ),
                )
            else:
                is_implementation_specific = True
        else:
            return (
                None,
                Error(
                    decorator,
                    f"Expected decorators of a method to be "
                    f"only ``ast.Name`` and ``ast.Call``, "
                    f"but got: {atok.get_text(decorator)!r}",
                ),
            )

    # endregion

    # region Reverse contracts

    # We need to reverse the contracts since the decorators are evaluated from bottom
    # up, while we parsed them from top to bottom.
    preconditions = list(reversed(preconditions))
    snapshots = list(reversed(snapshots))
    postconditions = list(reversed(postconditions))

    # endregion

    # region Parse arguments and body

    description = None  # type: Optional[Description]
    body = node.body

    if len(node.body) >= 1 and is_string_expr(expr=node.body[0]):
        assert isinstance(node.body[0], ast.Expr)
        assert isinstance(node.body[0].value, ast.Constant)

        description, error = _string_constant_to_description(
            constant=node.body[0].value)

        if error is not None:
            return None, error

        body = node.body[1:]

    arguments, error = _args_to_arguments(node=node.args, atok=atok)
    if error is not None:
        return (
            None,
            Error(
                node,
                f"Failed to parse arguments of the method: {name}",
                underlying=[error],
            ),
        )

    assert arguments is not None

    returns = None  # type: Optional[TypeAnnotation]
    if node.returns is None:
        return (
            None,
            Error(
                node,
                f"Unexpected method without a type annotation for the result: {name}",
            ),
        )

    if not (isinstance(node.returns, ast.Constant) and node.returns.value is None):
        returns, error = _type_annotation(node=node.returns, atok=atok)
        if error is not None:
            return None, error

    # endregion

    # region All contract arguments are included in the function arguments

    function_arg_set = set(arg.name for arg in arguments)

    for contract in preconditions:
        for arg in contract.args:
            if arg not in function_arg_set:
                return (
                    None,
                    Error(
                        contract.condition,
                        f"The argument of the precondition is not provided "
                        f"in the method: {arg}",
                    ),
                )

    has_snapshots = len(snapshots) > 0
    for contract in postconditions:
        for arg in contract.args:
            if arg == "OLD":
                if not has_snapshots and arg == "OLD":
                    return (
                        None,
                        Error(
                            contract.condition,
                            f"The argument OLD of the postcondition is not provided "
                            f"since there were no snapshots defined "
                            f"for the method: {name}",
                        ),
                    )

            elif arg == "result":
                continue

            elif arg not in function_arg_set:
                return (
                    None,
                    Error(
                        contract.condition,
                        f"The argument of the postcondition is not provided "
                        f"in the method: {arg}",
                    ),
                )
            else:
                # Everything is OK.
                pass

    for snapshot in snapshots:
        for arg in snapshot.args:
            if arg not in function_arg_set:
                return (
                    None,
                    Error(
                        snapshot.capture,
                        f"The argument of the snapshot is not provided "
                        f"in the method: {arg}",
                    ),
                )

    # endregion

    # region __init__ must return None
    if name == "__init__" and returns is not None:
        return (
            None,
            Error(
                node,
                f"Expected __init__ to return None, "
                f"but got: {atok.get_text(node.returns)}",
            ),
        )
    # endregion

    return (
        Method(
            name=Identifier(name),
            is_implementation_specific=is_implementation_specific,
            arguments=arguments,
            returns=returns,
            description=description,
            contracts=Contracts(
                preconditions=preconditions,
                snapshots=snapshots,
                postconditions=postconditions,
            ),
            body=body,
            node=node,
        ),
        None,
    )


@require(lambda constant: isinstance(constant.value, str))
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _string_constant_to_description(
        constant: ast.Constant
) -> Tuple[Optional[Description], Optional[Error]]:
    """Extract the docstring from the given string constant."""
    text = constant.value
    assert isinstance(text, str), (
        f"Expected a string constant node, but got: {ast.dump(constant)!r}")

    dedented = textwrap.dedent(text)

    warnings = io.StringIO()
    document = None  # type: Optional[docutils.nodes.document]
    try:
        document = docutils.core.publish_doctree(
            dedented,
            settings_overrides={
                "warning_stream": warnings
            })
    except Exception as err:
        return None, Error(
            constant,
            f"Failed to parse the description with docutils: {err}")

    warnings_text = warnings.getvalue()
    if warnings_text:
        return None, Error(
            constant,
            f"Failed to parse the description with docutils:\n{warnings_text.strip()}")

    assert document is not None

    return Description(document=document, node=constant), None


class _ClassMarker(enum.Enum):
    ABSTRACT = "abstract"
    IMPLEMENTATION_SPECIFIC = "implementation_specific"


_CLASS_MARKER_FROM_STRING: Mapping[str, _ClassMarker] = {
    marker.value: marker
    for marker in _ClassMarker
}


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _class_decorator_to_marker(
        decorator: ast.Name
) -> Tuple[Optional[_ClassMarker], Optional[Error]]:
    """Parse a simple decorator as a class marker."""
    class_marker = _CLASS_MARKER_FROM_STRING.get(decorator.id, None)

    if class_marker is None:
        return (None, Error(
            decorator,
            f"The handling of the marker has not been implemented: {decorator.id!r}"
        ))

    return class_marker, None


# fmt: off
@require(
    lambda decorator:
    isinstance(decorator.func, ast.Name)
    and isinstance(decorator.func.ctx, ast.Load)
    and decorator.func.id == 'json_serialization'
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _class_decorator_to_json_serialization(
        decorator: ast.Call
) -> Tuple[Optional[JsonSerialization], Optional[Error]]:
    """Translate a decorator to settings of the JSON serialization."""
    with_model_type_node = None  # type: Optional[ast.AST]

    if len(decorator.args) >= 1:
        with_model_type_node = decorator.args[0]

    if len(decorator.keywords) > 0:
        for kwarg in decorator.keywords:
            if kwarg.arg == 'with_model_type':
                with_model_type_node = kwarg.value
            else:
                return (None, Error(
                    decorator,
                    f"Handling of the keyword argument {kwarg.arg!r} "
                    f"for the json_serialization has not been implemented"))

    with_model_type = None  # type: Optional[bool]
    if with_model_type_node is not None:
        if not isinstance(with_model_type_node, ast.Constant):
            return (None, Error(
                with_model_type_node,
                f"Expected the value for ``with_model_type`` parameter "
                f"to be a constant, but got: {ast.dump(with_model_type_node)}"))

        if not isinstance(with_model_type_node.value, bool):
            return (None, Error(
                with_model_type_node,
                f"Expected the value for ``with_model_type`` parameter "
                f"to be a boolean, but got: {with_model_type_node.value}"))

        with_model_type = with_model_type_node.value

    return JsonSerialization(with_model_type=with_model_type), None


# fmt: off
@require(
    lambda decorator:
    isinstance(decorator.func, ast.Name)
    and isinstance(decorator.func.ctx, ast.Load)
    and decorator.func.id == 'xml_serialization'
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _class_decorator_to_xml_serialization(
        decorator: ast.Call
) -> Tuple[Optional[XmlSerialization], Optional[Error]]:
    """Translate a decorator to settings of the XML serialization."""
    property_as_text_node = None  # type: Optional[ast.AST]

    if len(decorator.args) >= 1:
        property_as_text_node = decorator.args[0]

    if len(decorator.keywords) > 0:
        for kwarg in decorator.keywords:
            if kwarg.arg == 'property_as_text':
                property_as_text_node = kwarg.value
            else:
                return (None, Error(
                    decorator,
                    f"Handling of the keyword argument {kwarg.arg!r} "
                    f"for the xml_serialization has not been implemented"))

    property_as_text = None  # type: Optional[Identifier]
    if property_as_text_node is not None:
        if not isinstance(property_as_text_node, ast.Constant):
            return (None, Error(
                property_as_text_node,
                f"Expected the value for ``property_as_text`` parameter "
                f"to be a constant, but got: {ast.dump(property_as_text_node)}"))

        if not isinstance(property_as_text_node.value, str):
            return (None, Error(
                property_as_text_node,
                f"Expected the value for ``property_as_text`` parameter "
                f"to be a string, but got: {property_as_text_node.value}"))

        if not IDENTIFIER_RE.fullmatch(property_as_text_node.value):
            return (None, Error(
                property_as_text_node,
                f"Expected the value for ``property_as_text`` parameter "
                f"to be a valid identifier, but got: {property_as_text_node.value}"))

        property_as_text = Identifier(property_as_text_node.value)

    return XmlSerialization(
        property_as_text=property_as_text,
        node=decorator), None


# fmt: off
@require(
    lambda decorator:
    isinstance(decorator.func, ast.Name)
    and isinstance(decorator.func.ctx, ast.Load)
    and decorator.func.id == 'invariant'
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _class_decorator_to_invariant(
        decorator: ast.Call,
        atok: asttokens.ASTTokens
) -> Tuple[Optional[Invariant], Optional[Error]]:
    """Parse the decorator node as a class invariant."""
    condition_node = None  # type: Optional[ast.AST]
    description_node = None  # type: Optional[ast.AST]

    # TODO: test parsing of args and kwargs
    if len(decorator.args) >= 1:
        condition_node = decorator.args[0]

    if len(decorator.args) >= 2:
        description_node = decorator.args[1]

    if len(decorator.keywords) > 0:
        for kwarg in decorator.keywords:
            if kwarg.arg == 'condition':
                condition_node = kwarg.value
            elif kwarg.arg == 'description':
                description_node = kwarg.value
            else:
                return (
                    None, Error(
                        decorator,
                        f"Handling of the keyword argument {kwarg.arg!r} "
                        f"for the invariant has not been implemented"))

    if not isinstance(condition_node, ast.Lambda):
        return (None, Error(
            decorator,
            f"Expected the condition of an invariant to be a lambda, "
            f"but got {type(condition_node)}: {atok.get_text(decorator)}"))

    if (
            description_node is not None
            and (not isinstance(description_node, ast.Constant)
                 or not isinstance(description_node.value, str))
    ):
        return (None, Error(
            decorator,
            f"Expected the description of an invariant to be "
            f"a string literal, but got: {type(description_node)}"))

    if (
            len(condition_node.args.args) != 1
            or condition_node.args.args[0].arg != 'self'
    ):
        return (None, Error(
            decorator,
            "Expected the invariant to have a single argument, ``self``"))

    body, error = _rules.ast_node_to_our_node(node=condition_node.body)
    if error is not None:
        return None, Error(
            condition_node.body, "Failed to parse the invariant", [error])

    if not isinstance(body, tree.Expression):
        return None, Error(
            condition_node.body,
            f"Expected an expression, but got: {tree.dump(body)}")

    return Invariant(
        description=(
            description_node.value
            if description_node is not None
            else None),
        body=body,
        node=decorator), None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _classdef_to_symbol(
        node: ast.ClassDef, atok: asttokens.ASTTokens
) -> Tuple[Optional[Symbol], Optional[Error]]:
    """Interpret the class definition as a symbol."""
    underlying_errors = []  # type: List[Error]

    if node.name.lower() in ['verification']:
        underlying_errors.append(Error(
            node,
            f"The name of the class is reserved for "
            f"aas-core: {node.name!r}"))

    base_names = []  # type: List[str]
    for base in node.bases:
        if not isinstance(base, ast.Name):
            underlying_errors.append(Error(
                base,
                f"Expected a base as a name, but got: {atok.get_text(base)}"))
        else:
            base_names.append(base.id)

    if len(underlying_errors) > 0:
        return (None, Error(
            node,
            f"Failed to parse the class definition: {node.name}",
            underlying=underlying_errors))

    if "Enum" in base_names and len(base_names) > 1:
        return (None, Error(
            node,
            f"Expected an enumeration to only inherit from ``Enum``, "
            f"but it inherits from: {base_names}"))

    if "Enum" in base_names:
        return _enum_to_symbol(node=node, atok=atok)

    # We have to parse the class definition from here on.

    # DBC is only used for inheritance of the contracts in the meta-model
    # so that the developers tinkering with the meta-model can play with it
    # at runtime. We can safely ignore it as we are not looking into any
    # runtime code.
    inheritances = [
        Identifier(base_name) for base_name in base_names if base_name != "DBC"
    ]

    # region Decorators

    invariants = []  # type: List[Invariant]

    is_abstract = False
    is_implementation_specific = False

    json_serialization = None  # type: Optional[JsonSerialization]
    xml_serialization = None  # type: Optional[XmlSerialization]

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            class_marker, error = _class_decorator_to_marker(decorator=decorator)
            if error is not None:
                underlying_errors.append(error)
                continue

            if class_marker == _ClassMarker.ABSTRACT:
                is_abstract = True
            elif class_marker == _ClassMarker.IMPLEMENTATION_SPECIFIC:
                is_implementation_specific = True
            else:
                raise AssertionError(f"Unhandled enum: {class_marker}")

        elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and isinstance(decorator.func.ctx, ast.Load)
        ):
            if decorator.func.id == 'invariant':
                invariant, error = _class_decorator_to_invariant(
                    decorator=decorator, atok=atok)

                if error is not None:
                    underlying_errors.append(error)
                    continue

                invariants.append(invariant)
            elif decorator.func.id == 'json_serialization':
                if json_serialization is not None:
                    underlying_errors.append(Error(
                        decorator,
                        "Repeated markings for JSON serialization are not allowed"))
                    continue

                json_serialization, error = _class_decorator_to_json_serialization(
                    decorator=decorator)

                if error is not None:
                    underlying_errors.append(error)
                    continue

            elif decorator.func.id == 'xml_serialization':
                if xml_serialization is not None:
                    underlying_errors.append(Error(
                        decorator,
                        "Repeated markings for XML serialization are not allowed"))
                    continue

                xml_serialization, error = _class_decorator_to_xml_serialization(
                    decorator=decorator)

                if error is not None:
                    underlying_errors.append(error)
                    continue

            elif decorator.func.id == 'reference_in_the_book':
                # NOTE (mristin, 2021-11-17):
                # We ignore references at the moment. At some later point, it might
                # make sense to integrate them in the generated code.
                pass

            else:
                underlying_errors.append(Error(
                    decorator,
                    f"Handling of a decorator has not been "
                    f"implemented: {decorator.func.id!r}"))
        else:
            underlying_errors.append(
                Error(
                    decorator,
                    message=f"Handling of a decorator has not been "
                            f"implemented: {decorator.id!r}"))

    if len(underlying_errors) > 0:
        return (None, Error(
            node,
            f"Failed to parse the class definition: {node.name}",
            underlying=underlying_errors))

    # endregion

    if is_abstract and is_implementation_specific:
        return (
            None,
            Error(
                node,
                message=f"Abstract classes can not be implementation-specific "
                        f"at the same time "
                        f"(otherwise we can not convert them to interfaces etc.)"))

    description = None  # type: Optional[Description]

    properties = []  # type: List[Property]
    methods = []  # type: List[Method]

    cursor = 0
    while cursor < len(node.body):
        old_cursor = cursor

        expr = node.body[cursor]

        if cursor == 0 and is_string_expr(expr):
            assert isinstance(expr, ast.Expr)
            description, error = _string_constant_to_description(expr.value)
            if error is not None:
                return None, error

            cursor += 1
            continue

        if isinstance(expr, ast.Pass):
            cursor += 1
            continue

        if isinstance(expr, ast.AnnAssign):
            property_description = None  # type: Optional[Description]

            next_expr = node.body[cursor + 1] if cursor < len(node.body) - 1 else None
            if next_expr is not None and is_string_expr(next_expr):
                assert isinstance(next_expr, ast.Expr)
                property_description, error = _string_constant_to_description(
                    next_expr.value)

                if error is not None:
                    return None, error

                cursor += 1

            prop, error = _ann_assign_to_property(
                node=expr, description=property_description, atok=atok
            )
            cursor += 1

            if error is not None:
                return (
                    None,
                    Error(expr, "Failed to parse a property", underlying=[error]),
                )

            assert prop is not None

            properties.append(prop)

        elif isinstance(expr, ast.FunctionDef):
            method, error = _function_def_to_method(node=expr, atok=atok)
            if error is not None:
                return (
                    None,
                    Error(
                        expr,
                        f"Failed to parse the method: {expr.name}",
                        underlying=[error],
                    ),
                )

            assert method is not None
            methods.append(method)

            cursor += 1

        else:
            return (None, Error(
                expr,
                f"Expected only either "
                f"properties explicitly annotated with types or "
                f"instance methods, but got: {atok.get_text(expr)}",
            ))

        assert old_cursor < cursor, f"Loop invariant: {old_cursor=}, {cursor=}"

    if is_abstract:
        factory_for_class = (
            AbstractClass
        )  # type: Union[Type[AbstractClass], Type[ConcreteClass]]
    else:
        factory_for_class = ConcreteClass

    return (
        factory_for_class(
            name=Identifier(node.name),
            is_implementation_specific=is_implementation_specific,
            inheritances=inheritances,
            properties=properties,
            methods=methods,
            invariants=invariants,
            json_serialization=json_serialization,
            xml_serialization=xml_serialization,
            description=description,
            node=node,
        ),
        None,
    )


def _verify_arity_of_type_annotation_subscript(
        type_annotation: SubscriptedTypeAnnotation
) -> Optional[Error]:
    """
    Check that the subscripted type annotation has the expected number of arguments.

    :return: error message, if any
    """
    expected_arity_map = {
        "List": 1,
        "Sequence": 1,
        "Set": 1,
        "Mapping": 2,
        "MutableMapping": 2,
        "Optional": 1,
        "Final": 1
    }
    expected_arity = expected_arity_map.get(type_annotation.identifier, None)
    if expected_arity is None:
        raise AssertionError(
            f"Unexpected subscripted type annotation: {type_annotation}")

    assert expected_arity >= 0
    if len(type_annotation.subscripts) != expected_arity:
        return Error(
            type_annotation.node,
            f"Expected {expected_arity} arguments of "
            f"a subscripted type annotation {type_annotation.identifier!r}, "
            f"but got {len(type_annotation.subscripts)}: {type_annotation}")

    return None


# fmt: off
@ensure(
    lambda result:
    result[1] is None or len(result[1]) > 0,
    "If errors are not None, there must be at least one error"
)
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
# fmt: on
def _verify_symbol_table(
        symbol_table: UnverifiedSymbolTable,
) -> Tuple[Optional[SymbolTable], Optional[List[Error]]]:
    """
    Check that the symbol table is consistent.

    For example, check that there are no dangling references in type annotations or
    inheritances.
    """
    errors = []  # type: List[Error]

    # region Check reserved names

    reserved_symbol_names = {
        'aas',
        'accept',
        'context',
        'class',
        'error',
        'errors',
        'iclass',
        'itransformer_with_context',
        'ivisitor',
        'ivisitor_with_context',
        'jsonization',
        'path',
        'stringification',
        'transform',
        'transformer',
        'transformer_with_context'
        'verification',
        'visit',
        'visitation',
        'visitor',
        'visitor_with_context',
    }
    reserved_member_names = {
        'descend', 'descend_once', 'accept', 'transform', 'model_type', 'property_name'
    }

    for symbol in symbol_table.symbols:
        if symbol.name.lower() in reserved_symbol_names:
            errors.append(Error(
                symbol.node,
                f"The name of the symbol is reserved "
                f"for the code generation: {symbol.name!r}"))

        if isinstance(symbol, Class):
            for method in symbol.methods:
                if method.name in reserved_member_names:
                    errors.append(Error(
                        method.node,
                        f"The name of the method is reserved "
                        f"for the code generation: {method.name!r}"))

            for prop in symbol.properties:
                if prop.name in reserved_member_names:
                    errors.append(Error(
                        prop.node,
                        f"The name of the property is reserved "
                        f"for the code generation: {prop.name!r}"))
    # endregion

    # region Check dangling inheritances

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for inheritance in symbol.inheritances:
            parent_symbol = symbol_table.find(name=inheritance)

            if parent_symbol is None:
                errors.append(
                    Error(
                        symbol.node,
                        f"The inheritance for class {symbol.name} "
                        f"is dangling: {inheritance}"))

            elif not isinstance(parent_symbol, Class):
                errors.append(
                    Error(
                        symbol.node,
                        f"Expected the class {symbol.name} to inherit "
                        f"from an abstract class, "
                        f"but it inherits from a symbol of type "
                        f"{parent_symbol.__class__.__name__}: {parent_symbol.name}"))

            elif not isinstance(parent_symbol, AbstractClass):
                errors.append(
                    Error(
                        symbol.node,
                        f"Expected the class {symbol.name} to inherit from "
                        f"an abstract class, but it inherits "
                        f"from a non-abstract one: {parent_symbol.name}",
                    )
                )

    if len(errors) > 0:
        return None, errors

    # endregion

    # region Check type annotations in properties and method signatures

    expected_subscripted_types = BUILTIN_COMPOSITE_TYPES.copy()
    expected_subscripted_types.add("Final")

    def verify_no_dangling_references_in_type_annotation(
            type_annotation: TypeAnnotation,
    ) -> Optional[Error]:
        """
        Check that the type annotation contains no dangling references.

        :return: error message, if any
        """
        if isinstance(type_annotation, AtomicTypeAnnotation):
            if type_annotation.identifier in BUILTIN_ATOMIC_TYPES:
                return None

            if type_annotation.identifier in expected_subscripted_types:
                return Error(
                    type_annotation.node,
                    f"The type annotation is expected with subscript(s), "
                    f"but got none: {type_annotation.identifier}"
                )

            if symbol_table.find(type_annotation.identifier) is not None:
                return None

            return Error(
                type_annotation.node,
                f"The type annotation could not be found "
                f"in the symbol table: {type_annotation.identifier}"
            )

        elif isinstance(type_annotation, SubscriptedTypeAnnotation):
            if type_annotation.identifier not in expected_subscripted_types:
                return Error(
                    type_annotation.node,
                    f"Unexpected subscripted type: {type_annotation.identifier}")

            for subscript in type_annotation.subscripts:
                error_in_subscript = verify_no_dangling_references_in_type_annotation(
                    type_annotation=subscript
                )
                if error_in_subscript is not None:
                    return error_in_subscript

            return None

        elif isinstance(type_annotation, SelfTypeAnnotation):
            return None

        else:
            assert_never(type_annotation)
            raise AssertionError(type_annotation)

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for prop in symbol.properties:
            error = verify_no_dangling_references_in_type_annotation(
                type_annotation=prop.type_annotation
            )

            if error is not None:
                errors.append(error)
            else:
                # TODO: test
                if isinstance(prop.type_annotation, SubscriptedTypeAnnotation):
                    error = _verify_arity_of_type_annotation_subscript(
                        prop.type_annotation)

                    if error is not None:
                        errors.append(error)

        for method in symbol.methods:
            for arg in method.arguments:
                error = verify_no_dangling_references_in_type_annotation(
                    type_annotation=arg.type_annotation)

                if error is not None:
                    errors.append(error)
                else:
                    # TODO: test
                    if isinstance(arg.type_annotation, SubscriptedTypeAnnotation):
                        error = _verify_arity_of_type_annotation_subscript(
                            arg.type_annotation)

                        if error is not None:
                            errors.append(error)

            if method.returns is not None:
                # TODO: test
                error = verify_no_dangling_references_in_type_annotation(
                    type_annotation=method.returns
                )
                if error is not None:
                    errors.append(error)
                else:
                    # TODO: test
                    if isinstance(method.returns, SubscriptedTypeAnnotation):
                        error = _verify_arity_of_type_annotation_subscript(
                            method.returns)

                        if error is not None:
                            errors.append(error)

    if len(errors) > 0:
        return None, errors

    # endregion

    return cast(SymbolTable, symbol_table), None


@require(lambda atok: isinstance(atok.tree, ast.Module))
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _atok_to_symbol_table(
        atok: asttokens.ASTTokens,
) -> Tuple[Optional[SymbolTable], Optional[Error]]:
    symbols = []  # type: List[Symbol]
    underlying_errors = []  # type: List[Error]

    for node in atok.tree.body:
        if isinstance(node, ast.ClassDef):
            symbol, symbol_error = _classdef_to_symbol(node=node, atok=atok)
            if symbol_error:
                underlying_errors.append(
                    Error(
                        node,
                        f"Failed to parse the class definition: {node.name}",
                        [symbol_error],
                    )
                )
            else:
                assert symbol is not None
                symbols.append(symbol)

    if len(underlying_errors) > 0:
        return None, Error(atok.tree, "Failed to parse the AST", underlying_errors)

    unverified_symbol_table = UnverifiedSymbolTable(symbols=symbols)

    symbol_table, verification_errors = _verify_symbol_table(unverified_symbol_table)

    if verification_errors is not None:
        return (
            None,
            Error(
                atok.tree, "Verification of the meta-model failed", verification_errors
            ),
        )

    assert symbol_table is not None
    return symbol_table, None


@require(lambda atok: isinstance(atok.tree, ast.Module))
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def atok_to_symbol_table(
        atok: asttokens.ASTTokens,
) -> Tuple[Optional[SymbolTable], Optional[Error]]:
    """Construct the symbol table based on the parsed AST."""
    table, error = _atok_to_symbol_table(atok=atok)
    if error is not None:
        return None, error

    return table, None
