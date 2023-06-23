// Check that [aastypes.IReferable.IDShort]'s among all the `inputVariables`,
// `outputVariables` and `inoutputVariables` are unique.
func IDShortsOfVariablesAreUnique[O1 aastypes.IOperationVariable,
		O2 aastypes.IOperationVariable,
		O3 aastypes.IOperationVariable] (
	inputVariables []O1,
	outputVariables []O2,
	inoutputVariables []O3) bool {
	idShortSet := make(map[string]struct{})

	var has bool

	if inputVariables != nil {
		for _, variable := range inputVariables {
			idShort := variable.Value().IDShort()

			if idShort != nil {
				_, has = idShortSet[*idShort]
				if has {
					return true
				}

				idShortSet[*idShort] = struct{}{}
			}
		}
	}

	if outputVariables != nil {
		for _, variable := range outputVariables {
			idShort := variable.Value().IDShort()

			if idShort != nil {
				_, has = idShortSet[*idShort]
				if has {
					return true
				}

				idShortSet[*idShort] = struct{}{}
			}
		}
	}

	if inoutputVariables != nil {
		for _, variable := range inoutputVariables {
			idShort := variable.Value().IDShort()

			if idShort != nil {
				_, has = idShortSet[*idShort]
				if has {
					return true
				}

				idShortSet[*idShort] = struct{}{}
			}
		}
	}

	return true
}
