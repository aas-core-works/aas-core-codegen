"""Generate the C++ data structures from the intermediate representation."""
import io
import itertools
import textwrap
from typing import (
    Optional,
    Dict,
    List,
    Tuple,
    cast,
    Union,
)

from icontract import ensure, require

from aas_core_codegen import intermediate
from aas_core_codegen import specific_implementations
from aas_core_codegen.common import (
    Error,
    Identifier,
    assert_never,
    Stripped,
    indent_but_first_line,
)
from aas_core_codegen.cpp import (
    common as cpp_common,
    naming as cpp_naming,
    description as cpp_description,
)
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
)
from aas_core_codegen.intermediate import construction as intermediate_construction


# region Checks


def _human_readable_identifier(
    something: Union[
        intermediate.Enumeration,
        intermediate.AbstractClass,
        intermediate.ConcreteClass,
        intermediate.EnumerationLiteral,
    ]
) -> str:
    """
    Represent ``something`` in a human-readable text.

    The reader should be able to trace ``something`` back to the meta-model.
    """
    # NOTE (mristin, 2023-03-29):
    # This function has been copy-pasted from
    # :py:mod:`aas_core_codegen.python.structure._generate`. We tried to refactor it to
    # :py:mod:`aas_core_codegen.intermediate`, but it turned out that the refactored
    # code was nigh unreadable. So we preferred a little bit of copying to a little
    # bit of complexity.

    result = None  # type: Optional[str]

    if isinstance(something, intermediate.Enumeration):
        result = f"meta-model enumeration {something.name!r}"
    elif isinstance(something, intermediate.EnumerationLiteral):
        result = f"meta-model enumeration literal {something.name!r}"
    elif isinstance(something, intermediate.AbstractClass):
        result = f"meta-model abstract class {something.name!r}"
    elif isinstance(something, intermediate.ConcreteClass):
        result = f"meta-model concrete class {something.name!r}"
    else:
        assert_never(something)

    assert result is not None
    return result


def _verify_structure_name_collisions(
    symbol_table: intermediate.SymbolTable,
) -> List[Error]:
    """Verify that the C++ names of the structures do not collide."""
    observed_type_names: Dict[
        Identifier,
        Union[
            intermediate.Enumeration,
            intermediate.AbstractClass,
            intermediate.ConcreteClass,
        ],
    ] = dict()

    errors = []  # type: List[Error]

    # region Inter-structure collisions

    for enum_or_cls in itertools.chain(symbol_table.enumerations, symbol_table.classes):
        names = None  # type: Optional[List[Identifier]]

        if isinstance(enum_or_cls, intermediate.Enumeration):
            names = [cpp_naming.enum_name(enum_or_cls.name)]
        elif isinstance(enum_or_cls, intermediate.AbstractClass):
            names = [cpp_naming.interface_name(enum_or_cls.name)]
        elif isinstance(enum_or_cls, intermediate.ConcreteClass):
            names = [
                cpp_naming.interface_name(enum_or_cls.name),
                cpp_naming.class_name(enum_or_cls.name),
            ]
        else:
            assert_never(enum_or_cls)

        for name in names:
            other = observed_type_names.get(name, None)

            if other is not None:
                errors.append(
                    Error(
                        enum_or_cls.parsed.node,
                        f"The C++ name {name!r} "
                        f"of the {_human_readable_identifier(enum_or_cls)} "
                        f"collides with the C++ name "
                        f"of the {_human_readable_identifier(other)}",
                    )
                )
            else:
                observed_type_names[name] = enum_or_cls

    # endregion

    # region Intra-structure collisions

    for our_type in symbol_table.our_types:
        collision_error = _verify_intra_structure_collisions(our_type=our_type)

        if collision_error is not None:
            errors.append(collision_error)

    # endregion

    return errors


def _verify_intra_structure_collisions(
    our_type: intermediate.OurType,
) -> Optional[Error]:
    """Verify that no member names collide in the Golang structure of our type."""
    errors = []  # type: List[Error]

    if isinstance(our_type, intermediate.Enumeration):
        observed_literal_names = {}  # type: Dict[Identifier, str]
        for literal in our_type.literals:
            name = cpp_naming.enum_literal_name(literal.name)

            if name in observed_literal_names:
                errors.append(
                    Error(
                        literal.parsed.node,
                        f"C++ name {name!r} corresponding "
                        f"to the meta-model enumeration literal {literal.name!r} "
                        f"collides with the literal {observed_literal_names[name]}",
                    )
                )
            else:
                observed_literal_names[name] = literal.name

    elif isinstance(our_type, intermediate.ConstrainedPrimitive):
        pass

    elif isinstance(our_type, intermediate.Class):
        observed_member_names = {}  # type: Dict[Identifier, str]

        for prop in our_type.properties:
            name = cpp_naming.getter_name(prop.name)
            if name in observed_member_names:
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C++ getter {name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[name]}",
                    )
                )
            else:
                observed_member_names[name] = (
                    f"C++ getter {name!r} corresponding to "
                    f"the meta-model property {prop.name!r}"
                )

            name = cpp_naming.mutable_getter_name(prop.name)
            if name in observed_member_names:
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C++ mutable getter {name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[name]}",
                    )
                )
            else:
                observed_member_names[name] = (
                    f"C++ mutable getter {name!r} corresponding to "
                    f"the meta-model property {prop.name!r}"
                )

            name = cpp_naming.setter_name(prop.name)
            if name in observed_member_names:
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C++ setter {name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[name]}",
                    )
                )
            else:
                observed_member_names[name] = (
                    f"C++ setter {name!r} corresponding to "
                    f"the meta-model property {prop.name!r}"
                )

            name = cpp_naming.private_property_name(prop.name)
            if name in observed_member_names:
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"C++ private property {name!r} corresponding "
                        f"to the meta-model property {prop.name!r} collides with "
                        f"the {observed_member_names[name]}",
                    )
                )
            else:
                observed_member_names[name] = (
                    f"C++ private property {name!r} corresponding to "
                    f"the meta-model property {prop.name!r}"
                )

        for method in our_type.methods:
            method_name = cpp_naming.method_name(method.name)

            if method_name in observed_member_names:
                errors.append(
                    Error(
                        method.parsed.node,
                        f"C++ method {method_name!r} corresponding "
                        f"to the meta-model method {method.name!r} collides with "
                        f"the {observed_member_names[method_name]}",
                    )
                )
            else:
                observed_member_names[method_name] = (
                    f"C++ method {method_name!r} corresponding to "
                    f"the meta-model method {method.name!r}"
                )

    else:
        assert_never(our_type)

    if len(errors) > 0:
        errors.append(
            Error(
                our_type.parsed.node,
                f"Naming collision(s) in C++ code for our type {our_type.name!r}",
                underlying=errors,
            )
        )

    return None


class VerifiedIntermediateSymbolTable(intermediate.SymbolTable):
    """Represent a verified symbol table which can be used for code generation."""

    # noinspection PyInitNewSignature
    def __new__(
        cls, symbol_table: intermediate.SymbolTable
    ) -> "VerifiedIntermediateSymbolTable":
        raise AssertionError("Only for type annotation")


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def verify(
    symbol_table: intermediate.SymbolTable,
) -> Tuple[Optional[VerifiedIntermediateSymbolTable], Optional[List[Error]]]:
    """Verify that Golang code can be generated from the ``symbol_table``."""
    errors = []  # type: List[Error]

    structure_name_collisions = _verify_structure_name_collisions(
        symbol_table=symbol_table
    )

    errors.extend(structure_name_collisions)

    if len(errors) > 0:
        return None, errors

    return cast(VerifiedIntermediateSymbolTable, symbol_table), None


# endregion

# region Generation


@require(lambda enumeration, literal: id(literal) in enumeration.literal_id_set)
@require(lambda literal: literal.description is not None)
def _generate_comment_for_enumeration_literal(
    enumeration: intermediate.Enumeration,
    literal: intermediate.EnumerationLiteral,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for the given enumeration literal."""
    # NOTE (mristin, 2023-07-14):
    # We need to state the pre-condition for the second time for mypy.
    assert literal.description is not None

    # fmt: off
    comment, errors = (
        cpp_description.generate_comment_for_summary_remarks(
            description=literal.description,
            context=cpp_description.Context(
                namespace=cpp_common.TYPES_NAMESPACE,
                cls_or_enum=enumeration
            )
        )
    )
    # fmt: on

    if errors is not None:
        return None, errors

    assert comment is not None

    return comment, None


@require(lambda cls_or_enum: cls_or_enum.description is not None)
def _generate_comment_for_cls_or_enum(
    cls_or_enum: Union[intermediate.Enumeration, intermediate.ClassUnion],
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the documentation comment for our type."""
    # NOTE (mristin, 2023-07-14):
    # We need to state the pre-condition for the second time for mypy.
    assert cls_or_enum.description is not None

    # fmt: off
    comment, errors = (
        cpp_description
        .generate_comment_for_summary_remarks_constraints(
            description=cls_or_enum.description,
            context=cpp_description.Context(
                namespace=cpp_common.TYPES_NAMESPACE,
                cls_or_enum=None
            )
        )
    )
    # fmt: on

    if errors is not None:
        return None, errors

    assert comment is not None

    return comment, None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _generate_enum(
    enum: intermediate.Enumeration,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the C++ code for the enum."""
    writer = io.StringIO()

    errors = []  # type: List[Error]

    comment = None  # type: Optional[Stripped]
    if enum.description is not None:
        comment, comment_errors = _generate_comment_for_cls_or_enum(cls_or_enum=enum)

        if comment_errors:
            errors.append(
                Error(
                    enum.description.parsed.node,
                    f"Failed to generate the comment "
                    f"for the enumeration {enum.name!r}",
                    comment_errors,
                )
            )
        else:
            assert comment is not None

    if comment is not None:
        writer.write(comment)
        writer.write("\n")

    name = cpp_naming.enum_name(enum.name)

    writer.write(f"enum class {name} : std::uint32_t {{\n")
    if len(enum.literals) == 0:
        writer.write("// Intentionally empty.")
    else:
        for i, literal in enumerate(enum.literals):
            if literal.description is not None:
                comment, comment_errors = _generate_comment_for_enumeration_literal(
                    enumeration=enum, literal=literal
                )
                if comment_errors is not None:
                    errors.append(
                        Error(
                            literal.description.parsed.node,
                            f"Failed to generate the documentation comment "
                            f"for enumeration literal {literal.name!r}",
                            comment_errors,
                        )
                    )
                else:
                    assert comment is not None
                    writer.write(textwrap.indent(comment, I))
                    writer.write("\n")

            literal_name = cpp_naming.enum_literal_name(literal.name)

            writer.write(textwrap.indent(f"{literal_name} = {i}", I))
            if i < len(enum.literals):
                writer.write(",\n")
            else:
                writer.write("\n")

        writer.write(f"}};  // enum class {name}")

    if len(errors) > 0:
        return None, Error(
            enum.parsed.node,
            f"Failed to generate the Golang code for the enumeration {enum.name!r}",
            errors,
        )

    return Stripped(writer.getvalue()), None


def _generate_literals_of_enum_definition(enum: intermediate.Enumeration) -> Stripped:
    """Generate the definition for the constant vector listing the literals."""
    enum_name = cpp_naming.enum_name(enum.name)
    constant_name = cpp_naming.constant_name(Identifier(f"literals_of_{enum.name}"))
    return Stripped(
        f"""\
extern const std::vector<
{I}{enum_name}
> {constant_name};"""
    )


def _generate_literals_of_enum_implementation(
    enum: intermediate.Enumeration,
) -> Stripped:
    """Generate the implementation for the constant vector listing the literals."""
    enum_name = cpp_naming.enum_name(enum.name)
    constant_name = cpp_naming.constant_name(Identifier(f"literals_of_{enum.name}"))

    literals = []
    for literal in enum.literals:
        literal_name = cpp_naming.enum_literal_name(literal.name)
        literals.append(f"{enum_name}::{literal_name}")

    literals_joined = ",\n".join(literals)

    return Stripped(
        f"""\
/**
 * List the literals of {enum_name}.
 *
 * C++ does not provide an elegant way to iterate over the literals, so
 * this array helps you avoid common errors and pitfalls.
 */
const std::vector<
{I}{enum_name}
> {constant_name} = {{
{I}{indent_but_first_line(literals_joined, I)}
}};"""
    )


def _generate_model_type_definition(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """
    Generate the enumeration corresponding to the model types.

    This is necessary so that we can have fast switches on instance types.
    """
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))

    literal_specs = []  # type: List[Stripped]
    for i, cls in enumerate(symbol_table.concrete_classes):
        literal_name = cpp_naming.enum_literal_name(cls.name)

        literal_specs.append(Stripped(f"{literal_name} = {i}"))

    literal_specs_joined = ",\n".join(literal_specs)

    if len(literal_specs) == 0:
        return Stripped(
            f"""\
enum class {enum_name} : std::uint32_t {{
{I}// Intentionally empty.
}};"""
        )

    return Stripped(
        f"""\
/**
 * Enumerate the model types for faster type switches.
 *
 * For example, switch statements can be implemented as jump tables.
 */
enum class {enum_name} : std::uint32_t {{
{I}{indent_but_first_line(literal_specs_joined, I)}
}};"""
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_class_interface(
    cls: intermediate.ClassUnion,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition of an interface representing a class."""
    errors = []  # type: List[Error]

    members = []  # type: List[Stripped]

    for prop in cls.properties:
        if prop.specified_for is not cls:
            continue

        description_comment = None  # type: Optional[Stripped]
        if prop.description is not None:
            (
                description_comment,
                description_errors,
            ) = cpp_description.generate_comment_for_summary_remarks(
                prop.description,
                context=cpp_description.Context(
                    namespace=cpp_common.TYPES_NAMESPACE, cls_or_enum=cls
                ),
            )
            if description_errors is not None:
                errors.append(
                    Error(
                        prop.parsed.node,
                        f"Failed to generate the description comment "
                        f"for the property {prop.name!r}",
                        description_errors,
                    )
                )
            else:
                assert description_comment is not None
                members.append(
                    Stripped(
                        f"""\
///@{{
{description_comment}"""
                    )
                )

        getter_name = cpp_naming.getter_name(prop.name)
        getter_type = cpp_common.generate_type_with_const_ref_if_applicable(
            prop.type_annotation
        )

        members.append(Stripped(f"virtual {getter_type} {getter_name}() const = 0;"))

        mutable_getter_name = cpp_naming.mutable_getter_name(prop.name)
        mutable_getter_type = cpp_common.generate_type_with_ref(prop.type_annotation)
        members.append(
            Stripped(f"virtual {mutable_getter_type} {mutable_getter_name}() = 0;")
        )

        setter_name = cpp_naming.setter_name(prop.name)
        # NOTE (mristin, 2023-09-13):
        # For a discussion on ``std::shared_ptr`` and referencing,
        # see: https://herbsutter.com/2013/06/05/gotw-91-solution-smart-pointer-parameters/

        # NOTE (mristin, 2023-09-13):
        # We provide setters which only set-by-value logic since this seems to be
        # the best approach for general cases,
        # see: https://stackoverflow.com/questions/10692345/is-it-worth-adding-a-move-enabled-setter.
        #
        # Whenever you know that you do not need the value after calling the setter,
        # make sure to call it with ``std::move(.)``.

        value_type = cpp_common.generate_type(type_annotation=prop.type_annotation)
        members.append(
            Stripped(
                f"""\
virtual void {setter_name}(
{I}{indent_but_first_line(value_type, I)} value
) = 0;"""
            )
        )

        if description_comment is not None:
            members.append(Stripped("///@}"))

    for method in cls.methods:
        if method.specified_for is not cls:
            continue

        returns = (
            cpp_common.generate_type(method.returns)
            if method.returns is not None
            else None
        )

        return_type = "void" if returns is None else returns

        arg_types_names = [
            (
                cpp_common.generate_type_with_const_ref_if_applicable(
                    arg.type_annotation
                ),
                cpp_naming.argument_name(arg.name),
            )
            for arg in method.arguments
        ]

        method_name = cpp_naming.method_name(method.name)

        const_suffix = " const" if method.non_mutating else ""

        description_comment_prefix = ""
        if method.description is not None:
            (
                description_comment,
                description_errors,
            ) = cpp_description.generate_comment_for_summary_remarks(
                method.description,
                context=cpp_description.Context(
                    namespace=cpp_common.TYPES_NAMESPACE, cls_or_enum=cls
                ),
            )
            if description_errors is not None:
                errors.append(
                    Error(
                        method.parsed.node,
                        f"Failed to generate the description comment "
                        f"for the method {method.name!r}",
                        description_errors,
                    )
                )
            else:
                assert description_comment is not None
                description_comment_prefix = description_comment + "\n"

        if len(method.arguments) == 0:
            members.append(
                Stripped(
                    f"{description_comment_prefix}"
                    f"virtual {return_type} {method_name}(){const_suffix} = 0;"
                )
            )
        else:
            arguments_definition = ",\n".join(
                f"{arg_type} {arg_name}" for arg_type, arg_name in arg_types_names
            )

            members.append(
                Stripped(
                    f"""\
{description_comment_prefix}virtual {return_type} {method_name}(
{I}{indent_but_first_line(arguments_definition, I)}
){const_suffix} = 0;"""
                )
            )

    interface_name = cpp_naming.interface_name(cls.name)

    members.append(Stripped(f"virtual ~{interface_name}() = default;"))

    members_joined = "\n\n".join(members)

    inheritances = [
        f"virtual public {cpp_naming.interface_name(inheritance.name)}"
        for inheritance in cls.inheritances
    ]

    if len(inheritances) == 0:
        inheritances = ["virtual public IClass"]

    inheritances_joined = ",\n".join(inheritances)

    description_comment = None
    if cls.description is not None:
        (
            description_comment,
            description_errors,
        ) = cpp_description.generate_comment_for_summary_remarks_constraints(
            description=cls.description,
            context=cpp_description.Context(
                namespace=cpp_common.TYPES_NAMESPACE, cls_or_enum=cls
            ),
        )
        if description_errors is not None:
            errors.append(
                Error(
                    cls.description.parsed.node,
                    "Failed to translate the class description to a comment",
                    description_errors,
                )
            )
        else:
            assert description_comment is not None

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node,
            f"Failed to generate the class definition for {cls.name!r}",
            errors,
        )

    maybe_description_comment_nl = (
        "" if description_comment is None else description_comment + "\n"
    )

    return (
        Stripped(
            f"""\
{maybe_description_comment_nl}class {interface_name}
{II}: {indent_but_first_line(inheritances_joined, II)} {{
 public:
{I}{indent_but_first_line(members_joined, I)}
}};"""
        ),
        None,
    )


def _generate_class_definition(cls: intermediate.ConcreteClass) -> Stripped:
    """Generate the definition of a concrete class."""
    public_members = []  # type: List[Stripped]

    cls_name = cpp_naming.class_name(cls.name)

    if len(cls.constructor.arguments) == 0:
        public_members.append(Stripped(f"{cls_name}() {{}}"))
    else:
        constructor_argument_specs = []  # type: List[str]
        for arg in cls.constructor.arguments:
            arg_type = cpp_common.generate_type(arg.type_annotation)
            arg_name = cpp_naming.argument_name(arg.name)

            assign_default_suffix = (
                " = common::nullopt"
                if isinstance(arg.type_annotation, intermediate.OptionalTypeAnnotation)
                else ""
            )

            constructor_argument_specs.append(
                f"{arg_type} {arg_name}{assign_default_suffix}"
            )

        constructor_arguments_specs_joined = ",\n".join(constructor_argument_specs)

        # NOTE (mristin, 2023-09-22):
        # See: https://stackoverflow.com/questions/12437241/c-always-use-explicit-constructor
        non_default_argument_count = sum(
            1 for arg in cls.constructor.arguments if arg.default is None
        )

        explicit_prefix = "explicit " if non_default_argument_count == 1 else ""

        public_members.append(
            Stripped(
                f"""\
{explicit_prefix}{cls_name}(
{I}{indent_but_first_line(constructor_arguments_specs_joined, I)}
);"""
            )
        )

    model_type_getter = cpp_naming.getter_name(Identifier("model_type"))
    model_type_enum = cpp_naming.enum_name(Identifier("Model_type"))

    public_members.append(
        Stripped(f"{model_type_enum} {model_type_getter}() const override;")
    )

    for prop in cls.properties:
        getter_name = cpp_naming.getter_name(prop.name)
        getter_type = cpp_common.generate_type_with_const_ref_if_applicable(
            prop.type_annotation
        )

        public_members.append(
            Stripped(
                f"// region Get and set {cpp_naming.private_property_name(prop.name)}"
            )
        )

        public_members.append(
            Stripped(f"{getter_type} {getter_name}() const override;")
        )

        mutable_getter_name = cpp_naming.mutable_getter_name(prop.name)
        mutable_getter_type = cpp_common.generate_type_with_ref(prop.type_annotation)
        public_members.append(
            Stripped(f"{mutable_getter_type} {mutable_getter_name}() override;")
        )

        setter_name = cpp_naming.setter_name(prop.name)

        value_type = cpp_common.generate_type(type_annotation=prop.type_annotation)
        public_members.append(
            Stripped(
                f"""\
void {setter_name}(
{I}{indent_but_first_line(value_type, I)} value
) override;"""
            )
        )

        public_members.append(Stripped("// endregion"))

    for method in cls.methods:
        returns = (
            cpp_common.generate_type(method.returns)
            if method.returns is not None
            else None
        )

        return_type = "void" if returns is None else returns

        arg_types_names = [
            (
                cpp_common.generate_type_with_const_ref_if_applicable(
                    arg.type_annotation
                ),
                cpp_naming.argument_name(arg.name),
            )
            for arg in method.arguments
        ]

        method_name = cpp_naming.method_name(method.name)

        const_suffix = " const" if method.non_mutating else ""

        if len(method.arguments) == 0:
            public_members.append(
                Stripped(f"{return_type} {method_name}(){const_suffix} override;")
            )
        else:
            arguments_definition = ",\n".join(
                f"{arg_type} {arg_name}" for arg_type, arg_name in arg_types_names
            )

            public_members.append(
                Stripped(
                    f"""\
{return_type} {method_name}(
{I}{indent_but_first_line(arguments_definition, I)}
){const_suffix} override;"""
                )
            )

    public_members.append(Stripped(f"~{cls_name}() override = default;"))

    public_members_joined = "\n\n".join(public_members)

    interface_name = cpp_naming.interface_name(cls.name)

    private_members = []  # type: List[Stripped]
    for prop in cls.properties:
        value_type = cpp_common.generate_type(type_annotation=prop.type_annotation)

        member_name = cpp_naming.private_property_name(prop.name)
        private_members.append(Stripped(f"{value_type} {member_name};"))

    blocks = [
        f"""\
 public:
{I}{indent_but_first_line(public_members_joined, I)}"""
    ]

    if len(private_members) > 0:
        private_members_joined = "\n\n".join(private_members)
        blocks.append(
            f"""\
 private:
{I}{indent_but_first_line(private_members_joined, I)}"""
        )

    blocks_joined = "\n\n".join(blocks)

    return Stripped(
        f"""\
class {cls_name}
{II}: public {interface_name} {{
{blocks_joined}
}};"""
    )


def _generate_is_cls_definition(cls: intermediate.ClassUnion) -> Stripped:
    """Generate the definition of the function to check is-a based on model type."""
    function_name = cpp_naming.function_name(Identifier(f"is_{cls.name}"))

    interface_name = cpp_naming.interface_name(cls.name)

    return Stripped(
        f"""\
/**
 * \\brief Check whether \\p that instance is of runtime type
 * \\ref {interface_name}.
 *
 * We use `IClass::model_type` to determine the runtime type, which is
 * a bit faster than native C++'s RTTI.
 *
 * \\param that instance to check for runtime type
 * \\return `true` if \\p that instance is indeed
 * an instance of \\ref {interface_name}
 */
bool {function_name}(
{I}const IClass& that
);"""
    )


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_header(
    symbol_table: VerifiedIntermediateSymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
    library_namespace: Stripped,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the C++ header code of the structures based on the symbol table."""
    namespace = Stripped(f"{library_namespace}::{cpp_common.TYPES_NAMESPACE}")

    include_guard_var = cpp_common.include_guard_var(namespace)

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        Stripped(
            f"""\
#ifndef {include_guard_var}
#define {include_guard_var}"""
        ),
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "{include_prefix_path}/common.hpp"

#pragma warning(push, 0)
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(library_namespace),
        Stripped(
            f"""\
/**
 * \\defgroup types Define data structures corresponding to the meta-model.
 * @{{
 */
namespace {cpp_common.TYPES_NAMESPACE} {{"""
        ),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    blocks.append(Stripped("// region Enumerations"))

    blocks.append(_generate_model_type_definition(symbol_table=symbol_table))

    for enum in symbol_table.enumerations:
        block, error = _generate_enum(enum=enum)
        if error is not None:
            errors.append(error)
        else:
            assert block is not None
            blocks.append(block)

    blocks.append(Stripped("// endregion Enumerations"))

    blocks.append(Stripped("// region Forward declaration of interfaces"))

    blocks.append(Stripped("// endregion Forward declaration of interfaces"))

    for cls in symbol_table.classes:
        interface_name = cpp_naming.interface_name(cls.name)
        blocks.append(Stripped(f"class {interface_name};"))

    blocks.append(Stripped("// region Class interfaces"))

    model_type_getter = cpp_naming.getter_name(Identifier("model_type"))
    model_type_enum = cpp_naming.enum_name(Identifier("Model_type"))

    blocks.append(
        Stripped(
            f"""\
/**
 * Model the most general instance of the model.
 */
class IClass {{
 public:
{I}/**
{I} * Indicate the runtime model type.
{I} */
{I}virtual {model_type_enum} {model_type_getter}() const = 0;
{I}virtual ~IClass() = default;
}};"""
        )
    )

    for cls in symbol_table.classes:
        block, error = _generate_class_interface(cls=cls)
        if error is not None:
            errors.append(error)
        else:
            assert block is not None
            blocks.append(block)

    blocks.append(Stripped("// endregion"))

    blocks.append(Stripped("// region Definitions of concrete classes"))

    for cls in symbol_table.concrete_classes:
        blocks.append(_generate_class_definition(cls=cls))

    blocks.append(Stripped("// endregion"))

    if len(errors) > 0:
        return None, errors

    blocks.append(Stripped("// region Is-a functions"))

    for cls in symbol_table.classes:
        blocks.append(_generate_is_cls_definition(cls=cls))

    blocks.append(Stripped("// endregion Is-a functions"))

    blocks.extend(
        [
            Stripped(
                f"""\
}}  // namespace {cpp_common.TYPES_NAMESPACE}
/**@}}*/"""
            ),
            cpp_common.generate_namespace_closing(library_namespace),
            cpp_common.WARNING,
            Stripped(f"#endif  // {include_guard_var}"),
        ]
    )

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None


def _generate_constructor_implementation(cls: intermediate.ConcreteClass) -> Stripped:
    """Transpile the constructor implementation for the given ``cls``."""
    assert all(
        isinstance(stmt, intermediate_construction.AssignArgument)
        for stmt in cls.constructor.inlined_statements
    ), (
        f"We expect only assigns in the inlined constructors, "
        f"but got for class {cls.name!r}: {cls.constructor.inlined_statements}"
    )

    body_statements = []  # type: List[Stripped]

    for stmt in cls.constructor.inlined_statements:
        assert isinstance(stmt, intermediate_construction.AssignArgument), (
            f"Only assigns expected in inlined constructors, but got the following "
            f"statement for the class {cls.name!r}: {stmt}"
        )

        prop_member = cpp_naming.private_property_name(stmt.name)
        arg_name = cpp_naming.argument_name(stmt.argument)

        if stmt.default is not None:
            if isinstance(stmt.default, intermediate_construction.EmptyList):
                body_statements.append(
                    Stripped(
                        f"""\
if ({arg_name}.has_value()) {{
{I}{prop_member} = *{arg_name};
}} else {{
{I}{prop_member}.emplace();
}}"""
                    )
                )
            elif isinstance(stmt.default, intermediate_construction.DefaultEnumLiteral):
                enum_name = cpp_naming.enum_name(stmt.default.enum.name)
                literal_name = cpp_naming.enum_literal_name(stmt.default.literal.name)

                body_statements.append(
                    Stripped(
                        f"""\
{prop_member} = ({arg_name}.has_value())
{I}? *{arg_name}
{I}: {enum_name}::{literal_name};"""
                    )
                )
            else:
                assert_never(stmt.default)

        else:
            prop = cls.properties_by_name[stmt.name]
            if cpp_common.is_referencable(prop.type_annotation):
                body_statements.append(
                    Stripped(f"{prop_member} = std::move({arg_name});")
                )
            else:
                body_statements.append(Stripped(f"{prop_member} = {arg_name};"))

    body = (
        "\n\n".join(body_statements)
        if len(body_statements) > 0
        else "// Intentionally empty."
    )

    cls_name = cpp_naming.class_name(cls.name)

    if len(cls.constructor.arguments) == 0:
        return Stripped(
            f"""\
{cls_name}::{cls_name}() {{
{I}{indent_but_first_line(body, I)}
}}"""
        )

    constructor_argument_specs = []  # type: List[str]
    for arg in cls.constructor.arguments:
        arg_type = cpp_common.generate_type(arg.type_annotation)
        arg_name = cpp_naming.argument_name(arg.name)

        constructor_argument_specs.append(f"{arg_type} {arg_name}")

    constructor_arguments_specs_joined = ",\n".join(constructor_argument_specs)

    return Stripped(
        f"""\
{cls_name}::{cls_name}(
{I}{indent_but_first_line(constructor_arguments_specs_joined, I)}
) {{
{I}{indent_but_first_line(body, I)}
}}"""
    )


def _generate_model_type_getter_implementation(
    cls: intermediate.ConcreteClass,
) -> Stripped:
    """Implement the getter for the runtime model type."""
    enum_name = cpp_naming.enum_name(Identifier("Model_type"))
    literal_name = cpp_naming.enum_literal_name(cls.name)

    cls_name = cpp_naming.class_name(cls.name)
    getter_name = cpp_naming.getter_name(Identifier("model_type"))

    return Stripped(
        f"""\
{enum_name} {cls_name}::{getter_name}() const {{
{I}return {enum_name}::{literal_name};
}}"""
    )


@require(lambda prop, cls: id(prop) in cls.property_id_set)
def _generate_getters_and_setter(
    prop: intermediate.Property, cls: intermediate.ConcreteClass
) -> List[Stripped]:
    """Generate the immutable and mutable getter and the setter."""
    cls_name = cpp_naming.class_name(cls.name)
    member_name = cpp_naming.private_property_name(prop.name)

    blocks = []  # type: List[Stripped]

    # region Getter
    getter_name = cpp_naming.getter_name(prop.name)
    getter_type = cpp_common.generate_type_with_const_ref_if_applicable(
        prop.type_annotation
    )

    blocks.append(
        Stripped(
            f"""\
{getter_type} {cls_name}::{getter_name}() const {{
{I}return {member_name};
}}"""
        )
    )
    # endregion

    # region Mutable getter
    mutable_getter_name = cpp_naming.mutable_getter_name(prop.name)
    mutable_getter_type = cpp_common.generate_type_with_ref(prop.type_annotation)

    blocks.append(
        Stripped(
            f"""\
{mutable_getter_type} {cls_name}::{mutable_getter_name}() {{
{I}return {member_name};
}}"""
        )
    )
    # endregion

    # region Setter
    setter_name = cpp_naming.setter_name(prop.name)
    value_type = cpp_common.generate_type(type_annotation=prop.type_annotation)

    blocks.append(
        Stripped(
            f"""\
void {cls_name}::{setter_name}(
{I}{indent_but_first_line(value_type, I)} value
) {{
{I}{member_name} = value;
}}"""
        )
    )
    # endregion

    return blocks


@require(lambda method, cls: id(method) in cls.method_id_set)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_method_implementation(
    method: intermediate.MethodUnion,
    cls: intermediate.ConcreteClass,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the implementation of the method."""
    body = None  # type: Optional[Stripped]
    if isinstance(method, intermediate.ImplementationSpecificMethod):
        implementation_key = specific_implementations.ImplementationKey(
            f"types/{method.specified_for.name}/{method.name}.body.cpp"
        )

        body = spec_impls.get(implementation_key, None)

        if body is None:
            return None, Error(
                method.parsed.node,
                f"The implementation is missing for "
                f"the implementation-specific method: {implementation_key}",
            )

    elif isinstance(method, intermediate.UnderstoodMethod):
        return None, Error(
            cls.parsed.node,
            "At the moment (2023-09-22), we do not transpile the method body and "
            "its contracts, as it is quite a difficult task. Please contact "
            "the developers if you need this feature.",
        )
    else:
        assert_never(method)

    assert body is not None

    returns = (
        cpp_common.generate_type(method.returns) if method.returns is not None else None
    )

    return_type = "void" if returns is None else returns

    arg_types_names = [
        (
            cpp_common.generate_type_with_const_ref_if_applicable(arg.type_annotation),
            cpp_naming.argument_name(arg.name),
        )
        for arg in method.arguments
    ]

    method_name = cpp_naming.method_name(method.name)

    const_suffix = " const" if method.non_mutating else ""

    cls_name = cpp_naming.class_name(cls.name)

    if len(method.arguments) == 0:
        return (
            Stripped(
                f"""\
{return_type} {cls_name}::{method_name}(){const_suffix} {{
{I}{indent_but_first_line(body, I)}
}}"""
            ),
            None,
        )
    else:
        arguments_definition = ",\n".join(
            f"{arg_type} {arg_name}" for arg_type, arg_name in arg_types_names
        )

        return (
            Stripped(
                f"""\
{return_type} {cls_name}::{method_name}(
{I}{indent_but_first_line(arguments_definition, I)}
){const_suffix} {{
{I}{indent_but_first_line(body, I)}
}}"""
            ),
            None,
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_class_implementation(
    cls: intermediate.ConcreteClass,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[List[Stripped]], Optional[Error]]:
    """Generate the implementation blocks for the given class."""
    blocks = [
        _generate_constructor_implementation(cls=cls),
        _generate_model_type_getter_implementation(cls=cls),
    ]  # type: List[Stripped]

    for prop in cls.properties:
        blocks.extend(_generate_getters_and_setter(prop=prop, cls=cls))

    errors = []  # type: List[Error]

    for method in cls.methods:
        code, error = _generate_method_implementation(
            method=method, cls=cls, spec_impls=spec_impls
        )
        if error is not None:
            errors.append(
                Error(
                    method.parsed.node,
                    f"Failed to generate the implementation "
                    f"for the method {method.name!r}",
                    [error],
                )
            )
        else:
            assert code is not None
            blocks.append(code)

    if len(errors) > 0:
        return None, Error(
            cls.parsed.node,
            f"Failed to generate the implementation for the class {cls.name!r}",
            errors,
        )

    return blocks, None


def _generate_is_cls_implementation(
    cls: intermediate.ClassUnion, symbol_table: intermediate.SymbolTable
) -> Stripped:
    """Generate the impl. of the function to check is-a based on model type."""
    function_name = cpp_naming.function_name(Identifier(f"is_{cls.name}"))

    case_blocks = []  # type: List[Stripped]
    for concrete_cls in symbol_table.concrete_classes:
        case_body = (
            "return true;" if concrete_cls.is_subclass_of(cls) else "return false;"
        )

        model_type_literal = cpp_naming.enum_literal_name(concrete_cls.name)

        case_blocks.append(
            Stripped(
                f"""\
case ModelType::{model_type_literal}:
{I}{indent_but_first_line(case_body, I)}"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}throw std::invalid_argument(
{II}common::Concat(
{III}"Unexpected model type: ",
{III}std::to_string(
{IIII}static_cast<std::uint32_t>(that.model_type())
{III})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    return Stripped(
        f"""\
bool {function_name}(
{I}const IClass& that
) {{
{I}switch (that.model_type()) {{
{II}{indent_but_first_line(case_blocks_joined, II)}
{I}}}
}}"""
    )


# fmt: off
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
@ensure(
    lambda result:
    not (result[0] is not None) or result[0].endswith('\n'),
    "Trailing newline mandatory for valid end-of-files"
)
# fmt: on
def generate_implementation(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
    library_namespace: Stripped,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the C++ implementation code for data structure."""
    namespace = Stripped(f"{library_namespace}::types")

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f'''\
#include "{include_prefix_path}/types.hpp"'''
        ),
        cpp_common.generate_namespace_opening(namespace),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    for concrete_cls in symbol_table.concrete_classes:
        if concrete_cls.is_implementation_specific:
            errors.append(
                Error(
                    concrete_cls.parsed.node,
                    f"We currently do not support implementation-specific classes "
                    f"in the C++ generator, but the class {concrete_cls.name!r} has "
                    f"been marked as implementation-specific. If you need "
                    f"this feature, please contact the developers.",
                )
            )
            continue

        cls_blocks, error = _generate_class_implementation(
            cls=concrete_cls, spec_impls=spec_impls
        )
        if error is not None:
            errors.append(error)
        else:
            assert cls_blocks is not None
            cls_name = cpp_naming.class_name(concrete_cls.name)
            blocks.append(Stripped(f"// region {cls_name}"))
            blocks.extend(cls_blocks)
            blocks.append(Stripped(f"// endregion {cls_name}"))

    if len(errors) > 0:
        return None, errors

    blocks.append(Stripped("// region Is-a functions"))

    for cls in symbol_table.classes:
        blocks.append(
            _generate_is_cls_implementation(cls=cls, symbol_table=symbol_table)
        )

    blocks.append(Stripped("// endregion Is-a functions"))

    blocks.extend(
        [
            cpp_common.generate_namespace_closing(namespace),
            cpp_common.WARNING,
        ]
    )

    writer = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            writer.write("\n\n")

        writer.write(block)

    writer.write("\n")

    return writer.getvalue(), None


# endregion
