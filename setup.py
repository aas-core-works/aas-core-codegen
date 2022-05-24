"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import os

from setuptools import setup, find_packages

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst"), encoding="utf-8") as fid:
    long_description = fid.read()

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fid:
    install_requires = [line for line in fid.read().splitlines() if line.strip()]

setup(
    name="aas-core-codegen",
    version="0.0.10",
    description="Generate different implementations and schemas based on an AAS meta-model.",
    long_description=long_description,
    url="https://github.com/aas-core-works/aas-core-codegen",
    author="Marko Ristin, Nico Braunisch, Robert Lehmann",
    author_email="marko@ristin.ch",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    license="License :: OSI Approved :: MIT License",
    keywords="asset administration shell code generation industry 4.0 industrie i4.0",
    packages=find_packages(exclude=["tests", "continuous_integration", "dev_scripts"]),
    install_requires=install_requires,
    # fmt: off
    extras_require={
        "dev": [
            "black==22.3.0",
            "mypy==0.930",
            "pylint==2.12.2",
            "pydocstyle>=2.1.1<3",
            "coverage>=4.5.1<5",
            "pygments>=2<3",
            "pyinstaller>=4<5",
            "twine",
            "jsonschema==3.2.0",
            "xmlschema==1.10.0",
            "aas-core-meta==2022.5.30a1",
        ]
    },
    # fmt: on
    py_modules=["aas_core_codegen"],
    package_data={"aas_core_codegen": ["py.typed"]},
    data_files=[(".", ["LICENSE", "README.rst", "requirements.txt"])],
    entry_points={
        "console_scripts": [
            "aas-core-codegen=aas_core_codegen.main:entry_point",
            "aas-core-codegen-smoke=aas_core_codegen.smoke.main:entry_point",
        ]
    },
)
