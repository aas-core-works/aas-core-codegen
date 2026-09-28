package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the First type.
 */
public class FirstBuilder {
  private List<String> texts;

  private Long count;

  private Kind kind;

  public FirstBuilder(
    List<String> texts,
    Long count) {
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.count = Objects.requireNonNull(
      count,
      "Argument \"count\" must be non-null.");
  }

  public FirstBuilder setKind(Kind kind) {
    this.kind = kind;
    return this;
  }

  public First build() {
    return new First(
      this.texts,
      this.count,
      this.kind);
  }
}
