import ast
import textwrap
import unittest
import unittest.mock

import docutils.core

from aas_core_csharp_codegen import intermediate
import aas_core_csharp_codegen.csharp.structure._generate as csharp_structure_generate
from aas_core_csharp_codegen.common import Stripped


class TestDescription(unittest.TestCase):
    @staticmethod
    def render(text: str) -> Stripped:
        document = docutils.core.publish_doctree(text)

        node_mock = unittest.mock.Mock(value="some dummy string")

        description = intermediate.Description(
            document=document,
            node=node_mock)

        code, error = csharp_structure_generate._description_comment(description)
        assert error is None, f'{error}'
        return code

    def test_empty(self) -> None:
        code = TestDescription.render("")
        self.assertEqual('', code)

    def test_only_summary(self) -> None:
        code = TestDescription.render(
            textwrap.dedent("""\
                Do & drink something.
                """)
        )
        self.assertEqual('', code)

    def test_summary_and_remarks(self) -> None:
        code = TestDescription.render(
            textwrap.dedent("""\
                Do & drink something.
                
                First & remark.
                
                Second & remark.
                """)
        )
        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>
                /// <remarks>
                /// <para>First &amp; remark.</para>
                /// <para>Second &amp; remark.</para>
                /// </remarks>'''),
            code)

    def test_summary_remarks_and_fields(self) -> None:
        code = TestDescription.render(
            textwrap.dedent("""\
                Do & drink something.

                First & remark.

                :param without_description:
                :param something: argument description same-line
                :param another:
                    argument description as paragraph &
                    longer
                    
                    text
                :returns: some result
                """))
        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>
                /// <remarks>
                /// First &amp; remark.
                /// </remarks>
                /// <param name="WithoutDescription"></param>
                /// <param name="Something">
                ///     argument description same-line
                /// </param>
                /// <param name="Another">
                ///     <para>argument description as paragraph &amp;
                ///     longer</para>
                ///     <para>text</para>
                /// </param>
                /// <returns>
                ///     some result
                /// </returns>'''),
            code)


if __name__ == "__main__":
    unittest.main()
