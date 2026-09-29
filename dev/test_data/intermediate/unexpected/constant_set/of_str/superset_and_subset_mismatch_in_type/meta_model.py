Some_set: AbstractSet[int] = constant_set(values=[1, 2, 3])

Another_set: AbstractSet[str] = constant_set(
    values=[
        "Hello",
        "World",
    ],
    superset_of=[Some_set],
)

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
