"""
TypeScript declares several utility types (see
https://www.typescriptlang.org/docs/handbook/utility-types.html) globally, in
every module, without any import. A class or an enumeration named exactly
after one of them would shadow the global utility type for the rest of the
generated file. This is not merely a cosmetic problem: we ourselves rely on
one of the utility types in the generated code (``Readonly<Class>`` in the
type matcher), so such a shadowing would break our own generated code.

In this test, we explicitly test that such conflicting names are renamed.
"""
from enum import Enum


class Readonly:
    something: str

    def __init__(self, something: str) -> None:
        self.something = something


class Record(Enum):
    Ok = "ok"
    Not_ok = "not-ok"


class Something:
    a_readonly: Readonly
    a_record: Record

    def __init__(self, a_readonly: Readonly, a_record: Record) -> None:
        self.a_readonly = a_readonly
        self.a_record = a_record


__version__ = "dummy"
__xml_namespace__ = "https://dummy.com"
