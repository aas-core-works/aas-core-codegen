  /**
   * @return the {@link ModellingKind} or the default value if it has not been set.
   */
  public ModellingKind kindOrDefault(){
    return kind != null ? kind : ModellingKind.INSTANCE;
  }