from icontract import DBC, invariant


@verification
def floor_mod(number: int) -> bool:
    """Collide with the helper for the modulo."""
    return number % 2 == 0


@verification
def abs_int64(number: int) -> bool:
    """Collide with the helper for the absolute value of integers in Go."""
    return abs(number) < 10


@invariant(lambda self: floor_mod(self.number), "Number must be even")
@invariant(lambda self: abs_int64(self.number), "Number must be small")
class Something(DBC):
    number: int

    def __init__(self, number: int) -> None:
        self.number = number


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
