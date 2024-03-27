package aas_core.aas3_0.generation;

import aas_core.aas3_0.types.enums.*;
import aas_core.aas3_0.types.impl.*;
import aas_core.aas3_0.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the SubmodelElementList type.
 */
public class SubmodelelementlistBuilder {
  /**
   * An extension of the element.
   */
  private List<IExtension> extensions;

  /**
   * The category is a value that gives further meta information
   * w.r.t. to the class of the element.
   * It affects the expected existence of attributes and the applicability of
   * constraints.
   *
   * <p>The category is not identical to the semantic definition
   * ({@link IHasSemantics}) of an element. The category e.g. could denote that
   * the element is a measurement value whereas the semantic definition of
   * the element would denote that it is the measured temperature.
   */
  private String category;

  /**
   * In case of identifiables this attribute is a short name of the element.
   * In case of referable this ID is an identifying string of the element within
   * its name space.
   *
   * <p>In case the element is a property and the property has a semantic definition
   * ({@link IHasSemantics#getSemanticId semanticId}) conformant to IEC61360
   * the {@link IReferable#getIdShort idShort} is typically identical to the short name in English.
   */
  private String idShort;

  /**
   * Display name. Can be provided in several languages.
   */
  private List<ILangStringNameType> displayName;

  /**
   * Description or comments on the element.
   *
   * <p>The description can be provided in several languages.
   *
   * <p>If no description is defined, then the definition of the concept
   * description that defines the semantics of the element is used.
   *
   * <p>Additional information can be provided, e.g., if the element is
   * qualified and which qualifier types can be expected in which
   * context or which additional data specification templates are
   * provided.
   */
  private List<ILangStringTextType> description;

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
   * Additional qualification of a qualifiable element.
   *
   * <p>Constraints:
   * <ul>
   *   <li> Constraint AASd-021:
   *   Every qualifiable can only have one qualifier with the same
   *   {@link Qualifier#getType type}.
   * </ul>
   */
  private List<IQualifier> qualifiers;

  /**
   * Embedded data specification.
   */
  private List<IEmbeddedDataSpecification> embeddedDataSpecifications;

  /**
   * Defines whether order in list is relevant. If {@link SubmodelElementList#getOrderRelevant orderRelevant} = {@literal False}
   * then the list is representing a set or a bag.
   *
   * <p>Default: {@literal True}
   */
  private Boolean orderRelevant;

  /**
   * Semantic ID the submodel elements contained in the list match to.
   *
   * <p>It is recommended to use a global reference.
   */
  private IReference semanticIdListElement;

  /**
   * The submodel element type of the submodel elements contained in the list.
   */
  private AasSubmodelElements typeValueListElement;

  /**
   * The value type of the submodel element contained in the list.
   */
  private DataTypeDefXsd valueTypeListElement;

  /**
   * Submodel element contained in the list.
   *
   * <p>The list is ordered.
   */
  private List<ISubmodelElement> value;

  public SubmodelelementlistBuilder(AasSubmodelElements typeValueListElement) {
    this.typeValueListElement = Objects.requireNonNull(
      typeValueListElement,
      "Argument \"typeValueListElement\" must be non-null.");
  }

  public SubmodelelementlistBuilder setExtensions(List<IExtension> extensions) {
    this.extensions = extensions;
    return this;
  }

  public SubmodelelementlistBuilder setCategory(String category) {
    this.category = category;
    return this;
  }

  public SubmodelelementlistBuilder setIdshort(String idShort) {
    this.idShort = idShort;
    return this;
  }

  public SubmodelelementlistBuilder setDisplayname(List<ILangStringNameType> displayName) {
    this.displayName = displayName;
    return this;
  }

  public SubmodelelementlistBuilder setDescription(List<ILangStringTextType> description) {
    this.description = description;
    return this;
  }

  public SubmodelelementlistBuilder setSemanticid(IReference semanticId) {
    this.semanticId = semanticId;
    return this;
  }

  public SubmodelelementlistBuilder setSupplementalsemanticids(List<IReference> supplementalSemanticIds) {
    this.supplementalSemanticIds = supplementalSemanticIds;
    return this;
  }

  public SubmodelelementlistBuilder setQualifiers(List<IQualifier> qualifiers) {
    this.qualifiers = qualifiers;
    return this;
  }

  public SubmodelelementlistBuilder setEmbeddeddataspecifications(List<IEmbeddedDataSpecification> embeddedDataSpecifications) {
    this.embeddedDataSpecifications = embeddedDataSpecifications;
    return this;
  }

  public SubmodelelementlistBuilder setOrderrelevant(Boolean orderRelevant) {
    this.orderRelevant = orderRelevant;
    return this;
  }

  public SubmodelelementlistBuilder setSemanticidlistelement(IReference semanticIdListElement) {
    this.semanticIdListElement = semanticIdListElement;
    return this;
  }

  public SubmodelelementlistBuilder setValuetypelistelement(DataTypeDefXsd valueTypeListElement) {
    this.valueTypeListElement = valueTypeListElement;
    return this;
  }

  public SubmodelelementlistBuilder setValue(List<ISubmodelElement> value) {
    this.value = value;
    return this;
  }

  public SubmodelElementList build() {
    return new SubmodelElementList(
      this.typeValueListElement,
      this.extensions,
      this.category,
      this.idShort,
      this.displayName,
      this.description,
      this.semanticId,
      this.supplementalSemanticIds,
      this.qualifiers,
      this.embeddedDataSpecifications,
      this.orderRelevant,
      this.semanticIdListElement,
      this.valueTypeListElement,
      this.value);
  }
}
