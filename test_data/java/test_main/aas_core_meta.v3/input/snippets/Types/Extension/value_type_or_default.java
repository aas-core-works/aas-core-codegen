/**
 *  @return the value type {@link DataTypeDefXsd} or the default value if it has not been set.
 */
public DataTypeDefXsd valueTypeOrDefault(){
  return valueType != null ? valueType : DataTypeDefXsd.STRING;
}