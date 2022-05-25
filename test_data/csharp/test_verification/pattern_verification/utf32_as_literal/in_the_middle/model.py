@verification
def match_something(text: str) -> bool:
    pattern = f"^some-prefix\\U00010000some-suffix$"
    return match(pattern, text) is not None


__book_url__ = "dummy"
__book_version__ = "dummy"
