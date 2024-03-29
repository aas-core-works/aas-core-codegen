/**
* Check that all {@link IExtension#getName() name}  are unique among extensions.
* @param extensions the extensions
*/
public static boolean extensionNamesAreUnique(
  Iterable<? extends IExtension> extensions) {
  Objects.requireNonNull(extensions);

  Set<String> nameSet = new HashSet<>();

  for (IExtension extension : extensions) {
    if (nameSet.contains(extension.getName())) {
      return false;
    }
    nameSet.add(extension.getName());
  }
  return true;
}
