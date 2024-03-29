/**
* Check that the elements which are
* {@link IProperty} or {@link IRange}
* have the given valueType.
 * @param elements the elements.
 * @param valueType the valueType.
*/
public static boolean propertiesOrRangesHaveValueType(
  Iterable<? extends ISubmodelElement> elements,
  DataTypeDefXsd valueType
) {
  Objects.requireNonNull(elements);
  Objects.requireNonNull(valueType);

  for (ISubmodelElement element : elements) {
     if(element instanceof IProperty) {
       if (((IProperty) element).getValueType() != valueType) {
         return false;
       }
     } else if (element instanceof IRange) {
       if (((IRange) element).getValueType() != valueType) {
         return false;
       }
     }
  }
  return true;
}
