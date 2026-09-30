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
  private Long number;

  private String text;

  private List<String> texts;

  private IParent parent;

  private String optionalText;

  public SomethingBuilder(
    Long number,
    String text,
    List<String> texts,
    IParent parent) {
    this.number = Objects.requireNonNull(
      number,
      "Argument \"number\" must be non-null.");
    this.text = Objects.requireNonNull(
      text,
      "Argument \"text\" must be non-null.");
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.parent = Objects.requireNonNull(
      parent,
      "Argument \"parent\" must be non-null.");
  }

  public SomethingBuilder setOptionalText(String optionalText) {
    this.optionalText = optionalText;
    return this;
  }

  public Something build() {
    return new Something(
      this.number,
      this.text,
      this.texts,
      this.parent,
      this.optionalText);
  }
}
