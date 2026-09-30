@verification
def some_func(number: int) -> bool:
    assert (number > 0, "Number must be positive")
    return number < 10


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
