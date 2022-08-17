@verification
def match_something(text: str) -> None:
    # The regular expression is invalid.
    return re.match(r"^x(", text)


__book_version__ = "dummy"
__book_url__ = "dummy"
__xml_namespace__ = "https://dummy.com"
