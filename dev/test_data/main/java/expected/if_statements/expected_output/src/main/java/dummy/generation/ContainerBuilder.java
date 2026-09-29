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
  private String optionalText;

  private List<IParent> children;

  public ContainerBuilder setOptionalText(String optionalText) {
    this.optionalText = optionalText;
    return this;
  }

  public ContainerBuilder setChildren(List<IParent> children) {
    this.children = children;
    return this;
  }

  public Container build() {
    return new Container(
      this.optionalText,
      this.children);
  }
}
