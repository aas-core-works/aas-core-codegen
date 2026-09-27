/**
 * Check that `text` reads the same backwards.
 *
 * @param text - to be verified
 * @returns `true` if the check passes
 */
function isPalindrome(text: string): boolean {
  const characters = Array.from(text);
  for (let i = 0, j = characters.length - 1; i < j; i++, j--) {
    if (characters[i] !== characters[j]) {
      return false;
    }
  }

  return true;
}
