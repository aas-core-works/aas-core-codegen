  /**
   * @return the value type or the default value.
   */
  public DataTypeDefXsd valueTypeOrDefault(){
    return valueType != null ? valueType : DataTypeDefXsd.STRING;
  }