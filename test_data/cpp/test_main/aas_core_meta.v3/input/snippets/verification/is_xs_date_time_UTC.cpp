const std::wregex kRegexDatePrefix(
  L"^(-?[0-9]+)-(0[1-9]|1[0-2])-(0[0-9]|1[0-9]|2[0-9]|30|31)"
);

/**
 * Determine the sign of the given year as text.
 *
 * @param year_str year as text
 * @return -1, 0 or 1; -1 means BC, 1 means AD. 0 means a zero year,
 * even if specified as -0.
 */
int DetermineEra(const std::wstring& year_str) {
  #ifdef DEBUG
  if (year_str.empty()) {
    throw std::invalid_argument(
      "Expected a valid year string, but got an empty string"
    );
  }
  #endif

  const int sign = (year_str[0] == L'-') ? -1 : 1;

  size_t cursor = 0;
  if (sign < 0) {
    // NOTE (mristin):
    // We skip the minus sign as prefix, including the edge case "-0".
    ++cursor;
  }

  bool is_zero = true;
  for (; cursor < year_str.size(); ++cursor) {
    if (year_str[cursor] != L'0') {
      is_zero = false;
      break;
    }
  }

  if (is_zero) {
    return 0;
  }

  return sign;
}

const std::map<int, int> kDaysInMonth = {
  {1, 31},
  // Please use IsLeapYear if you need to check
  // whether a concrete February has 28 or 29 days.
  {2, 29},
  {3, 31},
  {4, 30},
  {5, 31},
  {6, 30},
  {7, 31},
  {8, 31},
  {9, 30},
  {10, 31},
  {11, 30},
  {12, 31}
};

/**
 * \brief Check that \p value is a valid `xs:date` without the offset.
 *
 * Year 1 BCE is the last leap BCE year.
 * See: https://www.w3.org/TR/xmlschema-2/#dateTime.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:date`
 */
bool IsXsDateWithoutOffset(const std::wstring& text) {
  // NOTE (mristin):
  // We can not use date functions from the operation system as they do not
  // handle years BCE (*e.g.*, `-0003-01-02`).

  std::wsmatch match;
  const bool matched = std::regex_match(text, match, kRegexDatePrefix);

  if (!matched) {
    return false;
  }

  // NOTE (mristin):
  // We need to match the prefix as zone offsets are allowed in the dates. Optimally,
  // we would re-use the pattern matching from `MatchesXsDate`, but this
  // would make the code generation and constraint inference for schemas much more
  // difficult. Hence, we sacrifice the efficiency a bit for the clearer code & code
  // generation.

  // NOTE (mristin):
  // The year can be arbitrarily large in `xs:date` and `xs:dateTime`. Instead of
  // using a BigInt implementation -- and having to maintain another dependency --
  // we simply clip the year to the last four relevant digits for the computation of
  // leap years.

  const std::wstring year_str = match[1].str();

  const int era = DetermineEra(year_str);

  // NOTE (mristin):
  // We do not accept year zero, see the note at:
  // https://www.w3.org/TR/xmlschema-2/#dateTime
  if (era == 0) {
    return false;
  }

  std::wstring last_four_year_digits;

  const size_t year_start = (era < 0) ? 1 : 0;
  const size_t end = year_str.size();
  size_t start = end - 4;
  if (start < year_start) {
    start = year_start;
  }

  const std::wstring at_most_last_four_year_digits(
    year_str.substr(start, 4)
  );

  int year_suffix = era * std::stoi(at_most_last_four_year_digits);

  // NOTE (mristin):
  // We consider the years B.C. to be one-off.
  // See the note at: https://www.w3.org/TR/xmlschema-2/#dateTime:
  // "'-0001' is the lexical representation of the year 1 Before Common Era
  // (1 BCE, sometimes written "1 BC")."
  //
  // Hence, -1 year in XML is 1 BCE, which is 0 year in astronomical years.
  if (year_suffix < 0) {
    year_suffix = -year_suffix - 1;
  }

  bool is_leap_year = true;

  if (year_suffix % 4 > 0) {
    is_leap_year = false;
  } else if (year_suffix % 100 > 0) {
    is_leap_year = true;
  } else if (year_suffix % 400 > 0) {
    is_leap_year = false;
  }

  const int month = std::stoi(match[2].str());
  const int day = std::stoi(match[3].str());

  if (day <= 0) {
    return false;
  }

  if (month <= 0 || month >= 13) {
    return false;
  }

  const int max_days(
  	(month == 2)
	  ? (is_leap_year ? 29 : 28)
      : kDaysInMonth.at(month)
  );

  if (day > max_days) {
    return false;
  }

  return true;
}

bool IsXsDateTimeUtc(
  const std::wstring& text
) {
  if (!MatchesXsDateTimeUtc(text)) {
    return false;
  }

  const size_t pos = text.find(L'T');
  if (pos == std::wstring::npos) {
    std::wstringstream wss;
    wss
      << L"Expected 'T' in the date-time if it matches the expected regex, "
      << L"but got: "
      << text;

    throw std::logic_error(
      common::WstringToUtf8(wss.str())
    );
  }

  // NOTE (mristin):
  // We make a copy here to be compatible with C++11. Optimally, a string view
  // should be used here.
  std::wstring date = text.substr(0, pos);

  return IsXsDateWithoutOffset(date);
}
