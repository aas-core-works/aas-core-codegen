/// <summary>
/// Check that the <paramref name="value" /> is consistent with
/// the given <paramref name="valueType" />.
/// </summary>
public static bool ValueConsistentWithXsdType(
    string value,
    Aas.DataTypeDefXsd valueType
)
{
    switch (valueType)
    {
        case Aas.DataTypeDefXsd.AnyUri:
        {
            return MatchesXsAnyUri(value);
        }
        case Aas.DataTypeDefXsd.Base64Binary:
        {
            return MatchesXsBase64Binary(value);
        }
        case Aas.DataTypeDefXsd.Boolean:
        {
            return MatchesXsBoolean(value);
        }
        case Aas.DataTypeDefXsd.Byte:
        {
            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToSByte(value);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.Date:
        {
            if (!MatchesXsDate(value))
            {
                return false;
            }

            return IsPrefixedWithValidDate(value);
        }
        case Aas.DataTypeDefXsd.DateTime:
        {
            if (!MatchesXsDateTime(value))
            {
                return false;
            }

            // The time part and the time zone part will be checked by
            // MatchesXsDateTime. We need to check that the date part is
            // correct in sense of the day/month combination.
            return IsPrefixedWithValidDate(value);
        }
        case Aas.DataTypeDefXsd.Decimal:
        {
            return MatchesXsDecimal(value);
        }
        case Aas.DataTypeDefXsd.Double:
        {
            // We need to check explicitly for the regular expression since
            // System.Xml.XmlConvert.ToDouble is too permissive. For example,
            // it accepts "nan" although only "NaN" is valid.
            // See: https://www.w3.org/TR/xmlschema-2/#double
            if (!MatchesXsDouble(value))
            {
                return false;
            }

            double converted;
            try
            {
                converted = System.Xml.XmlConvert.ToDouble(value);
            }
            catch (System.FormatException)
            {
                return false;
            }

            if (System.Double.IsInfinity(converted))
            {
                // Check that the value is either "INF" or "-INF".
                // Otherwise, the value is a decimal which is too big
                // to be represented as a double-precision floating point
                // number.
                //
                // Earlier C# used to throw an exception in this case. Today it
                // simply rounds the parsed value to infinity. In the context
                // of data exchange formats (such as AAS), this can cause
                // critical errors, so we check for this edge case explicitly.
                if (value.Length == 3)
                {
                    return value == "INF";
                }
                else if (value.Length == 4)
                {
                    return value == "-INF";
                }
                else
                {
                    return false;
                }
            }
            return true;
        }
        case Aas.DataTypeDefXsd.Duration:
        {
            return MatchesXsDuration(value);
        }
        case Aas.DataTypeDefXsd.Float:
        {
            // We need to check explicitly for the regular expression since
            // System.Xml.XmlConvert.ToSingle is too permissive. For example,
            // it accepts "nan" although only "NaN" is valid.
            // See: https://www.w3.org/TR/xmlschema-2/#float
            if (!MatchesXsFloat(value))
            {
                return false;
            }

            float converted;
            try
            {
                converted = System.Xml.XmlConvert.ToSingle(value);
            }
            catch (System.FormatException)
            {
                return false;
            }

            if (System.Single.IsInfinity(converted))
            {
                // Check that the value is either "INF" or "-INF".
                // Otherwise, the value is a decimal which is too big
                // to be represented as a single-precision floating point
                // number.
                //
                // Earlier C# used to throw an exception in this case. Today it
                // simply rounds the parsed value to infinity. In the context
                // of data exchange formats (such as AAS), this can cause
                // critical errors, so we check for this edge case explicitly.
                if (value.Length == 3)
                {
                    return value == "INF";
                }
                else if (value.Length == 4)
                {
                    return value == "-INF";
                }
                else
                {
                    return false;
                }
            }
            return true;
        }
        case Aas.DataTypeDefXsd.GDay:
        {
            return MatchesXsGDay(value);
        }
        case Aas.DataTypeDefXsd.GMonth:
        {
            return MatchesXsGMonth(value);
        }
        case Aas.DataTypeDefXsd.GMonthDay:
        {
            if (!MatchesXsGMonthDay(value))
            {
                return false;
            }

            var month = int.Parse(value.Substring(2,2));
            var day = int.Parse(value.Substring(5,2));
            switch (month)
            {
                case 1: case 3: case 5: case 7: case 8: case 10: case 12:
                    return day <= 31;
                case 4: case 6: case 9: case 11:
                    return day <= 30;
                case 2:
                    return day <= 29;
                default:
                    throw new System.InvalidOperationException(
                        $"Unhandled month: {month}; " +
                        "is there maybe a bug in MatchesXsGMonthDay?"
                    );
            }
        }
        case Aas.DataTypeDefXsd.GYear:
        {
            return MatchesXsGYear(value);
        }
        case Aas.DataTypeDefXsd.GYearMonth:
        {
            return MatchesXsGYearMonth(value);
        }
        case Aas.DataTypeDefXsd.HexBinary:
        {
            return MatchesXsHexBinary(value);
        }
        case Aas.DataTypeDefXsd.Int:
        {
            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToInt32(value);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.Integer:
        {
            return MatchesXsInteger(value);
        }
        case Aas.DataTypeDefXsd.Long:
        {
            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToInt64(value);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.NegativeInteger:
        {
            return MatchesXsNegativeInteger(value);
        }
        case Aas.DataTypeDefXsd.NonNegativeInteger:
        {
            return MatchesXsNonNegativeInteger(value);
        }
        case Aas.DataTypeDefXsd.NonPositiveInteger:
        {
            return MatchesXsNonPositiveInteger(value);
        }
        case Aas.DataTypeDefXsd.PositiveInteger:
        {
            return MatchesXsPositiveInteger(value);
        }
        case Aas.DataTypeDefXsd.Short:
        {
            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToInt16(value);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.String:
        {
            return MatchesXsString(value);
        }
        case Aas.DataTypeDefXsd.Time:
        {
            return MatchesXsTime(value);
        }
        case Aas.DataTypeDefXsd.UnsignedByte:
        {
            if (value.Length == 0)
            {
                return false;
            }

            // We need to allow negative zeros which are allowed in the lexical
            // representation of an unsigned byte, but System.Xml.XmlConvert.ToByte
            // rejects it.
            // See: https://www.w3.org/TR/xmlschema11-2/#unsignedByte
            if (value == "-0")
            {
                return true;
            }

            // We need to strip the prefix positive sign since
            // System.Xml.XmlConvert.ToByte does not adhere to lexical representation
            // of an unsigned byte.
            //
            // The positive sign is indeed allowed in the lexical representation, see:
            // https://www.w3.org/TR/xmlschema11-2/#unsignedByte
            string clipped = (value[0] == '+')
                ? value.Substring(1, value.Length - 1)
                : value;

            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToByte(clipped);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.UnsignedInt:
        {
            if (value.Length == 0)
            {
                return false;
            }

            // We need to allow negative zeros which are allowed in the lexical
            // representation of an unsigned int, but System.Xml.XmlConvert.ToUInt32
            // rejects it.
            // See: https://www.w3.org/TR/xmlschema11-2/#unsignedInt
            if (value == "-0")
            {
                return true;
            }

            // We need to strip the prefix positive sign since
            // System.Xml.XmlConvert.ToUInt32 does not adhere to lexical representation
            // of an unsigned int.
            //
            // The positive sign is indeed allowed in the lexical representation, see:
            // https://www.w3.org/TR/xmlschema11-2/#unsignedInt
            string clipped = (value[0] == '+')
                ? value.Substring(1, value.Length - 1)
                : value;

            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToUInt32(clipped);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.UnsignedLong:
        {
            if (value.Length == 0)
            {
                return false;
            }

            // We need to allow negative zeros which are allowed in the lexical
            // representation of an unsigned long, but System.Xml.XmlConvert.ToUInt64
            // rejects it.
            // See: https://www.w3.org/TR/xmlschema11-2/#unsignedLong
            if (value == "-0")
            {
                return true;
            }

            // We need to strip the prefix positive sign since
            // System.Xml.XmlConvert.ToUInt64 does not adhere to lexical representation
            // of an unsigned long.
            //
            // The positive sign is indeed allowed in the lexical representation, see:
            // https://www.w3.org/TR/xmlschema11-2/#unsignedLong
            string clipped = (value[0] == '+')
                ? value.Substring(1, value.Length - 1)
                : value;

            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToUInt64(clipped);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        case Aas.DataTypeDefXsd.UnsignedShort:
        {
            if (value.Length == 0)
            {
                return false;
            }

            // We need to allow negative zeros which are allowed in the lexical
            // representation of an unsigned short, but System.Xml.XmlConvert.ToUInt16
            // rejects it.
            // See: https://www.w3.org/TR/xmlschema11-2/#unsignedShort
            if (value == "-0")
            {
                return true;
            }

            // We need to strip the prefix positive sign since
            // System.Xml.XmlConvert.ToUInt16 does not adhere to lexical representation
            // of an unsigned short.
            //
            // The positive sign is indeed allowed in the lexical representation, see:
            // https://www.w3.org/TR/xmlschema11-2/#unsignedShort
            string clipped = (value[0] == '+')
                ? value.Substring(1, value.Length - 1)
                : value;

            try
            {
                // ReSharper disable once ReturnValueOfPureMethodIsNotUsed
                System.Xml.XmlConvert.ToUInt16(clipped);
                return true;
            }
            catch (System.OverflowException)
            {
                return false;
            }
            catch (System.FormatException)
            {
                return false;
            }
        }
        default:
            throw new System.ArgumentException(
                $"valueType is an invalid DataTypeDefXsd: {valueType}"
            );
    }
}
