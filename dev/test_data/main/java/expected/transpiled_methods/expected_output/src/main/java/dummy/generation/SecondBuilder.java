package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the Second type.
 */
public class SecondBuilder {
  private List<String> texts;

  private Long count;

  private Kind kind;

  private String note;

  public SecondBuilder(
    List<String> texts,
    Long count,
    String note) {
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.count = Objects.requireNonNull(
      count,
      "Argument \"count\" must be non-null.");
    this.note = Objects.requireNonNull(
      note,
      "Argument \"note\" must be non-null.");
  }

  public SecondBuilder setKind(Kind kind) {
    this.kind = kind;
    return this;
  }

  public Second build() {
    return new Second(
      this.texts,
      this.count,
      this.note,
      this.kind);
  }
}
