@reference_in_the_book(section=(1, 2, 3))
class SomeEnum(Enum):
    pass


@reference_in_the_book(section=(1, 2, 3, 4))
class SomeConstrainedPrimitive(str):
    pass


@reference_in_the_book(section=(1, 2, 3, 4, 5))
class SomeClass:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
