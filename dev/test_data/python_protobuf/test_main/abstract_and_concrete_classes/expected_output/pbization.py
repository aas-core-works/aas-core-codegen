# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.


"""Convert instances from and to Protocol Buffers."""


from typing import Mapping, TypeVar

import google.protobuf.message

from aas_core3 import types
import aas_core3_protobuf.types_pb2 as types_pb


# region From Protocol Buffers


# fmt: off
_SOMETHING_ABSTRACT_FROM_PB_CHOICE_MAP = {
    'another_concrete':
        lambda that: another_concrete_from_pb(
            that.another_concrete
        ),
    'something_concrete':
        lambda that: something_concrete_from_pb(
            that.something_concrete
        )
}
# fmt: on


def something_abstract_from_pb_choice(
    that: types_pb.SomethingAbstract_choice
) -> types.SomethingAbstract:
    """
    Parse ``that`` Protocol Buffer based on its runtime ``WhichOneof``.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_abstract_from_pb_choice

        some_bytes = b'... serialized types_pb.SomethingAbstract_choice ...'
        something_abstract_choice_pb = types_pb.SomethingAbstract_choice()
        something_abstract_choice_pb.FromString(
            some_bytes
        )

        something_abstract = something_abstract_from_pb_choice(
            something_abstract_choice_pb
        )
        # Do something with the something_abstract...
    """
    get_concrete_instance_from_pb = (
        _SOMETHING_ABSTRACT_FROM_PB_CHOICE_MAP[
            that.WhichOneof("value")
        ]
    )

    result = get_concrete_instance_from_pb(that)  # type: ignore

    assert isinstance(result, types.SomethingAbstract)
    return result


def something_concrete_from_pb(
    that: types_pb.SomethingConcrete
) -> types.SomethingConcrete:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_concrete_from_pb

        some_bytes = b'... serialized types_pb.SomethingConcrete ...'
        something_concrete_pb = types_pb.SomethingConcrete()
        something_concrete_pb.FromString(
            some_bytes
        )

        something_concrete = something_concrete_from_pb(
            something_concrete_pb
        )
        # Do something with the something_concrete...

    """
    return types.SomethingConcrete(
        some_str=that.some_str,
        something_str=that.something_str
    )


def another_concrete_from_pb(
    that: types_pb.AnotherConcrete
) -> types.AnotherConcrete:
    """
    Parse ``that`` Protocol Buffer to an instance of a concrete class.

    Example usage:

    .. code-block::

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import another_concrete_from_pb

        some_bytes = b'... serialized types_pb.AnotherConcrete ...'
        another_concrete_pb = types_pb.AnotherConcrete()
        another_concrete_pb.FromString(
            some_bytes
        )

        another_concrete = another_concrete_from_pb(
            another_concrete_pb
        )
        # Do something with the another_concrete...

    """
    return types.AnotherConcrete(
        some_str=that.some_str,
        another_str=that.another_str
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
        something_abstract=something_abstract_from_pb_choice(
            that.something_abstract
        )
    )


# fmt: off
_FROM_PB_MAP = {
    types_pb.SomethingAbstract_choice:
        something_abstract_from_pb_choice,
    types_pb.SomethingConcrete:
        something_concrete_from_pb,
    types_pb.AnotherConcrete:
        another_concrete_from_pb,
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

        some_bytes = b'... serialized types_pb.SomethingConcrete ...'
        instance_pb = types_pb.SomethingConcrete()
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

    def visit_something_concrete_with_context(
        self,
        that: types.SomethingConcrete,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_another_concrete_with_context(
        self,
        that: types.AnotherConcrete,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")

    def visit_container_with_context(
        self,
        that: types.Container,
        context: T
    ) -> None:
        raise AssertionError(f"Unexpected visitation of {that.__class__}")


class _SomethingAbstractToPbChoice(
    _PartialVisitorWithContext[
        types_pb.SomethingAbstract_choice
    ]
):
    """Set the fields of the corresponding one-of value."""
    def visit_another_concrete_with_context(
        self,
        that: types.AnotherConcrete,
        context: types_pb.SomethingAbstract_choice
    ) -> None:
        """
        Set the fields of ``context.another_concrete``
        according to ``that`` instance.
        """
        another_concrete_to_pb(
            that,
            context.another_concrete
        )

    def visit_something_concrete_with_context(
        self,
        that: types.SomethingConcrete,
        context: types_pb.SomethingAbstract_choice
    ) -> None:
        """
        Set the fields of ``context.something_concrete``
        according to ``that`` instance.
        """
        something_concrete_to_pb(
            that,
            context.something_concrete
        )


_SOMETHING_ABSTRACT_TO_PB_CHOICE = _SomethingAbstractToPbChoice()


def something_abstract_to_pb_choice(
    that: types.SomethingAbstract,
    target: types_pb.SomethingAbstract_choice
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
        from aas_core3_protobuf.pbization import something_abstract_to_pb_choice

        something_abstract = types.AnotherConcrete(
            ... # some constructor arguments
        )

        something_abstract_choice_pb = types_pb.SomethingAbstract_choice()
        something_abstract_to_pb_choice(
            something_abstract,
            something_abstract_choice_pb
        )

        some_bytes = something_abstract_choice_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.

    """
    _SOMETHING_ABSTRACT_TO_PB_CHOICE.visit_with_context(
        that,
        target
    )


def something_concrete_to_pb(
    that: types.SomethingConcrete,
    target: types_pb.SomethingConcrete
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import something_concrete_to_pb

        something_concrete = types.SomethingConcrete(
            ... # some constructor arguments
        )

        something_concrete_pb = types_pb.SomethingConcrete()
        something_concrete_to_pb(
            something_concrete,
            something_concrete_pb
        )

        some_bytes = something_concrete_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.some_str = that.some_str

    target.something_str = that.something_str


def another_concrete_to_pb(
    that: types.AnotherConcrete,
    target: types_pb.AnotherConcrete
) -> None:
    """
    Set fields in ``target`` based on ``that`` instance.

    Example usage:

    .. code-block::

        import aas_core3.types as types

        import aas_core3_protobuf.types_pb2 as types_pb
        from aas_core3_protobuf.pbization import another_concrete_to_pb

        another_concrete = types.AnotherConcrete(
            ... # some constructor arguments
        )

        another_concrete_pb = types_pb.AnotherConcrete()
        another_concrete_to_pb(
            another_concrete,
            another_concrete_pb
        )

        some_bytes = another_concrete_pb.SerializeToString()
        # Do something with some_bytes. For example, transfer them
        # over the wire.
    """
    target.some_str = that.some_str

    target.another_str = that.another_str


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
    something_abstract_to_pb_choice(
        that.something_abstract,
        target.something_abstract
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
    def transform_something_concrete(
        self,
        that: types.SomethingConcrete
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.SomethingConcrete`.
        """
        result = types_pb.SomethingConcrete()
        something_concrete_to_pb(that, result)
        return result

    def transform_another_concrete(
        self,
        that: types.AnotherConcrete
    ) -> google.protobuf.message.Message:
        """
        Convert ``that`` instance
        to a :py:class:`types_pb.AnotherConcrete`.
        """
        result = types_pb.AnotherConcrete()
        another_concrete_to_pb(that, result)
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

        instance = types.SomethingConcrete(
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
