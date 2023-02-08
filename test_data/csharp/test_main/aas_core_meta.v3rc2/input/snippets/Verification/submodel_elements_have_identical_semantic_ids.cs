/// <summary>
/// Check that all <paramref name="elements" /> have the identical
/// <see cref="Aas.IHasSemantics.SemanticId" />'s.
/// </summary>
public static bool SubmodelElementsHaveIdenticalSemanticIds(
    IEnumerable<Aas.ISubmodelElement> elements
)
{
        Aas.IReference? thatSemanticId = null;

        foreach (var element in elements)
        {
            if (element.SemanticId == null)
            {
                continue;
            }

            if (thatSemanticId == null)
            {
                thatSemanticId = element.SemanticId;
                continue;
            }

            var thisSemanticId = element.SemanticId;

            if (thatSemanticId.Keys.Count != thisSemanticId.Keys.Count)
            {
                return false;
            }

            for (int i = 0; i < thisSemanticId.Keys.Count; i++)
            {
                if (thatSemanticId.Keys[i].Value != thisSemanticId.Keys[i].Value)
                {
                    return false;
                }
            }
        }

        return true;
}
