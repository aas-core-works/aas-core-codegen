public static bool PropertiesOrRangesHaveValueType(
    IEnumerable<Aas.ISubmodelElement> elements,
    Aas.DataTypeDefXsd? valueType
)
{
    // NOTE (mristin, 2022-04-07):
    // We have to use nullable valueType since the compiler does not really handle
    // nullable C# value types.
    //
    // See: https://endjin.com/blog/2022/02/csharp-10-generics-nullable-references-improvements-allownull

    throw new System.NotImplementedException("TODO");
}
