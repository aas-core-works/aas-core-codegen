/// <summary>
/// Check that all <paramref name="elements" /> have the identical
/// <see cref="Our.IHasSemantics.SemanticId" />'s.
/// </summary>
public static bool SubmodelElementsHaveIdenticalSemanticIds(
    IEnumerable<Our.ISubmodelElement> elements
)
{
        Our.IReference? thatSemanticId = null;

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
