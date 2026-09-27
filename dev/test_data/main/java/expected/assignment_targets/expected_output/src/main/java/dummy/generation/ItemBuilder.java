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
  private String text;

  private String maybeText;

  private Kind maybeKind;

  private List<String> texts;

  private List<String> maybeTexts;

  public ItemBuilder(
    String text,
    List<String> texts) {
    this.text = Objects.requireNonNull(
      text,
      "Argument \"text\" must be non-null.");
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
  }

  public ItemBuilder setMaybeText(String maybeText) {
    this.maybeText = maybeText;
    return this;
  }

  public ItemBuilder setMaybeKind(Kind maybeKind) {
    this.maybeKind = maybeKind;
    return this;
  }

  public ItemBuilder setMaybeTexts(List<String> maybeTexts) {
    this.maybeTexts = maybeTexts;
    return this;
  }

  public Item build() {
    return new Item(
      this.text,
      this.texts,
      this.maybeText,
      this.maybeKind,
      this.maybeTexts);
  }
}
