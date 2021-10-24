"""Represent general entities as strings for testing or debugging."""

import collections.abc
import io
import textwrap
from typing import Sequence, Union, Any

from icontract import require

from aas_core_csharp_codegen.common import assert_never

# We have to separate Stringifiable and Sequence[Stringifiable] since recursive types
# are not supported in mypy, see https://github.com/python/mypy/issues/731.
PrimitiveStringifiable = Union[bool, int, float, str, "Entity", None]

Stringifiable = Union[PrimitiveStringifiable, Sequence[PrimitiveStringifiable]]


class Property:
    """Represent a property of an entity to be stringified."""

    def __init__(self, name: str, value: Stringifiable) -> None:
        self.name = name
        self.value = value


class PropertyEllipsis:
    """Represent a property whose value is not displayed."""

    def __init__(self, name: str, ignored_value: Any) -> None:
        """Initialize with the given values."""
        self.name = name

        # The ignored value is usually not used. However, it instructs mypy and
        # other static checkers to raise a warning if its value can not be accessed
        # (*e.g.*, as can happen in a refactoring).
        self.ignored_value = ignored_value


class Entity:
    """Represent a stringifiable entity which is defined by its properties.

    Think of a dictionary with assigned type identifier.
    """

    def __init__(
        self, name: str, properties: Sequence[Union[Property, PropertyEllipsis]]
    ) -> None:
        """Initialize with the given values."""
        self.name = name
        self.properties = properties


@require(lambda spaces: spaces >= 0)
def _indent_but_first_line(text: str, spaces: int) -> str:
    """Indent all but the first of the given ``text`` by ``spaces``."""
    return "\n".join(
        " " * spaces + line if i > 0 else line
        for i, line in enumerate(text.splitlines())
    )


def dump(stringifiable: Stringifiable) -> str:
    """Produce a string representation of ``stringifiable`` for debugging or testing."""
    if isinstance(stringifiable, (bool, int, float, str)):
        return repr(stringifiable)

    elif isinstance(stringifiable, Entity):
        if len(stringifiable.properties) == 0:
            return f"{stringifiable.name}()"

        writer = io.StringIO()
        writer.write(f"{stringifiable.name}(\n")

        for i, prop in enumerate(stringifiable.properties):
            if isinstance(prop, Property):
                value_str = dump(prop.value)
                writer.write(f"  {prop.name}={_indent_but_first_line(value_str, 2)}")
            elif isinstance(prop, PropertyEllipsis):
                value_str = "None" if prop.ignored_value is None else "..."
                writer.write(f"  {prop.name}={value_str}")
            else:
                assert_never(prop)

            if i == len(stringifiable.properties) - 1:
                writer.write(")")
            else:
                writer.write(",\n")

        return writer.getvalue()

    elif isinstance(stringifiable, collections.abc.Sequence):
        if len(stringifiable) == 0:
            return "[]"
        else:
            writer = io.StringIO()
            writer.write(f"[\n")
            for i, value in enumerate(stringifiable):
                value_str = dump(value)
                writer.write(textwrap.indent(value_str, "  "))

                if i == len(stringifiable) - 1:
                    writer.write("]")
                else:
                    writer.write(",\n")

            return writer.getvalue()

    elif stringifiable is None:
        return repr(None)

    else:
        raise AssertionError(f"Unexpected: {stringifiable}")


@require(lambda obj: hasattr(obj, "__dict__"), error=ValueError)
def assert_compares_against_dict(entity: Entity, obj: object) -> None:
    """
    Compare that the properties in the ``entity`` and ``obj.__dict__`` match.

    Mind that the dunders and "protected" properties are excluded.
    """
    entity_property_set = {prop.name for prop in entity.properties}

    obj_property_set = {key for key in obj.__dict__.keys() if not key.startswith("_")}

    if entity_property_set != obj_property_set:
        first_diff_in_entity = next(
            iter(entity_property_set.difference(obj_property_set)), None
        )

        first_diff_in_obj = next(iter(obj_property_set.difference(entity_property_set)))

        raise AssertionError(
            "Expected the stringified properties to match the object properties, "
            "but they do not.\n\n"
            f"{type(obj)=}\n"
            f"{first_diff_in_entity=}\n"
            f"{first_diff_in_obj=}\n\n"
            f"{sorted(entity_property_set)=}\n"
            f"{sorted(obj_property_set)=}"
        )
