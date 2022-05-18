/// <summary>
/// Return the <see cref="Aas.Extension.ValueType" /> or the default value
/// if it has not been set.
/// </summary>
public Aas.DataTypeDefXsd ValueTypeOrDefault()
{
    return (this.valueType != null)
        ? this.valueType
        : Aas.DataTypeDefXsd.String;
}
