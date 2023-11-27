/**
 * @return if the order of the {@link SubmodelElementList} or the default value if it has not been set.
 */
public Boolean orderRelevantOrDefault() {
  return orderRelevant != null ? orderRelevant : true;
}
