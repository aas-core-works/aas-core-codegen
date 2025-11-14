@verification
def match_something(text: str) -> bool:
    pattern = f"^\\U00010000something$"
    return match(pattern, text) is not None


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
