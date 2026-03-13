/// <summary>
/// Return the <see cref="Qualifier.Kind" /> or the default value
/// if it has not been set.
/// </summary>
public QualifierKind KindOrDefault()
{
    return Kind ?? QualifierKind.ConceptQualifier;
}
