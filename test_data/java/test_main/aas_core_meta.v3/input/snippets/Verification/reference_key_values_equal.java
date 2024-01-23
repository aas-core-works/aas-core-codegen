/**
* Check that the two references,'that' and
* 'other', are equal by comparing
* their {@link IReference#getKeys() keys} by
* {@link IKey#getValue() value}'s.
*/
public static boolean referenceKeyValuesEqual(
  IReference that,
  IReference other) {
  if (that.getKeys().size() != other.getKeys().size()) {
    return false;
  }

  for (int i = 0; i < that.getKeys().size(); i++) {
    if (!Objects.equals(that.getKeys().get(i).getValue(), other.getKeys().get(i).getValue())) {
      return false;
    }
  }

  return true;
}
