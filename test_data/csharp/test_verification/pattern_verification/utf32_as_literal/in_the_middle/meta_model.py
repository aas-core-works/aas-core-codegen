@verification
def match_something(text: str) -> bool:
    pattern = f"^some-prefix\\U00010000some-suffix$"
    return match(pattern, text) is not None


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
