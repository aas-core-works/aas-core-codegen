@invariant(lambda self: re.match(r"^hello$", self), "The string must match hello.")
class Something(str):
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
