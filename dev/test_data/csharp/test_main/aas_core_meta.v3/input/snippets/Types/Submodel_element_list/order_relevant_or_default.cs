/// <summary>
/// Return the <see cref="SubmodelElementList.OrderRelevant" /> or the default value
/// if it has not been set.
/// </summary>
public bool OrderRelevantOrDefault()
{
    return OrderRelevant ?? true;
}
