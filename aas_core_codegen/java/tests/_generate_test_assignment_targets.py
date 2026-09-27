"""Generate code to test the assignments to the properties and the list items."""

from typing import List

from icontract import require

from aas_core_codegen import intermediate, tests_common
from aas_core_codegen.common import Stripped, indent_but_first_line
from aas_core_codegen.java import common as java_common
from aas_core_codegen.java.common import (
    INDENT as I,
    INDENT2 as II,
)


# fmt: off
@require(
    lambda symbol_table:
    tests_common.defines_assignment_target_verifications(symbol_table)
)
# fmt: on
def generate(
    package: java_common.PackageIdentifier,
    symbol_table: intermediate.SymbolTable,
) -> List[java_common.JavaFile]:
    """
    Generate code to test the assignments to the properties and the list items.

    The tests call the verification functions of the meta-model
    ``dev/test_data/common_meta_models/assignment_targets.py``, see
    :py:mod:`aas_core_codegen.tests_common`.
    """
    blocks = [
        Stripped(
            f"""\
@Test
public void testSetText() {{
{I}Item item = new Item("a", new ArrayList<>(Arrays.asList("b")));
{I}Verification.setText(item, "x");
{I}assertEquals("x", item.getText());
}} // public void testSetText"""
        ),
        Stripped(
            f"""\
@Test
public void testSetMaybeText() {{
{I}Item item = new Item("a", new ArrayList<>());
{I}Verification.setMaybeText(item, "x");
{I}assertEquals(Optional.of("x"), item.getMaybeText());
}} // public void testSetMaybeText"""
        ),
        Stripped(
            f"""\
@Test
public void testCopyMaybeTextAndSetMaybeKind() {{
{I}Item item = new Item("a", new ArrayList<>(), "old", null);
{I}Item other = new Item("b", new ArrayList<>());
{I}Verification.copyMaybeTextAndSetMaybeKind(item, other);
{I}assertEquals(Optional.empty(), item.getMaybeText());
{I}assertEquals(Optional.of(Kind.ALPHA), item.getMaybeKind());
}} // public void testCopyMaybeTextAndSetMaybeKind"""
        ),
        Stripped(
            f"""\
@Test
public void testSetTextThroughAlias() {{
{I}Item item = new Item("a", new ArrayList<>());
{I}Verification.setTextThroughAlias(item, "x");
{I}assertEquals("x", item.getText());
}} // public void testSetTextThroughAlias"""
        ),
        Stripped(
            f"""\
@Test
public void testSetTexts() {{
{I}Item item = new Item("a", new ArrayList<>(Arrays.asList("b")));
{I}List<String> texts = new ArrayList<>(Arrays.asList("x", "y"));
{I}Verification.setTexts(item, texts);
{I}assertSame(texts, item.getTexts());
}} // public void testSetTexts"""
        ),
        Stripped(
            f"""\
@Test
public void testSetFirstAndLastText() {{
{I}Item item = new Item("a", new ArrayList<>(Arrays.asList("a", "b", "c")));
{I}Verification.setFirstAndLastText(item, "x");
{I}assertEquals(Arrays.asList("x", "b", "x"), item.getTexts());
}} // public void testSetFirstAndLastText"""
        ),
        Stripped(
            f"""\
@Test
public void testSetTextThroughListAlias() {{
{I}Item item = new Item("a", new ArrayList<>(Arrays.asList("a", "b", "c")));
{I}Verification.setTextThroughListAlias(item, "x");
{I}assertEquals(Arrays.asList("a", "x", "c"), item.getTexts());
}} // public void testSetTextThroughListAlias"""
        ),
        Stripped(
            f"""\
@Test
public void testSetNumbers() {{
{I}List<Long> numbers = new ArrayList<>(Arrays.asList(1L, 2L, 3L, 4L));
{I}Verification.setNumbers(numbers, 10L);
{I}assertEquals(Arrays.asList(10L, 2L, 5L, 4L), numbers);
}} // public void testSetNumbers"""
        ),
        Stripped(
            f"""\
@Test
public void testSetNumbersOutOfRange() {{
{I}List<Long> numbers = new ArrayList<>(Arrays.asList(1L));
{I}assertThrows(
{II}IndexOutOfBoundsException.class,
{II}() -> Verification.setNumbers(numbers, 10L));
}} // public void testSetNumbersOutOfRange"""
        ),
        Stripped(
            f"""\
@Test
public void testSetNestedText() {{
{I}List<IItem> items = new ArrayList<>(Arrays.asList(
{II}new Item("a", new ArrayList<>(Arrays.asList("a", "b"))),
{II}new Item("b", new ArrayList<>(Arrays.asList("c")))));
{I}Verification.setNestedText(items, "x");
{I}assertEquals(Arrays.asList("a", "x"), items.get(0).getTexts());
{I}assertEquals("x", items.get(1).getText());
}} // public void testSetNestedText"""
        ),
        Stripped(
            f"""\
@Test
public void testReplaceFirstItem() {{
{I}List<IItem> items = new ArrayList<>(Arrays.asList(
{II}new Item("a", new ArrayList<>()),
{II}new Item("b", new ArrayList<>())));
{I}Item item = new Item("c", new ArrayList<>());
{I}Verification.replaceFirstItem(items, item);
{I}assertSame(item, items.get(0));
{I}assertEquals(2, items.size());
}} // public void testReplaceFirstItem"""
        ),
        Stripped(
            f"""\
@Test
public void testSetTextsInLoops() {{
{I}List<IItem> items = new ArrayList<>(Arrays.asList(
{II}new Item("a", new ArrayList<>(Arrays.asList("a"))),
{II}new Item("b", new ArrayList<>(Arrays.asList("b", "c")))));
{I}Verification.setTextsInLoops(items, "x");
{I}for (IItem item : items) {{
{II}assertEquals("x", item.getText());
{II}assertEquals("x", item.getTexts().get(0));
{I}}}
}} // public void testSetTextsInLoops"""
        ),
    ]  # type: List[Stripped]

    blocks_joined = "\n\n".join(blocks)

    return [
        java_common.JavaFile(
            "TestAssignmentTargets.java",
            f"""\
{java_common.WARNING}

package {package}.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import {package}.types.enums.Kind;
import {package}.types.impl.Item;
import {package}.types.model.IItem;
import {package}.verification.Verification;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/**
 * Test the assignments to the properties and to the items of the lists
 * in the verification functions.
 *
 * <p>The meta-model is written in Python, so the assignments follow the Python
 * semantics: the objects and the lists are shared by reference, and
 * a negative index counts from the end of the list.
 */
public class TestAssignmentTargets {{
{I}{indent_but_first_line(blocks_joined, I)}
}} // class TestAssignmentTargets

// package {package}.tests

{java_common.WARNING}
""",
        )
    ]


assert generate.__doc__ is not None
assert generate.__doc__.strip().startswith(__doc__.strip())
