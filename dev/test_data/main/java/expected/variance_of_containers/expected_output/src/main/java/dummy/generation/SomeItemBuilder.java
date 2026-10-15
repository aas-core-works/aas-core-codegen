package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the SomeItem type.
 */
public class SomeItemBuilder {
  private String name;

  private String nickname;

  public SomeItemBuilder(String name) {
    this.name = Objects.requireNonNull(
      name,
      "Argument \"name\" must be non-null.");
  }

  public SomeItemBuilder setNickname(String nickname) {
    this.nickname = nickname;
    return this;
  }

  public SomeItem build() {
    return new SomeItem(
      this.name,
      this.nickname);
  }
}
