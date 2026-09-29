package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the ChildA type.
 */
public class ChildABuilder {
  private String optionalText;

  private Long aOnly;

  public ChildABuilder(Long aOnly) {
    this.aOnly = Objects.requireNonNull(
      aOnly,
      "Argument \"aOnly\" must be non-null.");
  }

  public ChildABuilder setOptionalText(String optionalText) {
    this.optionalText = optionalText;
    return this;
  }

  public ChildA build() {
    return new ChildA(
      this.aOnly,
      this.optionalText);
  }
}
