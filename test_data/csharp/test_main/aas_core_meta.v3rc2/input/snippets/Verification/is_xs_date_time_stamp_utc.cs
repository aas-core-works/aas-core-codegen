private static readonly string[] XsDateFormats = {
    "yyyy-MM-dd"
};

/// <summary>
/// Clip the <paramref name="value" /> to the date part.
/// </summary>
/// <remarks>
/// We ignore the negative sign prefix and clip years to 4 digits.
/// This is necessary as <see cref="System.DateTime" /> can not handle
/// dates B.C. and the <see cref="o:System.DateTime.ParseExact" /> expects
/// exactly four digits.
///
/// We strip the negative sign and assume astronomical years.
/// See: https://en.wikipedia.org/wiki/Leap_year#Algorithm
///
/// Furthermore, we always assume that <paramref name="value" /> has been
/// already validated with the corresponding regular expression.
/// Hence we can use this function to validate the date-times as the time
/// segment and offsets are correctly matched by the regular expression,
/// while day/month combinations need to be validated by
/// <see cref="o:System.DateTime.ParseExact" />.
/// </remarks>
private static string ClipToDate(string value)
{
    int start = 0;
    if (value[0] == '-')
    {
        start++;
    }
    
    int yearEnd = start;
    for(; value[yearEnd] != '-'; yearEnd++)
    {
        // Intentionally empty.
    }

	return (yearEnd == 4 && value.Length == 10)
		? value
		: value.Substring(yearEnd - 4, 10);
}

/// <summary>
/// Check that <paramref name="value" /> is a <c>xs:dateTimeStamp</c> with
/// the time zone set to UTC.
/// </summary>
/// <remarks>
/// The <paramref name="value" /> is assumed to be already checked with
/// <see cref="MatchesXsDateTimeStampUtc" />.
/// </remarks>
public static bool IsXsDateTimeStampUtc(
    string value
)
{
    if (!MatchesXsDateTimeStampUtc(value))
    {
        return false;
    }

    try
    {
        // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
        System.DateTime.ParseExact(
			ClipToDate(value),
			XsDateFormats,
        	System.Globalization.CultureInfo.InvariantCulture,
			System.Globalization.DateTimeStyles.None );
        return true;
    }
    catch (System.FormatException)
    {
        return false;
    }
}
