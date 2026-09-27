def _is_palindrome(text: str) -> bool:
    """Check that :paramref:`text` reads the same backwards."""
    return text == text[::-1]
