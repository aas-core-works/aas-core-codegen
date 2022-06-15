@verification
def match_something(text: str) -> bool:
    pattern = f"^prefix[\\U00010005-\\U00010405]suffix$"
    return match(pattern, text) is not None


__book_url__ = "dummy"
__book_version__ = "dummy"
