/// <summary>
/// Check that all <see cref="Aas.IReferable.IdShort" />'s are among all the
/// <paramref name="inputVariables" />, <paramref name="outputVariables" /> and
/// <paramref name="inoutputVariables" /> are unique.
/// </summary>
public static bool IdShortsOfVariablesAreUnique(
    IEnumerable<Aas.IOperationVariable>? inputVariables,
    IEnumerable<Aas.IOperationVariable>? outputVariables,
    IEnumerable<Aas.IOperationVariable>? inoutputVariables
)
{
    var idShortSet = new HashSet<string>();
    
    if (inputVariables != null)
    {
        foreach (var variable in inputVariables)
        {
            if (variable.Value.IdShort != null)
            {
                if (idShortSet.Contains(variable.Value.IdShort))
                {
                    return false;
                }
                idShortSet.Add(variable.Value.IdShort);
            }
        }
    }

    if (outputVariables != null)
    {
        foreach (var variable in outputVariables)
        {
            if (variable.Value.IdShort != null)
            {
                if (idShortSet.Contains(variable.Value.IdShort))
                {
                    return false;
                }
                idShortSet.Add(variable.Value.IdShort);
            }
        }
    }
    
    if (inoutputVariables != null)
    {
        foreach (var variable in inoutputVariables)
        {
            if (variable.Value.IdShort != null)
            {
                if (idShortSet.Contains(variable.Value.IdShort))
                {
                    return false;
                }
                idShortSet.Add(variable.Value.IdShort);
            }
        }
    }

    return true;
}
