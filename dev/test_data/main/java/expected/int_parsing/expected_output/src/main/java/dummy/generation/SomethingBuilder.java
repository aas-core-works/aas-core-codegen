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
  private String number;

  private String padded;

  private String decimal;

  private String longText;

  private String maybeNumber;

  public SomethingBuilder(
    String number,
    String padded,
    String decimal,
    String longText) {
    this.number = Objects.requireNonNull(
      number,
      "Argument \"number\" must be non-null.");
    this.padded = Objects.requireNonNull(
      padded,
      "Argument \"padded\" must be non-null.");
    this.decimal = Objects.requireNonNull(
      decimal,
      "Argument \"decimal\" must be non-null.");
    this.longText = Objects.requireNonNull(
      longText,
      "Argument \"longText\" must be non-null.");
  }

  public SomethingBuilder setMaybeNumber(String maybeNumber) {
    this.maybeNumber = maybeNumber;
    return this;
  }

  public Something build() {
    return new Something(
      this.number,
      this.padded,
      this.decimal,
      this.longText,
      this.maybeNumber);
  }
}
