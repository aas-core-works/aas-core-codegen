bool IsXsDateTime(
  const std::wstring& text
) {
  if (!MatchesXsDateTime(text)) {
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
