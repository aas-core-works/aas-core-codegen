"""Check that metadata in ``pyproject.toml`` and ``__init__.py`` are consistent."""

import importlib.metadata
import sys
from typing import List, TypeVar, Protocol, Iterator, Union, Any, Optional, cast

import aas_core_codegen

# NOTE (mristin):
# We found the official PackageMetadata protocol to be unreliable, so we wrote our
# own, closer to the actual implementation.

_T = TypeVar("_T")


class PackageMetadata(Protocol):  # pylint: disable=missing-docstring
    def get_all(self, name: str, failobj: _T = ...) -> Union[List[Any], _T]:
        """
        Return all values associated with a possibly multi-valued key.
        """

    def __getitem__(self, key: str) -> Optional[str]:
        ...  # pragma: no cover

    def __iter__(self) -> Iterator[str]:
        ...  # pragma: no cover

    def __contains__(self, item: str) -> bool:
        ...  # pragma: no cover

    def __len__(self) -> int:
        ...  # pragma: no cover


def _extract_authors(metadata: PackageMetadata) -> List[str]:
    """Extract author names listed in the metadata."""
    author_email = metadata["Author-Email"]

    authors = []
    if author_email is not None:
        # We parse "Name <email>, Name <email>" format.
        for entry in author_email.split(","):
            entry = entry.strip()
            if "<" in entry:
                name = entry.split("<")[0].strip()
                if name:
                    authors.append(name)
            else:
                authors.append(entry)

    # We also check Author field as a fallback.
    try:
        author = metadata["Author"]
    except KeyError:
        author = None

    if author is not None and len(authors) == 0:
        authors = [author.strip()]

    return authors


def _extract_status_from_classifiers(
    metadata: PackageMetadata,
) -> str:
    """Extract development status from classifiers listed in the metadata."""
    classifiers = metadata.get_all("Classifier") or []

    for classifier in classifiers:
        assert isinstance(classifier, str)

        if classifier.startswith("Development Status"):
            parts = classifier.split("::")
            if len(parts) >= 2:
                status = parts[1].strip()
                # We extract just the status part (e.g.,
                # "5 - Production/Stable" -> "Production/Stable")
                if " - " in status:
                    return status.split(" - ", 1)[1]
                return status
    return ""


def _extract_license_from_classifiers(
    metadata: PackageMetadata,
) -> str:
    """Extract license from classifiers listed in the metadata."""
    classifiers = metadata.get_all("Classifier") or []

    for classifier in classifiers:
        assert isinstance(classifier, str)

        if classifier.startswith("License"):
            return classifier
    return ""


def main() -> None:
    """Execute the main routine."""
    errors = []

    metadata = cast(PackageMetadata, importlib.metadata.metadata("aas-core-codegen"))

    # Check version
    init_version = aas_core_codegen.__version__
    pyproject_toml_version = metadata["version"]

    if init_version != pyproject_toml_version:
        errors.append(
            f"Version mismatch: __init__.py has {init_version!r}, "
            f"pyproject.toml has {pyproject_toml_version!r}"
        )

    # Check authors
    init_authors = [author.strip() for author in aas_core_codegen.__author__.split(",")]
    pyproject_authors = _extract_authors(metadata=metadata)

    if init_authors != pyproject_authors:
        errors.append(
            f"Authors mismatch: __init__.py has {init_authors!r}, "
            f"pyproject.toml has {pyproject_authors!r}"
        )

    # Check development status
    init_status = aas_core_codegen.__status__
    pyproject_status = _extract_status_from_classifiers(metadata=metadata)

    if init_status != pyproject_status:
        errors.append(
            f"Status mismatch: __init__.py has {init_status!r}, "
            f"pyproject.toml classifiers have {pyproject_status!r}"
        )

    # Check license
    init_license = aas_core_codegen.__license__
    pyproject_license = _extract_license_from_classifiers(metadata=metadata)

    if init_license != pyproject_license:
        errors.append(
            f"License mismatch: __init__.py has {init_license!r}, "
            f"pyproject.toml classifiers have {pyproject_license!r}"
        )

    if errors:
        print("Metadata consistency check failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)

    print("All meta-data fields are consistent between __init__.py and pyproject.toml")


if __name__ == "__main__":
    main()
