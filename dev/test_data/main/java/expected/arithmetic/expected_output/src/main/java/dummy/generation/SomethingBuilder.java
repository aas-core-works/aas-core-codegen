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
  private Long even;

  private Long offset;

  private Long small;

  private Long byNegative;

  private String text;

  private Long negative;

  private Long deviation;

  private Double ratio;

  private Long alignment;

  private Long optionalNumber;

  private Double optionalRatio;

  public SomethingBuilder(
    Long even,
    Long offset,
    Long small,
    Long byNegative,
    String text,
    Long negative,
    Long deviation,
    Double ratio,
    Long alignment) {
    this.even = Objects.requireNonNull(
      even,
      "Argument \"even\" must be non-null.");
    this.offset = Objects.requireNonNull(
      offset,
      "Argument \"offset\" must be non-null.");
    this.small = Objects.requireNonNull(
      small,
      "Argument \"small\" must be non-null.");
    this.byNegative = Objects.requireNonNull(
      byNegative,
      "Argument \"byNegative\" must be non-null.");
    this.text = Objects.requireNonNull(
      text,
      "Argument \"text\" must be non-null.");
    this.negative = Objects.requireNonNull(
      negative,
      "Argument \"negative\" must be non-null.");
    this.deviation = Objects.requireNonNull(
      deviation,
      "Argument \"deviation\" must be non-null.");
    this.ratio = Objects.requireNonNull(
      ratio,
      "Argument \"ratio\" must be non-null.");
    this.alignment = Objects.requireNonNull(
      alignment,
      "Argument \"alignment\" must be non-null.");
  }

  public SomethingBuilder setOptionalNumber(Long optionalNumber) {
    this.optionalNumber = optionalNumber;
    return this;
  }

  public SomethingBuilder setOptionalRatio(Double optionalRatio) {
    this.optionalRatio = optionalRatio;
    return this;
  }

  public Something build() {
    return new Something(
      this.even,
      this.offset,
      this.small,
      this.byNegative,
      this.text,
      this.negative,
      this.deviation,
      this.ratio,
      this.alignment,
      this.optionalNumber,
      this.optionalRatio);
  }
}
