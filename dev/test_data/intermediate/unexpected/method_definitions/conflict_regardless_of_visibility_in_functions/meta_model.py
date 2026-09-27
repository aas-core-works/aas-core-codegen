@verification
def is_something(text: str) -> bool:
    return len(text) > 0


@verification
def _is_something(text: str) -> bool:
    return len(text) > 1


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
