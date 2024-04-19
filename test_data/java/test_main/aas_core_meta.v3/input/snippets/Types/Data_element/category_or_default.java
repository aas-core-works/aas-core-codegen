/**
 * @return the category or the default value if it has not been set.
 */
public String categoryOrDefault() {
  return category != null ? category : "VARIABLE";
}
