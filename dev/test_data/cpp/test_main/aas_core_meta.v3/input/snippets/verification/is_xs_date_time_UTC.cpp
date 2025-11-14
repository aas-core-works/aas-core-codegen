std::vector<
  std::unique_ptr<revm::Instruction>
> ConstructMatchesXsDatePrefixProgram() {
  std::vector<std::unique_ptr<revm::Instruction> > program;
  
  {  // ^(-?[0-9]+)-(0[1-9]|1[0-2])-(0[0-9]|1[0-9]|2[0-9]|30|31).*$
    {  // -?[0-9]+
      {  // -?
        program.emplace_back(
          std::make_unique<revm::InstructionSplit>(1, 2)
        );
        // -
        program.emplace_back(  // 1
          std::make_unique<revm::InstructionChar>(L'-')
        );
      }  // -?
      {  // [0-9]+
        // [0-9]
        program.emplace_back(  // 2
          std::make_unique<revm::InstructionSet>(
            std::vector<revm::Range>{
              revm::Range(L'0', L'9')
            }
          )
        );
        program.emplace_back(
          std::make_unique<revm::InstructionSplit>(2, 4)
        );
      }  // [0-9]+
    }  // -?[0-9]+
    // -
    program.emplace_back(  // 4
      std::make_unique<revm::InstructionChar>(L'-')
    );
    {  // 0[1-9]|1[0-2]
      program.emplace_back(
        std::make_unique<revm::InstructionSplit>(6, 9)
      );
      {  // 0[1-9]
        // 0
        program.emplace_back(  // 6
          std::make_unique<revm::InstructionChar>(L'0')
        );
        // [1-9]
        program.emplace_back(
          std::make_unique<revm::InstructionSet>(
            std::vector<revm::Range>{
              revm::Range(L'1', L'9')
            }
          )
        );
      }  // 0[1-9]
      program.emplace_back(
        std::make_unique<revm::InstructionJump>(11)
      );
      {  // 1[0-2]
        // 1
        program.emplace_back(  // 9
          std::make_unique<revm::InstructionChar>(L'1')
        );
        // [0-2]
        program.emplace_back(
          std::make_unique<revm::InstructionSet>(
            std::vector<revm::Range>{
              revm::Range(L'0', L'2')
            }
          )
        );
      }  // 1[0-2]
    }  // 0[1-9]|1[0-2]
    // -
    program.emplace_back(  // 11
      std::make_unique<revm::InstructionChar>(L'-')
    );
    {  // 0[0-9]|1[0-9]|2[0-9]|30|31
      program.emplace_back(
        std::make_unique<revm::InstructionSplit>(13, 16)
      );
      {  // 0[0-9]
        // 0
        program.emplace_back(  // 13
          std::make_unique<revm::InstructionChar>(L'0')
        );
        // [0-9]
        program.emplace_back(
          std::make_unique<revm::InstructionSet>(
            std::vector<revm::Range>{
              revm::Range(L'0', L'9')
            }
          )
        );
      }  // 0[0-9]
      program.emplace_back(
        std::make_unique<revm::InstructionJump>(30)
      );
      program.emplace_back(  // 16
        std::make_unique<revm::InstructionSplit>(17, 20)
      );
      {  // 1[0-9]
        // 1
        program.emplace_back(  // 17
          std::make_unique<revm::InstructionChar>(L'1')
        );
        // [0-9]
        program.emplace_back(
          std::make_unique<revm::InstructionSet>(
            std::vector<revm::Range>{
              revm::Range(L'0', L'9')
            }
          )
        );
      }  // 1[0-9]
      program.emplace_back(
        std::make_unique<revm::InstructionJump>(30)
      );
      program.emplace_back(  // 20
        std::make_unique<revm::InstructionSplit>(21, 24)
      );
      {  // 2[0-9]
        // 2
        program.emplace_back(  // 21
          std::make_unique<revm::InstructionChar>(L'2')
        );
        // [0-9]
        program.emplace_back(
          std::make_unique<revm::InstructionSet>(
            std::vector<revm::Range>{
              revm::Range(L'0', L'9')
            }
          )
        );
      }  // 2[0-9]
      program.emplace_back(
        std::make_unique<revm::InstructionJump>(30)
      );
      program.emplace_back(  // 24
        std::make_unique<revm::InstructionSplit>(25, 28)
      );
      {  // 30
        // 3
        program.emplace_back(  // 25
          std::make_unique<revm::InstructionChar>(L'3')
        );
        // 0
        program.emplace_back(
          std::make_unique<revm::InstructionChar>(L'0')
        );
      }  // 30
      program.emplace_back(
        std::make_unique<revm::InstructionJump>(30)
      );
      {  // 31
        // 3
        program.emplace_back(  // 28
          std::make_unique<revm::InstructionChar>(L'3')
        );
        // 1
        program.emplace_back(
          std::make_unique<revm::InstructionChar>(L'1')
        );
      }  // 31
    }  // 0[0-9]|1[0-9]|2[0-9]|30|31
    program.emplace_back(  // 30
      std::make_unique<revm::InstructionMatch>()
    );
  }  // ^(-?[0-9]+)-(0[1-9]|1[0-2])-(0[0-9]|1[0-9]|2[0-9]|30|31).*$

  return program;
}

const std::vector<
  std::unique_ptr<revm::Instruction>
> kMatchesXsDatePrefixProgram = ConstructMatchesXsDatePrefixProgram();

bool MatchesXsDatePrefix(
  const std::wstring& text
) {
  return revm::Match(
    kMatchesXsDatePrefixProgram,
    text
  );
}

/**
 * Represent a parsed date from a date string where we ignore the offset.
 */
struct MatchedDatePrefix {
  std::wstring year;
  std::wstring month;
  std::wstring day;

  MatchedDatePrefix(
    std::wstring a_year,
  	std::wstring a_month,
  	std::wstring a_day
  ) :
    year(std::move(a_year)),
    month(std::move(a_month)),
    day(std::move(a_day)) {
    // Intentionally empty.
  }
};  // MatchedDatePrefix

/**
 * Parse the date from the given text where the text is supposed to be an xs:date or
 * an xs:dateTime.
 */
MatchedDatePrefix ParseXsDatePrefix(const std::wstring& text) {
  size_t year_end = 0;
  if (text.size() < 5) {
    throw std::logic_error(
      common::WstringToUtf8(
        common::Concat(
          L"Expected text to be prefixed with a valid xs:date, but it was not: ",
          text
	    )
	  )
	);
  }

  if (text[0] == L'-') {
    ++year_end;
  }

  while (true) {
    if (year_end >= text.size()) {
      throw std::logic_error(
        common::WstringToUtf8(
          common::Concat(
            L"Expected text to be prefixed with a valid xs:date, but it was not: ",
            text
	      )
	    )
	  );
    }

    if (std::isdigit(text[year_end])) {
      ++year_end;
    } else if (text[year_end] == '-') {
      break;
    } else {
      throw std::logic_error(
        common::WstringToUtf8(
          common::Concat(
            L"Expected text to be prefixed with a valid xs:date, but it was not. ",
            L"We encountered an unexpected character while parsing the year: ",
            std::wstring(text[year_end], 1),
            L"; the text was: ",
            text
	      )
	    )
	  );
    }
  }

  const std::wstring year_str = text.substr(0, year_end);

  size_t month_end = year_end + 1;
  while (true) {
    if (month_end >= text.size()) {
      throw std::logic_error(
        common::WstringToUtf8(
          common::Concat(
            L"Expected text to be prefixed with a valid xs:date, but it was not: ",
            text
	      )
	    )
	  );
    }

    if (std::isdigit(text[month_end])) {
      ++month_end;
    } else if (text[month_end] == '-') {
      break;
    } else {
      throw std::logic_error(
        common::WstringToUtf8(
          common::Concat(
            L"Expected text to be prefixed with a valid xs:date, but it was not. ",
			L"We encountered an unexpected character while parsing the month: ",
            std::wstring(text[month_end], 1),
            L"; the text was: ",
            text
	      )
	    )
	  );
    }
  }

  std::wstring month_str = text.substr(year_end + 1, month_end - year_end - 1);

  size_t day_end = month_end + 1;

  while (true) {
    if (day_end == text.size()) {
      break;
    }

    if (std::isdigit(text[day_end])) {
      ++day_end;
    } else if(
      text[day_end] == L'-'
      || text[day_end] == L'+'
      || text[day_end] == L'Z'
      || text[day_end] == L'T'
    ) {
      // We encountered a valid suffix for xs:date offset or time in xs::dateTime.
      break;
    } else {
      throw std::logic_error(
        common::WstringToUtf8(
          common::Concat(
            L"Expected text to be prefixed with a valid xs:date, but it was not. ",
            L"We encountered an unexpected character while parsing the day: ",
            std::wstring(text[day_end], 1),
            L"; the text was: ",
            text
	      )
	    )
	  );
    }
  }

  std::wstring day_str = text.substr(month_end + 1, day_end - month_end - 1);

  return MatchedDatePrefix(year_str, month_str, day_str);
}

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

  if (!MatchesXsDatePrefix(text)) {
    return false;
  }

  // NOTE (mristin):
  // We need to match the prefix as zone offsets are allowed in the dates. Optimally,
  // we would re-use the pattern matching from `MatchesXsDatePrefix`, but this
  // would make the code generation and constraint inference for schemas much more
  // difficult. Hence, we sacrifice the efficiency a bit for the clearer code & code
  // generation.

  // NOTE (mristin):
  // The year can be arbitrarily large in `xs:date` and `xs:dateTime`. Instead of
  // using a BigInt implementation -- and having to maintain another dependency --
  // we simply clip the year to the last four relevant digits for the computation of
  // leap years.

  const MatchedDatePrefix match = ParseXsDatePrefix(text);

  const int era = DetermineEra(match.year);

  // NOTE (mristin):
  // We do not accept year zero, see the note at:
  // https://www.w3.org/TR/xmlschema-2/#dateTime
  if (era == 0) {
    return false;
  }

  std::wstring last_four_year_digits;

  const size_t year_start = (era < 0) ? 1 : 0;
  const size_t end = match.year.size();
  size_t start = end - 4;
  if (start < year_start) {
    start = year_start;
  }

  const std::wstring at_most_last_four_year_digits(
    match.year.substr(start, 4)
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

  const int month = std::stoi(match.month);
  const int day = std::stoi(match.day);

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
