/// <summary>
/// Check that <paramref name="text" /> reads the same backwards.
/// </summary>
internal static bool IsPalindrome(string text)
{
    for (int i = 0; i < text.Length / 2; i++)
    {
        if (text[i] != text[text.Length - 1 - i])
        {
            return false;
        }
    }
    return true;
}
