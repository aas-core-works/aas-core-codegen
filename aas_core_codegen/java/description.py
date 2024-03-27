"""Render descriptions to Java documentation comments."""
import abc
import collections
import io
import itertools
import textwrap
from typing import (
    Iterator,
    List,
    Optional,
    OrderedDict,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    Iterable,
)
import xml.sax.saxutils

from aas_core_codegen.common import (
    assert_never,
    Error,
    Identifier,
    Stripped,
)

import docutils.nodes
import docutils.parsers.rst.roles
import docutils.utils
from icontract import require, ensure, DBC

from aas_core_codegen import intermediate
from aas_core_codegen.common import (
    assert_union_of_descendants_exhaustive,
    assert_union_without_excluded,
)
from aas_core_codegen.java import (
    naming as java_naming,
)
from aas_core_codegen.intermediate import (
    doc as intermediate_doc,
    _translate as intermediate_translate,
)


class _Node(DBC):
    """Represent a node in an AST of a documentation comment."""

    @abc.abstractmethod
    def accept(self, visitor: "_NodeVisitor") -> None:
        """Accept the ``visitor`` and dispatch."""
        raise NotImplementedError()


class _Text(_Node):
    """Represent a text node in a documentation comment."""

    def __init__(self, content: str) -> None:
        """Initialize with the given values."""
        self.content = content

    def accept(self, visitor: "_NodeVisitor") -> None:
        """Accept the ``visitor`` and dispatch."""
        visitor.visit_text(self)

    def __repr__(self) -> str:
        """Generate a string representation for easier debugging."""
        return f"{self.__class__.__name__}({self.content!r})"


class _List(_Node):
    """
    Represent a sequence of nodes of a Java documentation comment.

    This is necessary so that we can render a concatenation where there is no
    enclosing element.
    """

    def __init__(self, items: List["_NodeUnion"]) -> None:
        self.items = items

    def accept(self, visitor: "_NodeVisitor") -> None:
        """Accept the ``visitor`` and dispatch."""
        visitor.visit_list(self)

    def __repr__(self) -> str:
        """Generate a string representation for easier debugging."""
        if len(self.items) == 0:
            return f"{self.__class__.__name__}([])"

        writer = io.StringIO()
        writer.write(f"{self.__class__.__name__}(\n")
        writer.write("  [\n")

        for i, item in enumerate(self.items):
            if i > 0:
                writer.write(",\n")
            writer.write(textwrap.indent(repr(item), "    "))

        writer.write("\n  ]\n)")
        return writer.getvalue()


class _Element(_Node):
    """Represent an element of a Java documentation comment."""

    def __init__(
        self,
        name: str,
        attrs: Optional[OrderedDict[str, str]] = None,
        children: Optional[_List] = None,
    ) -> None:
        self.name = name
        self.attrs = collections.OrderedDict() if attrs is None else attrs
        self.children = _List(items=[]) if children is None else children

    def accept(self, visitor: "_NodeVisitor") -> None:
        """Accept the ``visitor`` and dispatch."""
        visitor.visit_element(self)

    def __repr__(self) -> str:
        """Generate a string representation for easier debugging."""
        indented_name = textwrap.indent(repr(self.name), "  ")
        indented_attrs = textwrap.indent(repr(self.attrs), "  ")
        indented_children = textwrap.indent(repr(self.children), "  ")

        return f"""\
{self.__class__.__name__}(
{indented_name},
{indented_attrs},
{indented_children}
)"""


_NodeUnion = Union[_Text, _Element, _List]
assert_union_of_descendants_exhaustive(base_class=_Node, union=_NodeUnion)


class _NodeVisitor:
    def visit(self, node: _Node) -> None:
        """Visit *via* double-dispatch."""
        node.accept(self)

    def visit_text(self, node: _Text) -> None:
        """Visit the text node."""
        pass

    def visit_list(self, node: _List) -> None:
        """Visit the node list and its items recursively."""
        for item in node.items:
            self.visit(item)

    def visit_element(self, node: _Element) -> None:
        """Visit the element node and its children."""
        self.visit(node.children)


class _ElementRenderer(intermediate_doc.DocutilsElementTransformer[_NodeUnion]):
    """Render descriptions as Javadoc."""

    def transform_text(
        self, element: docutils.nodes.Text
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        return _Text(element.astext()), None

    def transform_reference_to_our_type_in_doc(
        self, element: intermediate_doc.ReferenceToOurType
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        name = None  # type: Optional[str]

        if isinstance(element.our_type, intermediate.Enumeration):
            name = java_naming.enum_name(element.our_type.name)

        elif isinstance(element.our_type, intermediate.ConstrainedPrimitive):
            # We do not generate a class for constrained primitives, but we
            # leave it as class name, as that is what we used for ``Verify*`` function.
            name = java_naming.class_name(element.our_type.name)

        elif isinstance(element.our_type, intermediate.Class):
            if isinstance(element.our_type, intermediate.AbstractClass):
                # We do not generate Java code for abstract classes, so we have to refer
                # to the interface.
                name = java_naming.interface_name(element.our_type.name)

            elif isinstance(element.our_type, intermediate.ConcreteClass):
                # Though a concrete class can have multiple descendants and the writer
                # might actually want to refer to the *interface* instead of
                # the concrete class, we do the best effort here and resolve it to the
                # name of the concrete class.
                name = java_naming.class_name(element.our_type.name)

            else:
                assert_never(element.our_type)

        else:
            # This is a very special case where we had problems with an interface.
            # We leave this check here, just in case the bug resurfaces.
            if isinstance(element.our_type, intermediate_translate._PlaceholderOurType):
                return None, [
                    f"Unexpected placeholder for our type: {element.our_type}; "
                    f"this is a bug"
                ]

            assert_never(element.our_type)

        assert name is not None

        return (
            _Element(
                name="see", attrs=collections.OrderedDict([("cref", name)])
            ),
            None,
        )

    def transform_reference_to_attribute_in_doc(
        self, element: intermediate_doc.ReferenceToAttribute
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        cref = None  # type: Optional[str]

        if isinstance(element.reference, intermediate_doc.ReferenceToProperty):
            name_of_our_type = None  # type: Optional[str]

            if isinstance(element.reference.cls, intermediate.AbstractClass):
                # We do not generate Java code for abstract classes, so we have to refer
                # to the interface.
                name_of_our_type = java_naming.interface_name(
                    element.reference.cls.name
                )
            elif isinstance(element.reference.cls, intermediate.ConcreteClass):
                # Though a concrete class can have multiple descendants and the writer
                # might actually want to refer to the *interface* instead of
                # the concrete class, we do the best effort here and resolve it to the
                # name of the concrete class.

                name_of_our_type = java_naming.class_name(element.reference.cls.name)
            else:
                assert_never(element.reference.cls)

            prop_name = java_naming.property_name(element.reference.prop.name)

            assert name_of_our_type is not None
            cref = f"{name_of_our_type}#{prop_name}"
        elif isinstance(
            element.reference, intermediate_doc.ReferenceToEnumerationLiteral
        ):
            name_of_our_type = java_naming.enum_name(
                element.reference.enumeration.name
            )
            literal_name = java_naming.enum_literal_name(
                element.reference.literal.name
            )

            cref = f"{name_of_our_type}#{literal_name}"
        else:
            # This is a very special case where we had problems with an interface.
            # We leave this check here, just in case the bug resurfaces.
            if isinstance(
                element.reference,
                intermediate_translate._PlaceholderReferenceToAttribute,
            ):
                return None, [
                    f"Unexpected placeholder "
                    f"for the attribute reference: {element.reference}; "
                    f"this is a bug"
                ]

            assert_never(element.reference)

        assert cref is not None

        return (
            _Element(
                name="see", attrs=collections.OrderedDict([("cref", cref)])
            ),
            None,
        )

    def transform_reference_to_argument_in_doc(
        self, element: intermediate_doc.ReferenceToArgument
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        arg_name = java_naming.argument_name(Identifier(element.reference))

        return (
            _Element(
                name="see", attrs=collections.OrderedDict([("cref", arg_name)])
            ),
            None,
        )

    def transform_reference_to_constraint_in_doc(
        self, element: intermediate_doc.ReferenceToConstraint
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        return _Text(content=f"Constraint {element.reference}"), None

    def transform_reference_to_constant_in_doc(
        self, element: intermediate_doc.ReferenceToConstant
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        constant_as_prop_name = java_naming.property_name(element.constant.name)
        cref = f"Constants.{constant_as_prop_name}"

        return (
            _Element(name="see", attrs=collections.OrderedDict([("cref", cref)])),
            None,
        )

    def transform_literal(
        self, element: docutils.nodes.literal
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        return (
            _Element(name="c", children=_List(items=[_Text(content=element.astext())])),
            None,
        )

    def _transform_children_of(
        self,
        element: docutils.nodes.Element,
    ) -> Tuple[Optional[_List], Optional[List[str]]]:
        """Transform the children to a Python list."""
        children = []  # type: List[_NodeUnion]

        errors = []  # type: List[str]
        for child in element.children:
            rendered_child, child_errors = self.transform(child)
            if child_errors is not None:
                errors.extend(child_errors)
            else:
                assert rendered_child is not None
                children.append(rendered_child)

        if len(errors) > 0:
            return None, errors

        return _List(items=children), None

    def transform_paragraph(
        self, element: docutils.nodes.paragraph
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        children, errors = self._transform_children_of(element)
        if errors is not None:
            return None, errors

        assert children is not None

        return _Element(name="para", children=children), None

    def transform_emphasis(
        self, element: docutils.nodes.emphasis
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        children, errors = self._transform_children_of(element)
        if errors is not None:
            return None, errors

        assert children is not None

        return _Element(name="em", children=children), None

    def transform_list_item(
        self, element: docutils.nodes.list_item
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        children, errors = self._transform_children_of(element)
        if errors is not None:
            return None, errors

        assert children is not None

        return _Element(name="li", children=children), None

    def transform_bullet_list(
        self, element: docutils.nodes.bullet_list
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        children, errors = self._transform_children_of(element)
        if errors is not None:
            return None, errors

        assert children is not None

        return _Element(name="ul", children=children), None

    def transform_note(
        self, element: docutils.nodes.note
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        children, errors = self._transform_children_of(element)

        if errors is not None:
            return None, errors

        assert children is not None

        return _Element(name="para", children=children), None

    def transform_reference(
        self, element: docutils.nodes.reference
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        return self._transform_children_of(element)

    def transform_field_body(
        self, element: docutils.nodes.field_body
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        return self._transform_children_of(element)

    def transform_document(
        self, element: docutils.nodes.document
    ) -> Tuple[Optional[_NodeUnion], Optional[List[str]]]:
        return self._transform_children_of(element)


class _FlattenListVisitor(_NodeVisitor):
    """Flatten all the node lists recursively and in-place."""

    def visit_list(self, node: _List) -> None:
        """Visit the node list and its items recursively."""
        new_items = []  # type: List[_NodeUnion]

        for item in node.items:
            self.visit(item)

            if isinstance(item, _List):
                new_items.extend(item.items)
            else:
                new_items.append(item)

        node.items = new_items


class _ConcatenateTextVisitor(_NodeVisitor):
    """Concatenate the consecutive text elements in lists recursively and in-place."""

    def visit_list(self, node: _List) -> None:
        """Visit the node list and its items recursively."""
        new_items = []  # type: List[_NodeUnion]

        accumulator = []  # type: List[_Text]
        for item in node.items:
            if isinstance(item, _Text):
                accumulator.append(item)
            else:
                self.visit(item)

                if len(accumulator) > 0:
                    new_items.append(
                        _Text(
                            content="".join(
                                text_element.content for text_element in accumulator
                            )
                        )
                    )
                    accumulator = []

                new_items.append(item)

        if len(accumulator) > 0:
            new_items.append(
                _Text(
                    content="".join(
                        text_element.content for text_element in accumulator
                    )
                )
            )

        node.items = new_items


class _RemoveRedundantParaVisitor(_NodeVisitor):
    """Remove the redundant ``<para>`` elements in-place."""

    def visit_element(self, node: _Element) -> None:
        self.visit(node.children)

        # noinspection PyUnresolvedReferences
        if (
            node.name in ("summary", "remarks", "li", "param", "returns", "para")
            and len(node.children.items) == 1
            and isinstance(node.children.items[0], _Element)
            and node.children.items[0].name == "para"
        ):
            # noinspection PyUnresolvedReferences
            node.children = node.children.items[0].children


class _RemoveInitialParaVisitor(_NodeVisitor):
    """Remove first ``<para>`` elements in a block in-place."""

    def visit_element(self, node: _Element) -> None:
        self.visit(node.children)

        # noinspection PyUnresolvedReferences
        if (
            node.name in ("summary", "remarks", "li", "param", "returns", "para")
            and isinstance(node.children.items[0], _Element)
            and node.children.items[0].name == "para"
        ):
            # noinspection PyUnresolvedReferences
            node.children.items[0] = node.children.items[0].children


def _compress_node_in_place(node: _NodeUnion) -> None:
    """Remove redundant nodes for more readability in the rendered text."""
    flatten_list_visitor = _FlattenListVisitor()
    flatten_list_visitor.visit(node)

    concatenate_text_visitor = _ConcatenateTextVisitor()
    concatenate_text_visitor.visit(node)

    remove_redundant_para_visitor = _RemoveRedundantParaVisitor()
    remove_redundant_para_visitor.visit(node)

    remove_initial_para_visitor = _RemoveInitialParaVisitor()
    remove_initial_para_visitor.visit(node)


def _render_summary_remarks_constraints(
    description: intermediate.SummaryRemarksConstraintsDescription,
) -> Tuple[Optional[_List], Optional[List[Error]]]:
    """Render a description where constraints are put in remarks."""
    result_items = []  # type: List[_NodeUnion]
    errors = []  # type: List[Error]

    element_renderer = _ElementRenderer()

    summary_node, summary_errors = element_renderer.transform(description.summary)
    if summary_errors is not None:
        errors.extend(
            Error(description.parsed.node, message) for message in summary_errors
        )
    else:
        assert summary_node is not None
        result_items.append(
            _Element(name="summary", children=_List(items=[summary_node]))
        )

    remark_nodes = []  # type: List[_NodeUnion]
    for remark in description.remarks:
        remark_node, remark_errors = element_renderer.transform(remark)
        if remark_errors:
            errors.extend(
                Error(description.parsed.node, message) for message in remark_errors
            )
        else:
            assert remark_node is not None
            remark_nodes.append(remark_node)

    constraint_nodes = []  # type: List[_NodeUnion]
    for identifier, docutils_element in description.constraints_by_identifier.items():
        body, body_errors = element_renderer.transform(docutils_element)
        if body_errors is not None:
            errors.extend(
                Error(description.parsed.node, message) for message in body_errors
            )
        else:
            assert body is not None

            # We in-line the constraint prefix for better readability.

            # noinspection PyUnresolvedReferences
            if (
                isinstance(body, _List)
                and len(body.items) > 0
                and isinstance(body.items[0], _Element)
                and body.items[0].name == "para"
            ):
                # noinspection PyUnresolvedReferences
                body.items[0].children.items.insert(
                    0, _Text(content=f"Constraint {identifier}:\n")
                )

                constraint_node = _Element(name="li", children=body)
            else:
                constraint_node = _Element(
                    name="li",
                    children=_List(
                        items=[
                            _Element(
                                name="para",
                                children=_List(
                                    items=[_Text(content=f"Constraint {identifier}:\n")]
                                ),
                            ),
                            body,
                        ]
                    ),
                )

            constraint_nodes.append(constraint_node)

    if len(errors) > 0:
        return None, errors

    if len(constraint_nodes) > 0:
        remark_nodes.append(
            _Element(name="para", children=_List(items=[_Text(content="Constraints:")]))
        )

        ul_node = _Element(name="ul", children=_List(items=constraint_nodes))

        remark_nodes.append(ul_node)

    if len(remark_nodes) > 0:
        result_items.append(
            _Element(name="remarks", children=_List(items=remark_nodes))
        )

    return _List(items=result_items), None


@require(lambda line: "\n" not in line)
def _comment_block_line(line: str) -> str:
    """Prepend `` * `` to the ``line``."""
    if len(line) == 0:
        return " *"

    return f" * {line}"


class _RelativeIndention:
    """
    Represent the relative indention.

    Since the indention is *relative*, it can be either positive, neutral or negative.
    """

    @require(lambda direction: direction in (-1, 0, 1))
    def __init__(self, direction: int) -> None:
        self.direction = direction

    def __repr__(self) -> str:
        """Generate text representation for easier debugging."""
        return f"{self.__class__.__name__}({self.direction!r})"


class _TextBlock(DBC):
    """
    Represent a block of text.

    This data structure is expected to be append-only mutable, where you keep adding
    new parts to the block. The parts are later expected to be joined by an empty
    string.

    All the text blocks are expected to be joined by empty strings.
    """

    def __init__(self, parts: List[str]) -> None:
        """Initialize with the given values."""
        self.parts = parts

    def __repr__(self) -> str:
        """Generate text representation for easier debugging."""
        return f"{self.__class__.__name__}({self.parts!r})"


class _EnforceNewLine(DBC):
    """
    Enforce that the following text starts on a new line.

    If there is already a new line output before, this text directive has no influence.
    """

    def __repr__(self) -> str:
        """Generate text representation for easier debugging."""
        return f"{self.__class__.__name__}()"


_TextDirective = Union[_RelativeIndention, _TextBlock, _EnforceNewLine]


class _ToTextDirectivesVisitor(_NodeVisitor):
    """
    Convert the nodes to a text as represented by text control directives.

    The text is expected to be valid XML and properly escaped.
    """

    #: The resulting text control directives
    directives: List[_TextDirective]

    def __init__(self) -> None:
        self.directives = []

    def _last_or_new_block(self) -> _TextBlock:
        """Retrieve the last block, or initialize a new block, if no last block."""
        if len(self.directives) == 0 or not isinstance(self.directives[-1], _TextBlock):
            self.directives.append(_TextBlock(parts=[]))

        assert isinstance(self.directives[-1], _TextBlock)
        return self.directives[-1]

    def visit_text(self, node: _Text) -> None:
        self._last_or_new_block().parts.append(xml.sax.saxutils.escape(node.content))

    def visit_element(self, node: _Element) -> None:
        """Visit the element node and its children."""

        if node.name in ("summary",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_EnforceNewLine())

        elif node.name in ("see",):
            assert (
                len(node.attrs) == 1 and "cref" in node.attrs
            ), f"Missing ref attribute in a link node {node.name!r}"

            link_target = node.attrs["cref"]

            self.directives.append(_TextBlock(parts=[f"{{@link {link_target}}}"]))

        elif node.name in ("c",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            self._last_or_new_block().parts.append("{@literal ")

            for item in node.children.items:
                self.visit(item)

            self._last_or_new_block().parts.append("}")

        elif node.name in ("para",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            self.directives.append(_EnforceNewLine())

            # single tag nodes
            self.directives.append(_TextBlock(parts=[f"<p>"]))

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_EnforceNewLine())

        elif node.name in ("remarks",):
            # single tag nodes
            self.directives.append(_TextBlock(parts=[f"<p>"]))

            for item in node.children.items:
                self.visit(item)

        elif node.name in ("em",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            self.directives.append(_TextBlock(parts=[f"<{node.name}>"]))

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_TextBlock(parts=[f"</{node.name}>"]))

        elif node.name in ("ul",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            self.directives.append(_EnforceNewLine())

            self.directives.append(_TextBlock(parts=[f"<{node.name}>"]))

            self.directives.append(_EnforceNewLine())

            self.directives.append(_RelativeIndention(direction=1))

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_EnforceNewLine())

            self.directives.append(_RelativeIndention(direction=-1))

            self.directives.append(_TextBlock(parts=[f"</{node.name}>"]))

        elif node.name in ("li",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            self.directives.append(_EnforceNewLine())

            self.directives.append(_TextBlock(parts=[f"<{node.name}> "]))

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_EnforceNewLine())

        elif node.name in ("param",):
            assert (
                len(node.attrs) == 1 and
                "name" in node.attrs
            ), f"Invalid attributes in a node {node.name!r}"

            param_name = node.attrs["name"]

            self.directives.append(_TextBlock(parts=[f"@{node.name} {param_name}"]))

            self.directives.append(_EnforceNewLine())

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_EnforceNewLine())

        elif node.name in ("returns",):
            assert (
                len(node.attrs) == 0
            ), f"Unexpected attributes in a node {node.name!r}"

            self.directives.append(_TextBlock(parts=[f"@{node.name} "]))

            self.directives.append(_EnforceNewLine())

            for item in node.children.items:
                self.visit(item)

            self.directives.append(_EnforceNewLine())

        else:
            assert False, f"Unexpected node type: {node.name!r}"


_TextDirectiveExceptEnforceNewLine = Union[_RelativeIndention, _TextBlock]
assert_union_without_excluded(
    original_union=_TextDirective,
    subset_union=_TextDirectiveExceptEnforceNewLine,
    excluded=[_EnforceNewLine],
)

T = TypeVar("T")

def pairwise(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
    """Iterate pair-wise over the iterator."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


# fmt: off
@ensure(
    lambda result:
    all(
        len(directive.parts) > 0
        for directive in result
        if isinstance(directive, _TextBlock)
    ),
    "No empty text blocks"
)
@ensure(
    lambda result:
    all(
        not (
            isinstance(prev, _TextBlock)
            and isinstance(current, _TextBlock)
        )
        for prev, current in pairwise(result)
    ),
    "All text blocks are merged and there are no consecutive text blocks"
)
# fmt: on
def _compress_text_directives(
    directives: Sequence[_TextDirective],
) -> List[_TextDirectiveExceptEnforceNewLine]:
    """Merge consecutive text blocks and enforce the new lines."""
    # region Remove empty blocks

    directives_wo_empty_blocks = [
        directive
        for directive in directives
        if not (isinstance(directive, _TextBlock) and len(directive.parts) == 0)
    ]

    # endregion

    # region Fulfill new-line enforcement

    directives_wo_enforce_new_line = (
        []
    )  # type: List[_TextDirectiveExceptEnforceNewLine]

    previous_text_block = None  # type: Optional[_TextBlock]

    for directive in directives_wo_empty_blocks:
        if isinstance(directive, _EnforceNewLine):
            if previous_text_block is not None:
                assert len(previous_text_block.parts) > 0

                if not previous_text_block.parts[-1].endswith("\n"):
                    previous_text_block.parts.append("\n")
        elif isinstance(directive, _TextBlock):
            assert len(directive.parts) > 0

            previous_text_block = directive
            directives_wo_enforce_new_line.append(directive)

        elif isinstance(directive, _RelativeIndention):
            directives_wo_enforce_new_line.append(directive)
        else:
            assert_never(directive)

    # endregion

    # region Merge consecutive text blocks

    directives_w_merged_blocks = []  # type: List[_TextDirectiveExceptEnforceNewLine]

    for directive in directives_wo_enforce_new_line:
        if isinstance(directive, _TextBlock):
            assert len(directive.parts) > 0

            if len(directives_w_merged_blocks) > 0 and isinstance(
                directives_w_merged_blocks[-1], _TextBlock
            ):
                directives_w_merged_blocks[-1].parts.extend(directive.parts)
            else:
                directives_w_merged_blocks.append(directive)
        else:
            directives_w_merged_blocks.append(directive)

    # endregion

    return directives_w_merged_blocks


def _to_text(node: _NodeUnion) -> str:
    """
    Convert the node to a text representation.

    For readability and no phantom elements, the ``node`` is expected to be compressed
    before.
    """
    to_text_directives_visitor = _ToTextDirectivesVisitor()
    to_text_directives_visitor.visit(node)

    # We compress to do away with the new-line enforcement and consecutive and empty
    # blocks, so that the operations below become much easier to write.
    directives = _compress_text_directives(to_text_directives_visitor.directives)

    writer = io.StringIO()
    level = 0  # indention level

    for directive in directives:
        if isinstance(directive, _TextBlock):
            writer.write(textwrap.indent("".join(directive.parts), level * "  "))

        elif isinstance(directive, _RelativeIndention):
            assert level + directive.direction >= 0, (
                f"Negative absolute indention not possible: "
                f"{level=}, {directive.direction=}"
            )
            level += directive.direction

        else:
            assert_never(directive)

    return writer.getvalue()


def _generate_summary_remarks_constraints(
    description: intermediate.SummaryRemarksConstraintsDescription,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for a summary-remarks-constraints."""
    node, errors = _render_summary_remarks_constraints(description=description)
    if errors is not None:
        return None, errors

    assert node is not None

    _compress_node_in_place(node=node)
    text = _to_text(node)

    commented_lines = ["/**"] + [_comment_block_line(line) for line in text.splitlines()] + [" */"]

    return Stripped("\n".join(commented_lines)), None


def _generate_summary_remarks(
    description: intermediate.SummaryRemarksDescription,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for a summary-remarks description."""
    node, errors = _render_summary_remarks(description=description)
    if errors is not None:
        return None, errors

    assert node is not None

    _compress_node_in_place(node=node)
    text = _to_text(node)

    commented_lines = ["/**"] + [_comment_block_line(line) for line in text.splitlines()] + [" */"]

    return Stripped("\n".join(commented_lines)), None


def _render_summary_remarks(
    description: intermediate.SummaryRemarksDescription,
) -> Tuple[Optional[_List], Optional[List[Error]]]:
    """Render a description to our description node."""
    result_items = []  # type: List[_NodeUnion]
    errors = []  # type: List[Error]

    element_renderer = _ElementRenderer()

    summary_node, summary_errors = element_renderer.transform(description.summary)
    if summary_errors is not None:
        errors.extend(
            Error(description.parsed.node, message) for message in summary_errors
        )
    else:
        assert summary_node is not None

        result_items.append(
            _Element(name="summary", children=_List(items=[summary_node]))
        )

    remark_nodes = []  # type: List[_NodeUnion]
    for remark in description.remarks:
        remark_node, remark_errors = element_renderer.transform(remark)
        if remark_errors:
            errors.extend(
                Error(description.parsed.node, message) for message in remark_errors
            )
        else:
            assert remark_node is not None
            remark_nodes.append(remark_node)

    if len(errors) > 0:
        return None, errors

    if len(remark_nodes) > 0:
        result_items.append(
            _Element(name="remarks", children=_List(items=remark_nodes))
        )

    return _List(items=result_items), None


def generate_comment_for_enumeration_literal(
    description: intermediate.DescriptionOfEnumerationLiteral,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for the given enumeration literal."""
    return _generate_summary_remarks(description)


def generate_comment_for_our_type(
    description: intermediate.DescriptionOfOurType,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for our type."""
    return _generate_summary_remarks_constraints(description)


def generate_comment_for_property(
    description: intermediate.DescriptionOfProperty,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for the given property."""
    return _generate_summary_remarks_constraints(description)


def _render_description_of_signature(
    description: intermediate.DescriptionOfSignature,
) -> Tuple[Optional[_List], Optional[List[Error]]]:
    """Render a description where constraints are put in remarks."""
    result_items = []  # type: List[_NodeUnion]
    errors = []  # type: List[Error]

    renderer = _ElementRenderer()

    summary_node, summary_errors = renderer.transform(description.summary)
    if summary_errors is not None:
        errors.extend(
            Error(description.parsed.node, message) for message in summary_errors
        )
    else:
        assert summary_node is not None
        result_items.append(
            _Element(name="summary", children=_List(items=[summary_node]))
        )

    remark_nodes = []  # type: List[_NodeUnion]
    for remark in description.remarks:
        remark_node, remark_errors = renderer.transform(remark)
        if remark_errors:
            errors.extend(
                Error(description.parsed.node, message) for message in remark_errors
            )
        else:
            assert remark_node is not None
            remark_nodes.append(remark_node)

    param_nodes = []  # type: List[_NodeUnion]

    for name, docutils_element in description.arguments_by_name.items():
        param, body_errors = renderer.transform(docutils_element)
        if body_errors is not None:
            errors.extend(
                Error(description.parsed.node, message) for message in body_errors
            )
        else:
            assert param is not None

            param_nodes.append(
                _Element(
                    name="param",
                    attrs=collections.OrderedDict([("name", name)]),
                    children=_List(items=[param]),
                )
            )

    returns_node = None  # type: Optional[_NodeUnion]

    if description.returns is not None:
        # We need to help the type checker in PyCharm a bit.
        assert isinstance(description.returns, docutils.nodes.field_body)

        returns, returns_errors = renderer.transform(description.returns)
        if returns_errors is not None:
            errors.extend(
                Error(description.parsed.node, message) for message in returns_errors
            )
        else:
            assert returns is not None

            returns_node = _Element(name="returns", children=_List(items=[returns]))

    if len(errors) > 0:
        return None, errors

    if len(remark_nodes) > 0:
        result_items.append(
            _Element(name="remarks", children=_List(items=remark_nodes))
        )

    result_items.extend(param_nodes)

    if returns_node is not None:
        result_items.append(returns_node)

    return _List(items=result_items), None


def generate_comment_for_signature(
    description: intermediate.DescriptionOfSignature,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """
    Generate the documentation comment for the given signature.

    A signature, in this context, means a function or a method signature.
    """
    node, errors = _render_description_of_signature(description=description)
    if errors is not None:
        return None, errors

    assert node is not None

    _compress_node_in_place(node=node)
    text = _to_text(node)

    commented_lines = ["/**"] + [_comment_block_line(line) for line in text.splitlines()] + [" */"]

    return Stripped("\n".join(commented_lines)), None
