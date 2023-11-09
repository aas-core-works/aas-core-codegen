"""Provide common functions shared among different Java code generation modules."""


# noinspection RegExpSimplifiable
PACKAGE_IDENTIFIER_RE = re.compile(
    r"[a-z][a-z_0-9]*(\.[a-z][a-z_0-9]*)*"
)


class PackageIdentifier(str):
    """Capture a package identifier."""

    @require(lambda identifier: PACKAGE_IDENTIFIER_RE.fullmatch(identifier))
    def __new__(cls, identifier: str) -> "PackageIdentifier":
        return cast(PackageIdentifier, identifier)
