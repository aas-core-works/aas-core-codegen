package aas_core.aas3_0.generation;

import aas_core.aas3_0.types.enums.*;
import aas_core.aas3_0.types.impl.*;
import aas_core.aas3_0.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the DataSpecificationIec61360 type.
 */
public class DataSpecificationIec61360Builder {
  /**
   * Preferred name
   *
   * <p>It is advised to keep the length of the name limited to 35 characters.
   *
   * <p>Constraints:
   * <ul>
   *   <li> Constraint AASc-3a-002:
   *   {@link DataSpecificationIec61360#getPreferredName preferredName} shall be provided at least in English.
   * </ul>
   */
  private List<ILangStringPreferredNameTypeIec61360> preferredName;

  /**
   * Short name
   */
  private List<ILangStringShortNameTypeIec61360> shortName;

  /**
   * Unit
   */
  private String unit;

  /**
   * Unique unit id
   *
   * <p>{@link DataSpecificationIec61360#getUnit unit} and {@link DataSpecificationIec61360#getUnitId unitId} need to be consistent if both attributes
   * are set
   *
   * <p>It is recommended to use an external reference ID.
   */
  private IReference unitId;

  /**
   * Source of definition
   */
  private String sourceOfDefinition;

  /**
   * Symbol
   */
  private String symbol;

  /**
   * Data Type
   */
  private DataTypeIec61360 dataType;

  /**
   * Definition in different languages
   */
  private List<ILangStringDefinitionTypeIec61360> definition;

  /**
   * Value Format
   *
   * <p>The value format is based on ISO 13584-42 and IEC 61360-2.
   */
  private String valueFormat;

  /**
   * List of allowed values
   */
  private IValueList valueList;

  /**
   * Value
   */
  private String value;

  /**
   * Set of levels.
   */
  private ILevelType levelType;

  public DataSpecificationIec61360Builder(List<ILangStringPreferredNameTypeIec61360> preferredName) {
    this.preferredName = Objects.requireNonNull(
      preferredName,
      "Argument \"preferredName\" must be non-null.");
  }

  public DataSpecificationIec61360Builder setShortname(List<ILangStringShortNameTypeIec61360> shortName) {
    this.shortName = shortName;
    return this;
  }

  public DataSpecificationIec61360Builder setUnit(String unit) {
    this.unit = unit;
    return this;
  }

  public DataSpecificationIec61360Builder setUnitid(IReference unitId) {
    this.unitId = unitId;
    return this;
  }

  public DataSpecificationIec61360Builder setSourceofdefinition(String sourceOfDefinition) {
    this.sourceOfDefinition = sourceOfDefinition;
    return this;
  }

  public DataSpecificationIec61360Builder setSymbol(String symbol) {
    this.symbol = symbol;
    return this;
  }

  public DataSpecificationIec61360Builder setDatatype(DataTypeIec61360 dataType) {
    this.dataType = dataType;
    return this;
  }

  public DataSpecificationIec61360Builder setDefinition(List<ILangStringDefinitionTypeIec61360> definition) {
    this.definition = definition;
    return this;
  }

  public DataSpecificationIec61360Builder setValueformat(String valueFormat) {
    this.valueFormat = valueFormat;
    return this;
  }

  public DataSpecificationIec61360Builder setValuelist(IValueList valueList) {
    this.valueList = valueList;
    return this;
  }

  public DataSpecificationIec61360Builder setValue(String value) {
    this.value = value;
    return this;
  }

  public DataSpecificationIec61360Builder setLeveltype(ILevelType levelType) {
    this.levelType = levelType;
    return this;
  }

  public DataSpecificationIec61360 build() {
    return new DataSpecificationIec61360(
      this.preferredName,
      this.shortName,
      this.unit,
      this.unitId,
      this.sourceOfDefinition,
      this.symbol,
      this.dataType,
      this.definition,
      this.valueFormat,
      this.valueList,
      this.value,
      this.levelType);
  }
}
