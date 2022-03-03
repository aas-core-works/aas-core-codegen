"""Fetch meta-models from aas-core-meta repository."""

import argparse
import os
import pathlib
import sys
import urllib.request


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    repo_root = this_path.parent.parent

    raw_aas_core_meta_url = (
        "https://raw.githubusercontent.com/aas-core-works/aas-core-meta/main"
    )

    sources_targets = [
        (
            f"{raw_aas_core_meta_url}/aas_core_meta/v3rc1.py",
            repo_root / "test_data/jsonschema/test_main/v3rc1/input/meta_model.py",
        ),
        (
            f"{raw_aas_core_meta_url}/aas_core_meta/v3rc1.py",
            repo_root / "test_data/rdf_shacl/test_main/v3rc1/input/meta_model.py",
        ),
        (
            f"{raw_aas_core_meta_url}/aas_core_meta/v3rc2.py",
            repo_root / "test_data/csharp/test_main/v3rc2/input/meta_model.py",
        ),
        (
            f"{raw_aas_core_meta_url}/aas_core_meta/v3rc2.py",
            repo_root
            / "test_data/intermediate/expected/real_meta_models/v3rc2/meta_model.py",
        ),
        (
            f"{raw_aas_core_meta_url}/aas_core_meta/v3rc2.py",
            repo_root / "test_data/jsonschema/test_main/v3rc2/input/meta_model.py",
        ),
        (
            f"{raw_aas_core_meta_url}/aas_core_meta/v3rc2.py",
            repo_root / "test_data/parse/expected/real_meta_models/v3rc2/meta_model.py",
        ),
    ]

    for url, tgt_pth in sources_targets:
        print(f"Downloading {url} to {tgt_pth.relative_to(repo_root)}...")
        urllib.request.urlretrieve(url=url, filename=str(tgt_pth))

    return 0


if __name__ == "__main__":
    sys.exit(main())
