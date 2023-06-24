# We test with this sample that the method signature is correctly translated.
@abstract
class Abstract:
    @require(lambda x: x > 0)
    def some_func(self, x: int) -> bool:
        pass


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
