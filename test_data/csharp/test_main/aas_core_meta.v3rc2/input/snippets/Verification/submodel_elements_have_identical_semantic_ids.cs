/// <summary>
/// Check that all <paramref name="elements" /> have the identical
/// <see cref="Aas.IHasSemantics.SemanticId" />'s.
/// </summary>
public static bool SubmodelElementsHaveIdenticalSemanticIds(
    IEnumerable<Aas.ISubmodelElement> elements
)
{
            Aas.Reference? thatSemanticId = null;
            bool thatNoKeys = false;

            foreach (var element in elements)
            {
                if (thatSemanticId == null)
                {
                    thatSemanticId = element.SemanticId;
                    thatNoKeys = (
                        element.SemanticId.Keys == null
                        || element.SemanticId.Keys.Count == 0);
                }
                else
                {
                    if (element.SemanticId == null)
                    {
                        return false;
                    }

                    bool thisNoKeys = (
                        element.SemanticId.Keys == null
                        || element.SemanticId.Keys.Count == 0);

                    if (thatNoKeys)
                    {
                        if (!thisNoKeys)
                        {
                            return false;
                        }
                    }
                    else
                    {
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
                }
            }

            return true;
}
