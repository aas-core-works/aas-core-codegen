/**
 * \brief Check whether the given \p year is a leap year.
 *
 * Year 1 BCE is a leap year.
 *
 * \param year to be checked
 * \return true if \p year is a leap year
 */
bool IsLeapYear(long long year);

/**
 *  \brief Check that \p text is a `xs:dateTime` with time zone set to UTC.
 *
 *  The `text` is assumed to match a pre-defined pattern for `xs:dateTime` with
 *  the time zone set to UTC. In this function, we check for days of month (e.g.,
 *  February 29th).
 *
 *  See: https://www.w3.org/TR/xmlschema-2/#dateTime
 */
bool IsXsDateTimeUtc(
  const std::wstring& text
);
