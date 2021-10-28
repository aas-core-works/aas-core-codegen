import textwrap
import unittest.mock

# noinspection PyProtectedMember
import aas_core_csharp_codegen.csharp.structure._generate as csharp_structure_generate
import tests.common
from aas_core_csharp_codegen.common import Stripped, Identifier


class TestDescription(unittest.TestCase):
    @staticmethod
    def render(source: str) -> Stripped:
        """
        Generate the C# description comment based on ``source``.

        The ``source`` is expected to contain only a single entity, a class
        ``Some_class``.
        """
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source)
        assert error is None, f"{error=}"

        some_class = symbol_table.must_find(Identifier('Some_class'))
        assert some_class.description is not None

        code, error = csharp_structure_generate._description_comment(
            some_class.description)
        assert error is None, f"{error=}"

        return code

    def test_empty(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                class Some_class:
                    """"""  # Intentionally left empty    
                '''))

        self.assertEqual('', comment_code)

    def test_only_summary(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                class Some_class:
                    """Do & drink something."""
                '''))

        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>'''), comment_code)

    def test_summary_with_class_reference(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                class Some_class:
                    """Do & drink :class:`.Some_class`."""
                '''))

        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink <see cref="SomeClass" />.
                /// </summary>'''), comment_code)

    def test_summary_with_interface_reference(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                @abstract
                class Some_class:
                    """Do & drink :class:`.Some_class`."""
                '''))

        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink <see cref="ISomeClass" />.
                /// </summary>'''), comment_code)

    def test_summary_with_enumeration_reference(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                class Some_class(Enum):
                    """Do & drink :class:`.Some_class`."""
                '''))

        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink <see cref="SomeClass" />.
                /// </summary>'''), comment_code)

    def test_summary_and_remarks(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                class Some_class:
                    """
                    Do & drink something.
                    
                    First & remark.
                    
                    Second & remark.
                    """
                '''))

        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>
                /// <remarks>
                /// <para>First &amp; remark.</para>
                /// <para>Second &amp; remark.</para>
                /// </remarks>'''),
            comment_code)

    def test_summary_remarks_and_fields(self) -> None:
        comment_code = TestDescription.render(
            textwrap.dedent('''\
                class Some_class:
                    """
                    Do & drink something.
    
                    First & remark.
    
                    :param without_description:
                    :param something: argument description same-line
                    :param another:
                        argument description as paragraph &
                        longer
                        
                        text
                    :returns: some result
                    """
                '''))
        self.assertEqual(
            textwrap.dedent('''\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>
                /// <remarks>
                /// First &amp; remark.
                /// </remarks>
                /// <param name="withoutDescription"></param>
                /// <param name="something">
                ///     argument description same-line
                /// </param>
                /// <param name="another">
                ///     <para>argument description as paragraph &amp;
                ///     longer</para>
                ///     <para>text</para>
                /// </param>
                /// <returns>
                ///     some result
                /// </returns>'''),
            comment_code)


if __name__ == "__main__":
    unittest.main()