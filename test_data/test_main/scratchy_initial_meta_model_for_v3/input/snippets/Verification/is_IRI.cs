private static Regex _constructIriRe() {
    var scheme = "[a-zA-Z][a-zA-Z0-9+\\-.]*";
    var ucschar = (
        "[\\xa0-\\ud7ff\\uf900-\\ufdcf\\ufdf0-\\uffef\\u10000-\\u1fffd"
        "\\u20000-\\u2fffd\\u30000-\\u3fffd\\u40000-\\u4fffd"
        "\\u50000-\\u5fffd\\u60000-\\u6fffd\\u70000-\\u7fffd"
        "\\u80000-\\u8fffd\\u90000-\\u9fffd\\ua0000-\\uafffd"
        "\\ub0000-\\ubfffd\\uc0000-\\ucfffd\\ud0000-\\udfffd"
        "\\ue1000-\\uefffd]"
    );
    var iunreserved = $"([a-zA-Z0-9\\-._~]|{ucschar})";
    var pctEncoded = "%[0-9A-Fa-f][0-9A-Fa-f]";
    var subDelims = $"[!$&'()*+,;=]";
    var iuserinfo = $"({iunreserved}|{pctEncoded}|{subDelims}|:)*";
    var h16 = "[0-9A-Fa-f]{1,4}";
    var dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])";
    var ipv4address = $"{dec_octet}\\.{dec_octet}\\.{dec_octet}\\.{dec_octet}";
    var ls32 = $"({h16}:{h16}|{ipv4address})";
    var ipv6address = (
        f"(({h16}:){{6,6}}{ls32}|::({h16}:){{5,5}}{ls32}|({h16})?::({h16}"
        f":){{4,4}}{ls32}|(({h16}:)?{h16})?::({h16}:){{3,3}}{ls32}|(({h16}"
        f":){{2}}{h16})?::({h16}:){{2,2}}{ls32}|(({h16}:){{3}}{h16})?::{h16}:"
        f"{ls32}|(({h16}:){{4}}{h16})?::{ls32}|(({h16}:){{5}}{h16})?::{h16}|"
        f"(({h16}:){{6}}{h16})?::)"
    );
    var unreserved = "[a-zA-Z0-9\\-._~]";
    var ipvfuture = $"[vV][0-9A-Fa-f]{{1,}}\\.({unreserved}|{subDelims}|:){{1,}}";
    var ipLiteral = $"\\[({ipv6address}|{ipvfuture})\\]";
    var iregName = $"({iunreserved}|{pctEncoded}|{subDelims})*";
    var ihost = $"({ipLiteral}|{ipv4address}|{iregName})";
    var port = "[0-9]*";
    var iauthority = $"({iuserinfo}@)?{ihost}(:{port})?";
    var ipchar = $"({iunreserved}|{pctEncoded}|{subDelims}|[:@])";
    var isegment = $"({ipchar})*";
    var ipath_abempty = $"(/{isegment})*";
    var isegment_nz = $"({ipchar}){{1,}}";
    var ipath_absolute = $"/({isegment_nz}(/{isegment})*)?";
    var ipathRootless = $"{isegment_nz}(/{isegment})*";
    var ipathEmpty = $"({ipchar}){{0,0}}";
    var ihierPart = (
        f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|"
        f"{ipathRootless}|{ipathEmpty})"
    );
    var iprivate = "[\\ue000-\\uf8ff\\uf0000-\\uffffd\\u100000-\\u10fffd]";
    var iquery = $"({ipchar}|{iprivate}|[/?])*";
    var absoluteIri = $"{scheme}:{ihierPart}(\\?{iquery})?";
    var genDelims = "[:/?#\\[\\]@]";
    var ifragment = $"({ipchar}|[/?])*";
    var isegmentNzNc = $"({iunreserved}|{pctEncoded}|{subDelims}|@){{1,}}";
    var ipathNoscheme = $"{isegmentNzNc}(/{isegment})*";
    var ipath = (
        f"({ipath_abempty}|{ipath_absolute}|{ipathNoscheme}|"
        f"{ipathRootless}|{ipathEmpty})"
    );
    var irelativePart = (
        f"(//{iauthority}{ipath_abempty}|{ipath_absolute}|"
        f"{ipathNoscheme}|{ipathEmpty})"
    );
    var irelativeRef = $"{irelativePart}(\\?{iquery})?(\\#{ifragment})?";
    var iri = $"{scheme}:{ihierPart}(\\?{iquery})?(\\#{ifragment})?";
    var iriReference = $"({iri}|{irelativeRef})";
    
    return new Regex(iri);
}

private static Regex _IriRegex = _constructIriRe();

/// <summary>
/// Check that the <paramref name="text"/> is a valid IRI.
/// </summary>
/// <remarks>
/// Related RFC: https://datatracker.ietf.org/doc/html/rfc3987
/// </remarks>
public static bool IsIri(string text) {
    return _IriRegex.IsMatch(text);
}
