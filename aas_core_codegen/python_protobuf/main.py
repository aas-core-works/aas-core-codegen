"""Generate the code for conversion from and to Protocol Buffers."""

import io
import os
import pathlib
from typing import Tuple, Optional, List, TextIO

from icontract import ensure, require

import aas_core_codegen.python.common as python_common
import aas_core_codegen.python.description as python_description
import aas_core_codegen.python.naming as python_naming
import aas_core_codegen.python_protobuf
from aas_core_codegen import intermediate, run, specific_implementations
from aas_core_codegen.common import (
    Error,
    Stripped,
    assert_never,
    Identifier,
    indent_but_first_line,
)
from aas_core_codegen.python.common import INDENT as I, INDENT2 as II, INDENT3 as III
from aas_core_codegen.python_protobuf import naming as python_protobuf_naming

assert aas_core_codegen.python_protobuf.__doc__ == __doc__


# region From-protobuf


def _generate_from_pb_for_enum(
    enum: intermediate.Enumeration, aas_pb_module: python_common.QualifiedModuleName
) -> List[Stripped]:
    """
    Generate the code to convert an enum back from a protocol buffer.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    literal_to_literal_items = []  # type: List[str]

    py_enum_name = python_naming.enum_name(enum.name)
    pb_enum_name = python_protobuf_naming.enum_name(enum.name)

    for literal in enum.literals:
        py_literal_name = python_naming.enum_literal_name(literal.name)
        pb_constant_name = python_protobuf_naming.enum_literal_constant_name(
            enumeration_name=enum.name, literal_name=literal.name
        )

        literal_to_literal_items.append(
            f"types_pb.{pb_enum_name}.{pb_constant_name}:\n"
            f"{I}types.{py_enum_name}.{py_literal_name}"
        )

    literal_to_literal_items_joined = ",\n".join(literal_to_literal_items)

    map_name = python_naming.private_constant_name(
        Identifier(f"{enum.name}_from_pb_map")
    )

    func_name = python_naming.function_name(Identifier(f"{enum.name}_from_pb"))

    if len(enum.literals) > 0:
        first_literal = enum.literals[0]
        first_literal_pb_constant = python_protobuf_naming.enum_literal_constant_name(
            enumeration_name=enum.name, literal_name=first_literal.name
        )
        first_literal_py_name = python_naming.enum_literal_name(first_literal.name)

        docstring = Stripped(
            f"""\
Parse ``that`` enum back from its Protocol Buffer representation.

>>> import {aas_pb_module}.types_pb2 as types_pb
>>> from {aas_pb_module}.pbization import {func_name}
>>> {func_name}(
...     types_pb.{pb_enum_name}.{first_literal_pb_constant}
... )
<{py_enum_name}.{first_literal_py_name}: {first_literal.value!r}>"""
        )
    else:
        docstring = Stripped(
            "Parse ``that`` enum back from its Protocol Buffer representation."
        )

    quoted_docstring = python_description.docstring(docstring)

    return [
        Stripped(
            f"""\
# fmt: off
{map_name} = {{
{I}{indent_but_first_line(literal_to_literal_items_joined, I)}
}}  # type: Mapping[types_pb.{pb_enum_name}, types.{py_enum_name}]
# fmt: on"""
        ),
        Stripped(
            f"""\
def {func_name}(
{I}that: types_pb.{pb_enum_name}
) -> types.{py_enum_name}:
{I}{indent_but_first_line(quoted_docstring, I)}
{I}return {map_name}[that]"""
        ),
    ]


def _determine_function_name_from_pb_for_class(
    cls: intermediate.ClassUnion,
) -> Identifier:
    """Determine from-pb function to use to parse the Protocol Buffer to a class."""
    if len(cls.concrete_descendants) > 0:
        convert_func_name = python_naming.function_name(
            Identifier(f"{cls.name}_from_pb_choice")
        )
    else:
        convert_func_name = python_naming.function_name(
            Identifier(f"{cls.name}_from_pb")
        )

    return convert_func_name


def _generate_concrete_from_pb_for_class(
    cls: intermediate.ConcreteClass, aas_pb_module: python_common.QualifiedModuleName
) -> Stripped:
    """
    Generate the function to convert an instance of ``cls`` back from a Protocol Buffer.

    This function performs explicitly no dispatch and directly converts back properties
    from the Protocol Buffer fields.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    constructor_kwargs = []  # type: List[Stripped]

    assert set(cls.properties_by_name.keys()) == set(
        cls.constructor.arguments_by_name.keys()
    ), "(mristin) We assume that the properties match the constructor arguments."

    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        is_optional = isinstance(
            prop.type_annotation, intermediate.OptionalTypeAnnotation
        )

        pb_prop_name = python_protobuf_naming.property_name(prop.name)
        py_prop_name = python_naming.property_name(prop.name)

        primitive_type = intermediate.try_primitive_type(type_anno)
        if primitive_type is not None:
            if (
                primitive_type is intermediate.PrimitiveType.BOOL
                or primitive_type is intermediate.PrimitiveType.INT
                or primitive_type is intermediate.PrimitiveType.FLOAT
                or primitive_type is intermediate.PrimitiveType.STR
            ):
                constructor_kwargs.append(
                    Stripped(
                        f"""\
{py_prop_name}=(
{I}that.{pb_prop_name}
{I}if that.HasField({pb_prop_name!r})
{I}else None
)"""
                    )
                    if is_optional
                    else Stripped(f"{py_prop_name}=that.{pb_prop_name}")
                )
            elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
                constructor_kwargs.append(
                    Stripped(
                        f"""\
{py_prop_name}=(
{I}bytearray(that.{pb_prop_name})
{I}if that.HasField({pb_prop_name!r})
{I}else None
)"""
                    )
                    if is_optional
                    else Stripped(f"{py_prop_name}=bytearray(that.{pb_prop_name})")
                )
            else:
                assert_never(primitive_type)

        else:
            if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
                raise AssertionError("Expected to be handled before")

            elif isinstance(type_anno, intermediate.OurTypeAnnotation):
                if isinstance(type_anno.our_type, intermediate.Enumeration):
                    convert_func_name = python_naming.function_name(
                        Identifier(f"{type_anno.our_type.name}_from_pb")
                    )

                    constructor_kwargs.append(
                        Stripped(
                            f"""\
{py_prop_name}=(
{I}{convert_func_name}(
{II}that.{pb_prop_name}
{I})
{I}if that.HasField({pb_prop_name!r})
{I}else None
)"""
                        )
                        if is_optional
                        else Stripped(
                            f"""\
{py_prop_name}={convert_func_name}(
{I}that.{pb_prop_name}
)"""
                        )
                    )

                elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                    raise AssertionError("Expected to be handled before")

                elif isinstance(
                    type_anno.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ):
                    convert_func_name = _determine_function_name_from_pb_for_class(
                        cls=type_anno.our_type
                    )

                    constructor_kwargs.append(
                        Stripped(
                            f"""\
{py_prop_name}=(
{I}{convert_func_name}(
{II}that.{pb_prop_name}
{I})
{I}if that.HasField({pb_prop_name!r})
{I}else None
)"""
                        )
                        if is_optional
                        else Stripped(
                            f"""\
{py_prop_name}={convert_func_name}(
{I}that.{pb_prop_name}
)"""
                        )
                    )

                else:
                    assert_never(type_anno.our_type)

            elif isinstance(type_anno, intermediate.ListTypeAnnotation):
                assert isinstance(
                    type_anno.items, intermediate.OurTypeAnnotation
                ) and isinstance(
                    type_anno.items.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ), (
                    f"NOTE (mristin): We expect only lists of classes "
                    f"at the moment, but you specified {type_anno}. "
                    f"Please contact the developers if you need this feature."
                )

                convert_func_name = _determine_function_name_from_pb_for_class(
                    cls=type_anno.items.our_type
                )

                # NOTE (mristin):
                # Protocol Buffers 3 do not support ``HasField`` on repeated fields,
                # see: https://github.com/protocolbuffers/protobuf/issues/10489
                #
                # We decide here to interpret empty repeated list containers as None
                # if the model property is optional, and as an empty list if the model
                # property is required.
                constructor_kwargs.append(
                    Stripped(
                        f"""\
{py_prop_name}=(
{I}list(map(
{II}{convert_func_name},
{II}that.{pb_prop_name}
{I}))
{I}if len(that.{pb_prop_name}) > 0
{I}else None
)"""
                    )
                    if is_optional
                    else Stripped(
                        f"""\
{py_prop_name}=list(map(
{I}{convert_func_name},
{I}that.{pb_prop_name}
))"""
                    )
                )
            else:
                assert_never(type_anno)

    func_name = python_naming.function_name(Identifier(f"{cls.name}_from_pb"))

    pb_cls_name = python_protobuf_naming.class_name(cls.name)
    py_cls_name = python_naming.class_name(cls.name)

    constructor_kwargs_joined = ",\n".join(constructor_kwargs)

    py_var = python_naming.variable_name(cls.name)
    pb_var = python_naming.variable_name(Identifier(cls.name + "_pb"))

    return Stripped(
        f'''\
def {func_name}(
{I}that: types_pb.{pb_cls_name}
) -> types.{py_cls_name}:
{I}"""
{I}Parse ``that`` Protocol Buffer to an instance of a concrete class.

{I}Example usage:

{I}.. code-block::

{II}import {aas_pb_module}.types_pb2 as types_pb
{II}from {aas_pb_module}.pbization import {func_name}

{II}some_bytes = b'... serialized types_pb.{pb_cls_name} ...'
{II}{pb_var} = types_pb.{pb_cls_name}()
{II}{pb_var}.FromString(
{III}some_bytes
{II})

{II}{py_var} = {func_name}(
{III}{pb_var}
{II})
{II}# Do something with the {py_var}...

{I}"""
{I}return types.{py_cls_name}(
{II}{indent_but_first_line(constructor_kwargs_joined, II)}
{I})'''
    )


@require(
    lambda cls: len(cls.concrete_descendants) > 0,
    "Dispatch only possible with concrete descendants.",
)
def _generate_from_pb_for_class_choice(
    cls: intermediate.ClassUnion, aas_pb_module: python_common.QualifiedModuleName
) -> List[Stripped]:
    """
    Generate the function to parse an instance of ``cls`` where a dispatch is necessary.

    If the class has concrete descendants, the generated function needs to determine
    the concrete runtime type of the Protocol Buffer, and dispatch it to
    the corresponding concrete from-pb function.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    blocks = []  # type: List[Stripped]

    # region Dispatch map
    items = []  # type: List[Stripped]

    concrete_classes = []  # type: List[intermediate.ConcreteClass]
    if isinstance(cls, intermediate.ConcreteClass):
        concrete_classes.append(cls)

    concrete_classes.extend(cls.concrete_descendants)

    for concrete_cls in concrete_classes:
        pb_which_one_of = python_protobuf_naming.property_name(concrete_cls.name)

        concrete_from_pb_name = python_naming.function_name(
            Identifier(f"{concrete_cls.name}_from_pb")
        )

        property_name = python_protobuf_naming.property_name(concrete_cls.name)

        items.append(
            Stripped(
                f"""\
{pb_which_one_of!r}:
{I}lambda that: {concrete_from_pb_name}(
{II}that.{property_name}
{I})"""
            )
        )

    map_name = python_naming.private_constant_name(
        Identifier(f"{cls.name}_from_pb_choice_map")
    )

    items_joined = ",\n".join(items)
    blocks.append(
        Stripped(
            f"""\
# fmt: off
{map_name} = {{
{I}{indent_but_first_line(items_joined, I)}
}}
# fmt: on"""
        )
    )

    # endregion Dispatch map

    # region Function

    pb_cls_name = python_protobuf_naming.choice_class_name(cls.name)

    func_name = python_naming.function_name(Identifier(f"{cls.name}_from_pb_choice"))

    py_cls_name = python_naming.class_name(cls.name)

    pb_var = python_naming.variable_name(Identifier(cls.name + "_choice_pb"))
    py_var = python_naming.variable_name(cls.name)

    blocks.append(
        Stripped(
            f'''\
def {func_name}(
{I}that: types_pb.{pb_cls_name}
) -> types.{py_cls_name}:
{I}"""
{I}Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

{I}Example usage:

{I}.. code-block::

{II}import {aas_pb_module}.types_pb2 as types_pb
{II}from {aas_pb_module}.pbization import {func_name}

{II}some_bytes = b'... serialized types_pb.{pb_cls_name} ...'
{II}{pb_var} = types_pb.{pb_cls_name}()
{II}{pb_var}.FromString(
{III}some_bytes
{II})

{II}{py_var} = {func_name}(
{III}{pb_var}
{II})
{II}# Do something with the {py_var}...
{I}"""
{I}get_concrete_instance_from_pb = (
{II}{map_name}[
{III}that.WhichOneof("value")
{II}]
{I})

{I}result = get_concrete_instance_from_pb(that)  # type: ignore

{I}assert isinstance(result, types.{py_cls_name})
{I}return result'''
        )
    )

    return blocks


def _generate_general_from_pb(
    symbol_table: intermediate.SymbolTable,
    aas_pb_module: python_common.QualifiedModuleName,
) -> List[Stripped]:
    """
    Generate the parsing from a Protocol Buffer based on its runtime type.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    map_items = []  # type: List[Stripped]
    for cls in symbol_table.classes:
        if len(cls.concrete_descendants) > 0:
            pb_cls_name = python_protobuf_naming.choice_class_name(cls.name)

            from_pb_func = python_naming.function_name(
                Identifier(f"{cls.name}_from_pb_choice")
            )
        else:
            pb_cls_name = python_protobuf_naming.class_name(cls.name)

            from_pb_func = python_naming.function_name(
                Identifier(f"{cls.name}_from_pb")
            )

        map_items.append(
            Stripped(
                f"""\
types_pb.{pb_cls_name}:
{I}{from_pb_func}"""
            )
        )

    map_items_joined = ",\n".join(map_items)

    # NOTE (mristin):
    # We had to put this message outside since black formatter struggled with it. This
    # is most probably a bug in the black formatter.
    key_class_not_found_message = '''\
f"We do not know how to parse the protocol buffer "
f"of type {that.__class__} into a model instance."'''

    first_cls_name = symbol_table.concrete_classes[0].name
    pb_first_cls_name = python_protobuf_naming.class_name(first_cls_name)

    return [
        Stripped(
            f"""\
# fmt: off
_FROM_PB_MAP = {{
{I}{indent_but_first_line(map_items_joined, I)}
}}
# fmt: on"""
        ),
        Stripped(
            f'''\
def from_pb(
{I}that: google.protobuf.message.Message
) -> types.Class:
{I}"""
{I}Parse ``that`` Protocol Buffer into a model instance.

{I}The concrete parsing is determined based on the runtime type of ``that``
{I}Protocol Buffer. It is assumed that ``that`` is an instance of a message
{I}coming from the Protocol Buffer definitions corresponding to the meta-model.

{I}Example usage:

{I}.. code-block::

{II}import {aas_pb_module}.types_pb2 as types_pb
{II}from {aas_pb_module}.pbization import from_pb

{II}some_bytes = b'... serialized types_pb.{pb_first_cls_name} ...'
{II}instance_pb = types_pb.{pb_first_cls_name}()
{II}instance_pb.FromString(
{III}some_bytes
{II})

{II}instance = from_pb(
{III}instance_pb
{II})
{II}# Do something with the instance...
{I}"""
{I}from_pb_func = _FROM_PB_MAP.get(that.__class__, None)

{I}if from_pb_func is None:
{II}raise ValueError(
{III}{indent_but_first_line(key_class_not_found_message, III)}
{II})

{I}result = from_pb_func(that)  # type: ignore
{I}assert isinstance(result, types.Class)
{I}return result'''
        ),
    ]


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_from_pb(
    symbol_table: intermediate.SymbolTable,
    aas_pb_module: python_common.QualifiedModuleName,
) -> Tuple[Optional[List[Stripped]], Optional[List[Error]]]:
    """
    Generate all the code for the conversion from protocol buffers.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    blocks = []  # type: List[Stripped]
    errors = []  # type: List[Error]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            blocks.extend(
                _generate_from_pb_for_enum(enum=our_type, aas_pb_module=aas_pb_module)
            )

        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin):
            # We do not represent constrained primitives in Protocol Buffer types.
            pass

        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if len(our_type.concrete_descendants) > 0:
                blocks.extend(
                    _generate_from_pb_for_class_choice(
                        cls=our_type, aas_pb_module=aas_pb_module
                    )
                )

            if isinstance(our_type, intermediate.ConcreteClass):
                blocks.append(
                    _generate_concrete_from_pb_for_class(
                        cls=our_type, aas_pb_module=aas_pb_module
                    )
                )

        else:
            assert_never(our_type)

    blocks.extend(
        _generate_general_from_pb(
            symbol_table=symbol_table, aas_pb_module=aas_pb_module
        )
    )

    if len(errors) > 0:
        return None, errors

    return blocks, None


# endregion


# region To-protobuf


def _generate_partial_visitor(symbol_table: intermediate.SymbolTable) -> Stripped:
    """Generate the transformer where all methods return assertion errors."""
    methods = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        method_name = python_naming.method_name(
            Identifier(f"visit_{cls.name}_with_context")
        )

        cls_name = python_naming.class_name(cls.name)

        methods.append(
            Stripped(
                f"""\
def {method_name}(
{I}self,
{I}that: types.{cls_name},
{I}context: T
) -> None:
{I}raise AssertionError(f"Unexpected visitation of {{that.__class__}}")"""
            )
        )
    body = "\n\n".join(methods)
    return Stripped(
        f'''\
class _PartialVisitorWithContext(types.AbstractVisitorWithContext[T]):
{I}"""
{I}Visit instances in context with double-dispatch.

{I}This class is meant to be inherited from. If you do not override a method,
{I}it will raise an exception. This is a partial visitor, meaning that some
{I}visits are unexpected by design.
{I}"""
{I}# pylint: disable=missing-docstring

{I}{indent_but_first_line(body, I)}'''
    )


def _generate_to_pb_for_enum(
    enum: intermediate.Enumeration,
    aas_module: python_common.QualifiedModuleName,
    aas_pb_module: python_common.QualifiedModuleName,
) -> List[Stripped]:
    """
    Generate the code to convert an enum to a protocol buffer.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    literal_to_literal_items = []  # type: List[str]

    py_enum_name = python_naming.enum_name(enum.name)
    pb_enum_name = python_protobuf_naming.enum_name(enum.name)

    for literal in enum.literals:
        py_literal_name = python_naming.enum_literal_name(literal.name)
        pb_constant_name = python_protobuf_naming.enum_literal_constant_name(
            enumeration_name=enum.name, literal_name=literal.name
        )

        literal_to_literal_items.append(
            f"types.{py_enum_name}.{py_literal_name}:\n"
            f"{I}types_pb.{pb_enum_name}.{pb_constant_name}"
        )

    literal_to_literal_items_joined = ",\n".join(literal_to_literal_items)

    map_name = python_naming.private_constant_name(Identifier(f"{enum.name}_to_pb_map"))

    func_name = python_naming.function_name(Identifier(f"{enum.name}_to_pb"))

    if len(enum.literals) > 0:
        first_literal = enum.literals[0]
        first_literal_py_name = python_naming.enum_literal_name(first_literal.name)

        docstring = Stripped(
            f"""\
Convert ``that`` enum to its Protocol Buffer representation.

>>> from {aas_pb_module}.pbization import {func_name}
>>> import {aas_module}.types as types
>>> {func_name}(
...     types.{py_enum_name}.{first_literal_py_name}
... )
1"""
        )
    else:
        docstring = Stripped(
            "Convert ``that`` enum to its Protocol Buffer representation."
        )

    quoted_docstring = python_description.docstring(docstring)

    return [
        Stripped(
            f"""\
# fmt: off
{map_name} = {{
{I}{indent_but_first_line(literal_to_literal_items_joined, I)}
}}  # type: Mapping[types.{py_enum_name}, types_pb.{pb_enum_name}]
# fmt: on"""
        ),
        Stripped(
            f"""\
def {func_name}(
{I}that: types.{py_enum_name}
) -> types_pb.{pb_enum_name}:
{I}{indent_but_first_line(quoted_docstring, I)}
{I}return {map_name}[that]"""
        ),
    ]


def _generate_concrete_to_pb_for_class(
    cls: intermediate.ConcreteClass,
    aas_module: python_common.QualifiedModuleName,
    aas_pb_module: python_common.QualifiedModuleName,
) -> Stripped:
    """
    Generate the code to convert an instance to a protocol buffer without dispatch.

    There are two situations when this generated function will be called:

    1) ``cls`` is a concrete class without descendants (no dispatch necessary), and
    2) ``cls`` is a concrete class with descendants. In this case, we will dispatch
       to this generated function if the runtime type equals exactly ``cls``.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    set_blocks = []  # type: List[Stripped]

    for prop in cls.properties:
        type_anno = intermediate.beneath_optional(prop.type_annotation)

        py_prop_name = python_naming.property_name(prop.name)
        pb_prop_name = python_protobuf_naming.property_name(prop.name)

        set_block: Stripped

        primitive_type = intermediate.try_primitive_type(type_anno)
        if primitive_type is not None:
            if (
                primitive_type is intermediate.PrimitiveType.BOOL
                or primitive_type is intermediate.PrimitiveType.INT
                or primitive_type is intermediate.PrimitiveType.FLOAT
                or primitive_type is intermediate.PrimitiveType.STR
            ):
                set_block = Stripped(f"target.{pb_prop_name} = that.{py_prop_name}")

            elif primitive_type is intermediate.PrimitiveType.BYTEARRAY:
                set_block = Stripped(
                    f"target.{pb_prop_name} = bytes(that.{py_prop_name})"
                )

            else:
                assert_never(primitive_type)
        else:
            if isinstance(type_anno, intermediate.PrimitiveTypeAnnotation):
                raise AssertionError("Expected to be handled before")

            elif isinstance(type_anno, intermediate.OurTypeAnnotation):
                if isinstance(type_anno.our_type, intermediate.Enumeration):
                    to_pb_func_for_enum = python_naming.function_name(
                        Identifier(f"{type_anno.our_type.name}_to_pb")
                    )

                    set_block = Stripped(
                        f"""\
target.{pb_prop_name} = {to_pb_func_for_enum}(
{I}that.{py_prop_name}
)"""
                    )

                elif isinstance(type_anno.our_type, intermediate.ConstrainedPrimitive):
                    raise AssertionError("Expected to be handled before")

                elif isinstance(
                    type_anno.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ):
                    if len(type_anno.our_type.concrete_descendants) > 0:
                        to_pb_choice_func = python_naming.function_name(
                            Identifier(f"{type_anno.our_type.name}_to_pb_choice")
                        )

                        set_block = Stripped(
                            f"""\
{to_pb_choice_func}(
{I}that.{py_prop_name},
{I}target.{pb_prop_name}
)"""
                        )
                    else:
                        to_pb_func = python_naming.function_name(
                            Identifier(f"{type_anno.our_type.name}_to_pb")
                        )

                        set_block = Stripped(
                            f"""\
# We clear so that the field is set even if all the properties are None.
target.{pb_prop_name}.Clear()

{to_pb_func}(
{I}that.{py_prop_name},
{I}target.{pb_prop_name}
)"""
                        )

                else:
                    assert_never(type_anno.our_type)

            elif isinstance(type_anno, intermediate.ListTypeAnnotation):
                assert isinstance(
                    type_anno.items, intermediate.OurTypeAnnotation
                ) and isinstance(
                    type_anno.items.our_type,
                    (intermediate.AbstractClass, intermediate.ConcreteClass),
                ), (
                    f"NOTE (mristin): We expect only lists of classes "
                    f"at the moment, but you specified {type_anno}. "
                    f"Please contact the developers if you need this feature."
                )

                if len(type_anno.items.our_type.concrete_descendants) > 0:
                    to_pb_func_for_items_cls = python_naming.function_name(
                        Identifier(f"{type_anno.items.our_type.name}_to_pb_choice")
                    )
                else:
                    to_pb_func_for_items_cls = python_naming.function_name(
                        Identifier(f"{type_anno.items.our_type.name}_to_pb")
                    )

                item_var = python_naming.variable_name(Identifier(f"{prop.name}_item"))
                set_block = Stripped(
                    f"""\
for {item_var} in that.{py_prop_name}:
{I}{item_var}_pb = target.{pb_prop_name}.add()
{I}{to_pb_func_for_items_cls}(
{II}{item_var},
{II}{item_var}_pb)"""
                )

            else:
                assert_never(type_anno)

        if isinstance(prop.type_annotation, intermediate.OptionalTypeAnnotation):
            set_block = Stripped(
                f"""\
if that.{py_prop_name} is not None:
{I}{indent_but_first_line(set_block, I)}"""
            )

        set_blocks.append(set_block)

    func_name = python_naming.function_name(Identifier(f"{cls.name}_to_pb"))

    py_cls_name = python_naming.class_name(cls.name)
    pb_cls_name = python_protobuf_naming.class_name(cls.name)

    set_blocks_joined = "\n\n".join(set_blocks)

    pb_var = python_naming.variable_name(Identifier(cls.name + "_pb"))
    py_var = python_naming.variable_name(cls.name)

    return Stripped(
        f'''\
def {func_name}(
{I}that: types.{py_cls_name},
{I}target: types_pb.{pb_cls_name}
) -> None:
{I}"""
{I}Set fields in ``target`` based on ``that`` instance.

{I}Example usage:

{I}.. code-block::

{II}import {aas_module}.types as types

{II}import {aas_pb_module}.types_pb2 as types_pb
{II}from {aas_pb_module}.pbization import {func_name}

{II}{py_var} = types.{py_cls_name}(
{III}... # some constructor arguments
{II})

{II}{pb_var} = types_pb.{pb_cls_name}()
{II}{func_name}(
{III}{py_var},
{III}{pb_var}
{II})

{II}some_bytes = {pb_var}.SerializeToString()
{II}# Do something with some_bytes. For example, transfer them
{II}# over the wire.
{I}"""
{I}{indent_but_first_line(set_blocks_joined, I)}'''
    )


@require(
    lambda cls: len(cls.concrete_descendants) > 0,
    "Dispatch needs concrete descendants.",
)
def _generate_to_pb_choice(
    cls: intermediate.ClassUnion,
    aas_module: python_common.QualifiedModuleName,
    aas_pb_module: python_common.QualifiedModuleName,
) -> List[Stripped]:
    """
    Generate the code to dispatch the serialization to a concrete serializer.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    blocks = []  # type: List[Stripped]

    pb_choice_cls_name = python_protobuf_naming.choice_class_name(cls.name)

    # region Visitor

    methods = []  # type: List[Stripped]

    concrete_classes = []  # type: List[intermediate.ConcreteClass]
    if isinstance(cls, intermediate.ConcreteClass):
        concrete_classes.append(cls)

    concrete_classes.extend(cls.concrete_descendants)

    for concrete_cls in concrete_classes:
        py_concrete_cls_name = python_naming.class_name(concrete_cls.name)
        pb_property = python_protobuf_naming.property_name(concrete_cls.name)

        conversion_func = python_naming.function_name(
            Identifier(f"{concrete_cls.name}_to_pb")
        )

        method_name = python_naming.method_name(
            Identifier(f"visit_{concrete_cls.name}_with_context")
        )

        methods.append(
            Stripped(
                f'''\
def {method_name}(
{I}self,
{I}that: types.{py_concrete_cls_name},
{I}context: types_pb.{pb_choice_cls_name}
) -> None:
{I}"""
{I}Set the fields of ``context.{pb_property}``
{I}according to ``that`` instance.
{I}"""
{I}{conversion_func}(
{II}that,
{II}context.{pb_property}
{I})'''
            )
        )

    visitor_class_name = python_naming.private_class_name(
        Identifier(f"{cls.name}_to_pb_choice")
    )
    body = "\n\n".join(methods)
    blocks.append(
        Stripped(
            f'''\
class {visitor_class_name}(
{I}_PartialVisitorWithContext[
{II}types_pb.{pb_choice_cls_name}
{I}]
):
{I}"""Set the fields of the corresponding one-of value."""
{I}{indent_but_first_line(body, I)}'''
        )
    )

    visitor_name = python_naming.private_constant_name(
        Identifier(f"{cls.name}_to_pb_choice")
    )
    blocks.append(Stripped(f"{visitor_name} = {visitor_class_name}()"))

    # endregion Visitor

    func_name = python_naming.function_name(Identifier(f"{cls.name}_to_pb_choice"))

    py_cls_name = python_naming.class_name(cls.name)

    py_concrete_descendant_cls_name = python_naming.class_name(
        cls.concrete_descendants[0].name
    )

    py_var = python_naming.variable_name(cls.name)
    pb_var = python_naming.variable_name(Identifier(cls.name + "_choice_pb"))

    blocks.append(
        Stripped(
            f'''\
def {func_name}(
{I}that: types.{py_cls_name},
{I}target: types_pb.{pb_choice_cls_name}
) -> None:
{I}"""
{I}Set the chosen value in ``target`` based on ``that`` instance.

{I}The chosen value in ``target`` is determined based on the runtime type of ``that``
{I}instance. All the fields of the value are recursively set according to ``that``
{I}instance.

{I}Example usage:

{I}.. code-block::

{II}import {aas_module}.types as types

{II}import {aas_pb_module}.types_pb2 as types_pb
{II}from {aas_pb_module}.pbization import {func_name}

{II}{py_var} = types.{py_concrete_descendant_cls_name}(
{III}... # some constructor arguments
{II})

{II}{pb_var} = types_pb.{pb_choice_cls_name}()
{II}{func_name}(
{III}{py_var},
{III}{pb_var}
{II})

{II}some_bytes = {pb_var}.SerializeToString()
{II}# Do something with some_bytes. For example, transfer them
{II}# over the wire.

{I}"""
{I}{visitor_name}.visit_with_context(
{II}that,
{II}target
{I})'''
        )
    )

    return blocks


@require(
    lambda symbol_table: len(symbol_table.concrete_classes) > 0,
    "At least one concrete class in the meta-model expected if you generate "
    "a general to-pb function",
)
def _generate_general_to_pb(
    symbol_table: intermediate.SymbolTable,
    aas_module: python_common.QualifiedModuleName,
    aas_pb_module: python_common.QualifiedModuleName,
) -> List[Stripped]:
    """
    Generate a dispatch to the concrete to-pb function.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    methods = []  # type: List[Stripped]

    for cls in symbol_table.concrete_classes:
        if len(cls.concrete_descendants) > 0:
            conversion_func_name = python_naming.function_name(
                Identifier(f"{cls.name}_to_pb_choice")
            )
            pb_cls_name = python_protobuf_naming.choice_class_name(cls.name)
        else:
            conversion_func_name = python_naming.function_name(
                Identifier(f"{cls.name}_to_pb")
            )
            pb_cls_name = python_protobuf_naming.class_name(cls.name)

        method_name = python_naming.function_name(Identifier(f"transform_{cls.name}"))

        py_cls_name = python_naming.class_name(cls.name)

        methods.append(
            Stripped(
                f'''\
def {method_name}(
{I}self,
{I}that: types.{py_cls_name}
) -> google.protobuf.message.Message:
{I}"""
{I}Convert ``that`` instance
{I}to a :py:class:`types_pb.{pb_cls_name}`.
{I}"""
{I}result = types_pb.{pb_cls_name}()
{I}{conversion_func_name}(that, result)
{I}return result'''
            )
        )

    body = "\n\n".join(methods)

    first_cls = symbol_table.concrete_classes[0]
    py_first_cls_name = python_naming.class_name(first_cls.name)

    return [
        Stripped(
            f'''\
class _ToPbTransformer(
{I}types.AbstractTransformer[google.protobuf.message.Message]
):
{I}"""
{I}Dispatch to-pb conversion to the concrete functions.

{I}The classes with descendants (i.e., subtypes) are always going to be converted
{I}to their concrete Protocol Buffer instead of the choice (union) Protocol Buffer
{I}class. We made this decision with the compactness of messages in mind.
{I}"""
{I}{indent_but_first_line(body, I)}'''
        ),
        Stripped("_TO_PB_TRANSFORMER = _ToPbTransformer()"),
        Stripped(
            f'''\
def to_pb(
{I}that: types.Class,
) -> google.protobuf.message.Message:
{I}"""
{I}Dispatch to-pb conversion to the concrete functions.

{I}The classes with descendants (i.e., subtypes) are always going to be converted
{I}to their concrete Protocol Buffer message type instead of the choice (union) type.
{I}We made this decision with the compactness of messages in mind as choice types
{I}would occupy a tiny bit more space.

{I}Example usage:

{I}.. code-block::

{II}import {aas_module}.types as types

{II}from {aas_pb_module}.pbization import to_pb

{II}instance = types.{py_first_cls_name}(
{III}... # some constructor arguments
{II})

{II}instance_pb = to_pb(
{III}instance
{II})

{II}some_bytes = instance_pb.SerializeToString()
{II}# Do something with some_bytes. For example, transfer them
{II}# over the wire.
{I}"""
{I}return _TO_PB_TRANSFORMER.transform(that)'''
        ),
    ]


@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate_to_pb(
    symbol_table: intermediate.SymbolTable,
    aas_module: python_common.QualifiedModuleName,
    aas_pb_module: python_common.QualifiedModuleName,
) -> Tuple[Optional[List[Stripped]], Optional[List[Error]]]:
    """
    Generate all the code for the conversion to protocol buffers.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    blocks = [
        Stripped('T = TypeVar("T")'),
        _generate_partial_visitor(symbol_table=symbol_table),
    ]  # type: List[Stripped]
    errors = []  # type: List[Error]

    for our_type in symbol_table.our_types:
        if isinstance(our_type, intermediate.Enumeration):
            enum_blocks = _generate_to_pb_for_enum(
                enum=our_type, aas_module=aas_module, aas_pb_module=aas_pb_module
            )
            blocks.extend(enum_blocks)
        elif isinstance(our_type, intermediate.ConstrainedPrimitive):
            # NOTE (mristin):
            # We do not represent constrained primitives in Python types.
            pass
        elif isinstance(
            our_type, (intermediate.AbstractClass, intermediate.ConcreteClass)
        ):
            if len(our_type.concrete_descendants) > 0:
                blocks.extend(
                    _generate_to_pb_choice(
                        cls=our_type, aas_module=aas_module, aas_pb_module=aas_pb_module
                    )
                )

            if isinstance(our_type, intermediate.ConcreteClass):
                blocks.append(
                    _generate_concrete_to_pb_for_class(
                        cls=our_type, aas_module=aas_module, aas_pb_module=aas_pb_module
                    )
                )
        else:
            assert_never(our_type)

    blocks.extend(
        _generate_general_to_pb(
            symbol_table=symbol_table,
            aas_module=aas_module,
            aas_pb_module=aas_pb_module,
        )
    )

    if len(errors) > 0:
        return None, errors

    return blocks, None


# endregion

_THIS_PATH = pathlib.Path(os.path.realpath(__file__))


@ensure(lambda result: not (result[0] is not None) or (result[0].endswith("\n")))
@ensure(lambda result: (result[0] is not None) ^ (result[1] is not None))
def _generate(
    symbol_table: intermediate.SymbolTable,
    spec_impls: specific_implementations.SpecificImplementations,
) -> Tuple[Optional[str], Optional[List[Error]]]:
    """
    Generate the content of the pbization module.

    The ``aas_module`` indicates the fully-qualified name of the base SDK module.

    The ``aas_pb_module`` indicates the fully-qualified name of this base module.
    """
    aas_module_key = specific_implementations.ImplementationKey(
        "base_qualified_module_name.txt"
    )

    aas_module_text = spec_impls.get(aas_module_key, None)
    if aas_module_text is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the base qualified module name "
                f"is missing: {aas_module_key}",
            )
        ]

    if not python_common.QUALIFIED_MODULE_NAME_RE.fullmatch(aas_module_text):
        return None, [
            Error(
                None,
                f"The text from the snippet {aas_module_key} "
                f"is not a valid qualified module name: {aas_module_text!r}\n",
            )
        ]

    aas_module = python_common.QualifiedModuleName(aas_module_text)

    aas_pb_module_key = specific_implementations.ImplementationKey(
        "qualified_module_name_for_protobuf_library.txt"
    )

    aas_pb_module_text = spec_impls.get(aas_pb_module_key, None)
    if aas_pb_module_text is None:
        return None, [
            Error(
                None,
                f"The implementation snippet for the qualified name of the protobuf "
                f"library is missing: {aas_pb_module_key}",
            )
        ]

    if not python_common.QUALIFIED_MODULE_NAME_RE.fullmatch(aas_pb_module_text):
        return None, [
            Error(
                None,
                f"The text from the snippet {aas_pb_module_key} "
                f"is not a valid qualified module name: {aas_pb_module_text!r}\n",
            )
        ]

    aas_pb_module = python_common.QualifiedModuleName(aas_pb_module_text)

    warning = Stripped(
        f"""\
# Automatically generated with {_THIS_PATH.parent.name}/{_THIS_PATH.name}.
# Do NOT edit or append."""
    )

    blocks = [
        warning,
        Stripped('"""Convert instances from and to Protocol Buffers."""'),
        Stripped(
            f"""\
from typing import Mapping, TypeVar

import google.protobuf.message

from {aas_module} import types
import {aas_pb_module}.types_pb2 as types_pb""",
        ),
        Stripped("# region From Protocol Buffers"),
    ]  # type: List[Stripped]

    errors = []  # type: List[Error]

    from_pb_blocks, from_pb_errors = _generate_from_pb(
        symbol_table=symbol_table, aas_pb_module=aas_pb_module
    )
    if from_pb_errors is not None:
        errors.append(
            Error(
                None,
                "Failed to generate one or more from-protobuf conversion",
                underlying=errors,
            )
        )
    else:
        assert from_pb_blocks is not None
        blocks.extend(from_pb_blocks)

    blocks.extend(
        [
            Stripped("# endregion From Protocol Buffers"),
            Stripped("# region To Protocol Buffers"),
        ]
    )

    to_pb_blocks, to_pb_errors = _generate_to_pb(
        symbol_table=symbol_table, aas_module=aas_module, aas_pb_module=aas_pb_module
    )
    if to_pb_errors is not None:
        errors.append(
            Error(
                None,
                "Failed to generate one or more to-protobuf conversion",
                underlying=errors,
            )
        )
    else:
        assert to_pb_blocks is not None
        blocks.extend(to_pb_blocks)

    blocks.append(
        Stripped("# endregion To Protocol Buffers"),
    )

    blocks.append(warning)

    out = io.StringIO()
    for i, block in enumerate(blocks):
        if i > 0:
            out.write("\n\n\n")

        out.write(block)

    out.write("\n")

    return out.getvalue(), None


def execute(
    context: run.Context,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """
    Execute the generation with the given parameters.

    Return the error code, or 0 if no errors.
    """
    code, errors = _generate(
        symbol_table=context.symbol_table, spec_impls=context.spec_impls
    )
    if errors is not None:
        run.write_error_report(
            message=f"Failed to generate the Python-Protobuf library "
            f"based on {context.model_path}",
            errors=[context.lineno_columner.error_message(error) for error in errors],
            stderr=stderr,
        )
        return 1

    assert code is not None

    pth = context.output_dir / "pbization.py"
    try:
        pth.write_text(code, encoding="utf-8")
    except Exception as exception:
        run.write_error_report(
            message=f"Failed to write the Python-Protobuf library to {pth}",
            errors=[str(exception)],
            stderr=stderr,
        )
        return 1

    stdout.write(f"Code generated to: {context.output_dir}\n")

    return 0
