import os
import pathlib
import textwrap
import unittest.mock

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

class Test_against_recorded(unittest.TestCase):
    # Set this variable to True if you want to re-record the test data,
    # without any checks
    RERECORD = True  # TODO: undo

    def test_on_meta_models(self) -> None:
        this_dir = pathlib.Path(os.path.realpath(__file__)).parent
        meta_models_dir = this_dir.parent / "test_data/meta_models"

        assert meta_models_dir.exists(), f"{meta_models_dir=}"
        assert meta_models_dir.is_dir(), f"{meta_models_dir=}"

        for meta_model_dir in meta_models_dir.iterdir():
            assert meta_model_dir.is_dir(), f"{meta_model_dir}"

            meta_model_pth = meta_model_dir / "meta_model.py"

            # TODO: move testing against meta-model to tests/csharp/test-end-to-end
            # TODO: arrange the expected files accordingly


        for source_pth in test_cases_dir.glob("**/source.py"):
            case_dir = source_pth.parent

            expected_symbol_table_pth = case_dir / "expected_symbol_table.txt"
            expected_error_pth = case_dir / "expected_error.txt"

            source = source_pth.read_text()
            symbol_table, error = tests.common.translate_source_to_intermediate(
                source=source)

            symbol_table_str = (
                "" if symbol_table is None
                else intermediate.dump(symbol_table)
            )

            error_str = (
                "" if error is None
                else tests.common.most_underlying_message(error)
            )

            if Test_against_recorded.RERECORD:
                expected_symbol_table_pth.write_text(symbol_table_str)
                expected_error_pth.write_text(error_str)
            else:
                expected_symbol_table_str = expected_symbol_table_pth.read_text()
                self.assertEqual(
                    expected_symbol_table_str, symbol_table_str,
                    f"{case_dir=}, {error=}")

                expected_error_str = expected_error_pth.read_text()
                self.assertEqual(expected_error_str, error_str, f"{case_dir=}")


if __name__ == "__main__":
    unittest.main()
