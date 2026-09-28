@verification
def some_func(text: str) -> bool:
    x = True
    if len(text) > 0:
        x = False
    elif len(text) > 1:
        return False
        x = False

    return x


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
