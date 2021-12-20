from aas_core_meta.marker import (
    associate_ref_with,
)

__book_url__ = "DUMMY"
__book_version__ = "DUMMY"


class Concrete:
    pass


class Reference:
    pass


associate_ref_with(cls=Reference)
