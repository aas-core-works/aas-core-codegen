"""Generate the C++ verification functions."""
import enum
import io
from typing import (
    Optional,
    List,
    Tuple,
    Union,
    Sequence,
    Mapping,
    Final,
    Set,
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
    wrap_text_into_lines,
)
from aas_core_codegen.cpp import (
    common as cpp_common,
    naming as cpp_naming,
    description as cpp_description,
    transpilation as cpp_transpilation,
    optionaling as cpp_optionaling,
    yielding as cpp_yielding,
)
from aas_core_codegen.cpp.common import (
    INDENT as I,
    INDENT2 as II,
    INDENT3 as III,
    INDENT4 as IIII,
    INDENT5 as IIIII,
)
from aas_core_codegen.intermediate import type_inference as intermediate_type_inference
from aas_core_codegen.parse import tree as parse_tree, retree as parse_retree
from aas_core_codegen.yielding import flow as yielding_flow


# region Generation


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_verification_function_definition(
    verification: Union[
        intermediate.ImplementationSpecificVerification,
        intermediate.TranspilableVerification,
        intermediate.PatternVerification,
    ],
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Generate the definition of a verification functions."""
    if isinstance(verification, intermediate.ImplementationSpecificVerification):
        implementation_key = specific_implementations.ImplementationKey(
            f"verification/{verification.name}.hpp"
        )

        code = spec_impls.get(implementation_key, None)

        if code is None:
            return None, Error(
                verification.parsed.node,
                f"The header snippet is missing for "
                f"the implementation-specific verification "
                f"function: {implementation_key}",
            )

        return code, None

    arg_types_names = [
        (
            cpp_common.generate_type_with_const_ref_if_applicable(
                type_annotation=arg.type_annotation,
                types_namespace=cpp_common.TYPES_NAMESPACE,
            ),
            cpp_naming.argument_name(arg.name),
        )
        for arg in verification.arguments
    ]

    function_name = cpp_naming.function_name(verification.name)
    arg_definitions_joined = ",\n".join(
        f"{arg_type} {arg_name}" for arg_type, arg_name in arg_types_names
    )

    blocks = []  # type: List[Stripped]
    if verification.description is not None:
        comment, errors = cpp_description.generate_comment_for_summary_remarks(
            description=verification.description,
            context=cpp_description.Context(
                namespace=cpp_common.VERIFICATION_NAMESPACE, cls_or_enum=None
            ),
        )
        if errors is not None:
            return None, Error(
                verification.parsed.node,
                f"Failed to generate the description for "
                f"verification function {verification.name!r}",
                errors,
            )
        assert comment is not None
        blocks.append(comment)

    blocks.append(
        Stripped(
            f"""\
bool {function_name}(
{I}{indent_but_first_line(arg_definitions_joined, I)}
);"""
        )
    )

    return Stripped("\n".join(blocks)), None


def _constrained_primitive_verificator_value_is_pointer(
    primitive_type: intermediate.PrimitiveType,
) -> bool:
    """
    Check whether we keep the value of a constrained primitive as a pointer.

    Values which are cheap to copy such as booleans and integers are copied by value
    in the verificator constructor. On the other hand, primitive types represented as
    STL containers are copied as pointers to avoid unnecessary cost.

    In many places in code we have to decide how to dereference the value.
    """
    if primitive_type is intermediate.PrimitiveType.BOOL:
        return False

    elif primitive_type is intermediate.PrimitiveType.INT:
        return False

    elif primitive_type is intermediate.PrimitiveType.FLOAT:
        return False

    elif primitive_type is intermediate.PrimitiveType.STR:
        return True

    elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
        return True

    else:
        assert_never(primitive_type)


def _generate_definition_of_verify_constrained_primitive(
    constrained_primitive: intermediate.ConstrainedPrimitive,
) -> Stripped:
    """Generate the def. of a verification function for the constrained primitive."""
    verify_name = cpp_naming.function_name(
        Identifier(f"verify_{constrained_primitive.name}")
    )

    arg_type = cpp_common.generate_primitive_type_with_const_ref_if_applicable(
        constrained_primitive.constrainee
    )

    arg_name = cpp_naming.argument_name(Identifier("that"))

    if _constrained_primitive_verificator_value_is_pointer(
        primitive_type=constrained_primitive.constrainee
    ):
        documentation_comment = Stripped(
            """\
/**
 * \\brief Verify that the invariants hold for \\p that value.
 *
 * The \\p that value should outlive the verification.
 *
 * \\param that value to be verified
 * \\return Iterable over constraint violations
 */"""
        )
    else:
        documentation_comment = Stripped(
            """\
/**
 * \\brief Verify that the invariants hold for \\p that value.
 *
 * \\param that value to be verified
 * \\return Iterable over constraint violations
 */"""
        )

    return Stripped(
        f"""\
{documentation_comment}
std::unique_ptr<IVerification> {verify_name}(
{I}{arg_type} {arg_name}
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
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
    library_namespace: Stripped,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """Generate the C++ header for the verification code."""
    namespace = Stripped(f"{library_namespace}::verification")

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
#include "{include_prefix_path}/iteration.hpp"
#include "{include_prefix_path}/types.hpp"

#pragma warning(push, 0)
#include <set>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(library_namespace),
        Stripped(
            """\
/**
 * \\defgroup verification Verify that instances conform to the meta-model constraints.
 * @{
 */
namespace verification {"""
        ),
        Stripped(
            """\
// region Forward declarations
class Iterator;
class IVerification;

namespace impl {
class IVerificator;
}  // namespace impl
// endregion Forward declarations"""
        ),
        Stripped(
            f"""\
/**
 * Represent a verification error in an instance.
 */
struct Error {{
{I}/**
{I} * Human-readable description of the error
{I} */
{I}std::wstring cause;

{I}/**
{I} * Path to the erroneous value
{I} */
{I}iteration::Path path;

{I}explicit Error(std::wstring a_cause);
{I}Error(std::wstring a_cause, iteration::Path a_path);
}};  // struct Error"""
        ),
        Stripped(
            f"""\
/**
 * \\brief Iterate over the verification errors.
 *
 * The user is expected to take ownership of the errors if they need to be further
 * processed.
 *
 * Unlike STL, this is <em>not</em> a light-weight iterator. We implement
 * a "yielding" iterator by leveraging code generation so that we always keep
 * the model stack as well as the properties verified thus far.
 *
 * This means that copy-construction and equality comparisons are much more heavy-weight
 * than you'd usually expect from an STL iterator. For example, if you want to sort
 * the errors by some criterion, you are most probably faster if you populate a vector,
 * and then sort the vector.
 *
 * Also, given that this iterator is not light-weight, you should in almost all cases
 * avoid the postfix increment (it++) and prefer the prefix one (++it) as the postfix
 * increment would create an iterator copy every time.
 *
 * We follow the C++ standard, and assume that comparison between the two iterators
 * over two different collections results in undefined behavior. See
 * http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2009/n2948.html and
 * https://stackoverflow.com/questions/4657513/comparing-iterators-from-different-containers.
 */
class Iterator {{
{I}using iterator_category = std::forward_iterator_tag;
{I}/// The difference is meaningless, but has to be defined.
{I}using difference_type = std::ptrdiff_t;
{I}using value_type = Error;
{I}using pointer = const Error*;
{I}using reference = const Error&;

 public:
{I}explicit Iterator(
{II}std::unique_ptr<impl::IVerificator> verificator
{I}) :
{I}verificator_(std::move(verificator)) {{
{II}  // Intentionally empty.
{I}}}

{I}Iterator(const Iterator& other);
{I}Iterator(Iterator&& other);

{I}Iterator& operator=(const Iterator& other);
{I}Iterator& operator=(Iterator&& other);

{I}reference operator*() const;
{I}pointer operator->() const;

{I}// Prefix increment
{I}Iterator& operator++();

{I}// Postfix increment
{I}Iterator operator++(int);

{I}friend bool operator==(const Iterator& a, const Iterator& b);
{I}friend bool operator!=(const Iterator& a, const Iterator& b);

 private:
{I}std::unique_ptr<impl::IVerificator> verificator_;
}};"""
        ),
        Stripped("bool operator==(const Iterator& a, const Iterator& b);"),
        Stripped("bool operator!=(const Iterator& a, const Iterator& b);"),
        Stripped(
            f"""\
/// \\cond HIDDEN
namespace impl {{
class IVerificator {{
 public:
{I}virtual void Start() = 0;
{I}virtual void Next() = 0;
{I}virtual bool Done() const = 0;

{I}virtual const Error& Get() const = 0;
{I}virtual Error& GetMutable() = 0;
{I}virtual long Index() const = 0;

{I}virtual std::unique_ptr<IVerificator> Clone() const = 0;

{I}virtual ~IVerificator() = default;
}};  // class IVerificator
}}  // namespace impl
/// \\endcond"""
        ),
        Stripped(
            f"""\
class IVerification {{
 public:
{I}virtual Iterator begin() const = 0;
{I}virtual const Iterator& end() const = 0;
{I}virtual ~IVerification() = default;
}};  // class IVerification"""
        ),
        Stripped(
            f"""\
/**
 * \\brief Verify that the instance conforms to the meta-model constraints.
 *
 * Do not proceed to verify the instances referenced from
 * the given instance.
 *
 * Range-based loops should fit the vast majority of the use cases:
 * \\code
 * std::shared_ptr<types::Environment> env = ...;
 * for (const Error& error : NonRecursiveVerification(env)) {{
 * {I}report_somehow(error);
 * }}
 * \\endcode
 *
 * We use const references to shared pointers here for efficiency. Since
 * we do not make a copy of \\p that shared pointer, it is very important that
 * the given shared pointer outlives the verification, lest cause undefined behavior.
 * See these StackOverflow questions:
 * * https://stackoverflow.com/questions/12002480/passing-stdshared-ptr-to-constructors/12002668#12002668
 * * https://stackoverflow.com/questions/3310737/should-we-pass-a-shared-ptr-by-reference-or-by-value
 * * https://stackoverflow.com/questions/37610494/passing-const-shared-ptrt-versus-just-shared-ptrt-as-parameter
 */
class NonRecursiveVerification : public IVerification {{
 public:
{I}NonRecursiveVerification(
{II}const std::shared_ptr<types::IClass>& instance
{I});

{I}Iterator begin() const override;
{I}const Iterator& end() const override;

{I}~NonRecursiveVerification() override = default;
 private:
{I}const std::shared_ptr<types::IClass>& instance_;
}};  // class NonRecursiveVerification"""
        ),
        Stripped(
            f"""\
/**
 * \\brief Verify that the instance conforms to the meta-model constraints.
 *
 * Also verify recursively all the instances referenced from
 * the given instance.
 *
 * Range-based loops should fit the vast majority of the use cases:
 * \\code
 * std::shared_ptr<types::Environment> env = ...;
 * for (const Error& error : RecursiveVerification(env)) {{
 * {I}report_somehow(error);
 * }}
 * \\endcode
 *
 * We use const references to shared pointers here for efficiency. Since
 * we do not make a copy of \\p that shared pointer, it is very important that
 * the given shared pointer outlives the verification, lest cause undefined behavior.
 * See these StackOverflow questions:
 * * https://stackoverflow.com/questions/12002480/passing-stdshared-ptr-to-constructors/12002668#12002668
 * * https://stackoverflow.com/questions/3310737/should-we-pass-a-shared-ptr-by-reference-or-by-value
 * * https://stackoverflow.com/questions/37610494/passing-const-shared-ptrt-versus-just-shared-ptrt-as-parameter
 */
class RecursiveVerification : public IVerification {{
 public:
{I}RecursiveVerification(
{II}const std::shared_ptr<types::IClass>& instance
{I});

{I}Iterator begin() const override;
{I}const Iterator& end() const override;

{I}~RecursiveVerification() override = default;
 private:
{I}const std::shared_ptr<types::IClass>& instance_;
}};  // class RecursiveVerification"""
        ),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    if len(symbol_table.verification_functions) > 0:
        blocks.append(Stripped("// region Verification functions"))

        for verification in symbol_table.verification_functions:
            block, error = _generate_verification_function_definition(
                verification=verification, spec_impls=spec_impls
            )
            if error is not None:
                errors.append(error)
                continue
            else:
                assert block is not None
                blocks.append(block)

        blocks.append(Stripped("// endregion Verification functions"))

    if len(symbol_table.constrained_primitives) > 0:
        blocks.append(Stripped("// region Verification of constrained primitives"))

        for constrained_primitive in symbol_table.constrained_primitives:
            blocks.append(
                _generate_definition_of_verify_constrained_primitive(
                    constrained_primitive=constrained_primitive
                )
            )

        blocks.append(Stripped("// endregion Verification of constrained primitives"))

    if len(errors) > 0:
        return None, errors

    blocks.extend(
        [
            Stripped(
                """\
}  // namespace verification
/**@}*/"""
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


def _generate_error_implementation() -> List[Stripped]:
    """Generate the implementation of the ``Error`` struct."""
    return [
        Stripped("// region struct Error"),
        Stripped(
            f"""\
Error::Error(
{I}std::wstring a_cause
) :
{I}cause(std::move(a_cause)) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Error::Error(
{I}std::wstring a_cause,
{I}iteration::Path a_path
) :
{I}cause(std::move(a_cause)),
{I}path(std::move(a_path)) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped("// endregion struct Error"),
    ]


def _generate_new_non_recursive_verificator_definition() -> Stripped:
    """Generate the def. of the factory function for non-recursive verificators."""
    new_non_recursive_verificator = cpp_naming.function_name(
        Identifier("new_non_recursive_verificator")
    )

    return Stripped(
        f"""\
/**
 * Produce a non-recursive verificator of the instance given its runtime model type.
 */
std::unique_ptr<impl::IVerificator> {new_non_recursive_verificator}(
{I}const std::shared_ptr<types::IClass>& instance
);"""
    )


def _generate_iterator_implementation() -> List[Stripped]:
    """Generate the implementation of the class ``Iterator``."""
    return [
        Stripped("// region struct Iterator"),
        Stripped(
            f"""\
Iterator::Iterator(
{I}const Iterator& other
) :
{I}verificator_(other.verificator_->Clone()) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Iterator::Iterator(
{I}Iterator&& other
) :
{I}verificator_(std::move(other.verificator_)) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Iterator& Iterator::operator=(const Iterator& other) {{
{I}return *this = Iterator(other);
}}"""
        ),
        Stripped(
            f"""\
Iterator& Iterator::operator=(Iterator&& other) {{
{I}if (this != &other) {{
{II}verificator_ = std::move(other.verificator_);
{I}}}

{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
const Error& Iterator::operator*() const {{
{I}if (verificator_->Done()) {{
{II}throw std::logic_error(
{III}"You want to de-reference from a completed iterator "
{III}"over verification errors."
{II});
{I}}}

{I}return verificator_->Get();
}}"""
        ),
        Stripped(
            f"""\
const Error* Iterator::operator->() const {{
{I}if (verificator_->Done()) {{
{II}throw std::logic_error(
{III}"You want to de-reference from a completed iterator "
{III}"over verification errors."
{II});
{I}}}

{I}return &(verificator_->Get());
}}"""
        ),
        Stripped(
            f"""\
// Prefix increment
Iterator& Iterator::operator++() {{
{I}if (verificator_->Done()) {{
{II}throw std::logic_error(
{III}"You want to move a completed iterator "
{III}"over verification errors."
{II});
{I}}}

{I}verificator_->Next();
{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
// Postfix increment
Iterator Iterator::operator++(int) {{
{I}Iterator result(*this);
{I}++(*this);
{I}return result;
}}"""
        ),
        Stripped(
            f"""\
bool operator==(const Iterator& a, const Iterator& b) {{
{I}return a.verificator_->Index() == b.verificator_->Index();
}}"""
        ),
        Stripped(
            f"""\
bool operator!=(const Iterator& a, const Iterator& b) {{
{I}return a.verificator_->Index() != b.verificator_->Index();
}}"""
        ),
        Stripped("// endregion struct Iterator"),
    ]


def _generate_non_recursive_verification() -> List[Stripped]:
    """Generate the ``RecursiveVerification`` class."""
    return [
        Stripped("// region NonRecursiveVerification"),
        Stripped(
            f"""\
NonRecursiveVerification::NonRecursiveVerification(
{I}const std::shared_ptr<types::IClass>& instance
) : instance_(instance) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Iterator NonRecursiveVerification::begin() const {{
{I}std::unique_ptr<impl::IVerificator> verificator(
{II}NewNonRecursiveVerificator(instance_)
{I});

{I}verificator->Start();

{I}// NOTE(mristin):
{I}// We short-circuit here for efficiency, as we can immediately dispose
{I}// of the verificator.
{I}if (verificator->Done()) {{
{II}return Iterator(common::make_unique<AlwaysDoneVerificator>());
{I}}}

{I}return Iterator(std::move(verificator));
}}"""
        ),
        Stripped(
            f"""\
const Iterator& NonRecursiveVerification::end() const {{
{I}static Iterator iterator(common::make_unique<AlwaysDoneVerificator>());
{I}return iterator;
}}"""
        ),
        Stripped("// endregion NonRecursiveVerification"),
    ]


def _generate_recursive_verification() -> List[Stripped]:
    """Generate the ``RecursiveVerification`` class."""
    return [
        Stripped("// region RecursiveVerification"),
        Stripped(
            f"""\
RecursiveVerification::RecursiveVerification(
{I}const std::shared_ptr<types::IClass>& instance
) : instance_(instance) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Iterator RecursiveVerification::begin() const {{
{I}std::unique_ptr<impl::IVerificator> verificator(
{II}common::make_unique<RecursiveVerificator>(instance_)
{I});

{I}verificator->Start();

{I}// NOTE(mristin):
{I}// We short-circuit here for efficiency, as we can immediately dispose
{I}// of the verificator.
{I}if (verificator->Done()) {{
{II}return Iterator(common::make_unique<AlwaysDoneVerificator>());
{I}}}

{I}return Iterator(std::move(verificator));
}}"""
        ),
        Stripped(
            f"""\
const Iterator& RecursiveVerification::end() const {{
{I}static Iterator iterator(common::make_unique<AlwaysDoneVerificator>());
{I}return iterator;
}}"""
        ),
        Stripped("// endregion RecursiveVerification"),
    ]


def _generate_always_done_verificator() -> List[Stripped]:
    """Generate the verificator which always has ``Done`` set."""
    return [
        Stripped("// region class AlwaysDoneVerificator"),
        Stripped(
            f"""\
class AlwaysDoneVerificator : public impl::IVerificator {{
 public:
{I}void Start() override;
{I}void Next() override;
{I}bool Done() const override;
{I}const Error& Get() const override;
{I}Error& GetMutable() override;
{I}long Index() const override;
{I}std::unique_ptr<impl::IVerificator> Clone() const override;

{I}virtual ~AlwaysDoneVerificator() = default;
}};  // class AlwaysDoneVerificator"""
        ),
        Stripped(
            f"""\
void AlwaysDoneVerificator::Start() {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
void AlwaysDoneVerificator::Next() {{
{I}throw std::logic_error(
{II}"You want to move an AlwaysDoneVerificator, "
{II}"but the verificator is always done, as its name suggests."
{I});
}}"""
        ),
        Stripped(
            f"""\
bool AlwaysDoneVerificator::Done() const {{
{I}return true;
}}"""
        ),
        Stripped(
            f"""\
const Error& AlwaysDoneVerificator::Get() const {{
{II}throw std::logic_error(
{III}"You want to get from an AlwaysDoneVerificator, "
{III}"but the verificator is always done, as its name suggests."
{II});
}}"""
        ),
        Stripped(
            f"""\
Error& AlwaysDoneVerificator::GetMutable() {{
{II}throw std::logic_error(
{III}"You want to get mutable from an AlwaysDoneVerificator, "
{III}"but the verificator is always done, as its name suggests."
{II});
}}"""
        ),
        Stripped(
            f"""\
long AlwaysDoneVerificator::Index() const {{
{I}return -1;
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<impl::IVerificator> AlwaysDoneVerificator::Clone() const {{
{I}return common::make_unique<AlwaysDoneVerificator>(*this);
}}"""
        ),
        Stripped("// endregion class AlwaysDoneVerificator"),
    ]


@ensure(lambda cls, result: all(id(prop) in cls.property_id_set for prop in result))
def _collect_constrained_primitive_properties(
    cls: intermediate.ConcreteClass,
) -> List[intermediate.Property]:
    """Select the properties which are annotated as constrained primitives."""
    result = []  # type: List[intermediate.Property]
    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
            pass

        elif isinstance(type_anno, intermediate.OurTypeAnnotation):
            if isinstance(type_anno.our_type, intermediate.Enumeration):
                pass

            elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                result.append(prop)

            elif isinstance(
                type_anno.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ):
                pass

            else:
                assert_never(type_anno.our_type)

        elif isinstance(type_anno, intermediate.ListTypeAnnotation):
            assert isinstance(
                type_anno.items, intermediate.OurTypeAnnotation
            ) and isinstance(
                type_anno.items.our_type,
                (intermediate.AbstractClass, intermediate.ConcreteClass),
            ), (
                f"NOTE (mristin, 2023-03-29): We expect only lists of classes "
                f"at the moment, but you specified {type_anno}. "
                f"Please contact the developers if you need this feature."
            )

            pass
        else:
            assert_never(type_anno)

    return result


class VerificatorQualities:
    """Model the relevant qualities of a verificator."""

    #: Class that we want to verify
    cls: Final[intermediate.ConcreteClass]

    #: If set, the verificator performs no verification steps.
    is_noop: Final[bool]

    #: List properties which are annotated with an (possibly optional) constrained
    #: primitive
    constrained_primitive_properties: Final[Sequence[intermediate.Property]]

    # fmt: off
    @ensure(
        lambda self:
        not (
            len(self.cls.invariants) == 0
            and len(self.constrained_primitive_properties) == 0
        ) or self.is_noop,
        "The verificator is a no-op if there are no invariants and no constrained "
        "primitive properties in the class"
    )
    @ensure(
        lambda self:
        not (
            len(self.cls.invariants) > 0
            or len(self.constrained_primitive_properties) > 0
        ) or not self.is_noop,
        "The verificator is *not* a no-op if there is at least one invariant or "
        "a property annotated with a constrained primitive"
    )
    # fmt: on
    def __init__(self, cls: intermediate.ConcreteClass) -> None:
        self.cls = cls

        self.constrained_primitive_properties = (
            _collect_constrained_primitive_properties(cls=cls)
        )

        self.is_noop = (
            len(cls.invariants) == 0 and len(self.constrained_primitive_properties) == 0
        )


@require(lambda verificator_qualities: verificator_qualities.is_noop)
def _generate_empty_non_recursive_verificator(
    verificator_qualities: VerificatorQualities,
) -> List[Stripped]:
    """
    Generate an implementation of a non-recursive verificator which is always done.

    Though the implementation is a duplicate in logic of ``AlwaysDoneVerificator``,
    the assertion error messages are different, so we generate a separate class.
    """
    # Shortcut
    cls = verificator_qualities.cls

    of_cls = cpp_naming.class_name(Identifier(f"Of_{cls.name}"))
    interface_name = cpp_naming.interface_name(cls.name)

    return [
        Stripped(
            f"""\
class {of_cls} : public impl::IVerificator {{
 public:
{I}{of_cls}(
{II}const std::shared_ptr<types::IClass>& instance
{I});

{I}void Start() override;
{I}void Next() override;
{I}bool Done() const override;
{I}const Error& Get() const override;
{I}Error& GetMutable() override;
{I}long Index() const override;

{I}std::unique_ptr<impl::IVerificator> Clone() const override;

{I}~{of_cls}() override = default;
}};  // class {of_cls}"""
        ),
        Stripped(
            f"""\
{of_cls}::{of_cls}(
{I}const std::shared_ptr<types::IClass>&
) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
void {of_cls}::Start() {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
void {of_cls}::Next() {{
{I}throw std::logic_error(
{II}"You want to move "
{II}"a verificator {of_cls}, "
{II}"but the verificator is always done as "
{II}"{interface_name} "
{II}"has no invariants defined."
{I});
}}"""
        ),
        Stripped(
            f"""\
bool {of_cls}::Done() const {{
{I}return true;
}}"""
        ),
        Stripped(
            f"""\
const Error& {of_cls}::Get() const {{
{I}throw std::logic_error(
{II}"You want to get from "
{II}"a verificator {of_cls}, "
{II}"but the verificator is always done as "
{II}"{interface_name} "
{II}"has no invariants defined."
{I});
}}"""
        ),
        Stripped(
            f"""\
Error& {of_cls}::GetMutable() {{
{I}throw std::logic_error(
{II}"You want to get mutable from "
{II}"a verificator {of_cls}, "
{II}"but the verificator is always done as "
{II}"{interface_name} "
{II}"has no invariants defined."
{I});
}}"""
        ),
        Stripped(
            f"""\
long {of_cls}::Index() const {{
{I}return -1;
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<impl::IVerificator> {of_cls}::Clone() const {{
{I}return common::make_unique<
{II}{of_cls}
{I}>(*this);
}}"""
        ),
    ]


class _ClassInvariantTranspiler(cpp_transpilation.Transpiler):
    """Transpile invariants of the classes."""

    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        is_optional_map: Mapping[parse_tree.Node, bool],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
    ) -> None:
        """Initialize with the given values."""
        cpp_transpilation.Transpiler.__init__(
            self,
            type_map=type_map,
            is_optional_map=is_optional_map,
            environment=environment,
            types_namespace=cpp_common.TYPES_NAMESPACE,
        )

        self._symbol_table = symbol_table

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            return Stripped(cpp_naming.variable_name(node.identifier)), None

        if node.identifier == "self":
            # The ``instance_`` refers to the instance under verification.
            return Stripped("instance_"), None

        if node.identifier in self._symbol_table.constants_by_name:
            constant = cpp_naming.constant_name(node.identifier)
            return Stripped(f"{cpp_common.CONSTANTS_NAMESPACE}::{constant}"), None

        if node.identifier in self._symbol_table.verification_functions_by_name:
            return Stripped(cpp_naming.function_name(node.identifier)), None

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            return (
                Stripped(
                    f"{cpp_common.TYPES_NAMESPACE}::{cpp_naming.enum_name(node.identifier)}"
                ),
                None,
            )

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to C++. We could not find it neither in the local variables, "
            f"nor in the global constants, nor in verification functions, "
            f"nor as an enumeration. If you expect this name to be transpilable, "
            f"please contact the developers.",
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _transpile_class_invariant(
    invariant: intermediate.Invariant,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Translate the invariant from the meta-model into a C++ condition."""
    canonicalizer = intermediate_type_inference.Canonicalizer()
    _ = canonicalizer.transform(invariant.body)

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment,
        representation_map=canonicalizer.representation_map,
    )

    _ = type_inferrer.transform(invariant.body)

    if len(type_inferrer.errors):
        return None, Error(
            invariant.parsed.node,
            "Failed to infer the types in the invariant",
            type_inferrer.errors,
        )

    optional_inferrer = cpp_optionaling.Inferrer(
        environment=environment, type_map=type_inferrer.type_map
    )

    _ = optional_inferrer.transform(invariant.body)

    if len(optional_inferrer.errors) > 0:
        return None, Error(
            invariant.parsed.node,
            "Failed to infer whether one or more nodes are ``common::optional`` "
            "in the invariant",
            optional_inferrer.errors,
        )

    transpiler = _ClassInvariantTranspiler(
        type_map=type_inferrer.type_map,
        is_optional_map=optional_inferrer.is_optional_map,
        environment=environment,
        symbol_table=symbol_table,
    )

    expr, error = transpiler.transform(invariant.body)

    if error is not None:
        return None, error

    assert expr is not None
    return expr, None


@require(lambda verificator_qualities: not verificator_qualities.is_noop)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_non_recursive_verificator_execute(
    verificator_qualities: VerificatorQualities,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the impl. of the ``Execute()`` for a verificator of class ``cls``."""
    flow = [
        yielding_flow.command_from_text(
            """\
done_ = false;
error_ = nullptr;
index_ = -1;"""
        )
    ]  # type: List[yielding_flow.Node]

    errors = []  # type: List[Error]
    for invariant in verificator_qualities.cls.invariants:
        condition_expr, error = _transpile_class_invariant(
            invariant=invariant, symbol_table=symbol_table, environment=environment
        )
        if error is not None:
            errors.append(error)
            continue

        assert condition_expr is not None

        # NOTE (mristin, 2023-10-17):
        # We need to wrap the description in multiple literals as a single long
        # string literal is often too much for the readability.
        invariant_description_lines = wrap_text_into_lines(invariant.description)

        invariant_description_literals_joined = "\n".join(
            cpp_common.wstring_literal(line) for line in invariant_description_lines
        )

        flow.append(
            yielding_flow.IfFalse(
                condition_expr,
                [
                    yielding_flow.command_from_text(
                        f"""\
error_ = common::make_unique<Error>(
{I}{indent_but_first_line(invariant_description_literals_joined, I)}
);
// No path is prepended as the error refers to the instance itself.
++index_;"""
                    ),
                    yielding_flow.Yield(),
                ],
            )
        )

    for prop in verificator_qualities.constrained_primitive_properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)
        assert isinstance(type_anno, intermediate.OurTypeAnnotation) and isinstance(
            type_anno.our_type, intermediate.ConstrainedPrimitive
        )

        of_constrained_primitive = cpp_naming.class_name(
            Identifier(f"Of_{type_anno.our_type.name}")
        )

        getter_name = cpp_naming.getter_name(prop.name)

        property_enum = cpp_naming.enum_name(Identifier("Property"))
        property_literal = cpp_naming.enum_literal_name(prop.name)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            # NOTE (mristin, 2023-11-01):
            # Be careful! You have to keep the following snippet in semantical sync with
            # the code in the else-clause!

            flow.append(
                yielding_flow.IfTrue(
                    f"instance_->{getter_name}().has_value()",
                    [
                        yielding_flow.command_from_text(
                            f"""\
constrained_primitive_verificator_ = (
{I}common::make_unique<
{II}constrained_primitive_verificator::{of_constrained_primitive}
{I}>(
{II}*(instance_->{getter_name}())
{I})
);
constrained_primitive_verificator_->Start();"""
                        ),
                        yielding_flow.For(
                            "!constrained_primitive_verificator_->Done()",
                            "constrained_primitive_verificator_->Next();",
                            [
                                yielding_flow.command_from_text(
                                    f"""\
// We intentionally take over the ownership of the errors' data members,
// as we know the implementation in all the detail, and want to avoid a costly
// copy.
error_ = common::make_unique<Error>(
{I}std::move(
{II}constrained_primitive_verificator_->GetMutable()
{I})
);

error_->path.segments.emplace_back(
{I}common::make_unique<iteration::PropertySegment>(
{II}iteration::{property_enum}::{property_literal}
{I})
);

++index_;"""
                                ),
                                yielding_flow.Yield(),
                            ],
                        ),
                        yielding_flow.command_from_text(
                            "constrained_primitive_verificator_ = nullptr;"
                        ),
                    ],
                )
            )
        else:
            # NOTE (mristin, 2023-11-01):
            # Be careful! You have to keep the following snippet in semantic sync with
            # the code in the if-clause!

            flow.append(
                yielding_flow.command_from_text(
                    f"""\
constrained_primitive_verificator_ = (
{I}common::make_unique<
{II}constrained_primitive_verificator::{of_constrained_primitive}
{I}>(
{II}instance_->{getter_name}()
{I})
);
constrained_primitive_verificator_->Start();"""
                )
            )
            flow.append(
                yielding_flow.For(
                    "!constrained_primitive_verificator_->Done()",
                    "constrained_primitive_verificator_->Next();",
                    [
                        yielding_flow.command_from_text(
                            f"""\
// We intentionally take over the ownership of the errors' data members,
// as we know the implementation in all the detail, and want to avoid a costly
// copy.
error_ = common::make_unique<Error>(
{I}std::move(
{II}constrained_primitive_verificator_->GetMutable()
{I})
);

error_->path.segments.emplace_back(
{I}common::make_unique<iteration::PropertySegment>(
{II}iteration::{property_enum}::{property_literal}
{I})
);

++index_;"""
                        ),
                        yielding_flow.Yield(),
                    ],
                )
            )
            flow.append(
                yielding_flow.command_from_text(
                    "constrained_primitive_verificator_ = nullptr;"
                )
            )

    flow.append(
        yielding_flow.command_from_text(
            """\
done_ = true;
error_ = nullptr;
index_ = -1;"""
        )
    )

    if len(errors) > 0:
        return None, errors

    code = cpp_yielding.generate_execute_body(
        flow=flow, state_member=Identifier("state_")
    )

    of_cls = cpp_naming.class_name(Identifier(f"of_{verificator_qualities.cls.name}"))

    return (
        Stripped(
            f"""\
void {of_cls}::Execute() {{
{I}{indent_but_first_line(code, I)}
}}"""
        ),
        None,
    )


@require(lambda verificator_qualities: not verificator_qualities.is_noop)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_non_recursive_verificator_implementation(
    verificator_qualities: VerificatorQualities,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[List[Stripped]], Optional[Error]]:
    """Generate the impl. of a non-recursive verificator for ``cls``."""
    cls = verificator_qualities.cls

    of_cls = cpp_naming.class_name(Identifier(f"Of_{cls.name}"))

    interface_name = cpp_naming.interface_name(cls.name)

    copy_data_members_snippet = Stripped(
        """\
instance_ = other.instance_;
done_ = other.done_;
index_ = other.index_;
error_ = common::make_unique<Error>(*other.error_);
state_ = other.state_;"""
    )

    move_data_members_snippet = Stripped(
        """\
instance_ = std::move(other.instance_);
done_ = other.done_;
index_ = other.index_;
error_ = std::move(other.error_);
state_ = other.state_;"""
    )

    if len(verificator_qualities.constrained_primitive_properties) > 0:
        copy_data_members_snippet = Stripped(
            f"""\
{copy_data_members_snippet}
constrained_primitive_verificator_ = (
{I}other.constrained_primitive_verificator_->Clone()
);"""
        )

        move_data_members_snippet = Stripped(
            f"""\
{move_data_members_snippet}
constrained_primitive_verificator_ = std::move(
{I}other.constrained_primitive_verificator_
);"""
        )

    blocks = [
        Stripped(
            f"""\
{of_cls}::{of_cls}(
{I}const std::shared_ptr<types::IClass>& instance
) :
{I}// NOTE (mristin)
{I}// We cast here despite the cost of increasing the use count of the shared pointer.
{I}// Otherwise, if we didn't cast, we would not be able to have a uniform interface
{I}// for the verification functions based on the shared pointer.
{I}instance_(
{II}std::dynamic_pointer_cast<
{III}types::{interface_name}
{II}>(
{III}instance
{II})
{I}) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
{of_cls}::{of_cls}(
{I}const {of_cls}& other
) {{
{I}{indent_but_first_line(copy_data_members_snippet, I)}
}}"""
        ),
        Stripped(
            f"""\
{of_cls}::{of_cls}(
{I}{of_cls}&& other
) {{
{I}{indent_but_first_line(move_data_members_snippet, I)}
}}"""
        ),
        Stripped(
            f"""\
{of_cls}& {of_cls}::operator=(
{I}const {of_cls}& other
) {{
{I}return *this = {of_cls}(other);
}}"""
        ),
        Stripped(
            f"""\
{of_cls}& {of_cls}::operator=(
{I}{of_cls}&& other
) {{
{I}if (this != &other) {{
{II}{indent_but_first_line(move_data_members_snippet, II)}
{I}}}
{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
void {of_cls}::Start() {{
{I}state_ = 0;
{I}Execute();
}}"""
        ),
        Stripped(
            f"""\
void {of_cls}::Next() {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to move a verificator {of_cls}, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}Execute();
}}"""
        ),
        Stripped(
            f"""\
bool {of_cls}::Done() const {{
{I}return done_;
}}"""
        ),
        Stripped(
            f"""\
const Error& {of_cls}::Get() const {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get from a verificator {of_cls}, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}return *error_;
}}"""
        ),
        Stripped(
            f"""\
Error& {of_cls}::GetMutable() {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get mutable from a verificator {of_cls}, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}return *error_;
}}"""
        ),
        Stripped(
            f"""\
long {of_cls}::Index() const {{
{I}#ifdef DEBUG
{I}if (Done() && index_ != -1) {{
{II}throw std::logic_error(
{III}common::Concat(
{IIII}"Expected index to be -1 "
{IIII}"from a done verificator {of_cls}, "
{IIII}"but got: ",
{IIII}std::to_string(index_)
{III})
{II});
{I}}}
{I}#endif

{I}return index_;
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<impl::IVerificator> {of_cls}::Clone() const {{
{I}return common::make_unique<
{II}{of_cls}
{I}>(*this);
}}"""
        ),
    ]  # type: List[Stripped]

    execute_block, execute_errors = _generate_non_recursive_verificator_execute(
        verificator_qualities=verificator_qualities,
        symbol_table=symbol_table,
        environment=environment,
    )
    if execute_errors is not None:
        return None, Error(
            cls.parsed.node,
            f"Failed to generate Execute() method as {of_cls!r}",
            execute_errors,
        )

    assert execute_block is not None
    blocks.append(execute_block)

    return blocks, None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_non_recursive_verificator(
    verificator_qualities: VerificatorQualities,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[List[Stripped]], Optional[Error]]:
    """Generate the non-recursive verificator for the ``cls``."""
    cls = verificator_qualities.cls

    if verificator_qualities.is_noop:
        return (
            _generate_empty_non_recursive_verificator(
                verificator_qualities=verificator_qualities
            ),
            None,
        )

    of_cls = cpp_naming.class_name(Identifier(f"Of_{cls.name}"))

    interface_name = cpp_naming.interface_name(cls.name)

    private_data_members = [
        Stripped(
            f"""\
std::shared_ptr<types::{interface_name}> instance_;
bool done_;
long index_;
std::unique_ptr<Error> error_;
std::uint32_t state_;"""
        )
    ]  # type: List[Stripped]

    if len(verificator_qualities.constrained_primitive_properties) > 0:
        private_data_members.append(
            Stripped(
                "std::unique_ptr<impl::IVerificator> "
                "constrained_primitive_verificator_;"
            )
        )

    private_data_members_joined = "\n".join(private_data_members)

    blocks = [
        Stripped(
            f"""\
class {of_cls} : public impl::IVerificator {{
 public:
{I}{of_cls}(
{II}const std::shared_ptr<types::IClass>& instance
{I});

{I}{of_cls}(
{II}const {of_cls}& other
{I});
{I}{of_cls}(
{II}{of_cls}&& other
{I});
{I}{of_cls}& operator=(
{II}const {of_cls}& other
{I});
{I}{of_cls}& operator=(
{II}{of_cls}&& other
{I});

{I}void Start() override;
{I}void Next() override;
{I}bool Done() const override;
{I}const Error& Get() const override;
{I}Error& GetMutable() override;
{I}long Index() const override;

{I}std::unique_ptr<impl::IVerificator> Clone() const override;

{I}~{of_cls}() override = default;

 private:
{I}{indent_but_first_line(private_data_members_joined, I)}

{I}void Execute();
}};  // class {of_cls}"""
        )
    ]  # type: List[Stripped]

    impl_blocks, error = _generate_non_recursive_verificator_implementation(
        verificator_qualities=verificator_qualities,
        symbol_table=symbol_table,
        environment=environment,
    )
    if error is not None:
        return None, error

    assert impl_blocks is not None
    blocks.extend(impl_blocks)

    return blocks, None


def _generate_new_non_recursive_verificator_implementation(
    symbol_table: intermediate.SymbolTable,
) -> Stripped:
    """Generate the factory of non-recursive verificators based on the model type."""
    case_blocks = []  # type: List[Stripped]
    for cls in symbol_table.concrete_classes:
        enum_name = cpp_naming.enum_name(Identifier("Model_type"))
        literal_name = cpp_naming.enum_literal_name(cls.name)
        verificator_of_cls = cpp_naming.class_name(Identifier(f"Of_{cls.name}"))

        case_blocks.append(
            Stripped(
                f"""\
case types::{enum_name}::{literal_name}:
{I}return common::make_unique<
{II}non_recursive_verificator::{verificator_of_cls}
{I}>(
{II}instance
{I});"""
            )
        )

    case_blocks.append(
        Stripped(
            f"""\
default:
{I}throw std::logic_error(
{II}common::Concat(
{III}"Unexpected model type: ",
{III}std::to_string(
{IIII}static_cast<std::uint32_t>(instance->model_type())
{III})
{II})
{I});"""
        )
    )

    case_blocks_joined = "\n".join(case_blocks)

    switch_stmt = Stripped(
        f"""\
switch (instance->model_type()) {{
{I}{indent_but_first_line(case_blocks_joined, I)}
}}"""
    )

    new_non_recursive_verificator = cpp_naming.function_name(
        Identifier("new_non_recursive_verificator")
    )

    return Stripped(
        f"""\
std::unique_ptr<impl::IVerificator> {new_non_recursive_verificator}(
{I}const std::shared_ptr<types::IClass>& instance
) {{
{I}{indent_but_first_line(switch_stmt, I)}
}}"""
    )


def _generate_recursive_verificator_execute() -> Stripped:
    """Generate the impl. of the ``Execute()`` method for recursive verificator."""
    flow = [
        yielding_flow.command_from_text(
            """\
error_ = nullptr;
index_ = -1;
done_ = false;

verificator_ = NewNonRecursiveVerificator(*instance_);
verificator_->Start();"""
        ),
        yielding_flow.For(
            "!verificator_->Done()",
            "verificator_->Next();",
            [
                yielding_flow.command_from_text(
                    f"""\
// We intentionally take over the ownership of the errors' data members,
// as we know the implementation in all the detail, and want to avoid a costly
// copy.
error_ = common::make_unique<Error>(
{I}std::move(
{II}verificator_->GetMutable()
{I})
);
// No path is prepended as the error refers to the instance itself.
++index_;"""
                )
            ],
        ),
        yielding_flow.command_from_text(
            f"""\
verificator_ = nullptr;

{{
{I}// NOTE (mristin):
{I}// We will not need descent, so we introduce it in the scope.
{I}iteration::Descent descent(
{II}*instance_
{I});
{I}iterator_ = std::move(descent.begin());

{I}// NOTE (mristin):
{I}// descent.end() is a constant reference, so we make an explicit
{I}// copy here.
{I}iterator_end_ = descent.end();
}}"""
        ),
        yielding_flow.For(
            "*iterator_ != *iterator_end_",
            "++(*iterator_);",
            [
                yielding_flow.command_from_text(
                    f"""\
verificator_ = NewNonRecursiveVerificator(
{I}*(*iterator_)
);
verificator_->Start();"""
                ),
                yielding_flow.For(
                    "!verificator_->Done()",
                    "verificator_->Next();",
                    [
                        yielding_flow.command_from_text(
                            f"""\
// We intentionally take over the ownership of the errors' data members,
// as we know the implementation in all the detail, and want to avoid a costly
// copy.
error_ = common::make_unique<Error>(
{I}std::move(
{II}verificator_->GetMutable()
{I})
);

error_->path = std::move(
{I}iteration::MaterializePath(
{II}*iterator_
{I})
);

++index_;"""
                        ),
                        yielding_flow.Yield(),
                    ],
                ),
                yielding_flow.command_from_text("verificator_ = nullptr;"),
            ],
        ),
        yielding_flow.command_from_text(
            """\
iterator_.reset();
iterator_end_.reset();
done_ = true;
index_ = -1;"""
        ),
    ]  # type: Sequence[yielding_flow.Node]

    code = cpp_yielding.generate_execute_body(
        flow=flow, state_member=Identifier("state_")
    )

    return Stripped(
        f"""\
void RecursiveVerificator::Execute() {{
{I}{indent_but_first_line(code, I)}
}}"""
    )


def _generate_recursive_verificator() -> List[Stripped]:
    """Generate the impl. and definition of the recursive verificator."""
    blocks = [
        Stripped(
            f"""\
class RecursiveVerificator : public impl::IVerificator {{
 public:
{I}RecursiveVerificator(
{II}const std::shared_ptr<types::IClass>& instance
{I});

{I}RecursiveVerificator(const RecursiveVerificator& other);
{I}RecursiveVerificator(RecursiveVerificator&& other);
{I}RecursiveVerificator& operator=(const RecursiveVerificator& other);
{I}RecursiveVerificator& operator=(RecursiveVerificator&& other);

{I}void Start() override;
{I}void Next() override;
{I}bool Done() const override;
{I}const Error& Get() const override;
{I}Error& GetMutable() override;
{I}long Index() const override;

{I}std::unique_ptr<impl::IVerificator> Clone() const override;

{I}~RecursiveVerificator() override = default;

 private:
{I}// NOTE(mristin):
{I}// We use a pointer to a shared pointer here so that we can implement
{I}// copy-assignment and move-assignment. Otherwise, if we used a constant
{I}// reference here, the assignments could not be implemented as C++ does not
{I}// allow re-binding of constant references.
{I}const std::shared_ptr<types::IClass>* instance_;

{I}std::uint32_t state_;
{I}std::unique_ptr<impl::IVerificator> verificator_;
{I}bool done_;
{I}long index_;
{I}std::unique_ptr<Error> error_;
{I}common::optional<iteration::Iterator> iterator_;
{I}common::optional<iteration::Iterator> iterator_end_;

{I}void Execute();
}};  // class RecursiveVerificator"""
        ),
        Stripped(
            f"""\
RecursiveVerificator::RecursiveVerificator(
{I}const std::shared_ptr<types::IClass>& instance
) : instance_(&instance) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
RecursiveVerificator::RecursiveVerificator(const RecursiveVerificator& other) {{
{I}instance_ = other.instance_;
{I}state_ = other.state_;
{I}verificator_ = other.verificator_->Clone();
{I}done_ = other.done_;
{I}index_ = other.index_;
{I}error_ = common::make_unique<Error>(*(other.error_));
{I}iterator_ = other.iterator_;
{I}iterator_end_ = other.iterator_end_;
}}"""
        ),
        Stripped(
            f"""\
RecursiveVerificator::RecursiveVerificator(RecursiveVerificator&& other) {{
{I}instance_ = other.instance_;
{I}state_ = other.state_;
{I}verificator_ = std::move(other.verificator_);
{I}done_ = other.done_;
{I}index_ = other.index_;
{I}error_ = std::move(other.error_);
{I}iterator_ = std::move(other.iterator_);
{I}iterator_end_ = std::move(other.iterator_end_);
}}"""
        ),
        Stripped(
            f"""\
RecursiveVerificator& RecursiveVerificator::operator=(
{I}const RecursiveVerificator& other
) {{
{I}return *this = RecursiveVerificator(other);
}}"""
        ),
        Stripped(
            f"""\
RecursiveVerificator& RecursiveVerificator::operator=(RecursiveVerificator&& other) {{
{I}if (this != &other) {{
{II}instance_ = other.instance_;
{II}state_ = other.state_;
{II}verificator_ = std::move(other.verificator_);
{II}done_ = other.done_;
{II}index_ = other.index_;
{II}error_ = std::move(other.error_);
{II}iterator_ = std::move(other.iterator_);
{II}iterator_end_ = std::move(other.iterator_end_);
{I}}}

{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
void RecursiveVerificator::Start() {{
{I}state_ = 0;
{I}Execute();
}}"""
        ),
        Stripped(
            f"""\
void RecursiveVerificator::Next() {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get from a RecursiveVerificator, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}Execute();
}}"""
        ),
        Stripped(
            f"""\
bool RecursiveVerificator::Done() const {{
{I}return done_;
}}"""
        ),
        Stripped(
            f"""\
const Error& RecursiveVerificator::Get() const {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get from a RecursiveVerificator, "
{III}"but the verificator is done."
{II});
{I}}}
{I}#endif

{I}return *error_;
}}"""
        ),
        Stripped(
            f"""\
Error& RecursiveVerificator::GetMutable() {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get mutable from a RecursiveVerificator, "
{III}"but the verificator is done."
{II});
{I}}}
{I}#endif

{I}return *error_;
}}"""
        ),
        Stripped(
            f"""\
long RecursiveVerificator::Index() const {{
{I}#ifdef DEBUG
{I}if (Done() && index_ != -1) {{
{II}throw std::logic_error(
{III}common::Concat(
{IIII}"Expected index to be -1 "
{IIII}"from a done RecursiveVerificator, "
{IIII}"but got: ",
{IIII}std::to_string(index_)
{III})
{II});
{I}}}
{I}#endif

{I}return index_;
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<impl::IVerificator> RecursiveVerificator::Clone() const {{
{I}return common::make_unique<RecursiveVerificator>(*this);
}}"""
        ),
    ]  # type: List[Stripped]

    execute_block = _generate_recursive_verificator_execute()
    blocks.append(execute_block)

    return blocks


class _RegexRendererForUTF16(parse_retree.Renderer):
    """Render the regular expressions for C++ consisting of only 2-byte characters."""

    def char_to_str_and_escape_or_encode_if_necessary(
        self, node: parse_retree.Char, escaping: Mapping[str, str]
    ) -> List[Union[str, parse_tree.FormattedValue]]:
        """Convert the ``node`` to a string, and escape and/or encode appropriately."""
        if not node.explicitly_encoded:
            escaped = escaping.get(node.character, None)
            if escaped is not None:
                result: List[Union[str, parse_tree.FormattedValue]] = [escaped]
            else:
                result = [node.character]

            return result
        else:
            code = ord(node.character)

            if code <= 255:
                return [f"\\x{code:02x}"]
            elif code <= 65535:
                # NOTE (mristin, 2023-10-18):
                # We have to escape, i.e., use ``\\u{code}`` instead of ``\u{code}``
                # since the regex engine in C++ can work with it, but the C++ compiler
                # complains if we do not supply valid Unicode code points.
                return [f"\\u{code:04x}"]
            else:
                raise AssertionError(
                    f"No code points expected above 65535, but got: {code} "
                    f"for character {node.character!r}"
                )


_REGEX_RENDERER_FOR_UTF16 = _RegexRendererForUTF16()


class _RegexRendererForUTF32(parse_retree.Renderer):
    """Render the regular expressions for C++ consisting of 4-byte characters."""

    def char_to_str_and_escape_or_encode_if_necessary(
        self, node: parse_retree.Char, escaping: Mapping[str, str]
    ) -> List[Union[str, parse_tree.FormattedValue]]:
        """Convert the ``node`` to a string, and escape and/or encode appropriately."""
        if not node.explicitly_encoded:
            escaped = escaping.get(node.character, None)
            if escaped is not None:
                result: List[Union[str, parse_tree.FormattedValue]] = [escaped]
            else:
                result = [node.character]

            return result
        else:
            code = ord(node.character)

            if code <= 255:
                return [f"\\x{code:02x}"]
            else:
                # NOTE (mristin, 2023-10-18):
                # We assume here that the character will be escaped in the wstring
                # literal in ``cpp_common.wstring_literal``.
                return [node.character]


_REGEX_RENDERER_FOR_UTF32 = _RegexRendererForUTF32()


class _WstringEncoding(enum.Enum):
    UTF16 = "UTF16"
    UTF32 = "UTF32"


class _PatternVerificationTranspiler(
    parse_tree.RestrictedTransformer[Tuple[Optional[Stripped], Optional[Error]]]
):
    """Transpile a statement of a pattern verification into C++."""

    def __init__(self, wstring_encoding: _WstringEncoding) -> None:
        """Initialize with the given values."""
        self.wstring_encoding = wstring_encoding
        self.defined_variable_set = set()  # type: Set[Identifier]

    def _fix_regex_in_place(self, regex: parse_retree.Regex) -> None:
        """Fix the regex in-place to conform to the wstring encoding."""
        if self.wstring_encoding is _WstringEncoding.UTF16:
            parse_retree.fix_for_utf16_regex_in_place(regex)

    def _render_regex(
        self, regex: parse_retree.Regex
    ) -> List[Union[str, parse_tree.FormattedValue]]:
        """Render the regular expression to parts of a joined string."""
        if self.wstring_encoding is _WstringEncoding.UTF16:
            return parse_retree.render(regex=regex, renderer=_REGEX_RENDERER_FOR_UTF16)

        elif self.wstring_encoding is _WstringEncoding.UTF32:
            return parse_retree.render(regex=regex, renderer=_REGEX_RENDERER_FOR_UTF32)

        else:
            assert_never(self.wstring_encoding)

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def _transform_joined_str_values(
        self, values: Sequence[Union[str, parse_tree.FormattedValue]]
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        """Transform the values of a joined string to a Python string literal."""
        # If we do not need interpolation, simply return the string literals
        # joined together.
        needs_interpolation = any(
            isinstance(value, parse_tree.FormattedValue) for value in values
        )
        if not needs_interpolation:
            return (
                Stripped(
                    cpp_common.wstring_literal(
                        "".join(value for value in values)  # type: ignore
                    )
                ),
                None,
            )

        args = []  # type: List[Stripped]

        for value in values:
            if isinstance(value, str):
                args.append(cpp_common.wstring_literal(value))

            elif isinstance(value, parse_tree.FormattedValue):
                code, error = self.transform(value.value)
                if error is not None:
                    return None, error

                assert code is not None

                assert (
                    "\n" not in code
                ), f"New-lines are not expected in formatted values, but got: {code}"

                args.append(code)
            else:
                assert_never(value)

        if len(args) == 1:
            return args[0], None

        args_joined = ",\n".join(args)
        return (
            Stripped(
                f"""\
common::Concat(
{I}{indent_but_first_line(args_joined, I)}
)"""
            ),
            None,
        )

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_constant(
        self, node: parse_tree.Constant
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if isinstance(node.value, str):
            # NOTE (mristin, 2023-10-18):
            # We assume that all the string constants are valid regular expressions.

            regex, parse_error = parse_retree.parse(values=[node.value])
            if parse_error is not None:
                regex_line, pointer_line = parse_retree.render_pointer(
                    parse_error.cursor
                )

                return (
                    None,
                    Error(
                        node.original_node,
                        f"The string constant could not be parsed "
                        f"as a regular expression: \n"
                        f"{parse_error.message}\n"
                        f"{regex_line}\n"
                        f"{pointer_line}",
                    ),
                )

            assert regex is not None
            self._fix_regex_in_place(regex=regex)

            # NOTE (mristin, 2023-10-18):
            # Strictly speaking, this is a joined string with a single value, a string
            # literal.
            return self._transform_joined_str_values(
                values=self._render_regex(regex=regex)
            )
        else:
            raise AssertionError(f"Unexpected {node=}")

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        return Stripped(cpp_naming.variable_name(node.identifier)), None

    @ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
    def transform_joined_str(
        self, node: parse_tree.JoinedStr
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        regex, parse_error = parse_retree.parse(values=node.values)
        if parse_error is not None:
            regex_line, pointer_line = parse_retree.render_pointer(parse_error.cursor)

            return (
                None,
                Error(
                    node.original_node,
                    f"The joined string could not be parsed "
                    f"as a regular expression: \n"
                    f"{parse_error.message}\n"
                    f"{regex_line}\n"
                    f"{pointer_line}",
                ),
            )

        assert regex is not None
        self._fix_regex_in_place(regex=regex)

        return self._transform_joined_str_values(values=self._render_regex(regex=regex))

    def transform_assignment(
        self, node: parse_tree.Assignment
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        assert isinstance(node.target, parse_tree.Name)
        variable = cpp_naming.variable_name(node.target.identifier)
        code, error = self.transform(node.value)
        if error is not None:
            return None, error
        assert code is not None

        if variable in self.defined_variable_set:
            return Stripped(f"{variable} = {code};"), None

        self.defined_variable_set.add(variable)
        return Stripped(f"std::wstring {variable} = {code};"), None


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_pattern_verification_implementation(
    verification: intermediate.PatternVerification,
) -> Tuple[Optional[List[Stripped]], Optional[Error]]:
    """Generate the implementation of the given pattern verification function."""
    # NOTE (mristin, 2023-10-18):
    # We assume that we performed all the checks at the intermediate stage.

    errors = []  # type: List[Error]

    transpiler_utf16 = _PatternVerificationTranspiler(
        wstring_encoding=_WstringEncoding.UTF16
    )
    stmts_utf16 = []  # type: List[Stripped]

    for i, stmt in enumerate(verification.parsed.body):
        # NOTE (mristin, 2023-10-18):
        # We will transpile the return statement separately.
        if i == len(verification.parsed.body) - 1:
            break

        code, error = transpiler_utf16.transform(stmt)
        if error is not None:
            errors.append(error)
        else:
            assert code is not None
            stmts_utf16.append(code)

    pattern_expr_utf16, error = transpiler_utf16.transform(verification.pattern_expr)
    if error is not None:
        errors.append(error)

    transpiler_utf32 = _PatternVerificationTranspiler(
        wstring_encoding=_WstringEncoding.UTF32
    )
    stmts_utf32 = []  # type: List[Stripped]

    for i, stmt in enumerate(verification.parsed.body):
        # NOTE (mristin, 2023-10-18):
        # We will transpile the return statement separately.
        if i == len(verification.parsed.body) - 1:
            break

        code, error = transpiler_utf32.transform(stmt)
        if error is not None:
            errors.append(error)
        else:
            assert code is not None
            stmts_utf32.append(code)

    pattern_expr_utf32, error = transpiler_utf32.transform(verification.pattern_expr)
    if error is not None:
        errors.append(error)

    if len(errors) > 0:
        return None, Error(
            verification.parsed.node,
            f"Failed to transpile verification function {verification.name!r}",
            errors,
        )

    assert pattern_expr_utf16 is not None
    assert pattern_expr_utf32 is not None

    construct_name = cpp_naming.function_name(
        Identifier(f"construct_{verification.name}")
    )

    stmts_utf16_joined = "\n".join(stmts_utf16)
    stmts_utf32_joined = "\n".join(stmts_utf32)

    regex_name = cpp_naming.constant_name(Identifier(f"regex_{verification.name}"))

    assert len(verification.arguments) == 1
    arg = verification.arguments[0]

    arg_type = cpp_common.generate_type_with_const_ref_if_applicable(
        type_annotation=arg.type_annotation, types_namespace=cpp_common.TYPES_NAMESPACE
    )
    arg_name = cpp_naming.argument_name(arg.name)

    verification_name = cpp_naming.function_name(verification.name)

    blocks: List[Stripped]

    if (
        stmts_utf16_joined == stmts_utf32_joined
        and pattern_expr_utf16 == pattern_expr_utf32
    ):
        blocks = [
            Stripped(
                f"""\
std::wregex {construct_name}() {{
{I}{indent_but_first_line(stmts_utf16_joined, I)}
{I}return std::wregex(
{II}{indent_but_first_line(pattern_expr_utf16, II)}
{I});
}}"""
            )
        ]
    else:
        blocks = [
            Stripped(
                f"""\
std::wregex {construct_name}() {{
{I}static_assert(
{II}sizeof(wchar_t) == 2 || sizeof(wchar_t) == 4,
{II}"Expected either 2 or 4 bytes for wchar_t, but got something else."
{I});

{I}switch (sizeof(wchar_t)) {{
{II}case 2: {{
{III}{indent_but_first_line(stmts_utf16_joined, III)}
{III}return std::wregex(
{IIII}{indent_but_first_line(pattern_expr_utf16, IIII)}
{III});
{II}}}

{II}case 4: {{
{III}{indent_but_first_line(stmts_utf32_joined, III)}
{III}return std::wregex(
{IIII}{indent_but_first_line(pattern_expr_utf32, IIII)}
{III});
{II}}}

{II}default:
{III}throw std::logic_error(
{IIII}common::Concat(
{IIIII}"Unexpected size of wchar_t: ",
{IIIII}std::to_string(sizeof(wchar_t))
{IIII})
{III});
{I}}}
}}"""
            )
        ]

    blocks.extend(
        [
            Stripped(f"const std::wregex {regex_name} = {construct_name}();"),
            Stripped(
                f"""\
bool {verification_name}(
{I}{indent_but_first_line(arg_type, I)} {arg_name}
) {{
{I}return std::regex_search(
{II}{arg_name},
{II}{regex_name}
{I});
}}"""
            ),
        ]
    )

    return blocks, None


class _TranspilableVerificationTranspiler(cpp_transpilation.Transpiler):
    """Transpile the body of a :class:`TranspilableVerification`."""

    # fmt: off
    @require(
        lambda environment, verification:
        all(
            environment.find(arg.name) is not None
            for arg in verification.arguments
        ),
        "All arguments defined in the environment"
    )
    # fmt: on
    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        is_optional_map: Mapping[parse_tree.Node, bool],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
        verification: intermediate.TranspilableVerification,
    ) -> None:
        """Initialize with the given values."""
        cpp_transpilation.Transpiler.__init__(
            self,
            type_map=type_map,
            is_optional_map=is_optional_map,
            environment=environment,
            types_namespace=cpp_common.TYPES_NAMESPACE,
        )

        self._symbol_table = symbol_table

        self._argument_name_set = frozenset(arg.name for arg in verification.arguments)

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            return Stripped(cpp_naming.variable_name(node.identifier)), None

        if node.identifier in self._argument_name_set:
            return Stripped(cpp_naming.argument_name(node.identifier)), None

        if node.identifier in self._symbol_table.constants_by_name:
            constant = cpp_naming.constant_name(node.identifier)
            return Stripped(f"{cpp_common.CONSTANTS_NAMESPACE}::{constant}"), None

        if node.identifier in self._symbol_table.verification_functions_by_name:
            return Stripped(cpp_naming.function_name(node.identifier)), None

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            return (
                Stripped(
                    f"{cpp_common.TYPES_NAMESPACE}::{cpp_naming.enum_name(node.identifier)}"
                ),
                None,
            )

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to C++. We could not find it neither in the constants, nor in "
            f"verification functions, nor as an enumeration. "
            f"If you expect this name to be transpilable, please contact "
            f"the developers.",
        )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_implementation_of_transpilable_verification(
    verification: intermediate.TranspilableVerification,
    symbol_table: intermediate.SymbolTable,
    base_environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Transpile the verification to a function implementation."""
    canonicalizer = intermediate_type_inference.Canonicalizer()
    for node in verification.parsed.body:
        _ = canonicalizer.transform(node)

    environment = intermediate_type_inference.MutableEnvironment(
        parent=base_environment
    )
    for arg in verification.arguments:
        environment.set(
            identifier=arg.name,
            type_annotation=intermediate_type_inference.convert_type_annotation(
                arg.type_annotation
            ),
        )

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment,
        representation_map=canonicalizer.representation_map,
    )

    for node in verification.parsed.body:
        _ = type_inferrer.transform(node)

    if len(type_inferrer.errors):
        return None, Error(
            verification.parsed.node,
            f"Failed to infer the types "
            f"in the verification function {verification.name!r}",
            type_inferrer.errors,
        )

    optional_inferrer = cpp_optionaling.Inferrer(
        environment=environment, type_map=type_inferrer.type_map
    )
    for node in verification.parsed.body:
        _ = optional_inferrer.transform(node)

    if len(optional_inferrer.errors) > 0:
        return None, Error(
            verification.parsed.node,
            f"Failed to infer whether one or more nodes are ``common::optional`` "
            f"in the verification function {verification.name!r}",
            optional_inferrer.errors,
        )

    transpiler = _TranspilableVerificationTranspiler(
        type_map=type_inferrer.type_map,
        is_optional_map=optional_inferrer.is_optional_map,
        environment=environment,
        symbol_table=symbol_table,
        verification=verification,
    )

    body = []  # type: List[Stripped]
    for node in verification.parsed.body:
        stmt, error = transpiler.transform(node)
        if error is not None:
            return None, Error(
                verification.parsed.node,
                f"Failed to transpile the verification function {verification.name!r}",
                [error],
            )

        assert stmt is not None
        body.append(stmt)

    arg_types_names = [
        (
            cpp_common.generate_type_with_const_ref_if_applicable(
                type_annotation=arg.type_annotation,
                types_namespace=cpp_common.TYPES_NAMESPACE,
            ),
            cpp_naming.argument_name(arg.name),
        )
        for arg in verification.arguments
    ]

    function_name = cpp_naming.function_name(verification.name)
    arg_definitions_joined = ",\n".join(
        f"{arg_type} {arg_name}" for arg_type, arg_name in arg_types_names
    )

    body_joined = "\n".join(body)

    return (
        Stripped(
            f"""\
bool {function_name}(
{I}{indent_but_first_line(arg_definitions_joined, I)}
) {{
{I}{indent_but_first_line(body_joined, I)}
}}"""
        ),
        None,
    )


@require(lambda constrained_primitive: len(constrained_primitive.invariants) == 0)
def _generate_empty_constrained_primitive_verificator(
    constrained_primitive: intermediate.ConstrainedPrimitive,
) -> List[Stripped]:
    """
    Generate a constrained primitive verificator which is always done.

    Though the implementation is a duplicate in logic of ``AlwaysDoneVerificator``,
    the assertion error messages are different, so we generate a separate class.
    """
    of_constrained_primitive = cpp_naming.class_name(
        Identifier(f"Of_{constrained_primitive.name}")
    )

    value_type = cpp_common.generate_primitive_type_with_const_ref_if_applicable(
        primitive_type=constrained_primitive.constrainee
    )

    return [
        Stripped(
            f"""\
class {of_constrained_primitive} : public impl::IVerificator {{
 public:
{I}{of_constrained_primitive}(
{II}{value_type} value
{I});

{I}void Start() override;
{I}void Next() override;
{I}bool Done() const override;
{I}const Error& Get() const override;
{I}Error& GetMutable() override;
{I}long Index() const override;

{I}std::unique_ptr<impl::IVerificator> Clone() const override;

{I}virtual ~{of_constrained_primitive}() = default;
}};  // class {of_constrained_primitive}"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}::{of_constrained_primitive}(
{I}{value_type}
) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
void {of_constrained_primitive}::Start() {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
void {of_constrained_primitive}::Next() {{
{I}throw std::logic_error(
{II}"You want to move "
{II}"a verificator {of_constrained_primitive}, "
{II}"but the verificator is always done as "
{II}"there are no invariants defined for this constrained primitive."
{I});
}}"""
        ),
        Stripped(
            f"""\
bool {of_constrained_primitive}::Done() const {{
{I}return true;
}}"""
        ),
        Stripped(
            f"""\
const Error& {of_constrained_primitive}::Get() const {{
{I}throw std::logic_error(
{II}"You want to get from "
{II}"a verificator {of_constrained_primitive}, "
{II}"but the verificator is always done as "
{II}"there are no invariants defined for this constrained primitive."
{I});
}}"""
        ),
        Stripped(
            f"""\
Error& {of_constrained_primitive}::GetMutable() {{
{I}throw std::logic_error(
{II}"You want to get mutable from "
{II}"a verificator {of_constrained_primitive}, "
{II}"but the verificator is always done as "
{II}"there are no invariants defined for this constrained primitive."
{I});
}}"""
        ),
        Stripped(
            f"""\
long {of_constrained_primitive}::Index() const {{
{I}return -1;
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<impl::IVerificator> {of_constrained_primitive}::Clone() const {{
{I}return common::make_unique<
{II}{of_constrained_primitive}
{I}>(*this);
}}"""
        ),
    ]


class _ConstrainedPrimitiveInvariantTranspiler(cpp_transpilation.Transpiler):
    """Transpile invariants of the constrained primitives."""

    def __init__(
        self,
        type_map: Mapping[
            parse_tree.Node, intermediate_type_inference.TypeAnnotationUnion
        ],
        is_optional_map: Mapping[parse_tree.Node, bool],
        environment: intermediate_type_inference.Environment,
        symbol_table: intermediate.SymbolTable,
        constrained_primitive: intermediate.ConstrainedPrimitive,
    ) -> None:
        """Initialize with the given values."""
        cpp_transpilation.Transpiler.__init__(
            self,
            type_map=type_map,
            is_optional_map=is_optional_map,
            environment=environment,
            types_namespace=cpp_common.TYPES_NAMESPACE,
        )

        self._symbol_table = symbol_table
        self._constrained_primitive = constrained_primitive

    def transform_name(
        self, node: parse_tree.Name
    ) -> Tuple[Optional[Stripped], Optional[Error]]:
        if node.identifier in self._variable_name_set:
            return Stripped(cpp_naming.variable_name(node.identifier)), None

        if node.identifier == "self":
            # The ``value_`` refers to the value under verification.
            if _constrained_primitive_verificator_value_is_pointer(
                primitive_type=self._constrained_primitive.constrainee
            ):
                return Stripped("(*value_)"), None
            else:
                return Stripped("value_"), None

        if node.identifier in self._symbol_table.constants_by_name:
            constant = cpp_naming.constant_name(node.identifier)
            return Stripped(f"{cpp_common.CONSTANTS_NAMESPACE}::{constant}"), None

        if node.identifier in self._symbol_table.verification_functions_by_name:
            return Stripped(cpp_naming.function_name(node.identifier)), None

        our_type = self._symbol_table.find_our_type(name=node.identifier)
        if isinstance(our_type, intermediate.Enumeration):
            return (
                Stripped(
                    f"{cpp_common.TYPES_NAMESPACE}::{cpp_naming.enum_name(node.identifier)}"
                ),
                None,
            )

        return None, Error(
            node.original_node,
            f"We can not determine how to transpile the name {node.identifier!r} "
            f"to C++. We could not find it neither in the local variables, "
            f"nor in the global constants, nor in verification functions, "
            f"nor as an enumeration. If you expect this name to be transpilable, "
            f"please contact the developers.",
        )


# fmt: off
@require(
    lambda invariant, constrained_primitive:
    id(invariant) in constrained_primitive.invariant_id_set
)
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
# fmt: on
def _transpile_constrained_primitive_invariant(
    invariant: intermediate.Invariant,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
    constrained_primitive: intermediate.ConstrainedPrimitive,
) -> Tuple[Optional[Stripped], Optional[Error]]:
    """Translate the invariant from the meta-model into a C++ condition."""
    canonicalizer = intermediate_type_inference.Canonicalizer()
    _ = canonicalizer.transform(invariant.body)

    type_inferrer = intermediate_type_inference.Inferrer(
        symbol_table=symbol_table,
        environment=environment,
        representation_map=canonicalizer.representation_map,
    )

    _ = type_inferrer.transform(invariant.body)

    if len(type_inferrer.errors):
        return None, Error(
            invariant.parsed.node,
            "Failed to infer the types in the invariant",
            type_inferrer.errors,
        )

    optional_inferrer = cpp_optionaling.Inferrer(
        environment=environment, type_map=type_inferrer.type_map
    )

    _ = optional_inferrer.transform(invariant.body)

    if len(optional_inferrer.errors) > 0:
        return None, Error(
            invariant.parsed.node,
            "Failed to infer whether one or more nodes are ``common::optional`` "
            "in the invariant",
            optional_inferrer.errors,
        )

    transpiler = _ConstrainedPrimitiveInvariantTranspiler(
        type_map=type_inferrer.type_map,
        is_optional_map=optional_inferrer.is_optional_map,
        environment=environment,
        symbol_table=symbol_table,
        constrained_primitive=constrained_primitive,
    )

    expr, error = transpiler.transform(invariant.body)

    if error is not None:
        return None, error

    assert expr is not None
    return expr, None


@require(lambda constrained_primitive: len(constrained_primitive.invariants) > 0)
def _generate_constrained_primitive_verificator_execute(
    constrained_primitive: intermediate.ConstrainedPrimitive,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[Stripped], Optional[List[Error]]]:
    """Generate the ``Execute()`` in the constrained primitive verificator."""
    flow = [
        yielding_flow.command_from_text(
            """\
done_ = false;
error_ = nullptr;
index_ = -1;"""
        )
    ]  # type: List[yielding_flow.Node]

    errors = []  # type: List[Error]
    for invariant in constrained_primitive.invariants:
        condition_expr, error = _transpile_constrained_primitive_invariant(
            invariant=invariant,
            symbol_table=symbol_table,
            environment=environment,
            constrained_primitive=constrained_primitive,
        )
        if error is not None:
            errors.append(error)
            continue

        assert condition_expr is not None

        # NOTE (mristin, 2023-11-01):
        # We need to wrap the description in multiple literals as a single long
        # string literal is often too much for the readability.
        invariant_description_lines = wrap_text_into_lines(invariant.description)

        invariant_description_literals_joined = "\n".join(
            cpp_common.wstring_literal(line) for line in invariant_description_lines
        )

        flow.append(
            yielding_flow.IfFalse(
                condition_expr,
                [
                    yielding_flow.command_from_text(
                        f"""\
error_ = common::make_unique<Error>(
{I}{indent_but_first_line(invariant_description_literals_joined, I)}
);
// No path is prepended as the error refers to the value itself.
++index_;"""
                    ),
                    yielding_flow.Yield(),
                ],
            )
        )

    flow.append(
        yielding_flow.command_from_text(
            """\
done_ = true;
error_ = nullptr;
index_ = -1;"""
        )
    )

    if len(errors) > 0:
        return None, errors

    code = cpp_yielding.generate_execute_body(
        flow=flow, state_member=Identifier("state_")
    )

    of_constrained_primitive = cpp_naming.class_name(
        Identifier(f"of_{constrained_primitive.name}")
    )

    return (
        Stripped(
            f"""\
void {of_constrained_primitive}::Execute() {{
{I}{indent_but_first_line(code, I)}
}}"""
        ),
        None,
    )


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_constrained_primitive_verificator(
    constrained_primitive: intermediate.ConstrainedPrimitive,
    symbol_table: intermediate.SymbolTable,
    environment: intermediate_type_inference.Environment,
) -> Tuple[Optional[List[Stripped]], Optional[Error]]:
    """Generate the def. and impl. of a verificator for a constrained primitive."""
    if len(constrained_primitive.invariants) == 0:
        return (
            _generate_empty_constrained_primitive_verificator(
                constrained_primitive=constrained_primitive
            ),
            None,
        )

    of_constrained_primitive = cpp_naming.class_name(
        Identifier(f"Of_{constrained_primitive.name}")
    )

    input_value_type = cpp_common.generate_primitive_type_with_const_ref_if_applicable(
        primitive_type=constrained_primitive.constrainee
    )

    value_type = cpp_common.generate_primitive_type(constrained_primitive.constrainee)
    if _constrained_primitive_verificator_value_is_pointer(
        constrained_primitive.constrainee
    ):
        data_value_type = f"const {value_type}*"

        constructor_init = "value_(&value)"

    else:
        data_value_type = value_type

        constructor_init = "value_(value)"

    move_snippet = Stripped(
        """\
value_ = other.value_;
index_ = other.index_;
error_ = std::move(other.error_);
done_ = other.done_;
state_ = other.state_;"""
    )

    blocks = [
        Stripped(
            f"""\
class {of_constrained_primitive} : public impl::IVerificator {{
 public:
{I}{of_constrained_primitive}(
{II}{input_value_type} value
{I});

{I}{of_constrained_primitive}(
{II}const {of_constrained_primitive}& other
{I});
{I}{of_constrained_primitive}(
{II}{of_constrained_primitive}&& other
{I});
{I}{of_constrained_primitive}& operator=(
{II}const {of_constrained_primitive}& other
{I});
{I}{of_constrained_primitive}& operator=(
{II}{of_constrained_primitive}&& other
{I});

{I}void Start() override;
{I}void Next() override;
{I}bool Done() const override;
{I}const Error& Get() const override;
{I}Error& GetMutable() override;
{I}long Index() const override;

{I}std::unique_ptr<impl::IVerificator> Clone() const override;

{I}~{of_constrained_primitive}() override = default;

 private:
{I}{data_value_type} value_;
{I}long index_;
{I}std::unique_ptr<Error> error_;
{I}bool done_;
{I}std::uint32_t state_;

{I}void Execute();
}};  // class {of_constrained_primitive}"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}::{of_constrained_primitive}(
{I}{input_value_type} value
) : {constructor_init} {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}::{of_constrained_primitive}(
{I}const {of_constrained_primitive}& other
) {{
{I}value_ = other.value_;
{I}index_ = other.index_;
{I}error_ = common::make_unique<Error>(*other.error_);
{I}done_ = other.done_;
{I}state_ = other.state_;
}}"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}::{of_constrained_primitive}(
{I}{of_constrained_primitive}&& other
) {{
{I}{indent_but_first_line(move_snippet, I)}
}}"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}& {of_constrained_primitive}::operator=(
{I}const {of_constrained_primitive}& other
) {{
{I}return *this = {of_constrained_primitive}(other);
}}"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}& {of_constrained_primitive}::operator=(
{I}{of_constrained_primitive}&& other
) {{
{I}if (this != &other) {{
{II}{indent_but_first_line(move_snippet, II)}
{I}}}

{I}return *this;
}}"""
        ),
        Stripped(
            f"""\
void {of_constrained_primitive}::Start() {{
{I}state_ = 0;
{I}Execute();
}}"""
        ),
        Stripped(
            f"""\
void {of_constrained_primitive}::Next() {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to move a verificator {of_constrained_primitive}, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}Execute();
}}"""
        ),
        Stripped(
            f"""\
bool {of_constrained_primitive}::Done() const {{
{I}return done_;
}}"""
        ),
        Stripped(
            f"""\
const Error& {of_constrained_primitive}::Get() const {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get from a verificator {of_constrained_primitive}, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}return *error_;
}}"""
        ),
        Stripped(
            f"""\
Error& {of_constrained_primitive}::GetMutable() {{
{I}#ifdef DEBUG
{I}if (Done()) {{
{II}throw std::logic_error(
{III}"You want to get mutable from a verificator {of_constrained_primitive}, "
{III}"but the verificator was done."
{II});
{I}}}
{I}#endif

{I}return *error_;
}}"""
        ),
        Stripped(
            f"""\
long {of_constrained_primitive}::Index() const {{
{I}#ifdef DEBUG
{I}if (Done() && index_ != -1) {{
{II}throw std::logic_error(
{III}common::Concat(
{IIII}"Expected index to be -1 "
{IIII}"from a done verificator {of_constrained_primitive}, "
{IIII}"but got: ",
{IIII}std::to_string(index_)
{III})
{II});
{I}}}
{I}#endif

{I}return index_;
}}"""
        ),
        Stripped(
            f"""\
std::unique_ptr<impl::IVerificator> {of_constrained_primitive}::Clone() const {{
{I}return common::make_unique<
{II}{of_constrained_primitive}
{I}>(*this);
}}"""
        ),
    ]  # type: List[Stripped]

    execute_block, execute_errors = _generate_constrained_primitive_verificator_execute(
        constrained_primitive=constrained_primitive,
        symbol_table=symbol_table,
        environment=environment,
    )
    if execute_errors is not None:
        return None, Error(
            constrained_primitive.parsed.node,
            f"Failed to generate Execute() method for {of_constrained_primitive!r}",
            execute_errors,
        )

    assert execute_block is not None
    blocks.append(execute_block)

    return blocks, None


def _generate_implementation_of_verify_constrained_primitive(
    constrained_primitive: intermediate.ConstrainedPrimitive,
) -> Stripped:
    """Generate the implementation of the function ``Verify{Constrained Primitive}``."""
    verify_name = cpp_naming.function_name(
        Identifier(f"verify_{constrained_primitive.name}")
    )

    of_constrained_primitive = cpp_naming.class_name(
        Identifier(f"Of_{constrained_primitive.name}")
    )

    value_type = cpp_common.generate_primitive_type_with_const_ref_if_applicable(
        primitive_type=constrained_primitive.constrainee
    )

    return Stripped(
        f"""\
std::unique_ptr<IVerification> {verify_name}(
{I}{value_type} that
) {{
{I}return common::make_unique<
{II}constrained_primitive_verification::{of_constrained_primitive}
{I}>(that);
}}"""
    )


def _generate_constrained_primitive_verification(
    constrained_primitive: intermediate.ConstrainedPrimitive,
) -> List[Stripped]:
    """Generate the verification class for the constrained primitive."""
    of_constrained_primitive = cpp_naming.class_name(
        Identifier(f"Of_{constrained_primitive.name}")
    )

    value_type = cpp_common.generate_primitive_type_with_const_ref_if_applicable(
        primitive_type=constrained_primitive.constrainee
    )

    return [
        Stripped(f"// region {of_constrained_primitive}"),
        Stripped(
            f"""\
class {of_constrained_primitive} : public IVerification {{
 public:
{I}{of_constrained_primitive}(
{II}{value_type} value
{I});

{I}Iterator begin() const override;
{I}const Iterator& end() const override;

{I}~{of_constrained_primitive}() override = default;
 private:
{I}{value_type} value_;
}};  // class ConstrainedPrimitiveVerification"""
        ),
        Stripped(
            f"""\
{of_constrained_primitive}::{of_constrained_primitive}(
{I}{value_type} value
) : value_(value) {{
{I}// Intentionally empty.
}}"""
        ),
        Stripped(
            f"""\
Iterator {of_constrained_primitive}::begin() const {{
{I}std::unique_ptr<impl::IVerificator> verificator(
{II}common::make_unique<
{III}constrained_primitive_verificator::{of_constrained_primitive}
{II}>(value_)
{I});

{I}verificator->Start();

{I}// NOTE(mristin):
{I}// We short-circuit here for efficiency, as we can immediately dispose
{I}// of the verificator.
{I}if (verificator->Done()) {{
{II}return Iterator(common::make_unique<AlwaysDoneVerificator>());
{I}}}

{I}return Iterator(std::move(verificator));
}}"""
        ),
        Stripped(
            f"""\
const Iterator& {of_constrained_primitive}::end() const {{
{I}static Iterator iterator(common::make_unique<AlwaysDoneVerificator>());
{I}return iterator;
}}"""
        ),
        Stripped(f"// endregion {of_constrained_primitive}"),
    ]


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
    """Generate the C++ implementation of the verification code.."""
    namespace = Stripped(f"{library_namespace}::{cpp_common.VERIFICATION_NAMESPACE}")

    include_prefix_path = cpp_common.generate_include_prefix_path(library_namespace)

    errors = []  # type: List[Error]

    base_environment = intermediate_type_inference.populate_base_environment(
        symbol_table=symbol_table
    )

    blocks = [
        cpp_common.WARNING,
        Stripped(
            f"""\
#include "{include_prefix_path}/common.hpp"
#include "{include_prefix_path}/constants.hpp"
#include "{include_prefix_path}/verification.hpp"

#pragma warning(push, 0)
#include <map>
#include <regex>
#include <set>
#pragma warning(pop)"""
        ),
        cpp_common.generate_namespace_opening(namespace),
        *_generate_error_implementation(),
        *_generate_always_done_verificator(),
    ]  # type: List[Stripped]

    if len(symbol_table.verification_functions) > 0:
        blocks.append(Stripped("// region Verification functions"))

        for verification in symbol_table.verification_functions:
            if isinstance(verification, intermediate.PatternVerification):
                (
                    verification_blocks,
                    error,
                ) = _generate_pattern_verification_implementation(
                    verification=verification
                )

                if error is not None:
                    errors.append(error)
                else:
                    assert verification_blocks is not None
                    blocks.extend(verification_blocks)

            elif isinstance(verification, intermediate.TranspilableVerification):
                block, error = _generate_implementation_of_transpilable_verification(
                    verification=verification,
                    symbol_table=symbol_table,
                    base_environment=base_environment,
                )

                if error is not None:
                    errors.append(error)
                else:
                    assert block is not None
                    blocks.append(block)

            elif isinstance(
                verification, intermediate.ImplementationSpecificVerification
            ):
                implementation_key = specific_implementations.ImplementationKey(
                    f"verification/{verification.name}.cpp"
                )

                block = spec_impls.get(implementation_key, None)

                if block is None:
                    errors.append(
                        Error(
                            verification.parsed.node,
                            f"The implementation is missing for "
                            f"the implementation-specific verification "
                            f"function: {implementation_key}",
                        )
                    )
                else:
                    # NOTE (mristin, 2024-01-09):
                    # Some verification functions only live in the header and have
                    # no code in the implementation file. For example, the verification
                    # functions which are templated.
                    if len(block.strip()) > 0:
                        blocks.append(block)
            else:
                assert_never(verification)

        blocks.append(Stripped("// endregion Verification functions"))

    if len(symbol_table.constrained_primitives) > 0:
        blocks.append(Stripped("// region Verification of constrained primitives"))

        blocks.append(Stripped("namespace constrained_primitive_verificator {"))

        for constrained_primitive in symbol_table.constrained_primitives:
            invariant_environment = intermediate_type_inference.MutableEnvironment(
                parent=base_environment
            )

            assert invariant_environment.find(Identifier("self")) is None
            invariant_environment.set(
                identifier=Identifier("self"),
                type_annotation=intermediate_type_inference.OurTypeAnnotation(
                    our_type=constrained_primitive
                ),
            )

            verificator_blocks, error = _generate_constrained_primitive_verificator(
                constrained_primitive=constrained_primitive,
                symbol_table=symbol_table,
                environment=invariant_environment,
            )

            if error is not None:
                errors.append(error)
            else:
                assert verificator_blocks is not None
                blocks.extend(verificator_blocks)

        blocks.append(Stripped("}  // namespace constrained_primitive_verificator"))

        blocks.append(Stripped("namespace constrained_primitive_verification {"))

        for constrained_primitive in symbol_table.constrained_primitives:
            blocks.extend(
                _generate_constrained_primitive_verification(
                    constrained_primitive=constrained_primitive
                )
            )

        blocks.append(Stripped("}  // namespace constrained_primitive_verification"))

        for constrained_primitive in symbol_table.constrained_primitives:
            blocks.append(
                _generate_implementation_of_verify_constrained_primitive(
                    constrained_primitive=constrained_primitive
                )
            )

        blocks.append(Stripped("// endregion Verification of constrained primitives"))

    blocks.extend(
        [
            _generate_new_non_recursive_verificator_definition(),
            Stripped("// region Non-recursive verificators"),
            Stripped("namespace non_recursive_verificator {"),
        ]
    )

    for cls in symbol_table.concrete_classes:
        invariant_environment = intermediate_type_inference.MutableEnvironment(
            parent=base_environment
        )

        assert invariant_environment.find(Identifier("self")) is None
        invariant_environment.set(
            identifier=Identifier("self"),
            type_annotation=intermediate_type_inference.OurTypeAnnotation(our_type=cls),
        )

        verificator_qualities = VerificatorQualities(cls=cls)

        nrv_blocks, nrv_error = _generate_non_recursive_verificator(
            verificator_qualities=verificator_qualities,
            symbol_table=symbol_table,
            environment=invariant_environment,
        )
        if nrv_error is not None:
            errors.append(nrv_error)
        else:
            assert nrv_blocks is not None
            blocks.extend(nrv_blocks)

    blocks.append(Stripped("}  // namespace non_recursive_verificator"))

    blocks.extend(
        [
            _generate_new_non_recursive_verificator_implementation(
                symbol_table=symbol_table
            ),
            Stripped("// endregion Non-recursive verificators"),
            Stripped("// region Recursive verificators"),
        ]
    )

    blocks.extend(
        [
            *_generate_recursive_verificator(),
            Stripped("// endregion Recursive verificators"),
            *_generate_non_recursive_verification(),
            *_generate_recursive_verification(),
            *_generate_iterator_implementation(),
        ]
    )

    if len(errors) > 0:
        return None, errors

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
