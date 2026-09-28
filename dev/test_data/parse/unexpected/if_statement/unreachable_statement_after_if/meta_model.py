@verification
def some_func(text: str) -> bool:
    x = True
    if len(text) > 0:
        return False
    elif len(text) > 1:
        return False
    else:
        return True

    x = False
    return x


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
