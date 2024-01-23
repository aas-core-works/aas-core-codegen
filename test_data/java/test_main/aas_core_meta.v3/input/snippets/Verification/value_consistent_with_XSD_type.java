/**
* Check that the value is consistent with
* the given valueType.
* @param value the value to check
* @param valueType the value type
*/
public static boolean valueConsistentWithXsdType(
  String value,
  DataTypeDefXsd valueType){
  switch (valueType) {
    case ANY_URI: {
      return matchesXsAnyUri(value);
    }
    case BASE_64_BINARY: {
      return matchesXsBase64Binary(value);
    }
    case BOOLEAN: {
      return matchesXsBoolean(value);
    }
    case BYTE: {
      try {
        Byte.valueOf(value);
        return true;
      } catch (NumberFormatException numberFormatException) {
        return false;
      }
    }
    case DATE: {
      if (!matchesXsDate(value)) {
        return false;
      }

      return isPrefixedWithValidDate(value);
    }
    case DATE_TIME: {
      if (!matchesXsDateTime(value)) {
        return false;
      }

      // The time part and the time zone part will be checked by
      // MatchesXsDateTime. We need to check that the date part is
      // correct in sense of the day/month combination.
      return isPrefixedWithValidDate(value);
    }
    case DECIMAL: {
      return matchesXsDecimal(value);
    }
    case DOUBLE: {
      // We need to check explicitly for the regular expression.
      // See: https://www.w3.org/TR/xmlschema-2/#double
      if (!matchesXsDouble(value)) {
        return false;
      }

      if("INF".equals(value) || "-INF".equals(value)) return true;

      double converted;
      try {
        converted = Double.parseDouble(value);
      } catch (Exception exception) {
        return false;
      }
      return !Double.isInfinite(converted);
    }
    case DURATION: {
      return matchesXsDuration(value);
    }
    case FLOAT: {
      // We need to check explicitly for the regular expression.
      // See: https://www.w3.org/TR/xmlschema-2/#float
      if (!matchesXsFloat(value)) {
        return false;
      }

      if("INF".equals(value) || "-INF".equals(value)) return true;

      float converted;
      try {
        converted = Float.parseFloat(value);
      } catch (Exception exception) {
        return false;
      }
      return !Float.isInfinite(converted);
    }
    case G_DAY: {
      return matchesXsGDay(value);
    }
    case G_MONTH: {
      return matchesXsGMonth(value);
    }
    case G_MONTH_DAY: {
      if (!matchesXsGMonthDay(value)) {
        return false;
      }

      int month = Integer.parseInt(value.substring(2,4));
      int day = Integer.parseInt(value.substring(5,7));
      switch (month)
      {
        case 1:
        case 3:
        case 5:
        case 7:
        case 8:
        case 10:
        case 12:
        return day <= 31;
        case 4:
        case 6:
        case 9:
        case 11:
        return day <= 30;
        case 2:
          return day <= 29;
        default:
          throw new IllegalArgumentException(
              "Unhandled month: " + month +
              "is there maybe a bug in MatchesXsGMonthDay?"
          );
      }
    }
    case G_YEAR: {
      return matchesXsGYear(value);
    }
    case G_YEAR_MONTH: {
      return matchesXsGYearMonth(value);
    }
    case HEX_BINARY: {
      return matchesXsHexBinary(value);
    }
    case INT: {
      try {
        Integer.parseInt(value);
        return true;
      } catch (Exception exception) {
        return false;
      }
    }
    case INTEGER: {
      return matchesXsInteger(value);
    }
    case LONG: {
      try {
        Long.parseLong(value);
        return true;
      } catch (Exception exception) {
        return false;
      }
    }
    case NEGATIVE_INTEGER: {
      return matchesXsNegativeInteger(value);
    }
    case NON_NEGATIVE_INTEGER: {
      return matchesXsNonNegativeInteger(value);
    }
    case NON_POSITIVE_INTEGER: {
      return matchesXsNonPositiveInteger(value);
    }
    case POSITIVE_INTEGER: {
      return matchesXsPositiveInteger(value);
    }
    case SHORT: {
      try {
        Short.parseShort(value);
        return true;
      } catch (Exception exception) {
        return false;
      }
    }
    case STRING: {
      return matchesXsString(value);
    }
    case TIME: {
      return matchesXsTime(value);
    }
    case UNSIGNED_BYTE: {
      if (value.isEmpty()) {
        return false;
      }

      // We need to allow negative zeros which are allowed in the lexical
      // representation of an unsigned byte.
      // See: https://www.w3.org/TR/xmlschema11-2/#unsignedByte
      if (value.equals("-0")) {
        return true;
      }

      try {
        int converted = Integer.parseInt(value);
        return 0 <= converted && converted <= 255;
      } catch (Exception exception) {
        return false;
      }
    }
    case UNSIGNED_INT: {
      if (value.isEmpty()) {
        return false;
      }

      // We need to allow negative zeros which are allowed in the lexical
      // representation of an unsigned int.
      // See: https://www.w3.org/TR/xmlschema11-2/#unsignedInt
      if (value.equals("-0")) {
        return true;
      }

      try {
        //Java does not support UInt32 like C#, so we need to use long.
        long converted = Long.parseUnsignedLong(value);
        return converted <= 4294967295L;
      } catch (Exception exception) {
        return false;
      }
    }
    case UNSIGNED_LONG: {
      if (value.isEmpty()) {
        return false;
      }

      // We need to allow negative zeros which are allowed in the lexical
      // representation of an unsigned long.
      // See: https://www.w3.org/TR/xmlschema11-2/#unsignedLong
      if (value.equals("-0")) {
        return true;
      }

      try {
        Long.parseUnsignedLong(value);
        return true;
      } catch (Exception exception) {
        return false;
      }
    }
    case UNSIGNED_SHORT: {
      if (value.isEmpty()) {
        return false;
      }

      // We need to allow negative zeros which are allowed in the lexical
      // representation of an unsigned short.
      // See: https://www.w3.org/TR/xmlschema11-2/#unsignedShort
      if (value.equals("-0")) {
        return true;
      }

      try {
        int converted = Integer.parseInt(value);
        return  0 <= converted && converted <= 65535;
      } catch (Exception exception) {
        return false;
      }
    }
    default:
      throw new IllegalArgumentException(
          "valueType is an invalid DataTypeDefXsd: " + valueType
      );
  }
}
