class Some_enum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"
    Yet_another_literal = "YET-ANOTHER-LITERAL"


class Another_enum(Enum):
    Some_literal = "SOME-LITERAL"
    Another_literal = "ANOTHER-LITERAL"
    Yet_another_literal = "YET-ANOTHER-LITERAL"


Some_set: Final[AbstractSet[Some_enum]] = constant_set(
    values=[
        Some_enum.Some_literal,
        Some_enum.Another_literal,
    ]
)

Another_set: Final[AbstractSet[Another_enum]] = constant_set(
    values=[
        Another_enum.Some_literal,
        Another_enum.Another_literal,
        Another_enum.Yet_another_literal,
    ],
    superset_of=[Some_set],
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
