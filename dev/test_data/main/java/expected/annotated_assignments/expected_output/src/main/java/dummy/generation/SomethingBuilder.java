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

  private Boolean flag;

  private Kind kind;

  private String code;

  private IItem item;

  private IParent parent;

  private List<IParent> parents;

  private List<String> texts;

  private String optionalText;

  private Kind optionalKind;

  private IParent optionalParent;

  private List<String> optionalTexts;

  private byte[] optionalData;

  private ParentOrItem optionalMember;

  public SomethingBuilder(
    String text,
    Long number,
    Boolean flag,
    Kind kind,
    String code,
    IItem item,
    IParent parent,
    List<IParent> parents,
    List<String> texts) {
    this.text = Objects.requireNonNull(
      text,
      "Argument \"text\" must be non-null.");
    this.number = Objects.requireNonNull(
      number,
      "Argument \"number\" must be non-null.");
    this.flag = Objects.requireNonNull(
      flag,
      "Argument \"flag\" must be non-null.");
    this.kind = Objects.requireNonNull(
      kind,
      "Argument \"kind\" must be non-null.");
    this.code = Objects.requireNonNull(
      code,
      "Argument \"code\" must be non-null.");
    this.item = Objects.requireNonNull(
      item,
      "Argument \"item\" must be non-null.");
    this.parent = Objects.requireNonNull(
      parent,
      "Argument \"parent\" must be non-null.");
    this.parents = Objects.requireNonNull(
      parents,
      "Argument \"parents\" must be non-null.");
    this.texts = Objects.requireNonNull(
      texts,
      "Argument \"texts\" must be non-null.");
  }

  public SomethingBuilder setOptionalText(String optionalText) {
    this.optionalText = optionalText;
    return this;
  }

  public SomethingBuilder setOptionalKind(Kind optionalKind) {
    this.optionalKind = optionalKind;
    return this;
  }

  public SomethingBuilder setOptionalParent(IParent optionalParent) {
    this.optionalParent = optionalParent;
    return this;
  }

  public SomethingBuilder setOptionalTexts(List<String> optionalTexts) {
    this.optionalTexts = optionalTexts;
    return this;
  }

  public SomethingBuilder setOptionalData(byte[] optionalData) {
    this.optionalData = optionalData;
    return this;
  }

  public SomethingBuilder setOptionalMember(ParentOrItem optionalMember) {
    this.optionalMember = optionalMember;
    return this;
  }

  public Something build() {
    return new Something(
      this.text,
      this.number,
      this.flag,
      this.kind,
      this.code,
      this.item,
      this.parent,
      this.parents,
      this.texts,
      this.optionalText,
      this.optionalKind,
      this.optionalParent,
      this.optionalTexts,
      this.optionalData,
      this.optionalMember);
  }
}
