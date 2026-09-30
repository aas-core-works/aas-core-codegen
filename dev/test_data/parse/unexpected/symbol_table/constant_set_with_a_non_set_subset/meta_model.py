Some_string: Final[str] = constant_str(value="some text")

Something: Final[AbstractSet[str]] = constant_set(values=[], subsets=[Some_string])

__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
