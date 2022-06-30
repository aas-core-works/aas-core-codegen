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

__book_url__ = "dummy"
__book_version__ = "dummy"
