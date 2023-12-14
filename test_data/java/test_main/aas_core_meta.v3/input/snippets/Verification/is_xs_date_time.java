private static final Pattern regexDatePrefix = Pattern.compile("^(-?[0-9]+)-([0-9]{2})-([0-9]{2})");

/**
* Check whether the given year is a leap year.
* Year 1 BCE is a leap year.
* @param year to be checked
* @return  True if 'year' is a leap year
*/

public static boolean isLeapYear(int year)
{
    // We consider the years B.C. to be one-off.
    // See the note at: https://www.w3.org/TR/xmlschema-2/#dateTime:
    // "'-0001' is the lexical representation of the year 1 Before Common Era
    // (1 BCE, sometimes written "1 BC")."
    //
    // Hence, -1 year in XML is 1 BCE, which is 0 year in astronomical years.
    if (year < 0)
    {
        year = -year - 1;
    }

    // See: See: https://en.wikipedia.org/wiki/Leap_year#Algorithm
    if (year % 4 > 0)
    {
        return false;
    }

    if (year % 100 > 0)
    {
        return true;
    }

    if (year % 400 > 0)
    {
        return false;
    }
    return true;
}

/**
* Check that the value starts with a valid date.
* @param value an xs:date, an xs:dateTime,or an xs:dateTimeStamp
* @return true if the value starts with a valid date
*/
private static boolean isPrefixedWithValidDate(
    String value
){
    Matcher match = regexDatePrefix.matcher(value);
    if (!match.matches())
    {
        return false;
    }

    int year;
    try{
        year = Integer.parseInt(match.group(1));
    }catch (NumberFormatException exception){
        throw new IllegalArgumentException(
                "Expected to parse the year from " + match.group(1)
                + "but the parsing failed");
    }

    int month;
    try{
        month = Integer.parseInt(match.group(2));
    }catch (NumberFormatException exception){
        throw new IllegalArgumentException(
                "Expected to parse the month from " + match.group(2)
                        + "but the parsing failed");
    }

    int day;
    try{
        day = Integer.parseInt(match.group(3));
    }catch (NumberFormatException exception){
        throw new IllegalArgumentException(
                "Expected to parse the day from " + match.group(3)
                        + "but the parsing failed");
    }

    // Year zero does not exist, see: https://www.w3.org/TR/xmlschema-2/#dateTime
    if (year == 0)
    {
        return false;
    }

    if (day <= 0 || day > 31)
    {
        return false;
    }

    if (month <= 0 || month >= 13)
    {
        return false;
    }

    int maxDaysInMonth;
    switch (month)
    {
        case 1:
            maxDaysInMonth = 31;
            break;
        case 2:
            maxDaysInMonth = (isLeapYear(year)) ? 29 : 28;
            break;
        case 3:
            maxDaysInMonth = 31;
            break;
        case 4:
            maxDaysInMonth = 30;
            break;
        case 5:
            maxDaysInMonth = 31;
            break;
        case 6:
            maxDaysInMonth = 30;
            break;
        case 7:
            maxDaysInMonth = 31;
            break;
        case 8:
            maxDaysInMonth = 31;
            break;
        case 9:
            maxDaysInMonth = 30;
            break;
        case 10:
            maxDaysInMonth = 31;
            break;
        case 11:
            maxDaysInMonth = 30;
            break;
        case 12:
            maxDaysInMonth = 31;
            break;
        default:
            throw new IllegalArgumentException("Unexpected month: " + month);
    }

    if (day > maxDaysInMonth)
    {
        return false;
    }


    return true;
}



/**
* Check that value is a xs:dateTime with
* the time zone set to UTC.
* @param value to check
*/
public static boolean isXsDateTime(
        String value
){
    if (!matchesXsDateTime(value))
    {
        return false;
    }

    return isPrefixedWithValidDate(value);
}
