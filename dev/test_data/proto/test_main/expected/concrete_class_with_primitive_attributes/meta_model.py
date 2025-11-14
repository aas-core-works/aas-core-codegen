class Something:
    some_bool: bool
    some_int: int
    some_float: float
    some_str: str
    some_byte_array: bytearray

    some_optional_bool: Optional[bool]
    some_optional_int: Optional[int]
    some_optional_float: Optional[float]
    some_optional_str: Optional[str]
    some_optional_byte_array: Optional[bytearray]

    def __init__(
        self,
        some_bool: bool,
        some_int: int,
        some_float: float,
        some_str: str,
        some_byte_array: bytearray,
        some_optional_bool: Optional[bool] = None,
        some_optional_int: Optional[int] = None,
        some_optional_float: Optional[float] = None,
        some_optional_str: Optional[str] = None,
        some_optional_byte_array: Optional[bytearray] = None,
    ) -> None:
        self.some_bool = some_bool
        self.some_int = some_int
        self.some_float = some_float
        self.some_str = some_str
        self.some_byte_array = some_byte_array
        self.some_optional_bool = some_optional_bool
        self.some_optional_int = some_optional_int
        self.some_optional_float = some_optional_float
        self.some_optional_str = some_optional_str
        self.some_optional_byte_array = some_optional_byte_array


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
