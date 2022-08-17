class SomeEnum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"
    Yet_another_literal = "YET-ANOTHER-LITERAL"


Something: Set[SomeEnum] = constant_set(
    values=[SomeEnum.Some_literal, SomeEnum.Another_literal]
)

__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
