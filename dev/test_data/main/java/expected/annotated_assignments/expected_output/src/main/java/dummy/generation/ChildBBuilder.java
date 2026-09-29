package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the ChildB type.
 */
public class ChildBBuilder {
  private String optionalText;

  private Long bOnly;

  public ChildBBuilder(Long bOnly) {
    this.bOnly = Objects.requireNonNull(
      bOnly,
      "Argument \"bOnly\" must be non-null.");
  }

  public ChildBBuilder setOptionalText(String optionalText) {
    this.optionalText = optionalText;
    return this;
  }

  public ChildB build() {
    return new ChildB(
      this.bOnly,
      this.optionalText);
  }
}
