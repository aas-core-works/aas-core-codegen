bool IsXsDate(const std::wstring& text) {
  // NOTE (mristin):
  // Optimally, we would re-use the parts of `MatchesXsDate` program and
  // `IsXsDateWithoutOffset`, but this would make the implementation much more
  // difficult to read and maintain. Hence, we opt here for simplicity of implementation
  // to computational performance.

  if (!MatchesXsDate(text)) {
    return false;
  }

  return IsXsDateWithoutOffset(text);
}

bool IsXsDouble(const std::wstring& value) {
  // NOTE (mristin):
  // We need to check explicitly for the regular expression since
  // `stod` allows `nan`, `infinity` and `inf` case-insensitive, while
  // XSD accepts only case-sensitive literals, see:
  // https://en.cppreference.com/w/cpp/string/basic_string/stof,
  // https://www.w3.org/TR/xmlschema-2/#double
  if (!MatchesXsDouble(value)) {
    return false;
  }

  try {
  // NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
    const bool sizeof_double_is_8 = sizeof(double) == 8;
    const bool sizeof_long_double_is_8 = sizeof(long double) == 8;

    if (sizeof_double_is_8) {
      static_cast<void>(
        std::stod(value)
      );
    } else if (sizeof_long_double_is_8) {
      static_cast<void>(
        std::stold(value)
      );
    } else {
      std::stringstream ss;
      ss
        << "The size of long double was not 8 (it was "
        << sizeof(long double) << "), nor was the size of double 8 ("
        << "it was " << sizeof(double) << "). Hence, we do not know "
        << "how to check for string parsing of a 64-bit floating-point number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable floating-point number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }

  return true;
}

bool IsXsFloat(const std::wstring& value) {
  // NOTE (mristin):
  // We need to check explicitly for the regular expression since
  // `stof` allows `nan`, `infinity` and `inf` case-insensitive, while
  // XSD accepts only case-sensitive literals, see:
  // https://en.cppreference.com/w/cpp/string/basic_string/stof,
  // https://www.w3.org/TR/xmlschema-2/#float
  if (!MatchesXsFloat(value)) {
    return false;
  }

  try {
    // NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
    const bool sizeof_float_is_4 = sizeof(float) == 4;
    const bool sizeof_double_is_4 = sizeof(double) == 4;

    if (sizeof_float_is_4) {
      static_cast<void>(
        std::stof(value)
      );
    } else if(sizeof_double_is_4) {
      static_cast<void>(
        std::stod(value)
      );
    } else {
      std::stringstream ss;
      ss
        << "The size of float was not 4 (it was "
        << sizeof(float) << "), nor was the size of double 4 ("
        << "it was " << sizeof(double) << "). Hence, we do not know "
        << "how to check for string parsing of a 32-bit floating-point number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable floating-point number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }

  return true;
}

bool IsXsGMonthDay(const std::wstring& value) {
  if (!MatchesXsGMonthDay(value)) {
    return false;
  }

  const std::wstring month_str = value.substr(2, 2);

  const int month = std::stoi(value.substr(2, 2));
  const int day = std::stoi(value.substr(5, 2));

  // We know by regular expression that the month will be 1-12.
  return day <= kDaysInMonth.at(month);
}

bool IsXsLong(const std::wstring& value) {
  if (!MatchesXsLong(value)) {
    return false;
  }

  try {
	// NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
    const bool sizeof_long_is_8 = sizeof(long) == 8;
    const bool sizeof_long_long_is_8 = sizeof(long long) == 8;

    if (sizeof_long_is_8) {
      static_cast<void>(
        std::stol(value)
      );
    } else if (sizeof_long_long_is_8) {
      static_cast<void>(
        std::stoll(value)
      );
    } else {
      std::stringstream ss;
      ss
        << "The size of long was not 8 (it was "
        << sizeof(long) << "), nor was the size of long long 8 ("
        << "it was " << sizeof(long long) << "). Hence, we do not know "
        << "how to check for string parsing of a 64-bit integer number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable integer number from the value matching the regex: "
      << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }

  return true;
}

bool IsXsInt(const std::wstring& value) {
  if (!MatchesXsInt(value)) {
    return false;
  }

  try {
	// NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
  	const bool sizeof_int_is_4 = sizeof(int) == 4;
  	const bool sizeof_long_is_4 = sizeof(long) == 4;

    if (sizeof_int_is_4) {
      static_cast<void>(
        std::stoi(value)
      );
    } else if (sizeof_long_is_4) {
      static_cast<void>(
        std::stol(value)
      );
    } else {
      std::stringstream ss;
      ss
        << "The size of int was not 4 (it was "
        << sizeof(int) << "), nor was the size of long 4 ("
        << "it was " << sizeof(long) << "). Hence, we do not know "
        << "how to check for string parsing of a 32-bit integer number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable integer number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
    common::WstringToUtf8(wss.str())
  );
  } catch (const std::out_of_range&) {
    return false;
  }

  return true;
}

bool IsXsShort(const std::wstring& value) {
  if (!MatchesXsShort(value)) {
    return false;
  }

  int converted;
  try {
    converted = std::stoi(value);
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable integer number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }

  return -32768 <= converted && converted <= 32767;
}

bool IsXsByte(const std::wstring& value) {
  if (!MatchesXsByte(value)) {
    return false;
  }

  int converted;
  try {
    converted = std::stoi(value);
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable integer number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }

  return -128 <= converted && converted <= 127;
}

bool IsXsUnsignedLong(const std::wstring& value) {
  if (!MatchesXsUnsignedLong(value)) {
    return false;
  }

  try {
  	// NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
	const bool sizeof_unsigned_long_is_8 = sizeof(unsigned long) == 8;
	const bool sizeof_unsigned_long_long_is_8 = sizeof(unsigned long long) == 8;

    if (sizeof_unsigned_long_is_8) {
      static_cast<void>(
        std::stoul(value)
      );
    } else if (sizeof_unsigned_long_long_is_8) {
      static_cast<void>(
        std::stoull(value)
      );
    } else {
      std::stringstream ss;
      ss
        << "The size of unsigned long was not 8 (it was "
        << sizeof(unsigned long) << "), nor was the size of unsigned long long 8 ("
        << "it was " << sizeof(unsigned long long) << "). Hence, we do not know "
        << "how to check for string parsing of an unsigned 64-bit integer number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable integer number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }

  return true;
}

bool IsXsUnsignedInt(const std::wstring& value) {
  if (!MatchesXsUnsignedInt(value)) {
    return false;
  }

  // NOTE (mristin):
  // There exist no std::stoui or std::stou, see:
  // https://stackoverflow.com/questions/8715213/why-is-there-no-stdstou,
  // so we have to work with std::stoul.

  try {
	// NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
	const bool sizeof_unsigned_long_ge_4 = sizeof(unsigned long) >= 4;
	const bool sizeof_unsigned_long_long_ge_4 = sizeof(unsigned long long) >= 4;

    if (sizeof_unsigned_long_ge_4) {
      const unsigned long number = std::stoul(value);
      return number <= 4294967295ul;
    } else if (sizeof_unsigned_long_long_ge_4) {
      const unsigned long long number = std::stoull(value);
      return number <= 4294967295ull;
    } else {
      std::stringstream ss;
      ss
        << "The size of unsigned long was less than 4 (it was "
        << sizeof(unsigned long) << "), and the size of "
        << "unsigned long long was also less than 4 ("
        << "it was " << sizeof(unsigned long long) << "). Hence, we do not "
        << "know how to check for string parsing of "
        << "an unsigned 32-bit integer number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
    std::wstringstream wss;
      wss
        << "Unexpected unparsable integer number from "
        << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }
}

bool IsXsUnsignedShort(const std::wstring& value) {
  if (!MatchesXsUnsignedShort(value)) {
    return false;
  }

  // NOTE (mristin):
  // There exist no std::stoui or std::stou, see:
  // https://stackoverflow.com/questions/8715213/why-is-there-no-stdstou,
  // so we have to work with std::stoul.

  try {
	// NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
    const bool sizeof_unsigned_long_ge_4(
    	sizeof(unsigned long) >= 4
    );
    const bool sizeof_unsigned_long_long_ge_4(
    	sizeof(unsigned long long) >= 4
    );

    if (sizeof_unsigned_long_ge_4) {
      const unsigned long number = std::stoul(value);
      return number <= 65535ul;
    } else if (sizeof_unsigned_long_long_ge_4) {
      const unsigned long long number = std::stoull(value);
      return number <= 65535ull;
    } else {
      std::stringstream ss;
      ss
        << "The size of unsigned long was less than 4 (it was "
        << sizeof(unsigned long) << "), and the size of "
        << "unsigned long long was also less than 4 ("
        << "it was " << sizeof(unsigned long long) << "). Hence, we do not "
        << "know how to check for string parsing of "
        << "an unsigned 16-bit integer number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
    std::wstringstream wss;
      wss
        << "Unexpected unparsable integer number from "
        << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }
}

bool IsXsUnsignedByte(const std::wstring& value) {
  if (!MatchesXsUnsignedByte(value)) {
    return false;
  }

  // NOTE (mristin):
  // There exist no std::stoui or std::stou, see:
  // https://stackoverflow.com/questions/8715213/why-is-there-no-stdstou,
  // so we have to work with std::stoul.

  try {
	// NOTE (mristin):
    // We remove the warning C4101 in MSVC with constants.
    // See: https://stackoverflow.com/questions/25573996/c4127-conditional-expression-is-constant
  	const bool sizeof_unsigned_long_ge_4(
	  sizeof(unsigned long) >= 4
  	);
  	const bool sizeof_unsigned_long_long_ge_4(
  	  sizeof(unsigned long long) >= 4
  	);

    if (sizeof_unsigned_long_ge_4) {
      const unsigned long number = std::stoul(value);
      return number <= 255ul;
    } else if (sizeof_unsigned_long_long_ge_4) {
      const unsigned long long number = std::stoull(value);
      return number <= 255ull;
    } else {
      std::stringstream ss;
      ss
        << "The size of unsigned long was less than 4 (it was "
        << sizeof(unsigned long) << "), and the size of "
        << "unsigned long long was also less than 4 ("
        << "it was " << sizeof(unsigned long long) << "). Hence, we do not "
        << "know how to check for string parsing of "
        << "an unsigned 8-bit integer number.";
      throw std::logic_error(ss.str());
    }
  } catch (const std::invalid_argument&) {
  std::wstringstream wss;
    wss
      << "Unexpected unparsable integer number from "
      << "the value matching the regex: " << value;

    throw std::invalid_argument(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    return false;
  }
}

// NOTE (mristin):
// We use a map instead of a switch statement to check for exhaustiveness.

std::map<
  types::DataTypeDefXsd,
  std::function<bool(const std::wstring&)>
> ConstructDataTypeDefXsdToValueConsistency() {
  std::map<
    types::DataTypeDefXsd,
    std::function<bool(const std::wstring&)>
  > result = {
    {
      types::DataTypeDefXsd::kAnyUri,
      MatchesXsAnyUri
    },
  {
      types::DataTypeDefXsd::kBase64Binary,
      MatchesXsBase64Binary
    },
    {
      types::DataTypeDefXsd::kBoolean,
      MatchesXsBoolean
    },
    {
      types::DataTypeDefXsd::kByte,
      IsXsByte
    },
    {
      types::DataTypeDefXsd::kDate,
      IsXsDate
    },
    {
      types::DataTypeDefXsd::kDateTime,
      IsXsDateTime
    },
    {
      types::DataTypeDefXsd::kDecimal,
      MatchesXsDecimal
    },
    {
      types::DataTypeDefXsd::kDouble,
      IsXsDouble
    },
    {
      types::DataTypeDefXsd::kDuration,
      MatchesXsDuration
    },
    {
      types::DataTypeDefXsd::kFloat,
      IsXsFloat
    },
    {
      types::DataTypeDefXsd::kGDay,
      MatchesXsGDay
    },
    {
      types::DataTypeDefXsd::kGMonth,
      MatchesXsGMonth
    },
    {
      types::DataTypeDefXsd::kGMonthDay,
      IsXsGMonthDay
    },
    {
      types::DataTypeDefXsd::kGYear,
      MatchesXsGYear
    },
    {
      types::DataTypeDefXsd::kGYearMonth,
      MatchesXsGYearMonth
    },
    {
      types::DataTypeDefXsd::kHexBinary,
      MatchesXsHexBinary
    },
    {
      types::DataTypeDefXsd::kInt,
      IsXsInt
    },
    {
      types::DataTypeDefXsd::kInteger,
      MatchesXsInteger
    },
    {
      types::DataTypeDefXsd::kLong,
      IsXsLong
    },
    {
      types::DataTypeDefXsd::kNegativeInteger,
      MatchesXsNegativeInteger
    },
    {
      types::DataTypeDefXsd::kNonNegativeInteger,
      MatchesXsNonNegativeInteger
    },
    {
      types::DataTypeDefXsd::kNonPositiveInteger,
      MatchesXsNonPositiveInteger
    },
    {
      types::DataTypeDefXsd::kPositiveInteger,
      MatchesXsPositiveInteger
    },
    {
      types::DataTypeDefXsd::kShort,
      IsXsShort
    },
    {
      types::DataTypeDefXsd::kString,
      MatchesXsString
    },
    {
      types::DataTypeDefXsd::kTime,
      MatchesXsTime
    },
    {
      types::DataTypeDefXsd::kUnsignedByte,
      IsXsUnsignedByte
    },
    {
      types::DataTypeDefXsd::kUnsignedInt,
      IsXsUnsignedInt
    },
    {
      types::DataTypeDefXsd::kUnsignedLong,
      IsXsUnsignedLong
    },
    {
      types::DataTypeDefXsd::kUnsignedShort,
      IsXsUnsignedShort
    }
  };

  #ifdef DEBUG
  for (types::DataTypeDefXsd literal : iteration::kOverDataTypeDefXsd) {
    const auto it = result.find(literal);
    if (it == result.end()) {
      std::stringstream ss;
      ss
        << "The enumeration literal "
        << stringification::to_string(literal)
        << " of types::DataTypeDefXsd "
        << " is not covered in ConstructDataTypeDefXsdToValueConsistency";
      throw std::logic_error(ss.str());
    }
  }
  #endif

  return result;
}

const std::map<
  types::DataTypeDefXsd,
  std::function<bool(const std::wstring&)>
> kDataTypeDefXsdToValueConsistency(
  ConstructDataTypeDefXsdToValueConsistency()
);


bool ValueConsistentWithXsdType(
  const std::wstring& value,
  types::DataTypeDefXsd value_type
) {
  const auto it = kDataTypeDefXsdToValueConsistency.find(
    value_type
  );

  if (it == kDataTypeDefXsdToValueConsistency.end()) {
    std::ostringstream ss;
    ss
      << "The value type is invalid. Expected a literal of "
      << "types::DataTypeDefXsd, but got: "
      << static_cast<std::uint32_t>(value_type);
    throw std::invalid_argument(ss.str());
  }

  const std::function<bool(const std::wstring&)>& func(
    it->second
  );

  return func(value);
}
