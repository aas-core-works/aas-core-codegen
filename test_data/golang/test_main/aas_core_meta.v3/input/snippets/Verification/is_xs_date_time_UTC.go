// Check that `value` is a valid `xs:dateTime` with
// the time zone set to UTC.
func IsXsDateTimeUTC(value string) bool {
	if !MatchesXsDateTime(value) {
		return false
	}

	date, _, ok := strings.Cut(value, "T")
	if !ok {
		panic(
			fmt.Sprintf(
				"Expected 'T' in the date-time if it matches the expected regex, " +
				"but got: %s",
				value,
			),
		)
	}
	return IsXsDate(date)
}
