#!/usr/bin/env python3

import unittest
import pickle
import textwrap
import os
import sys

from aas_core_codegen.common import Identifier

# Add the parent directory to sys.path so we can import tests.common
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tests.common


class TestPickle(unittest.TestCase):
    """Test cases for pickle functionality of intermediate objects."""

    def test_enumeration_pickle(self):
        """Test that Enumeration objects can be pickled and unpickled correctly."""
        source = textwrap.dedent(
            """\
            from enum import Enum

            class TestEnum(Enum):
                LITERAL1 = "literal_1"
                LITERAL2 = "literal_2"

            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        self.assertIsNone(error, tests.common.most_underlying_messages(error) if error else "")
        self.assertIsNotNone(symbol_table)

        enum = symbol_table.must_find_enumeration(Identifier("TestEnum"))

        # Test that ID sets are working before pickling
        original_id_set = enum.literal_id_set
        self.assertEqual(len(original_id_set), 2)
        self.assertIn(id(enum.literals[0]), original_id_set)
        self.assertIn(id(enum.literals[1]), original_id_set)

        # Pickle and unpickle
        pickled_data = pickle.dumps(enum)
        unpickled_enum = pickle.loads(pickled_data)

        # Test that the unpickled object works correctly
        self.assertEqual(unpickled_enum.name, "TestEnum")
        self.assertEqual(len(unpickled_enum.literals), 2)
        self.assertEqual(unpickled_enum.literals[0].name, "LITERAL1")
        self.assertEqual(unpickled_enum.literals[1].name, "LITERAL2")

        # Test that ID sets are rebuilt correctly
        new_id_set = unpickled_enum.literal_id_set
        self.assertEqual(len(new_id_set), 2)
        self.assertIn(id(unpickled_enum.literals[0]), new_id_set)
        self.assertIn(id(unpickled_enum.literals[1]), new_id_set)

        # The ID sets should be different since objects have new IDs after unpickling
        self.assertNotEqual(original_id_set, new_id_set)

    def test_constant_set_of_enumeration_literals_pickle(self):
        """Test that ConstantSetOfEnumerationLiterals objects can be pickled correctly."""
        source = textwrap.dedent(
            """\
            from enum import Enum

            class TestEnum(Enum):
                LIT1 = "lit1"
                LIT2 = "lit2"

            TEST_CONSTANT_SET: Set[TestEnum] = {TestEnum.LIT1}

            __version__ = "dummy"
            __xml_namespace__ = "https://dummy.com"
            """
        )

        symbol_table, error = tests.common.translate_source_to_intermediate(
            source=source
        )
        self.assertIsNone(error, tests.common.most_underlying_messages(error) if error else "")
        self.assertIsNotNone(symbol_table)

        const_set = symbol_table.must_find_constant_set_of_enumeration_literals(
            Identifier("TEST_CONSTANT_SET")
        )

        # Test before pickling
        original_id_set = const_set.literal_id_set
        self.assertEqual(len(original_id_set), 1)
        self.assertIn(id(const_set.literals[0]), original_id_set)

        # Pickle and unpickle
        pickled_data = pickle.dumps(const_set)
        unpickled_const_set = pickle.loads(pickled_data)

        # Test after unpickling
        self.assertEqual(unpickled_const_set.name, "TEST_CONSTANT_SET")
        self.assertEqual(len(unpickled_const_set.literals), 1)
        self.assertEqual(unpickled_const_set.literals[0].name, "LIT1")

        # Test that ID sets are rebuilt correctly
        new_id_set = unpickled_const_set.literal_id_set
        self.assertEqual(len(new_id_set), 1)
        self.assertIn(id(unpickled_const_set.literals[0]), new_id_set)


if __name__ == "__main__":
    unittest.main()