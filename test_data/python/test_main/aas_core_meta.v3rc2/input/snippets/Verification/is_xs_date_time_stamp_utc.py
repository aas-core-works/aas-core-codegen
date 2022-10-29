def is_xs_date_time_stamp_utc(
        value: str
) -> bool:
    """
    Check that :paramref:`value` is a ``xs:dateTimeStamp`` with
    the time zone set to UTC.
    """
    if matches_xs_date_time_stamp_utc(value) is None:
        return False

    date, _ = value.split('T')
    return is_xs_date(date)
