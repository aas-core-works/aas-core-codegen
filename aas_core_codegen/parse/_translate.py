"""Translate the abstract syntax tree of the meta-model into parsed structures."""
import ast
import collections
import enum
import io
import itertools
import sys
import textwrap
from typing import (
    List,
    Any,
    Optional,
    cast,
    Type,
    Tuple,
    Union,
    Mapping,
    Set,
    Sequence,
    MutableMapping,
)

import asttokens
import docutils.io
import docutils.core
import docutils.nodes
import docutils.utils.error_reporting
from icontract import ensure, require

from aas_core_codegen.common import (
    Error,
    Identifier,
    IDENTIFIER_RE,
    LinenoColumner,
    assert_never,
)
from aas_core_codegen.parse import tree, _rules
from aas_core_codegen.parse._types import (
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
    is_string_expr,
    Serialization,
    Property,
    SelfTypeAnnotation,
    Snapshot,
    SubscriptedTypeAnnotation,
    Symbol,
    SymbolTable,
    TypeAnnotation,
    UnverifiedSymbolTable,
    PRIMITIVE_TYPES,
    GENERIC_TYPES,
    Description,
    MetaModel,
    ImplementationSpecificMethod,
    UnderstoodMethod,
    ConstructorToBeUnderstood,
    FunctionUnion,
    ReferenceInTheBook,
    MethodUnion,
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
    # pylint: disable=missing-docstring

    def __init__(self) -> None:
        self.errors = []  # type: List[Error]

    def visit_Import(self, node: ast.Import) -> Any:
        self.errors.append(
            Error(
                node,
                "Unexpected ``import ...``. "
                "Only ``from ... import...`` statements are expected.",
            )
        )

    _EXPECTED_NAME_FROM_MODULE = collections.OrderedDict(
        [
            ("match", "re"),
            ("Enum", "enum"),
            ("List", "typing"),
            ("Optional", "typing"),
            ("DBC", "icontract"),
            ("invariant", "icontract"),
            ("ensure", "icontract"),
            ("require", "icontract"),
            ("abstract", "aas_core_meta.marker"),
            ("implementation_specific", "aas_core_meta.marker"),
            ("reference_in_the_book", "aas_core_meta.marker"),
            ("is_superset_of", "aas_core_meta.marker"),
            ("serialization", "aas_core_meta.marker"),
            ("verification", "aas_core_meta.marker"),
        ]
    )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for name in node.names:
            assert isinstance(name, ast.alias)
            if name.asname is not None:
                self.errors.append(
                    Error(
                        name,
                        "Unexpected ``from ... import ... as ...``. "
                        "Only ``from ... import...`` statements are expected.",
                    )
                )
            else:
                if name.name not in self._EXPECTED_NAME_FROM_MODULE:
                    self.errors.append(
                        Error(name, f"Unexpected import of a name {name.name!r}.")
                    )

                else:
                    expected_module = self._EXPECTED_NAME_FROM_MODULE[name.name]
                    if expected_module != node.module:
                        self.errors.append(
                            Error(
                                name,
                                f"Expected to import {name.name!r} "
                                f"from the module {expected_module}, "
                                f"but it is imported from {node.module}.",
                            )
                        )


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
def _type_annotation(
    node: ast.AST, atok: asttokens.ASTTokens
) -> Tuple[Optional[TypeAnnotation], Optional[Error]]:
    """Parse the type annotation."""
    if isinstance(node, ast.Name):
        return AtomicTypeAnnotation(identifier=Identifier(node.id), node=node), None

    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, str):
            return (
                None,
                Error(
                    node.value,
                    f"Expected a string literal "
                    f"if the type annotation is given as a constant, "
                    f"but got: "
                    f"{node.value!r} (as {type(node.value)})",
                ),
            )

        return AtomicTypeAnnotation(identifier=Identifier(node.value), node=node), None

    elif isinstance(node, ast.Subscript):
        if not isinstance(node.value, ast.Name):
            return (
                None,
                Error(
                    node.value,
                    f"Expected a name to define "
                    f"a subscripted type annotation,"
                    f"but got: {atok.get_text(node.value)}",
                ),
            )

        # NOTE (mristin, 2022-01-22):
        # There were breaking changes between Python 3.8 and 3.9 in ``ast`` module.
        # Relevant to this particular piece of parsing logic is the deprecation of
        # ``ast.Index`` and ``ast.ExtSlice`` which is replaced with their actual value
        # and ``ast.Tuple``, respectively.
        #
        # Hence we need to switch on Python version and get the underlying slice value
        # explicitly.
        #
        # See deprecation notes just at the end of:
        # https://docs.python.org/3/library/ast.html#ast.AST

        if isinstance(node.slice, ast.Slice):
            return (
                None,
                Error(
                    node.slice,
                    f"Expected an index to define a subscripted type annotation, "
                    f"but got a slice: {atok.get_text(node.slice)}",
                ),
            )

        # noinspection PyUnresolvedReferences
        if (sys.version_info < (3, 9) and isinstance(node.slice, ast.ExtSlice)) or (
            sys.version_info >= (3, 9)
            and isinstance(node.slice, ast.Tuple)
            and any(isinstance(elt, ast.Slice) for elt in node.slice.elts)
        ):
            return (
                None,
                Error(
                    node.slice,
                    f"Expected an index to define a subscripted type annotation, "
                    f"but got an extended slice: {atok.get_text(node.slice)}",
                ),
            )

        # NOTE (mristin, 2022-01-22):
        # Please see the note about the deprecation of ``ast.Index`` above.
        index_node = None  # type: Optional[ast.AST]
        if sys.version_info < (3, 9):
            # noinspection PyUnresolvedReferences
            if isinstance(node.slice, ast.Index):
                index_node = node.slice.value
            else:
                return (
                    None,
                    Error(
                        node.slice,
                        f"Expected an index to define a subscripted type annotation, "
                        f"but got: {atok.get_text(node.slice)}",
                    ),
                )
        else:
            index_node = node.slice

        assert index_node is not None

        subscripts = []  # type: List[TypeAnnotation]

        if isinstance(index_node, ast.Tuple):
            for elt in index_node.elts:
                subscript_annotation, error = _type_annotation(node=elt, atok=atok)
                if error is not None:
                    return None, error

                assert subscript_annotation is not None

                subscripts.append(subscript_annotation)

        elif isinstance(index_node, (ast.Name, ast.Subscript, ast.Constant)):
            subscript_annotation, error = _type_annotation(node=index_node, atok=atok)
            if error is not None:
                return None, error

            assert subscript_annotation is not None

            subscripts.append(subscript_annotation)

        else:
            return (
                None,
                Error(
                    index_node,
                    f"Expected a tuple, a name, a subscript or a string literal "
                    f"for a subscripted type annotation, "
                    f"but got: {atok.get_text(index_node)}",
                ),
            )

        return (
            SubscriptedTypeAnnotation(
                identifier=Identifier(node.value.id),
                subscripts=subscripts,
                node=node,
            ),
            None,
        )

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
    node: ast.AnnAssign, description: Optional[Description], atok: asttokens.ASTTokens
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
                "Expected a property with a simple target (no parentheses!)",
            ),
        )

    if node.annotation is None:
        return (
            None,
            Error(node.target, "Expected property to be annotated with a type"),
        )

    type_annotation, error = _type_annotation(node=node.annotation, atok=atok)
    if error is not None:
        return None, error

    assert type_annotation is not None

    if node.value is not None:
        return (
            None,
            Error(node.value, "Unexpected assignment of a value to a property"),
        )

    return (
        Property(
            name=Identifier(node.target.id),
            type_annotation=type_annotation,
            description=description,
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
        return None, Error(node, "Unexpected positional-only arguments")

    if node.vararg is not None or node.kwarg is not None:
        return None, Error(node, "Unexpected variable arguments")

    if len(node.kwonlyargs) > 0:
        return None, Error(node, "Unexpected keyword-only arguments")

    assert len(node.kw_defaults) == 0, (
        "No keyword-only arguments implies "
        "there should be no defaults "
        "for keyword-only arguments either."
    )

    if len(node.args) == 0:
        return None, Error(node, "Unexpected no arguments")

    arguments = []  # type: List[Argument]

    # region ``self``

    found_self = False

    if len(node.args) >= 1 and node.args[0].arg == "self":
        found_self = True

        if node.args[0].annotation is not None:
            return (
                None,
                Error(
                    node.args[0],
                    "Unexpected type annotation for the method argument ``self``",
                ),
            )

        if len(node.defaults) == len(node.args):
            return (
                None,
                Error(
                    node.args[0],
                    "Unexpected default value for the method argument ``self``",
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

    # We skip the first argument if we found ``self`` as it has been added to
    # ``arguments`` already.

    for i in range(1 if found_self else 0, len(node.args)):
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

        # endregion

        # region Default
        default = None  # type: Optional[Default]

        # BEFORE-RELEASE (mristin, 2021-12-16):
        #  test the defaults in verification function
        #
        # BEFORE-RELEASE (mristin, 2021-12-16):
        #  test the defaults in a class method

        # NOTE (mristin, 2021-12-16):
        # A simple hypothetical test calculation:
        # 5 args
        # 2 defaults
        #
        # i = 3
        #   i - offset = 0 🠒 index in the node.defaults
        #   offset must be 3
        #   offset = len(node.args) - len(node.defaults) = 5 - 2 = 3

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

    description = None  # type: Optional[str]
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
                ),
            )

        description = description_node.value

    body, error = _rules.ast_node_to_our_node(node=condition_node.body)
    if error is not None:
        return None, Error(condition_node.body, "Failed to parse the contract", [error])

    assert body is not None

    if not isinstance(body, tree.Expression):
        return None, Error(
            condition_node.body,
            f"Expected an expression in the contract condition body, "
            f"but got: {tree.dump(body)}",
        )

    return (
        Contract(
            args=[Identifier(arg.arg) for arg in condition_node.args.args],
            description=description,
            body=body,
            node=node,
        ),
        None,
    )


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
            ),
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
                "Expected the name of the snapshot to be defined, "
                "but there was neither the single argument in the capture "
                "nor explicit ``name`` given",
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

    body, error = _rules.ast_node_to_our_node(node=capture_node.body)
    if error is not None:
        return None, Error(capture_node.body, "Failed to parse the snapshot", [error])

    assert body is not None

    if not isinstance(body, tree.Expression):
        return None, Error(
            capture_node.body,
            f"Expected an expression in the contract condition body, "
            f"but got: {tree.dump(body)}",
        )

    return (
        Snapshot(
            args=[Identifier(arg.arg) for arg in capture_node.args.args],
            name=Identifier(name),
            body=body,
            node=node,
        ),
        None,
    )


# BEFORE-RELEASE (mristin, 2021-12-13):
#  include severity levels for contracts in the meta model and
#  consider them in the imports

# BEFORE-RELEASE (mristin, 2021-12-13):
#  test for unknown severity level

# fmt: off
@ensure(
    lambda expect_self, result:
    not (result[0] is not None and not expect_self)
    or 'self' not in result[0].arguments_by_name,
    "No ``self`` argument if not ``expect_self``"
)
@ensure(
    lambda expect_self, result:
    not (result[0] is not None and expect_self)
    or (
            len(result[0].arguments) >= 0
            and result[0].arguments[0].name == 'self'
            and isinstance(result[0].arguments[0].type_annotation, SelfTypeAnnotation)
    ),
    "If ``expect_self`` set, expect at least one argument and that should be ``self``"
)
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
# fmt: on
def _function_def_to_method(
    node: ast.FunctionDef, expect_self: bool, atok: asttokens.ASTTokens
) -> Tuple[Optional[MethodUnion], Optional[Error]]:
    """
    Parse the function definition into a method.

    Though we have to distinguish in Python between a function and a method, we term
    both of them "methods" in our model.

    If ``expect_self`` is set, the first argument is expected to be ``self``. Otherwise,
    no ``self`` argument is expected.
    """
    # NOTE (mristin, 2021-12-19):
    # This run-time check is necessary as we already burned our fingers with it.
    assert isinstance(node, ast.FunctionDef)

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
    verification = False  # Set if the function is decorated with ``@verification``

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
            if decorator.id == "implementation_specific":
                is_implementation_specific = True

            elif decorator.id == "verification":
                verification = True

            else:
                return (
                    None,
                    Error(
                        decorator,
                        f"Unexpected simple decorator of a method: {decorator.id}; "
                        f"expected at most ``implementation_specific``",
                    ),
                )
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
            constant=node.body[0].value
        )

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
                        contract.node,
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
                            contract.node,
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
                        contract.node,
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
                        snapshot.node,
                        f"The argument of the snapshot is not provided "
                        f"in the method: {arg}",
                    ),
                )

    # endregion

    # region Check __init__ constraints
    if name == "__init__":
        # Must return None
        if returns is not None:
            return (
                None,
                Error(
                    node,
                    f"Expected __init__ to return None, "
                    f"but got: {atok.get_text(node.returns)}",
                ),
            )

        # Must not be a verification
        if verification:
            return (
                None,
                Error(
                    node,
                    "Expected __init__ not to be a verification function",
                ),
            )

    # endregion

    # region Check that the parsed method conforms to ``expect_self``

    if expect_self and len(arguments) == 0:
        return (
            None,
            Error(
                node,
                f"A ``self`` argument is expected, but no arguments were specified "
                f"in the method {name!r}",
            ),
        )

    if expect_self and len(arguments) >= 1:
        if arguments[0].name != "self":
            return (
                None,
                Error(
                    node,
                    f"Expected the first argument to be ``self`` "
                    f"in the method {name!r}, but got {arguments[0].name!r}",
                ),
            )

        if not isinstance(arguments[0].type_annotation, SelfTypeAnnotation):
            return (
                None,
                Error(
                    node,
                    f"Expected the ``self`` argument to have no annotation "
                    f"in the method {name!r}, but got {arguments[0].type_annotation!r}",
                ),
            )

    # endregion

    if is_implementation_specific:
        return (
            ImplementationSpecificMethod(
                name=Identifier(name),
                verification=verification,
                arguments=arguments,
                returns=returns,
                description=description,
                contracts=Contracts(
                    preconditions=preconditions,
                    snapshots=snapshots,
                    postconditions=postconditions,
                ),
                node=node,
            ),
            None,
        )
    else:
        if name == "__init__":
            assert not verification
            assert returns is None
            return (
                ConstructorToBeUnderstood(
                    arguments=arguments,
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
        else:
            understanding_errors = []  # type: List[Error]

            understood_body = []  # type: List[tree.Node]

            for body_child in body:
                # NOTE (mristin, 2021-12-27):
                # We deliberately ignore ``pass`` as it makes no sense in our
                # context of multiple programming languages.
                if isinstance(body_child, ast.Pass):
                    continue

                understood_node, understanding_error = _rules.ast_node_to_our_node(
                    body_child
                )

                if understanding_error is not None:
                    understanding_errors.append(understanding_error)
                    continue

                assert understood_node is not None
                understood_body.append(understood_node)

            if len(understanding_errors) > 0:
                return None, Error(
                    node,
                    f"Failed to understand the body of the function {name!r}",
                    understanding_errors,
                )

            return (
                UnderstoodMethod(
                    name=Identifier(name),
                    verification=verification,
                    arguments=arguments,
                    returns=returns,
                    description=description,
                    contracts=Contracts(
                        preconditions=preconditions,
                        snapshots=snapshots,
                        postconditions=postconditions,
                    ),
                    body=understood_body,
                    node=node,
                ),
                None,
            )


@require(lambda constant: isinstance(constant.value, str))
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _string_constant_to_description(
    constant: ast.Constant,
) -> Tuple[Optional[Description], Optional[Error]]:
    """Extract the docstring from the given string constant."""
    text = constant.value
    assert isinstance(
        text, str
    ), f"Expected a string constant node, but got: {ast.dump(constant)!r}"

    dedented = textwrap.dedent(text)

    warnings = io.StringIO()
    # noinspection PyUnusedLocal
    document = None  # type: Optional[docutils.nodes.document]
    try:
        document = docutils.core.publish_doctree(
            dedented, settings_overrides={"warning_stream": warnings}
        )
    except Exception as err:
        return None, Error(
            constant, f"Failed to parse the description with docutils: {err}"
        )

    warnings_text = warnings.getvalue()
    if warnings_text:
        return None, Error(
            constant,
            f"Failed to parse the description with docutils:\n"
            f"{warnings_text.strip()}\n\n"
            f"The original text was: {dedented!r}",
        )

    assert document is not None

    return Description(document=document, node=constant), None


class _ClassMarker(enum.Enum):
    ABSTRACT = "abstract"
    IMPLEMENTATION_SPECIFIC = "implementation_specific"
    TEMPLATE = "template"


_CLASS_MARKER_FROM_STRING: Mapping[str, _ClassMarker] = {
    marker.value: marker for marker in _ClassMarker
}


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _class_decorator_to_marker(
    decorator: ast.Name,
) -> Tuple[Optional[_ClassMarker], Optional[Error]]:
    """Parse a simple decorator as a class marker."""
    class_marker = _CLASS_MARKER_FROM_STRING.get(decorator.id, None)

    if class_marker is None:
        return (
            None,
            Error(
                decorator,
                f"The handling of the marker has not been implemented: {decorator.id!r}",
            ),
        )

    return class_marker, None


class _IsSupersetOf:
    """Represent the parsed supersets of an enumeration."""

    def __init__(self, enums: List[Identifier]) -> None:
        """Initialize with the given values."""
        self.enums = enums


# fmt: off
@require(
    lambda decorator:
    isinstance(decorator.func, ast.Name)
    and isinstance(decorator.func.ctx, ast.Load)
    and decorator.func.id == 'is_superset_of'
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _class_decorator_to_is_superset_of(
    decorator: ast.Call,
) -> Tuple[Optional[_IsSupersetOf], Optional[Error]]:
    """Translate a decorator to an Is-superset-of information."""
    superset_arg_node = None  # type: Optional[ast.AST]
    if len(decorator.args) >= 1:
        superset_arg_node = decorator.args[0]
    elif len(decorator.keywords) > 0:
        for keyword in decorator.keywords:
            if keyword.arg == "enums":
                superset_arg_node = keyword.value
    else:
        pass

    if superset_arg_node is None:
        return None, Error(
            decorator,
            "The ``enums`` argument is missing in the ``is_superset_of`` " "decorator",
        )

    if not isinstance(superset_arg_node, ast.List):
        return None, Error(
            decorator,
            "Expected the ``enums`` argument of the ``is_superset_of`` "
            "to be a list literal, but it is not",
        )

    enums = []  # type: List[Identifier]

    for elt in superset_arg_node.elts:
        if not isinstance(elt, ast.Name):
            return None, Error(
                decorator,
                f"Expected all elements of the ``enums`` argument to "
                f"the ``is_superset_of`` to be a list literal of enum names, "
                f"but got: {ast.dump(elt)}",
            )

        enums.append(Identifier(elt.id))

    return _IsSupersetOf(enums=enums), None


# fmt: off
@require(
    lambda decorator:
    isinstance(decorator.func, ast.Name)
    and isinstance(decorator.func.ctx, ast.Load)
    and decorator.func.id == 'serialization'
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _class_decorator_to_serialization(
    decorator: ast.Call,
) -> Tuple[Optional[Serialization], Optional[Error]]:
    """Translate a decorator to general serialization settings."""
    with_model_type_node = None  # type: Optional[ast.AST]

    if len(decorator.args) >= 1:
        with_model_type_node = decorator.args[0]

    if len(decorator.keywords) > 0:
        for kwarg in decorator.keywords:
            if kwarg.arg == "with_model_type":
                with_model_type_node = kwarg.value
            else:
                return (
                    None,
                    Error(
                        decorator,
                        f"Handling of the keyword argument {kwarg.arg!r} "
                        f"for the serialization decorator has not been implemented",
                    ),
                )

    with_model_type = None  # type: Optional[bool]
    if with_model_type_node is not None:
        if not isinstance(with_model_type_node, ast.Constant):
            return (
                None,
                Error(
                    with_model_type_node,
                    f"Expected the value for ``with_model_type`` parameter "
                    f"to be a constant, but got: {ast.dump(with_model_type_node)}",
                ),
            )

        if not isinstance(with_model_type_node.value, bool):
            return (
                None,
                Error(
                    with_model_type_node,
                    f"Expected the value for ``with_model_type`` parameter "
                    f"to be a boolean, but got: {with_model_type_node.value}",
                ),
            )

        with_model_type = with_model_type_node.value

    return Serialization(with_model_type=with_model_type), None


# fmt: off
@require(
    lambda decorator:
    isinstance(decorator.func, ast.Name)
    and isinstance(decorator.func.ctx, ast.Load)
    and decorator.func.id == 'reference_in_the_book'
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _class_decorator_to_reference_in_the_book(
    decorator: ast.Call,
) -> Tuple[Optional[ReferenceInTheBook], Optional[Error]]:
    """Translate a decorator to general serialization settings."""
    section_node = None  # type: Optional[ast.AST]
    index_node = None  # type: Optional[ast.AST]
    fragment_node = None  # type: Optional[ast.AST]

    if len(decorator.args) >= 1:
        section_node = decorator.args[0]

    if len(decorator.args) >= 2:
        index_node = decorator.args[1]

    if len(decorator.args) >= 3:
        fragment_node = decorator.args[2]

    if len(decorator.keywords) > 0:
        for kwarg in decorator.keywords:
            if kwarg.arg == "section":
                section_node = kwarg.value
            elif kwarg.arg == "index":
                index_node = kwarg.value
            elif kwarg.arg == "fragment":
                fragment_node = kwarg.value
            else:
                return (
                    None,
                    Error(
                        decorator,
                        f"Handling of the keyword argument {kwarg.arg!r} "
                        f"for the reference_in_the_book decorator has not been "
                        f"implemented",
                    ),
                )

    section = None  # type: Optional[Tuple[int, ...]]
    index = None  # type: Optional[int]
    fragment = None  # type: Optional[str]

    if section_node is not None:
        section_parts = []  # type: List[int]
        if not isinstance(section_node, ast.Tuple):
            return None, Error(
                section_node,
                f"Expected a tuple as a section, " f"but got: {ast.dump(section_node)}",
            )

        for i, elt in enumerate(section_node.elts):
            if not isinstance(elt, ast.Constant):
                return None, Error(
                    elt,
                    f"Expected a constant as part of the section, "
                    f"but got at position {i+1}: {ast.dump(elt)}",
                )

            if not isinstance(elt.value, int):
                return None, Error(
                    elt,
                    f"Expected integers as section numbers, "
                    f"but got a {type(elt.value)} at position {i+1}: {elt.value}",
                )

            section_parts.append(elt.value)

        section = tuple(section_parts)

    if index_node is not None:
        if not isinstance(index_node, ast.Constant):
            return None, Error(
                index_node,
                f"Expected a constant as the index, "
                f"but got: {ast.dump(index_node)}",
            )

        if not isinstance(index_node.value, int):
            return None, Error(
                index_node,
                f"Expected an integer as the index, "
                f"but got a {type(index_node.value)}: {index_node.value}",
            )

        index = index_node.value

    if fragment_node is not None:
        if not isinstance(fragment_node, ast.Constant):
            return None, Error(
                fragment_node,
                f"Expected a constant as the fragment, "
                f"but got: {ast.dump(fragment_node)}",
            )

        if not isinstance(fragment_node.value, str):
            return None, Error(
                fragment_node,
                f"Expected a string as the fragment, "
                f"but got a {type(fragment_node.value)}: {fragment_node.value}",
            )

        fragment = fragment_node.value

    assert section is not None
    if index is None:
        index = 0

    return ReferenceInTheBook(section=section, index=index, fragment=fragment), None


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
    decorator: ast.Call, atok: asttokens.ASTTokens
) -> Tuple[Optional[Invariant], Optional[Error]]:
    """Parse the decorator node as a class invariant."""
    condition_node = None  # type: Optional[ast.AST]
    description_node = None  # type: Optional[ast.AST]

    # BEFORE-RELEASE (mristin, 2021-12-13): test parsing of args and kwargs
    if len(decorator.args) >= 1:
        condition_node = decorator.args[0]

    if len(decorator.args) >= 2:
        description_node = decorator.args[1]

    if len(decorator.keywords) > 0:
        for kwarg in decorator.keywords:
            if kwarg.arg == "condition":
                condition_node = kwarg.value
            elif kwarg.arg == "description":
                description_node = kwarg.value
            else:
                return (
                    None,
                    Error(
                        decorator,
                        f"Handling of the keyword argument {kwarg.arg!r} "
                        f"for the invariant has not been implemented",
                    ),
                )

    if not isinstance(condition_node, ast.Lambda):
        return (
            None,
            Error(
                decorator,
                f"Expected the condition of an invariant to be a lambda, "
                f"but got {type(condition_node)}: {atok.get_text(decorator)}",
            ),
        )

    if description_node is not None and (
        not isinstance(description_node, ast.Constant)
        or not isinstance(description_node.value, str)
    ):
        return (
            None,
            Error(
                decorator,
                f"Expected the description of an invariant to be "
                f"a string literal, but got: {type(description_node)}",
            ),
        )

    if len(condition_node.args.args) != 1 or condition_node.args.args[0].arg != "self":
        return (
            None,
            Error(
                decorator, "Expected the invariant to have a single argument, ``self``"
            ),
        )

    body, error = _rules.ast_node_to_our_node(node=condition_node.body)
    if error is not None:
        return None, Error(
            condition_node.body, "Failed to parse the invariant", [error]
        )

    assert body is not None

    if not isinstance(body, tree.Expression):
        return None, Error(
            condition_node.body,
            f"Expected an expression in an invariant, but got: {tree.dump(body)}",
        )

    return (
        Invariant(
            description=(
                description_node.value if description_node is not None else None
            ),
            body=body,
            node=decorator,
        ),
        None,
    )


_ClassDecoratorUnion = Union[
    _ClassMarker,
    _IsSupersetOf,
    Serialization,
    ReferenceInTheBook,
    Invariant,
]


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _parse_class_decorator(
    decorator: ast.AST, atok: asttokens.ASTTokens
) -> Tuple[Optional[_ClassDecoratorUnion], Optional[Error]]:
    """
    Parse a class decorator.

    The decorator needs to be further interpreted in the context of the class.
    The class here refers to a general Python class, not the concrete or abstract
    class of the meta-model. For example, an enumeration is also defined as a Python
    class inheriting from ``Enum``.
    """
    if isinstance(decorator, ast.Name):
        return _class_decorator_to_marker(decorator=decorator)
    elif isinstance(decorator, ast.Call):
        if not isinstance(decorator.func, ast.Name):
            return None, Error(
                decorator,
                f"Expected a name for a decorator function, "
                f"but got: {ast.dump(decorator.func)}",
            )

        if not isinstance(decorator.func.ctx, ast.Load):
            return None, Error(
                decorator,
                f"Unexpected decorator function in "
                f"a non-Load context: {decorator.func.ctx=}",
            )

        if decorator.func.id == "is_superset_of":
            return _class_decorator_to_is_superset_of(decorator=decorator)
        elif decorator.func.id == "serialization":
            return _class_decorator_to_serialization(decorator=decorator)
        elif decorator.func.id == "reference_in_the_book":
            return _class_decorator_to_reference_in_the_book(decorator=decorator)
        elif decorator.func.id == "invariant":
            return _class_decorator_to_invariant(decorator=decorator, atok=atok)
        else:
            return None, Error(
                decorator,
                f"We do not know how to handle "
                f"the class decorator: {decorator.func.id}.",
            )
    else:
        return None, Error(
            decorator,
            f"Handling of a non-name or a non-call class decorator "
            f"has not been implemented: {ast.dump(decorator)}",
        )


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _enum_to_symbol(
    node: ast.ClassDef, atok: asttokens.ASTTokens
) -> Tuple[Optional[Enumeration], Optional[Error]]:
    """Interpret a class which defines an enumeration."""
    is_superset_of = None  # type: Optional[Sequence[Identifier]]
    reference_in_the_book = None  # type: Optional[ReferenceInTheBook]

    for decorator_node in node.decorator_list:
        decorator, error = _parse_class_decorator(decorator=decorator_node, atok=atok)
        if error is not None:
            return None, error
        assert decorator is not None

        if isinstance(decorator, _IsSupersetOf):
            if is_superset_of is not None:
                return None, Error(
                    decorator_node,
                    "Double definitions of ``is_superset_of`` are not allowed",
                )

            is_superset_of = decorator.enums

        elif isinstance(decorator, ReferenceInTheBook):
            if reference_in_the_book is not None:
                return None, Error(
                    decorator_node,
                    "Unexpected double reference_in_the_book markers",
                )

            reference_in_the_book = decorator

        else:
            return None, Error(
                node,
                f"Unexpected class decorator {decorator} "
                f"for the enumeration {node.name!r}",
            )

    if is_superset_of is None:
        is_superset_of = []

    if len(node.body) == 0:
        return (
            Enumeration(
                name=Identifier(node.name),
                is_superset_of=is_superset_of,
                literals=[],
                reference_in_the_book=reference_in_the_book,
                description=None,
                node=node,
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
            assert isinstance(body_node.value, ast.Constant)
            description, error = _string_constant_to_description(body_node.value)
            if error is not None:
                return None, error

            cursor += 1

        elif isinstance(body_node, ast.Pass):
            cursor += 1

        elif isinstance(body_node, ast.Assign):
            assign = body_node

            if len(assign.targets) != 1:
                return (
                    None,
                    Error(
                        assign,
                        f"Expected a single target in the assignment, "
                        f"but got: {len(assign.targets)}",
                    ),
                )

            if not isinstance(assign.targets[0], ast.Name):
                return (
                    None,
                    Error(
                        assign.targets[0],
                        f"Expected a name as a target of the assignment, "
                        f"but got: {assign.targets[0]}",
                    ),
                )

            if not isinstance(assign.value, ast.Constant):
                return (
                    None,
                    Error(
                        assign.value,
                        f"Expected a constant in the enumeration assignment, "
                        f"but got: {atok.get_text(assign.value)}",
                    ),
                )

            if not isinstance(assign.value.value, str):
                return (
                    None,
                    Error(
                        assign.value,
                        f"Expected a string literal in the enumeration, "
                        f"but got: {assign.value.value}",
                    ),
                )

            literal_name = Identifier(assign.targets[0].id)
            literal_value = assign.value.value

            literal_description = None  # type: Optional[Description]
            next_expr = node.body[cursor + 1] if cursor < len(node.body) - 1 else None

            if next_expr is not None and is_string_expr(next_expr):
                assert isinstance(next_expr, ast.Expr)
                assert isinstance(next_expr.value, ast.Constant)
                literal_description, error = _string_constant_to_description(
                    next_expr.value
                )

                if error is not None:
                    return None, error

                cursor += 1

            enumeration_literals.append(
                EnumerationLiteral(
                    name=literal_name,
                    value=literal_value,
                    description=literal_description,
                    node=assign,
                )
            )

            cursor += 1

        else:

            return (
                None,
                Error(
                    node.body[cursor],
                    f"Expected either a docstring at the beginning or an assignment "
                    f"in an enumeration, "
                    f"but got an unexpected body element at index {cursor} "
                    f"of the class definition {node.name!r}: "
                    f"{atok.get_text(node.body[cursor])}",
                ),
            )

        assert cursor > old_cursor, f"Loop invariant: {cursor=}, {old_cursor=}"

    return (
        Enumeration(
            name=Identifier(node.name),
            is_superset_of=is_superset_of,
            literals=enumeration_literals,
            reference_in_the_book=reference_in_the_book,
            description=description,
            node=node,
        ),
        None,
    )


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _classdef_to_symbol(
    node: ast.ClassDef, atok: asttokens.ASTTokens
) -> Tuple[Optional[Symbol], Optional[Error]]:
    """Interpret the class definition as a symbol."""
    underlying_errors = []  # type: List[Error]

    base_names = []  # type: List[str]
    for base in node.bases:
        if not isinstance(base, ast.Name):
            underlying_errors.append(
                Error(
                    base, f"Expected a base as a name, but got: {atok.get_text(base)}"
                )
            )
        else:
            base_names.append(base.id)

    if len(underlying_errors) > 0:
        return (
            None,
            Error(
                node,
                f"Failed to parse the class definition: {node.name}",
                underlying=underlying_errors,
            ),
        )

    if "Enum" in base_names and len(base_names) > 1:
        return (
            None,
            Error(
                node,
                f"Expected an enumeration to only inherit from ``Enum``, "
                f"but it inherits from: {base_names}",
            ),
        )

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

    reference_in_the_book = None  # type: Optional[ReferenceInTheBook]
    serialization = None  # type: Optional[Serialization]

    for decorator_node in node.decorator_list:
        decorator, error = _parse_class_decorator(decorator=decorator_node, atok=atok)
        if error is not None:
            underlying_errors.append(error)
            continue

        assert decorator is not None
        if isinstance(decorator, _ClassMarker):
            if decorator is _ClassMarker.ABSTRACT:
                is_abstract = True
            elif decorator is _ClassMarker.IMPLEMENTATION_SPECIFIC:
                is_implementation_specific = True
            elif decorator is _ClassMarker.TEMPLATE:
                # NOTE (mristin, 2021-11-28):
                # We ignore the template marker at this moment. However, we will most
                # probably have to consider them in the future so we leave them in the
                # meta-model, but ignore them in the code generation.
                pass

            else:
                assert_never(decorator)

        elif isinstance(decorator, _IsSupersetOf):
            underlying_errors.append(
                Error(
                    decorator_node,
                    "Unexpected is_superset_of on a non-enumeration class",
                )
            )
            continue

        elif isinstance(decorator, Serialization):
            if serialization is not None:
                underlying_errors.append(
                    Error(decorator_node, "Unexpected double serialization markers")
                )
                continue

            serialization = decorator

        elif isinstance(decorator, ReferenceInTheBook):
            if reference_in_the_book is not None:
                underlying_errors.append(
                    Error(
                        decorator_node,
                        "Unexpected double reference_in_the_book markers",
                    )
                )
                continue

            reference_in_the_book = decorator

        elif isinstance(decorator, Invariant):
            invariants.append(decorator)

        else:
            assert_never(decorator)

    if len(underlying_errors) > 0:
        return (
            None,
            Error(
                node,
                f"Failed to parse the class definition: {node.name}",
                underlying=underlying_errors,
            ),
        )

    # NOTE (mristin, 20222-01-02):
    # We need to inverse the invariants as we collect them top-down, while
    # the decorators are applied bottom-up.
    invariants = list(reversed(invariants))

    # endregion

    if is_abstract and is_implementation_specific:
        return (
            None,
            Error(
                node,
                "Abstract classes can not be implementation-specific "
                "at the same time "
                "(otherwise we can not convert them to interfaces etc.)",
            ),
        )

    description = None  # type: Optional[Description]

    properties = []  # type: List[Property]
    methods = []  # type: List[MethodUnion]

    cursor = 0
    while cursor < len(node.body):
        old_cursor = cursor

        expr = node.body[cursor]

        if cursor == 0 and is_string_expr(expr):
            assert isinstance(expr, ast.Expr)
            assert isinstance(expr.value, ast.Constant)
            description, error = _string_constant_to_description(expr.value)
            if error is not None:
                return None, error

            assert description is not None

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
                assert isinstance(next_expr.value, ast.Constant)
                property_description, error = _string_constant_to_description(
                    next_expr.value
                )

                if error is not None:
                    return None, error

                assert property_description is not None

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
            method, error = _function_def_to_method(
                node=expr, expect_self=True, atok=atok
            )

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
            return (
                None,
                Error(
                    expr,
                    f"Expected only either "
                    f"properties explicitly annotated with types or "
                    f"instance methods, but got: {atok.get_text(expr)}",
                ),
            )

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
            serialization=serialization,
            reference_in_the_book=reference_in_the_book,
            description=description,
            node=node,
        ),
        None,
    )


def _verify_arity_of_type_annotation_subscript(
    type_annotation: SubscriptedTypeAnnotation,
) -> Optional[Error]:
    """
    Check that the subscripted type annotation has the expected number of arguments.

    :return: error message, if any
    """
    expected_arity_map = {"List": 1, "Optional": 1}
    expected_arity = expected_arity_map.get(type_annotation.identifier, None)
    if expected_arity is None:
        raise AssertionError(
            f"Unexpected subscripted type annotation: {type_annotation}"
        )

    assert expected_arity >= 0
    if len(type_annotation.subscripts) != expected_arity:
        return Error(
            type_annotation.node,
            f"Expected {expected_arity} arguments of "
            f"a subscripted type annotation {type_annotation.identifier!r}, "
            f"but got {len(type_annotation.subscripts)}: {type_annotation}",
        )

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

    builtin_types_in_many_implementations = {
        "str",
        "string",
        "int",
        "integer",
        "float",
        "real",
        "decimal",
        "number",
        "bool",
        "boolean",
        "bytes",
        "bytearray",
    }

    reserved_symbol_names = builtin_types_in_many_implementations.union(
        {
            # General aas-core classes
            "aas",
            "accept",
            "context",
            "class",
            "error",
            "errors",
            "iclass",
            "itransformer_with_context",
            "ivisitor",
            "ivisitor_with_context",
            "jsonization",
            "path",
            "stringification",
            "transform",
            "transformer",
            "transformer_with_context",
            "verification",
            "visit",
            "visitation",
            "visitor",
            "visitor_with_context",
            "match",
        }
    )

    reserved_member_names = builtin_types_in_many_implementations.union(
        {
            "descend",
            "descend_once",
            "accept",
            "transform",
            "type_name",
            "property_name",
            "match",
        }
    )

    for symbol in symbol_table.symbols:
        if symbol.name.startswith("I_"):
            errors.append(
                Error(
                    symbol.node,
                    f"The prefix ``I_`` in the name of the symbol is reserved "
                    f"for the code generation: {symbol.name!r}",
                )
            )

        if symbol.name.lower() in reserved_symbol_names:
            errors.append(
                Error(
                    symbol.node,
                    f"The name of the symbol is reserved "
                    f"for the code generation: {symbol.name!r}",
                )
            )

        if isinstance(symbol, Class):
            for method in symbol.methods:
                if method.name.lower() in reserved_member_names:
                    errors.append(
                        Error(
                            method.node,
                            f"The name of the method is reserved "
                            f"for the code generation: {method.name!r}",
                        )
                    )

            for prop in symbol.properties:
                if prop.name.lower() in reserved_member_names:
                    errors.append(
                        Error(
                            prop.node,
                            f"The name of the property is reserved "
                            f"for the code generation: {prop.name!r}",
                        )
                    )

    for func in symbol_table.verification_functions:
        func_name_lower = func.name.lower()
        if (
            func_name_lower in reserved_member_names
            or func_name_lower in reserved_symbol_names
        ):
            errors.append(
                Error(
                    func.node,
                    f"The name of the verification function is reserved "
                    f"for the code generation: {func.name!r}",
                )
            )

    # endregion

    # region Check that there are no duplicate symbol names

    observed_names = dict()  # type: MutableMapping[Identifier, Symbol]
    for symbol in symbol_table.symbols:
        other_symbol = observed_names.get(symbol.name, None)
        if other_symbol is None:
            observed_names[symbol.name] = symbol
        else:
            errors.append(
                Error(
                    symbol.node,
                    f"The symbol with the name {symbol.name!r} conflicts with "
                    f"other symbol with the same name.",
                )
            )

    if len(errors) > 0:
        return None, errors

    # endregion

    # region Check that imported symbols are not re-assigned in an understood method

    for understood_method in itertools.chain(
        (
            method
            for method in symbol_table.verification_functions
            if isinstance(method, UnderstoodMethod)
        ),
        (
            method
            for symbol in symbol_table.symbols
            if isinstance(symbol, Class)
            for method in symbol.methods
            if isinstance(method, UnderstoodMethod)
        ),
    ):
        # BEFORE-RELEASE (mristin, 2021-12-19): test
        for stmt in understood_method.body:
            if (
                isinstance(stmt, tree.Assignment)
                and isinstance(stmt.target, tree.Name)
                and stmt.target.identifier == "match"
            ):
                errors.append(
                    Error(
                        stmt.original_node,
                        "The name ``match`` is reserved "
                        "for the function ``match`` "
                        "imported from the ``re`` module of "
                        "the standard Python library",
                    )
                )

    # endregion

    # region Check that no class methods are used in verification

    # BEFORE-RELEASE (mristin, 2021-12-16): test
    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for method in symbol.methods:
            if method.verification:
                errors.append(
                    Error(
                        method.node,
                        f"Unexpected verification function "
                        f"in a class {symbol.name!r}: {method.name!r}",
                    )
                )

    # endregion

    # region Check dangling inheritances

    for symbol in symbol_table.symbols:
        if not isinstance(symbol, Class):
            continue

        for inheritance in symbol.inheritances:
            # NOTE (mristin, 2021-12-22):
            # Inheritance from primitive types allows us to constrain a primitive type.
            if inheritance in PRIMITIVE_TYPES:
                continue

            parent_symbol = symbol_table.find(name=inheritance)

            if parent_symbol is None:
                errors.append(
                    Error(
                        symbol.node,
                        f"A parent of the class {symbol.name!r} "
                        f"is dangling: {inheritance!r}",
                    )
                )

            elif isinstance(parent_symbol, Class):
                # A class can inherit from a class.
                pass
            else:
                errors.append(
                    Error(
                        symbol.node,
                        f"Expected the class {symbol.name!r} to inherit "
                        f"from another class, "
                        f"but it inherits from a symbol {parent_symbol.name!r} of type "
                        f"{parent_symbol.__class__.__name__!r}",
                    )
                )

    if len(errors) > 0:
        return None, errors

    # endregion

    # region Check type annotations in properties and method signatures

    expected_subscripted_types = GENERIC_TYPES

    # NOTE (mristin, 2021-11-19):
    # If you expect type qualifiers such as ``Final``, make a copy of
    # the ``GENERIC_TYPES`` and add them to the copy.

    def verify_no_dangling_references_in_type_annotation(
        type_annotation: TypeAnnotation,
    ) -> Optional[Error]:
        """
        Check that the type annotation contains no dangling references.

        :return: error message, if any
        """
        if isinstance(type_annotation, AtomicTypeAnnotation):
            if type_annotation.identifier in PRIMITIVE_TYPES:
                return None

            if type_annotation.identifier in expected_subscripted_types:
                return Error(
                    type_annotation.node,
                    f"The type annotation is expected with subscript(s), "
                    f"but got none: {type_annotation.identifier}",
                )

            if symbol_table.find(type_annotation.identifier) is not None:
                return None

            return Error(
                type_annotation.node,
                f"The type annotation could not be found "
                f"in the symbol table: {type_annotation.identifier}",
            )

        elif isinstance(type_annotation, SubscriptedTypeAnnotation):
            if type_annotation.identifier not in expected_subscripted_types:
                return Error(
                    type_annotation.node,
                    f"Unexpected subscripted type: {type_annotation.identifier}",
                )

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
                # BEFORE-RELEASE (mristin, 2021-12-13): test
                if isinstance(prop.type_annotation, SubscriptedTypeAnnotation):
                    error = _verify_arity_of_type_annotation_subscript(
                        prop.type_annotation
                    )

                    if error is not None:
                        errors.append(error)

        for method in symbol.methods:
            for arg in method.arguments:
                error = verify_no_dangling_references_in_type_annotation(
                    type_annotation=arg.type_annotation
                )

                if error is not None:
                    errors.append(error)
                else:
                    # BEFORE-RELEASE (mristin, 2021-12-13): test
                    if isinstance(arg.type_annotation, SubscriptedTypeAnnotation):
                        error = _verify_arity_of_type_annotation_subscript(
                            arg.type_annotation
                        )

                        if error is not None:
                            errors.append(error)

            if method.returns is not None:
                # BEFORE-RELEASE (mristin, 2021-12-13): test
                error = verify_no_dangling_references_in_type_annotation(
                    type_annotation=method.returns
                )
                if error is not None:
                    errors.append(error)
                else:
                    # BEFORE-RELEASE (mristin, 2021-12-13): test
                    if isinstance(method.returns, SubscriptedTypeAnnotation):
                        error = _verify_arity_of_type_annotation_subscript(
                            method.returns
                        )

                        if error is not None:
                            errors.append(error)

    if len(errors) > 0:
        return None, errors

    # endregion

    if len(errors) > 0:
        return None, errors

    return cast(SymbolTable, symbol_table), None


@require(lambda atok: isinstance(atok.tree, ast.Module))
@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _atok_to_symbol_table(
    atok: asttokens.ASTTokens,
) -> Tuple[Optional[SymbolTable], Optional[Error]]:
    symbols = []  # type: List[Symbol]
    underlying_errors = []  # type: List[Error]

    description = None  # type: Optional[Description]
    book_url = None  # type: Optional[str]
    book_version = None  # type: Optional[str]

    verification_functions = []  # type: List[FunctionUnion]

    # region Parse

    for node in atok.tree.body:
        # NOTE (mristin, 2021-12-27):
        # Pass statement makes no sense in our multi-language setting.
        if isinstance(node, ast.Pass):
            continue

        matched = False

        if isinstance(node, ast.ClassDef):
            matched = True

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

        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            matched = True

            # The first string literal is assumed to be the docstring of the meta-model.
            description, description_error = _string_constant_to_description(
                constant=node.value
            )

            if description_error is not None:
                assert description is None
                underlying_errors.append(description_error)
                continue

        elif isinstance(node, ast.FunctionDef):
            matched = True

            method, error = _function_def_to_method(
                node=node, expect_self=False, atok=atok
            )

            if error is not None:
                underlying_errors.append(error)
                continue

            assert method is not None

            if not method.verification:
                underlying_errors.append(
                    Error(
                        node,
                        f"We do not know how to interpret a non-verification function "
                        f"in the meta-model: {method.name!r}",
                    )
                )

            assert isinstance(method, (UnderstoodMethod, ImplementationSpecificMethod))
            verification_functions.append(method)

        elif isinstance(node, ast.ImportFrom):
            matched = True

            # Ignore import statements
            pass

        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            matched = True

            if node.targets[0].id == "__book_url__":
                book_url = node.targets[0].id
            elif node.targets[0].id == "__book_version__":
                book_version = node.targets[0].id
            else:
                underlying_errors.append(
                    Error(
                        node,
                        f"We do not know how to interpret "
                        f"the assignment node: {ast.dump(node)}",
                    )
                )
                continue

        else:
            matched = False

        if not matched:
            underlying_errors.append(
                Error(
                    node, f"We do not know how to parse the AST node: {ast.dump(node)}"
                )
            )

    if book_url is None:
        underlying_errors.append(
            Error(
                None,
                "The book URL (given as assignment to ``__book_url__``) is missing",
            )
        )

    if book_version is None:
        underlying_errors.append(
            Error(
                None,
                "The book version (given as assignment to ``__book_version__``) "
                "is missing",
            )
        )

    if len(underlying_errors) > 0:
        return None, Error(None, "Failed to parse the meta-model", underlying_errors)

    observed_symbol_names = set()  # type: Set[Identifier]
    duplicate_symbols = []  # type: List[Symbol]
    for symbol in symbols:
        if symbol.name not in observed_symbol_names:
            observed_symbol_names.add(symbol.name)
        else:
            duplicate_symbols.append(symbol)

    if len(duplicate_symbols) > 0:
        return None, Error(
            None,
            "There are one or more duplicate symbol definitions",
            [
                Error(
                    symbol.node,
                    f"The symbol {symbol.name!r} has been already defined before",
                )
                for symbol in duplicate_symbols
            ],
        )

    # endregion

    assert book_version is not None
    assert book_url is not None

    unverified_symbol_table = UnverifiedSymbolTable(
        symbols=symbols,
        verification_functions=verification_functions,
        meta_model=MetaModel(
            book_version=book_version, book_url=book_url, description=description
        ),
    )

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
