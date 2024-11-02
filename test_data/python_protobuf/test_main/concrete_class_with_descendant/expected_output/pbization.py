# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.


"""Convert instances from and to Protocol Buffers."""


from typing import Mapping, TypeVar

import google.protobuf.message

from aas_core3 import types
import aas_core3_protobuf.types_pb2 as types_pb


# region From Protocol Buffers


# fmt: off
_SOMETHING_FROM_PB_CHOICE_MAP = {
    'something':
        lambda that: something_from_pb(
            that.something
        ),
    'something_more_concrete':
        lambda that: something_more_concrete_from_pb(
            that.something_more_concrete
        )
}
# fmt: on


def something_from_pb_choice(
    that: types_pb.Something_choice
) -> types.Something:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_from_pb_choice

        some_bytes = b'... serialized types_pb.Something_choice ...'
        something_choice_pb = types_pb.Something_choice()
        something_choice_pb.FromString(
            some_bytes
        )

        something = something_from_pb_choice(
            something_choice_pb
        )
        # Do something with the something...
    """
    get_concrete_instance_from_pb = (
        _SOMETHING_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.Something)
    return result


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
        some_str=that.some_str
    )


def something_more_concrete_from_pb(
    that: types_pb.SomethingMoreConcrete
) -> types.SomethingMoreConcrete:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_more_concrete_from_pb

        some_bytes = b'... serialized types_pb.SomethingMoreConcrete ...'
        something_more_concrete_pb = types_pb.SomethingMoreConcrete()
        something_more_concrete_pb.FromString(
            some_bytes
        )

        something_more_concrete = something_more_concrete_from_pb(
            something_more_concrete_pb
        )
        # Do something with the something_more_concrete...

    """
    return types.SomethingMoreConcrete(
        some_str=that.some_str,
        some_more_concrete_str=that.some_more_concrete_str
    )


def container_from_pb(
    that: types_pb.Container
) -> types.Container:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import container_from_pb

        some_bytes = b'... serialized types_pb.Container ...'
        container_pb = types_pb.Container()
        container_pb.FromString(
            some_bytes
        )

        container = container_from_pb(
            container_pb
        )
        # Do something with the container...

    """
    return types.Container(
        something=something_from_pb_choice(
            that.something
        )
    )


# fmt: off
_FROM_PB_MAP = {
    types_pb.Something_choice:
        something_from_pb_choice,
    types_pb.SomethingMoreConcrete:
        something_more_concrete_from_pb,
    types_pb.Container:
        container_from_pb
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

    def visit_something_more_concrete_with_context(
        self,
        that: types.SomethingMoreConcrete,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_container_with_context(
        self,
        that: types.Container,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")


class _SomethingToPbChoice(
    _PartialVisitorWithContext[
        types_pb.Something_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_something_with_context(
        self,
        that: types.Something,
        context: types_pb.Something_choice
    ) -> None:
        """
        Set the fields of ``context.something``
        according to ``that`` instance.
        """
        something_to_pb(
            that,
            context.something
        )

    def visit_something_more_concrete_with_context(
        self,
        that: types.SomethingMoreConcrete,
        context: types_pb.Something_choice
    ) -> None:
        """
        Set the fields of ``context.something_more_concrete``
        according to ``that`` instance.
        """
        something_more_concrete_to_pb(
            that,
            context.something_more_concrete
        )


_SOMETHING_TO_PB_CHOICE = _SomethingToPbChoice()


def something_to_pb_choice(
    that: types.Something,
    target: types_pb.Something_choice
) -> None:
    """
    Set the chosen value in ``target`` based on ``that`` instance.

    The chosen value in ``target`` is determined based on the runtime type of ``that``
    instance. All the fields of the value are recursively set according to ``that``
    instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_to_pb_choice

        something = types.SomethingMoreConcrete(
            ... # some constructor arguments
        )

        something_choice_pb = types_pb.Something_choice()
        something_to_pb_choice(
            something,
            something_choice_pb
        )

        some_bytes = something_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _SOMETHING_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


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
    target.some_str = that.some_str


def something_more_concrete_to_pb(
    that: types.SomethingMoreConcrete,
    target: types_pb.SomethingMoreConcrete
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_more_concrete_to_pb

        something_more_concrete = types.SomethingMoreConcrete(
            ... # some constructor arguments
        )

        something_more_concrete_pb = types_pb.SomethingMoreConcrete()
        something_more_concrete_to_pb(
            something_more_concrete,
            something_more_concrete_pb
        )

        some_bytes = something_more_concrete_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.some_str = that.some_str

    target.some_more_concrete_str = that.some_more_concrete_str


def container_to_pb(
    that: types.Container,
    target: types_pb.Container
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import container_to_pb

        container = types.Container(
            ... # some constructor arguments
        )

        container_pb = types_pb.Container()
        container_to_pb(
            container,
            container_pb
        )

        some_bytes = container_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    something_to_pb_choice(
        that.something,
        target.something
    )


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
        to a :py:class:`types_pb.Something_choice`.
        """
        result = types_pb.Something_choice()
        something_to_pb_choice(that, result)
        return result

    def transform_something_more_concrete(
        self,
        that: types.SomethingMoreConcrete
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.SomethingMoreConcrete`.
        """
        result = types_pb.SomethingMoreConcrete()
        something_more_concrete_to_pb(that, result)
        return result

    def transform_container(
        self,
        that: types.Container
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.Container`.
        """
        result = types_pb.Container()
        container_to_pb(that, result)
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
