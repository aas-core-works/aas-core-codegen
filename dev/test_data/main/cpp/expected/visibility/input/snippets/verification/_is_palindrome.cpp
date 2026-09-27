bool IsPalindrome(
  const std::wstring& text
) {
  if (text.empty()) {
    return true;
  }

  for (
    std::size_t i = 0, j = text.size() - 1;
    i < j;
    ++i, --j
  ) {
    if (text[i] != text[j]) {
      return false;
    }
  }

  return true;
}
