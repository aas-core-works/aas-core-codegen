package dummy.generation;

import dummy.common.*;
import dummy.types.enums.*;
import dummy.types.impl.*;
import dummy.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Map;

/**
 * Builder for the Registry type.
 */
public class RegistryBuilder {
  private Map<String, Long> counts;

  private Map<Long, Long> countsByNumber;

  private Map<Direction, Long> weights;

  private Map<String, Kind> kindsByCode;

  private Map<String, String> codesByName;

  private Map<String, IItem> itemsByName;

  private Map<String, List<List<Map<Long, String>>>> labels;

  private Map<String, Long> optionalCounts;

  public RegistryBuilder(
    Map<String, Long> counts,
    Map<Long, Long> countsByNumber,
    Map<Direction, Long> weights,
    Map<String, Kind> kindsByCode,
    Map<String, String> codesByName,
    Map<String, IItem> itemsByName,
    Map<String, List<List<Map<Long, String>>>> labels) {
    this.counts = Objects.requireNonNull(
      counts,
      "Argument \"counts\" must be non-null.");
    this.countsByNumber = Objects.requireNonNull(
      countsByNumber,
      "Argument \"countsByNumber\" must be non-null.");
    this.weights = Objects.requireNonNull(
      weights,
      "Argument \"weights\" must be non-null.");
    this.kindsByCode = Objects.requireNonNull(
      kindsByCode,
      "Argument \"kindsByCode\" must be non-null.");
    this.codesByName = Objects.requireNonNull(
      codesByName,
      "Argument \"codesByName\" must be non-null.");
    this.itemsByName = Objects.requireNonNull(
      itemsByName,
      "Argument \"itemsByName\" must be non-null.");
    this.labels = Objects.requireNonNull(
      labels,
      "Argument \"labels\" must be non-null.");
  }

  public RegistryBuilder setOptionalCounts(Map<String, Long> optionalCounts) {
    this.optionalCounts = optionalCounts;
    return this;
  }

  public Registry build() {
    return new Registry(
      this.counts,
      this.countsByNumber,
      this.weights,
      this.kindsByCode,
      this.codesByName,
      this.itemsByName,
      this.labels,
      this.optionalCounts);
  }
}
