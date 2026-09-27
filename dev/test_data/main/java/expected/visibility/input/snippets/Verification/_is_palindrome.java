/**
* Check that the text reads the same backwards.
* @param text the text to be checked
*/
private static boolean isPalindrome(String text) {
  Objects.requireNonNull(text);

  for (int i = 0; i < text.length() / 2; i++) {
    if (text.charAt(i) != text.charAt(text.length() - 1 - i)) {
      return false;
    }
  }
  return true;
}
