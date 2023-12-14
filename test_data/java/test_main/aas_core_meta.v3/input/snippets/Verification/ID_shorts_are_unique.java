/**
* Check that all {@link IReferable#getIdShort() idShort}  are unique among referables.
* @param referables the referables.
*/
public static boolean idShortsAreUnique(
        Iterable<IReferable> referables
){
    Set<String> idShortSet = new HashSet<>();
    for (IReferable referable : referables)
    {
        if (referable.getIdShort().isPresent())
        {
            if (idShortSet.contains(referable.getIdShort().get()))
            {
                return false;
            }
            idShortSet.add(referable.getIdShort().get());
        }
    }
    return true;
}
