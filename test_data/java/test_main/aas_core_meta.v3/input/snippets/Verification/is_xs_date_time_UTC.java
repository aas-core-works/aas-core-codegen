/**
* Check that value is a xs:dateTime with
* the time zone set to UTC.
* @param value the value to check
*/
public static boolean isXsDateTimeUtc(
        String value
){
    if (!matchesXsDateTimeUtc(value))
    {
        return false;
    }

    return isPrefixedWithValidDate(value);
}