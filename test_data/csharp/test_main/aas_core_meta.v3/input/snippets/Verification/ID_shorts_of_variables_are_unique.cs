def ID_shorts_of_variables_are_unique(
    input_variables: Optional[List["Operation_variable"]],
    output_variables: Optional[List["Operation_variable"]],
    inoutput_variables: Optional[List["Operation_variable"]],
) -> bool:
    """
    Check that the :attr:`Referable.ID_short`'s among all the
    :paramref:`input_variables`, :paramref:`output_variables`
    and :paramref:`inoutput_variables` are unique.
    """


/// <summary>
/// Check that all <see cref="Aas.IReferable.IdShort" />'s are among all the
/// <paramref name="inputVariables" />, <paramref name="outputVariables" /> and
/// <paramref name="inoutputVariables" /> are unique.
/// </summary>
public static bool IdShortsOfVariablesAreUnique(
    IEnumerable<Aas.OperationVariable>? inputVariables,
    IEnumerable<Aas.OperationVariable>? outputVariables,
    IEnumerable<Aas.OperationVariable>? inoutputVariables,
)
{
    var idShortSet = new HashSet<string>();
    
    if (inputVariables != null)
    {
        foreach (var variable in inputVariables)
        {
            if (idShortSet.Contains(variable.IdShort))
            {
                return false;
            }
            idShortSet.Add(variable.IdShort);
        }
    }

    if (outputVariables != null)
    {
        foreach (var variable in outputVariables)
        {
            if (idShortSet.Contains(variable.IdShort))
            {
                return false;
            }
            idShortSet.Add(variable.IdShort);
        }
    }
    
    if (inoutputVariables != null)
    {
        foreach (var variable in inoutputVariables)
        {
            if (idShortSet.Contains(variable.IdShort))
            {
                return false;
            }
            idShortSet.Add(variable.IdShort);
        }
    }

    return true;
}
