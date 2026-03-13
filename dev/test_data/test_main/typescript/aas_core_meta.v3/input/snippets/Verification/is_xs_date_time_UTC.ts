/**
 * Check that `value` is a valid `xs:dateTime` with
 * the time zone set to UTC.
 *
 * @param value - to be checked
 * @returns `true` if `value` is a valid `xs:dateTime` with the UTC time zone
 */
export function isXsDateTimeUtc(
  value: string
): boolean {
  if (!matchesXsDateTimeUtc(value)) {
    return false;
  }

  const date = value.split("T", 1)[0];
  return isXsDate(date);
}
