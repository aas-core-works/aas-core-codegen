/// <summary>
/// Return the <see cref="ModelingKind.Kind" /> or the default value
/// if it has not been set.
/// </summary>
public ModelingKind KindOrDefault()
{
    return this.Kind ?? ModelingKind.Instance;
}
