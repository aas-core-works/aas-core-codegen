/// <summary>
/// Check that the <paramref name="elements" /> which are
/// <see cref="Aas.Property" /> or <see cref="Aas.Range" />
/// have the given <paramref name="valueType" />.
/// </summary>
/// <remarks>
/// We have to use nullable valueType since the compiler does not really handle
/// nullable C# value types.
///
/// See https://endjin.com/blog/2022/02/csharp-10-generics-nullable-references-improvements-allownull
/// </remarks>
public static bool PropertiesOrRangesHaveValueType(
    IEnumerable<Aas.ISubmodelElement> elements,
    Aas.DataTypeDefXsd? valueType
)
{
    foreach (var element in elements)
    {
        switch (element)
        {
            case Aas.Property prop:
                if (prop.ValueType != valueType)
                {
                    return false;
                }
                break;
            case Aas.Range range:
                if (range.ValueType != valueType)
                {
                    return false;
                }
                break;
        }
    }
    return true;
}
