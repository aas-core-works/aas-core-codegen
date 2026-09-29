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
  private String text;

  private Long number;

  private Kind kind;

  private List<String> texts;

  private List<Long> numbers;

  private List<Kind> kinds;

  private List<String> codes;

  private List<Boolean> flags;

  private List<String> optionalTexts;

  private Kind optionalKind;

  public SomethingBuilder(
    String text,
    Long number,
    Kind kind,
    List<String> texts,
    List<Long> numbers,
    List<Kind> kinds,
    List<String> codes,
    List<Boolean> flags) {
    this.text = Objects.requireNonNull(
      text,
      "Argument \"text\" must be non-null.");
    this.number = Objects.requireNonNull(
      number,
      "Argument \"number\" must be non-null.");
    this.kind = Objects.requireNonNull(
      kind,
      "Argument \"kind\" must be non-null.");
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
    this.numbers = Objects.requireNonNull(
      numbers,
      "Argument \"numbers\" must be non-null.");
    this.kinds = Objects.requireNonNull(
      kinds,
      "Argument \"kinds\" must be non-null.");
    this.codes = Objects.requireNonNull(
      codes,
      "Argument \"codes\" must be non-null.");
    this.flags = Objects.requireNonNull(
      flags,
      "Argument \"flags\" must be non-null.");
  }

  public SomethingBuilder setOptionalTexts(List<String> optionalTexts) {
    this.optionalTexts = optionalTexts;
    return this;
  }

  public SomethingBuilder setOptionalKind(Kind optionalKind) {
    this.optionalKind = optionalKind;
    return this;
  }

  public Something build() {
    return new Something(
      this.text,
      this.number,
      this.kind,
      this.texts,
      this.numbers,
      this.kinds,
      this.codes,
      this.flags,
      this.optionalTexts,
      this.optionalKind);
  }
}
