class Modelling_kind(Enum):
    Template = "Template"
    Instance = "Instance"


class Something:
    modelling_kind: Modelling_kind
    optional_modelling_kind: Optional[Modelling_kind]

    def __init__(
        self,
        modelling_kind: Modelling_kind,
        optional_modelling_kind: Optional[Modelling_kind] = None,
    ) -> None:
        self.modelling_kind = modelling_kind
        self.optional_modelling_kind = optional_modelling_kind


__version__ = "V198.4"

__xml_namespace__ = "https://dummy/198/4"
