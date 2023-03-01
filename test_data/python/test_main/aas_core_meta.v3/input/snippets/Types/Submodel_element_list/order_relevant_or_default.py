def order_relevant_or_default(self) -> bool:
    """Return :py:attr:`order_relevant` if set, and the default otherwise."""
    return self.order_relevant if self.order_relevant is not None else True
