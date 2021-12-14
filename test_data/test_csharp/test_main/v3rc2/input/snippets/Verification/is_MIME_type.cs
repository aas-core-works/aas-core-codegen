private static Regex _constructMimeTypeRegex()
{
    var tchar = "[!#$%&'*+\\-.^_`|~0-9a-zA-Z]";
    var token = $"({tchar})+";
    var type = $"{token}";
    var subtype = $"{token}";
    var ows = "[ \t]*";
    var obsText = "[\\x80-\\xff]";
    var qdText = $"([\t !#-\\[\\]-~]|{obsText})";
    var quotedPair = $"\\\\([\t !-~]|{obsText})";
    var quotedString = $"\"({qdText}|{quotedPair})*\"";
    var parameter = $"{token}=({token}|{quotedString})";
    var mediaType = $"{type}/{subtype}({ows};{ows}{parameter})*";
 
    return new Regex(mediaType);
}

private static readonly Regex _MimeTypeRegex = _constructMimeTypeRegex();

/// <summary>
/// Check that the <paramref name="text"/> is a valid MIME type.
/// </summary>
/// <remarks>
/// Related RFCs:
/// <ul>
/// <li>https://www.rfc-editor.org/rfc/rfc7231#section-3.1.1.1,</li>
/// <li>https://www.rfc-editor.org/rfc/rfc7230#section-3.2.3 and</li>
/// <li>https://www.rfc-editor.org/rfc/rfc7230#section-3.2.6</li>
/// </ul>
/// </remarks>
public static bool IsMimeType(string text)
{
    return _MimeTypeRegex.IsMatch(text);
}
