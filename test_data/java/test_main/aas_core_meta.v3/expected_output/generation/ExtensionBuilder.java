package aas_core.aas3_0.generation;

import aas_core.aas3_0.types.enums.*;
import aas_core.aas3_0.types.impl.*;
import aas_core.aas3_0.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the Extension type.
 */
public class ExtensionBuilder {
  /**
   * Identifier of the semantic definition of the element. It is called semantic ID
   * of the element or also main semantic ID of the element.
   *
   * <p>It is recommended to use a global reference.
   */
  private IReference semanticId;

  /**
   * Identifier of a supplemental semantic definition of the element.
   * It is called supplemental semantic ID of the element.
   *
   * <p>It is recommended to use a global reference.
   */
  private List<IReference> supplementalSemanticIds;

  /**
   * Name of the extension.
   *
   * <p>Constraints:
   * <ul>
   *   <li> Constraint AASd-077:
   *   The name of an extension (Extension/name) within {@link IHasExtensions} needs
   *   to be unique.
   * </ul>
   */
  private String name;

  /**
   * Type of the value of the extension.
   *
   * <p>Default: {@link DataTypeDefXsd#STRING}
   */
  private DataTypeDefXsd valueType;

  /**
   * Value of the extension
   */
  private String value;

  /**
   * Reference to an element the extension refers to.
   */
  private List<IReference> refersTo;

  public ExtensionBuilder(String name) {
    this.name = Objects.requireNonNull(
      name,
      "Argument \"name\" must be non-null.");
  }

  public ExtensionBuilder setSemanticid(IReference semanticId) {
    this.semanticId = semanticId;
    return this;
  }

  public ExtensionBuilder setSupplementalsemanticids(List<IReference> supplementalSemanticIds) {
    this.supplementalSemanticIds = supplementalSemanticIds;
    return this;
  }

  public ExtensionBuilder setValuetype(DataTypeDefXsd valueType) {
    this.valueType = valueType;
    return this;
  }

  public ExtensionBuilder setValue(String value) {
    this.value = value;
    return this;
  }

  public ExtensionBuilder setRefersto(List<IReference> refersTo) {
    this.refersTo = refersTo;
    return this;
  }

  public Extension build() {
    return new Extension(
      this.name,
      this.semanticId,
      this.supplementalSemanticIds,
      this.valueType,
      this.value,
      this.refersTo);
  }
}
