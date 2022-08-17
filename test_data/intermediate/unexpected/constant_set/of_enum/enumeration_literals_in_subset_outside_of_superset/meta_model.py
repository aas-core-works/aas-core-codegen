class Some_enum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"
    Yet_another_literal = "YET-ANOTHER-LITERAL"


Some_set: Set[Some_enum] = constant_set(
    values=[
        Some_enum.Some_literal,
        Some_enum.Another_literal,
        Some_enum.Yet_another_literal,
    ]
)

Another_set: Set[Some_enum] = constant_set(
    values=[Some_enum.Some_literal, Some_enum.Another_literal], superset_of=[Some_set]
)

__book_url__ = "dummy"
__book_version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
