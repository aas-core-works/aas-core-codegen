# ``with_model_type`` is missing in the serialization.
class Something:
    pass


class Concrete(Something):
    pass


class Bundle:
    something: Something

    def __init__(self, something: Something) -> None:
        self.something = something


__book_version__ = "dummy"
__book_url__ = "dummy"
__xml_namespace__ = "https://dummy.com"
