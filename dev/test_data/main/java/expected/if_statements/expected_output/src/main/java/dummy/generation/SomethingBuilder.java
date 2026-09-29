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
  private Kind kind;

  private String text;

  private Long number;

  private Boolean flag;

  private IItem item;

  private IParent optionalParent;

  private List<IParent> parents;

  public SomethingBuilder(
    Kind kind,
    String text,
    Long number,
    Boolean flag,
    IItem item) {
    this.kind = Objects.requireNonNull(
      kind,
      "Argument \"kind\" must be non-null.");
    this.text = Objects.requireNonNull(
      text,
      "Argument \"text\" must be non-null.");
    this.number = Objects.requireNonNull(
      number,
      "Argument \"number\" must be non-null.");
    this.flag = Objects.requireNonNull(
      flag,
      "Argument \"flag\" must be non-null.");
    this.item = Objects.requireNonNull(
      item,
      "Argument \"item\" must be non-null.");
  }

  public SomethingBuilder setOptionalParent(IParent optionalParent) {
    this.optionalParent = optionalParent;
    return this;
  }

  public SomethingBuilder setParents(List<IParent> parents) {
    this.parents = parents;
    return this;
  }

  public Something build() {
    return new Something(
      this.kind,
      this.text,
      this.number,
      this.flag,
      this.item,
      this.optionalParent,
      this.parents);
  }
}
