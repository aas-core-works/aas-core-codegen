from enum import Enum


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


@verification
def is_alpha(kind: Mutable[Kind]) -> bool:
    return kind == Kind.Alpha


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
