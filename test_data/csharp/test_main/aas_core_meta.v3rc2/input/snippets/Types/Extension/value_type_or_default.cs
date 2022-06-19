/// <summary>
/// Return the <see cref="Extension.ValueType" /> or the default value
/// if it has not been set.
/// </summary>
public DataTypeDefXsd ValueTypeOrDefault()
{
    return ValueType ?? DataTypeDefXsd.String;
}
