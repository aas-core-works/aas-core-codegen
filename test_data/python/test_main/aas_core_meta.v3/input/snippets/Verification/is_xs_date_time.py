def is_xs_date_time(value: str) -> bool:
    """
    Check that :paramref:`value` is a ``xs:dateTime`` with
    the time zone set to UTC.
    """
    if not matches_xs_date_time(value):
        return False

    date, _ = value.split("T")
    return is_xs_date(date)
