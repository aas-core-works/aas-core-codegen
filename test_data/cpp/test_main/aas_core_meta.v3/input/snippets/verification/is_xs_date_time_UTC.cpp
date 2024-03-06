const std::wregex kRegexDatePrefix(
  L"^(-?[0-9]+)-(0[1-9]|11|12)-(0[0-9]|1[0-9]|2[0-9]|30|31)"
);

bool IsLeapYear(long long year) {
  // NOTE (mristin):
  // We consider the years B.C. to be one-off.
  // See the note at: https://www.w3.org/TR/xmlschema-2/#dateTime:
  // "'-0001' is the lexical representation of the year 1 Before Common Era
  // (1 BCE, sometimes written "1 BC")."
  //
  // Hence, -1 year in XML is 1 BCE, which is 0 year in astronomical years.
  if (year < 0) {
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
 * \brief Check that \p value is a valid `xs:date`.
 *
 * Year 1 BCE is the last leap BCE year.
 * See: https://www.w3.org/TR/xmlschema-2/#dateTime.
 *
 * \param value to be checked
 * \return true if \p value is a valid `xs:date`
 */
bool IsXsDate(
  const std::wstring& text
) {
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

  long long year;

  try {
    year = std::stoll(match[1].str());
  } catch (const std::invalid_argument&) {
    std::wstringstream wss;
    wss
      << "The year matched the regex, but could not be parsed as integer: "
      << match[1].str();

    throw std::logic_error(
      common::WstringToUtf8(wss.str())
    );
  } catch (const std::out_of_range&) {
    std::wstringstream wss;
    wss
      << "The year is out of range for long long integers: "
      << match[1].str()
      << (
        "; we at aas-core-works planned to include handling of BigInt years "
        "in the SDK, but eventually lacked the time for it. Please let the developers "
        "know that you need this feature."
      );

    throw std::out_of_range(
      common::WstringToUtf8(wss.str())
    );
  }

  const int month = std::stoi(match[2].str());
  const int day = std::stoi(match[3].str());

  // NOTE (mristin):
  // We do not accept year zero, see the note at:
  // https://www.w3.org/TR/xmlschema-2/#dateTime
  if (year == 0) {
    return false;
  }

  if (day <= 0) {
    return false;
  }

  if (month <= 0 || month >= 13) {
    return false;
  }

  const int max_days(
  	(month == 2)
	  ? (IsLeapYear(year) ? 29 : 28)
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

  return IsXsDate(date);
}
