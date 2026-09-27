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
  private List<Long> numbers;

  private List<String> texts;

  private Long count;

  private Long maybeCount;

  public SomethingBuilder(
    List<Long> numbers,
    List<String> texts,
    Long count) {
    this.numbers = Objects.requireNonNull(
      numbers,
      "Argument \"numbers\" must be non-null.");
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.count = Objects.requireNonNull(
      count,
      "Argument \"count\" must be non-null.");
  }

  public SomethingBuilder setMaybeCount(Long maybeCount) {
    this.maybeCount = maybeCount;
    return this;
  }

  public Something build() {
    return new Something(
      this.numbers,
      this.texts,
      this.count,
      this.maybeCount);
  }
}
