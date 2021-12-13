import textwrap
import unittest

import continuous_integration.reformat


class Test_reformat(unittest.TestCase):
    def test_empty(self) -> None:
        text = ''

        out = continuous_integration.reformat.reformat(text=text)
        self.assertEqual('', out)

    def test_no_error_import_from_aas_core_codegen_does_not_reformat(self) -> None:
        text = textwrap.dedent('''\
            import sys
            from something import Error
            
            print("hello")
            sys.exit(1)
            ''')

        out = continuous_integration.reformat.reformat(text=text)
        self.assertEqual(text, out)

    def test_return_error(self) -> None:
        # TODO: re-run
        text = textwrap.dedent('''\
            import sys
            from aas_core_codegen.common import (
                Error,
                SomethingElse
            )

            return Error(
                some_node, 
                message="some test "
                "on more lines", underlying=underlying_errors
            )
            ''')

        out = continuous_integration.reformat.reformat(text=text)

        expected = textwrap.dedent('''\
            import sys
            from aas_core_codegen.common import (
                Error,
                SomethingElse
            )

            return Error(
                some_node, 
                "some test "
                "on more lines, 
                underlying_errors)
            ''')

        self.assertEqual(expected, out)

    def test_return_none_error(self) -> None:
        # TODO: re-run
        text = textwrap.dedent('''\
            import sys
            from aas_core_codegen.common import (
                Error,
                SomethingElse
            )

            return (
                None, 
                Error(
                    some_node, 
                    message="some test "
                    "on more lines", 
                    underlying=underlying_errors
                )
            )
            ''')

        out = continuous_integration.reformat.reformat(text=text)

        expected = textwrap.dedent('''\
            import sys
            from aas_core_codegen.common import (
                Error,
                SomethingElse
            )

            return None, Error(
                some_node, 
                "some test "
                "on more lines", 
                underlying_errors))
            ''')

        self.assertEqual(expected, out)

if __name__ == "__main__":
    unittest.main()
