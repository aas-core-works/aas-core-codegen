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
  private List<IItem> items;

  private IItem maybeItem;

  public SomethingBuilder(List<IItem> items) {
    this.items = Objects.requireNonNull(
      items,
      "Argument \"items\" must be non-null.");
  }

  public SomethingBuilder setMaybeItem(IItem maybeItem) {
    this.maybeItem = maybeItem;
    return this;
  }

  public Something build() {
    return new Something(
      this.items,
      this.maybeItem);
  }
}
