"""Provide entry point if run as a module."""
import sys

import aas_core_csharp_codegen.main

if __name__ == "__main__":
    sys.exit(aas_core_csharp_codegen.main.main(prog="aas_core_csharp_codegen"))
