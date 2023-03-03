def kind_or_default(self) -> "ModellingKind":
    """Return :py:attr:`kind` if set, and the default otherwise."""
    return self.kind if self.kind is not None else ModellingKind.INSTANCE
