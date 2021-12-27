from aas_core_meta.marker import (
    associate_ref_with,
)

class Concrete:
    pass


class Reference:
    pass


__book_url__ = "dummy"
__book_version__ = "dummy"
associate_ref_with(Reference)
