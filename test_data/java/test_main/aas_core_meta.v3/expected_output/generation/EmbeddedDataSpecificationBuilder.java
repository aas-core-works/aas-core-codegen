package aas_core.aas3_0.generation;

import aas_core.aas3_0.types.enums.*;
import aas_core.aas3_0.types.impl.*;
import aas_core.aas3_0.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the EmbeddedDataSpecification type.
 */
public class EmbeddedDataSpecificationBuilder {
  /**
   * Actual content of the data specification
   */
  private IDataSpecificationContent dataSpecificationContent;

  /**
   * Reference to the data specification
   */
  private IReference dataSpecification;

  public EmbeddedDataSpecificationBuilder(IDataSpecificationContent dataSpecificationContent) {
    this.dataSpecificationContent = Objects.requireNonNull(
      dataSpecificationContent,
      "Argument \"dataSpecificationContent\" must be non-null.");
  }

  public EmbeddedDataSpecificationBuilder setDataSpecification(IReference dataSpecification) {
    this.dataSpecification = dataSpecification;
    return this;
  }

  public EmbeddedDataSpecification build() {
    return new EmbeddedDataSpecification(
      this.dataSpecificationContent,
      this.dataSpecification);
  }
}
