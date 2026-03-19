/**
* Check that there are no duplicate {@link IQualifier#getType() type}'s
* in the qualifiers.
 * @param qualifiers the qualifiers
*/
public static boolean qualifierTypesAreUnique(
  Iterable<IQualifier> qualifiers
) {
  Objects.requireNonNull(qualifiers);

  Set<String> typeSet = new HashSet<>();
  for (IQualifier qualifier : qualifiers) {
    if (typeSet.contains(qualifier.getType())) {
      return false;
    }
    typeSet.add(qualifier.getType());
  }
  return true;
}
