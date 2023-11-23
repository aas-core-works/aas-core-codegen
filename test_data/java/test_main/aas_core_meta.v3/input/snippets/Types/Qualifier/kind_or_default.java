  /**
   * @return the {@link QualifierKind} or the default value if it has not been set.
   */
  public QualifierKind kindOrDefault(){
    return kind != null ? kind : QualifierKind.CONCEPT_QUALIFIER;
  }