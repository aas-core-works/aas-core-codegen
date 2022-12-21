/**
 * Check that `value` is a valid `xs:dateTimeStamp` with
 * the time zone set to UTC.
 *
 * @param value - to be checked
 * @returns `true` if `value` is a valid `xs:dateTimeStamp` with the UTC time zone
 */
export function isXsDateTimeStampUtc(
  value: string
): boolean {
  if (!matchesXsDateTimeStampUtc(value)) {
    return false;
  }

  const date = value.split("T", 1)[0];
  return isXsDate(date);
}
