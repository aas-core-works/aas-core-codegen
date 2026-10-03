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
  private List<String> texts;

  private List<Kind> kinds;

  private List<String> optionalTexts;

  public SomethingBuilder(
    List<String> texts,
    List<Kind> kinds) {
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.kinds = Objects.requireNonNull(
      kinds,
      "Argument \"kinds\" must be non-null.");
  }

  public SomethingBuilder setOptionalTexts(List<String> optionalTexts) {
    this.optionalTexts = optionalTexts;
    return this;
  }

  public Something build() {
    return new Something(
      this.texts,
      this.kinds,
      this.optionalTexts);
  }
}
