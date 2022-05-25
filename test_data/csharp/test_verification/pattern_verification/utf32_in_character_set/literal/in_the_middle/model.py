@verification
def match_something(text: str) -> bool:
    pattern = f"^prefix[a-z\\U00010000A-Z]suffix$"
    return match(pattern, text) is not None


__book_url__ = "dummy"
__book_version__ = "dummy"
