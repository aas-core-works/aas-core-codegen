from enum import Enum


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


@verification
def some_func(kind: Kind, other: Kind) -> bool:
    if Kind.Alpha == kind or Kind.Alpha == other:
        return False

    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
