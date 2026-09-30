from enum import Enum


class Kind(Enum):
    Alpha = "alpha"
    Beta = "beta"


@verification
def some_func(kind: Kind) -> bool:
    if kind == Kind.Alpha:
        pass
        return False
    elif kind == Kind.Beta:
        return True

    return True


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
