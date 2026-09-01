class Something:
    some_property: Annotated[
        Optional[int], json_name("someProperty"), xml_name("someProperty")
    ]


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
