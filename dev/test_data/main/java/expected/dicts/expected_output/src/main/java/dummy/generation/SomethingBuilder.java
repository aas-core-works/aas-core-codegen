package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the Something type.
 */
public class SomethingBuilder {
  private List<String> texts;

  private List<Long> numbers;

  private List<Kind> kinds;

  private List<String> codes;

  private List<IItem> items;

  private List<String> optionalTexts;

  public SomethingBuilder(
    List<String> texts,
    List<Long> numbers,
    List<Kind> kinds,
    List<String> codes,
    List<IItem> items) {
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.numbers = Objects.requireNonNull(
      numbers,
      "Argument \"numbers\" must be non-null.");
    this.kinds = Objects.requireNonNull(
      kinds,
      "Argument \"kinds\" must be non-null.");
    this.codes = Objects.requireNonNull(
      codes,
      "Argument \"codes\" must be non-null.");
    this.items = Objects.requireNonNull(
      items,
      "Argument \"items\" must be non-null.");
  }

  public SomethingBuilder setOptionalTexts(List<String> optionalTexts) {
    this.optionalTexts = optionalTexts;
    return this;
  }

  public Something build() {
    return new Something(
      this.texts,
      this.numbers,
      this.kinds,
      this.codes,
      this.items,
      this.optionalTexts);
  }
}
