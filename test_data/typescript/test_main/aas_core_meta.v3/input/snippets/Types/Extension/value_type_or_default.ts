/**
 * @returns {@link valueType} if set or the default value otherwise.
 */
valueTypeOrDefault(): DataTypeDefXsd {
    return (this.valueType !== null)
        ? this.valueType
        : DataTypeDefXsd.String;
}
