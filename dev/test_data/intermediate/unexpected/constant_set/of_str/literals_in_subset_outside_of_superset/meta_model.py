Some_set: Set[str] = constant_set(
    values=[
        "Hello",
        "World",
        "Tonight",
    ]
)

Another_set: Set[str] = constant_set(
    values=[
        "Hello",
        "World",
    ],
    superset_of=[Some_set],
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
