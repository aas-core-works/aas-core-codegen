package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the SpecialItem type.
 */
public class SpecialItemBuilder {
  private String name;

  private String nickname;

  private Long level;

  public SpecialItemBuilder(
    String name,
    Long level) {
    this.name = Objects.requireNonNull(
      name,
      "Argument \"name\" must be non-null.");
    this.level = Objects.requireNonNull(
      level,
      "Argument \"level\" must be non-null.");
  }

  public SpecialItemBuilder setNickname(String nickname) {
    this.nickname = nickname;
    return this;
  }

  public SpecialItem build() {
    return new SpecialItem(
      this.name,
      this.level,
      this.nickname);
  }
}
