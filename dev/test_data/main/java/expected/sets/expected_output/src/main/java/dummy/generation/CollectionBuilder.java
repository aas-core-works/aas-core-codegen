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
 * Builder for the Collection type.
 */
public class CollectionBuilder {
  private Set<String> texts;

  private Set<Long> numbers;

  private Set<Boolean> flags;

  private Set<Direction> directions;

  private Set<String> codes;

  private Set<String> optionalTexts;

  private Set<Direction> optionalDirections;

  public CollectionBuilder(
    Set<String> texts,
    Set<Long> numbers,
    Set<Boolean> flags,
    Set<Direction> directions,
    Set<String> codes) {
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.numbers = Objects.requireNonNull(
      numbers,
      "Argument \"numbers\" must be non-null.");
    this.flags = Objects.requireNonNull(
      flags,
      "Argument \"flags\" must be non-null.");
    this.directions = Objects.requireNonNull(
      directions,
      "Argument \"directions\" must be non-null.");
    this.codes = Objects.requireNonNull(
      codes,
      "Argument \"codes\" must be non-null.");
  }

  public CollectionBuilder setOptionalTexts(Set<String> optionalTexts) {
    this.optionalTexts = optionalTexts;
    return this;
  }

  public CollectionBuilder setOptionalDirections(Set<Direction> optionalDirections) {
    this.optionalDirections = optionalDirections;
    return this;
  }

  public Collection build() {
    return new Collection(
      this.texts,
      this.numbers,
      this.flags,
      this.directions,
      this.codes,
      this.optionalTexts,
      this.optionalDirections);
  }
}
