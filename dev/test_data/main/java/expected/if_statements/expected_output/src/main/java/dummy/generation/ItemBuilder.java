package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the Item type.
 */
public class ItemBuilder {
  private String name;

  private String optionalText;

  public ItemBuilder(String name) {
    this.name = Objects.requireNonNull(
      name,
      "Argument \"name\" must be non-null.");
  }

  public ItemBuilder setOptionalText(String optionalText) {
    this.optionalText = optionalText;
    return this;
  }

  public Item build() {
    return new Item(
      this.name,
      this.optionalText);
  }
}
