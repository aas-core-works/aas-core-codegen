# pylint: disable=missing-docstring

import re
import unittest

from aas_core_codegen.golang.lib import _generate_verification as golang_verification
from aas_core_codegen.parse import retree as parse_retree


class TestRegexRenderer(unittest.TestCase):
    def test_encoded_metacharacters(self) -> None:
        for pattern in [
            r"^\x5Btext\x5D$",
            r"^[\x5B\x5D\x5E\x2D\x5C]+$",
            r"^[\x20-\x5B\x5D-\uD7FF]+$",
        ]:
            with self.subTest(pattern=pattern):
                parsed, error = parse_retree.parse([pattern])
                self.assertIsNone(error)
                assert parsed is not None
                rendered = parse_retree.render(
                    parsed, golang_verification.RegexRenderer()
                )
                self.assertEqual(1, len(rendered))
                assert isinstance(rendered[0], str)
                for text in ["[text]", "[", "]", "^", "-", "\\", "text", "\uD7FF"]:
                    with self.subTest(text=text):
                        self.assertEqual(
                            re.fullmatch(pattern, text) is not None,
                            re.fullmatch(rendered[0], text) is not None,
                        )


if __name__ == "__main__":
    unittest.main()
