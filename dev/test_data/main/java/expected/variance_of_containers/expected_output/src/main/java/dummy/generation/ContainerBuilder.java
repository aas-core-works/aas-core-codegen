package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the Container type.
 */
public class ContainerBuilder {
  private List<IItem> items;

  private List<ISomeItem> someItems;

  private List<ISpecialItem> specialItems;

  public ContainerBuilder(
    List<IItem> items,
    List<ISomeItem> someItems) {
    this.items = Objects.requireNonNull(
      items,
      "Argument \"items\" must be non-null.");
    this.someItems = Objects.requireNonNull(
      someItems,
      "Argument \"someItems\" must be non-null.");
  }

  public ContainerBuilder setSpecialItems(List<ISpecialItem> specialItems) {
    this.specialItems = specialItems;
    return this;
  }

  public Container build() {
    return new Container(
      this.items,
      this.someItems,
      this.specialItems);
  }
}
