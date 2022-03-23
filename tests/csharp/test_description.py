# pylint: disable=missing-docstring

import textwrap
import unittest.mock

# noinspection PyProtectedMember
import aas_core_codegen.csharp.description as csharp_description
import tests.common
from aas_core_codegen.common import Stripped, Identifier


class Test_to_render_meta_model_description(unittest.TestCase):
    @staticmethod
    def render(source: str) -> Stripped:
        """Generate the C# description comment based on ``source``."""
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        assert (
            symbol_table.meta_model.description is not None
        ), "Expected a meta-model description, but found none."

        code, errors = csharp_description.generate_meta_model_comment(
            symbol_table.meta_model.description
        )
        assert errors is None, tests.common.most_underlying_messages(errors)

        assert code is not None

        return code

    def test_empty_description_not_allowed(self) -> None:
        source = textwrap.dedent(
            '''\
            """"""  # Intentionally left empty

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        _, error = tests.common.translate_source_to_intermediate(source=source)
        assert error is not None
        self.assertEqual(
            "Unexpected empty description", tests.common.most_underlying_messages(error)
        )

    def test_only_summary(self) -> None:
        comment_code = Test_to_render_meta_model_description.render(
            textwrap.dedent(
                '''\
                """Do & drink something."""

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>"""
            ),
            comment_code,
        )


class Test_to_render_symbol_description(unittest.TestCase):
    @staticmethod
    def render(source: str) -> Stripped:
        """
        Generate the C# description comment based on ``source``.

        The ``source`` is expected to contain only a single class, a class
        ``Some_class``.
        """
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        some_class = symbol_table.must_find(Identifier("Some_class"))
        assert some_class.description is not None

        code, errors = csharp_description.generate_symbol_comment(
            some_class.description
        )
        assert errors is None, tests.common.most_underlying_messages(errors)

        assert code is not None

        return code

    def test_empty_description_not_allowed(self) -> None:
        source = textwrap.dedent(
            '''\
            class Some_class:
                """"""  # Intentionally left empty

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        _, error = tests.common.translate_source_to_intermediate(source=source)
        assert error is not None
        self.assertEqual(
            "Unexpected empty description", tests.common.most_underlying_messages(error)
        )

    def test_no_summary(self) -> None:
        source = textwrap.dedent(
            '''\
            class Some_class:
                """
                * Some
                * Bullet
                * List
                """

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        _, error = tests.common.translate_source_to_intermediate(source=source)

        assert error is not None

        self.assertEqual(
            "Expected the first document element to be a summary and thus a paragraph, "
            "but got: "
            '<bullet_list bullet="*">'
            "<list_item><paragraph>Some</paragraph></list_item>"
            "<list_item><paragraph>Bullet</paragraph></list_item>"
            "<list_item><paragraph>List</paragraph></list_item>"
            "</bullet_list>",
            tests.common.most_underlying_messages(error),
        )

    def test_unexpected_directive(self) -> None:
        source = textwrap.dedent(
            '''\
            class Some_class:
                """
                Do something.

                :someDirective:
                    I am unexpected.
                """

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        _, error = tests.common.translate_source_to_intermediate(source=source)

        assert error is not None

        self.assertEqual(
            "Expected only directives such as ``constraint some-identifier`` "
            "in this context, but got a directive with 1 part(s): someDirective",
            tests.common.most_underlying_messages(error),
        )

    def test_only_summary(self) -> None:
        comment_code = Test_to_render_symbol_description.render(
            textwrap.dedent(
                '''\
                class Some_class:
                    """Do & drink something."""

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>"""
            ),
            comment_code,
        )

    def test_summary_with_class_reference(self) -> None:
        comment_code = Test_to_render_symbol_description.render(
            textwrap.dedent(
                '''\
                class Some_class:
                    """Do & drink :class:`.Some_class`."""

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink <see cref="SomeClass" />.
                /// </summary>"""
            ),
            comment_code,
        )

    def test_summary_with_interface_reference(self) -> None:
        comment_code = Test_to_render_symbol_description.render(
            textwrap.dedent(
                '''\
                @abstract
                class Some_class:
                    """Do & drink :class:`.Some_class`."""

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink <see cref="ISomeClass" />.
                /// </summary>"""
            ),
            comment_code,
        )

    def test_summary_with_enumeration_reference(self) -> None:
        comment_code = Test_to_render_symbol_description.render(
            textwrap.dedent(
                '''\
                class Some_class(Enum):
                    """Do & drink :class:`.Some_class`."""

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink <see cref="SomeClass" />.
                /// </summary>"""
            ),
            comment_code,
        )

    def test_summary_and_remarks(self) -> None:
        comment_code = Test_to_render_symbol_description.render(
            textwrap.dedent(
                '''\
                class Some_class:
                    """
                    Do & drink something.

                    First & remark.

                    Second & remark.
                    """

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>
                /// <remarks>
                /// First &amp; remark.
                ///
                /// Second &amp; remark.
                /// </remarks>"""
            ),
            comment_code,
        )

    def test_summary_remarks_and_constraints(self) -> None:
        comment_code = Test_to_render_symbol_description.render(
            textwrap.dedent(
                '''\
                class Some_class:
                    """
                    Do & drink something.

                    First & remark.

                    :constraint AAS-001:
                        You have to do something.
                    """

                __book_url__ = "dummy"
                __book_version__ = "dummy"
                '''
            )
        )
        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Do &amp; drink something.
                /// </summary>
                /// <remarks>
                /// First &amp; remark.
                ///
                /// Constraints:
                /// <ul>
                ///     <li>
                ///     Constraint AAS-001:
                ///     You have to do something.
                ///     </li>
                /// </ul>
                /// </remarks>"""
            ),
            comment_code,
        )


class Test_to_render_signature_description(unittest.TestCase):
    @staticmethod
    def render(source: str) -> Stripped:
        """
        Generate the C# description comment based on ``source``.

        The ``source`` is expected to contain only a single verification function,
        ``verify_something``.
        """
        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        assert error is None, tests.common.most_underlying_messages(error)
        assert symbol_table is not None

        verification = symbol_table.verification_functions_by_name[
            Identifier("verify_something")
        ]

        assert verification.description is not None

        code, errors = csharp_description.generate_signature_comment(
            verification.description
        )
        assert errors is None, tests.common.most_underlying_messages(errors)

        assert code is not None

        return code

    def test_empty_description_not_allowed(self) -> None:
        source = textwrap.dedent(
            '''\
            @verification
            def verify_something(text: str) -> bool:
                """"""  # Intentionally left empty
                return match(r'.*', text) is not None

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        _, error = tests.common.translate_source_to_intermediate(source=source)

        assert error is not None

        self.assertEqual(
            "Unexpected empty description", tests.common.most_underlying_messages(error)
        )

    def test_only_summary(self) -> None:
        source = textwrap.dedent(
            '''\
            @verification
            def verify_something(text: str) -> bool:
                """Verify something."""
                return match(r'.*', text) is not None

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        code = Test_to_render_signature_description.render(source=source)

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Verify something.
                /// </summary>"""
            ),
            code,
        )

    def test_params_and_returns(self) -> None:
        source = textwrap.dedent(
            '''\
            @verification
            def verify_something(text: str) -> bool:
                """
                Verify something.

                :param text: to be checked
                :returns: True if :paramref:`text` is a valid something.
                """
                return match(r'.*', text) is not None

            __book_url__ = "dummy"
            __book_version__ = "dummy"
            '''
        )

        code = Test_to_render_signature_description.render(source=source)

        self.assertEqual(
            textwrap.dedent(
                """\
                /// <summary>
                /// Verify something.
                /// </summary>
                /// <param name="text">
                /// to be checked
                /// </param>
                /// <returns>
                /// True if <paramref name="text" /> is a valid something.
                /// </returns>"""
            ),
            code,
        )


if __name__ == "__main__":
    unittest.main()
