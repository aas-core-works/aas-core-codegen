# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.


"""Convert instances from and to Protocol Buffers."""


from typing import Mapping, TypeVar

import google.protobuf.message

from aas_core3 import types
import aas_core3_protobuf.types_pb2 as types_pb


# region From Protocol Buffers


def something_from_pb(
    that: types_pb.Something
) -> types.Something:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_from_pb

        some_bytes = b'... serialized types_pb.Something ...'
        something_pb = types_pb.Something()
        something_pb.FromString(
            some_bytes
        )

        something = something_from_pb(
            something_pb
        )
        # Do something with the something...

    """
    return types.Something(
        some_bool=that.some_bool,
        some_int=that.some_int,
        some_float=that.some_float,
        some_str=that.some_str,
        some_byte_array=bytearray(that.some_byte_array),
        some_optional_bool=(
            that.some_optional_bool
            if that.HasField('some_optional_bool')
            else None
        ),
        some_optional_int=(
            that.some_optional_int
            if that.HasField('some_optional_int')
            else None
        ),
        some_optional_float=(
            that.some_optional_float
            if that.HasField('some_optional_float')
            else None
        ),
        some_optional_str=(
            that.some_optional_str
            if that.HasField('some_optional_str')
            else None
        ),
        some_optional_byte_array=(
            bytearray(that.some_optional_byte_array)
            if that.HasField('some_optional_byte_array')
            else None
        )
    )


# fmt: off
_FROM_PB_MAP = {
    types_pb.Something:
        something_from_pb
}
# fmt: on


def from_pb(
    that: google.protobuf.message.Message
) -> types.Class:
    """
    Parse ``that`` Protocol Buffer into a model instance.

    The concrete parsing is determined based on the runtime type of ``that``
    Protocol Buffer. It is assumed that ``that`` is an instance of a message
    coming from the Protocol Buffer definitions corresponding to the meta-model.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import from_pb

        some_bytes = b'... serialized types_pb.Something ...'
        instance_pb = types_pb.Something()
        instance_pb.FromString(
            some_bytes
        )

        instance = from_pb(
            instance_pb
        )
        # Do something with the instance...
    """
    from_pb_func = _FROM_PB_MAP.get(that.__class__, None)

    if from_pb_func is None:
        raise ValueError(
            f"We do not know how to parse the protocol buffer "
            f"of type {that.__class__} into a model instance."
        )

    result = from_pb_func(that)  # type: ignore
    assert isinstance(result, types.Class)
    return result


# endregion From Protocol Buffers


# region To Protocol Buffers


T = TypeVar("T")


class _PartialVisitorWithContext(types.AbstractVisitorWithContext[T]):
    """
    Visit instances in context with double-dispatch.

    This class is meant to be inherited from. If you do not override a method,
    it will raise an exception. This is a partial visitor, meaning that some
    visits are unexpected by design.
    """
    # pylint: disable=missing-docstring

    def visit_something_with_context(
        self,
        that: types.Something,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")


def something_to_pb(
    that: types.Something,
    target: types_pb.Something
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_to_pb

        something = types.Something(
            ... # some constructor arguments
        )

        something_pb = types_pb.Something()
        something_to_pb(
            something,
            something_pb
        )

        some_bytes = something_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.some_bool = that.some_bool

    target.some_int = that.some_int

    target.some_float = that.some_float

    target.some_str = that.some_str

    target.some_byte_array = bytes(that.some_byte_array)

    if that.some_optional_bool is not None:
        target.some_optional_bool = that.some_optional_bool

    if that.some_optional_int is not None:
        target.some_optional_int = that.some_optional_int

    if that.some_optional_float is not None:
        target.some_optional_float = that.some_optional_float

    if that.some_optional_str is not None:
        target.some_optional_str = that.some_optional_str

    if that.some_optional_byte_array is not None:
        target.some_optional_byte_array = bytes(that.some_optional_byte_array)


class _ToPbTransformer(
    types.AbstractTransformer[google.protobuf.message.Message]
):
    """
    Dispatch to-pb conversion to the concrete functions.

    The classes with descendants (i.e., subtypes) are always going to be converted
    to their concrete Protocol Buffer instead of the choice (union) Protocol Buffer
    class. We made this decision with the compactness of messages in mind.
    """
    def transform_something(
        self,
        that: types.Something
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Something`.
        """
        result = types_pb.Something()
        something_to_pb(that, result)
        return result


_TO_PB_TRANSFORMER = _ToPbTransformer()


def to_pb(
    that: types.Class,
) -> google.protobuf.message.Message:
    """
    Dispatch to-pb conversion to the concrete functions.

    The classes with descendants (i.e., subtypes) are always going to be converted
    to their concrete Protocol Buffer message type instead of the choice (union) type.
    We made this decision with the compactness of messages in mind as choice types
    would occupy a tiny bit more space.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        from aas_core3_protobuf.pbization import to_pb

        instance = types.Something(
            ... # some constructor arguments
        )

        instance_pb = to_pb(
            instance
        )

        some_bytes = instance_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    return _TO_PB_TRANSFORMER.transform(that)


# endregion To Protocol Buffers


# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.
