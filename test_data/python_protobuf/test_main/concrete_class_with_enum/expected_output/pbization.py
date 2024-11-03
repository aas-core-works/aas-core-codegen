# Automatically generated with python_protobuf/main.py.
# Do NOT edit or append.


"""Convert instances from and to Protocol Buffers."""


from typing import Mapping, TypeVar

import google.protobuf.message

from aas_core3 import types
import aas_core3_protobuf.types_pb2 as types_pb


# region From Protocol Buffers


# fmt: off
_MODELLING_KIND_FROM_PB_MAP = {
    types_pb.ModellingKind.Modellingkind_TEMPLATE:
        types.ModellingKind.TEMPLATE,
    types_pb.ModellingKind.Modellingkind_INSTANCE:
        types.ModellingKind.INSTANCE
}  # type: Mapping[types_pb.ModellingKind, types.ModellingKind]
# fmt: on


def modelling_kind_from_pb(
    that: types_pb.ModellingKind
) -> types.ModellingKind:
    """
    Parse ``that`` enum back from its Protocol Buffer representation.

    >>> import aas_core3_protobuf.types_pb2 as types_pb
    >>> from aas_core3_protobuf.pbization import modelling_kind_from_pb
    >>> modelling_kind_from_pb(
    ...     types_pb.ModellingKind.Modellingkind_TEMPLATE
    ... )
    <ModellingKind.TEMPLATE: 'Template'>
    """
    return _MODELLING_KIND_FROM_PB_MAP[that]


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
        modelling_kind=modelling_kind_from_pb(
            that.modelling_kind
        ),
        optional_modelling_kind=(
            modelling_kind_from_pb(
                that.optional_modelling_kind
            )
            if that.HasField('optional_modelling_kind')
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


# fmt: off
_MODELLING_KIND_TO_PB_MAP = {
    types.ModellingKind.TEMPLATE:
        types_pb.ModellingKind.Modellingkind_TEMPLATE,
    types.ModellingKind.INSTANCE:
        types_pb.ModellingKind.Modellingkind_INSTANCE
}  # type: Mapping[types.ModellingKind, types_pb.ModellingKind]
# fmt: on


def modelling_kind_to_pb(
    that: types.ModellingKind
) -> types_pb.ModellingKind:
    """
    Convert ``that`` enum to its Protocol Buffer representation.

    >>> from aas_core3_protobuf.pbization import modelling_kind_to_pb
    >>> import aas_core3.types as types
    >>> modelling_kind_to_pb(
    ...     types.ModellingKind.TEMPLATE
    ... )
    1
    """
    return _MODELLING_KIND_TO_PB_MAP[that]


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
    target.modelling_kind = modelling_kind_to_pb(
        that.modelling_kind
    )

    if that.optional_modelling_kind is not None:
        target.optional_modelling_kind = modelling_kind_to_pb(
            that.optional_modelling_kind
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
