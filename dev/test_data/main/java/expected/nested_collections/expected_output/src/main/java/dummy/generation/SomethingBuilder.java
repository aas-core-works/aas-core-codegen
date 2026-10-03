package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/**
 * Builder for the Something type.
 */
public class SomethingBuilder {
  private List<List<Long>> grid;

  private List<List<Tuple2<Long, Set<String>>>> rowsOfPairs;

  private Tuple3<
    List<IAbstractItem>,
    Set<Color>,
    Tuple2<Long, String>> mixed;

  private List<Set<Color>> setsOfColors;

  private List<List<SomeUnion>> gridOfUnions;

  private List<List<IAbstractItem>> optionalGridOfItems;

  public SomethingBuilder(
    List<List<Long>> grid,
    List<List<Tuple2<Long, Set<String>>>> rowsOfPairs,
    Tuple3<
      List<IAbstractItem>,
      Set<Color>,
      Tuple2<Long, String>> mixed,
    List<Set<Color>> setsOfColors,
    List<List<SomeUnion>> gridOfUnions) {
    this.grid = Objects.requireNonNull(
      grid,
      "Argument \"grid\" must be non-null.");
    this.rowsOfPairs = Objects.requireNonNull(
      rowsOfPairs,
      "Argument \"rowsOfPairs\" must be non-null.");
    this.mixed = Objects.requireNonNull(
      mixed,
      "Argument \"mixed\" must be non-null.");
    this.setsOfColors = Objects.requireNonNull(
      setsOfColors,
      "Argument \"setsOfColors\" must be non-null.");
    this.gridOfUnions = Objects.requireNonNull(
      gridOfUnions,
      "Argument \"gridOfUnions\" must be non-null.");
  }

  public SomethingBuilder setOptionalGridOfItems(List<List<IAbstractItem>> optionalGridOfItems) {
    this.optionalGridOfItems = optionalGridOfItems;
    return this;
  }

  public Something build() {
    return new Something(
      this.grid,
      this.rowsOfPairs,
      this.mixed,
      this.setsOfColors,
      this.gridOfUnions,
      this.optionalGridOfItems);
  }
}
