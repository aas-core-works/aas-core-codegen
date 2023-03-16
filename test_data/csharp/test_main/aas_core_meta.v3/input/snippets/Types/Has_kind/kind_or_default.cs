/// <summary>
/// Return the <see cref="IHasKind.Kind" /> or the default value
/// if it has not been set.
/// </summary>
public ModellingKind KindOrDefault()
{
    return Kind ?? ModellingKind.Instance;
}
