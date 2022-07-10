Something: Set[str] = constant_set(values=["some literal", "another literal"])

Something_extended: Set[str] = constant_set(
    values=[
        "some literal",
        "another literal",
        "yet another literal",
    ],
    superset_of=[Something],
)


__book_url__ = "dummy"
__book_version__ = "dummy"
