Something: Set[str] = constant_set(values=["some literal", "another literal"])

Something_extended: Set[str] = constant_set(
    values=[
        "some literal",
        "another literal",
        "yet another literal",
    ],
    superset_of=[Something],
)


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
