// Check that [aastypes.DataSpecificationIec61360.Definition]
// is defined for all data specifications whose content is given as
// IEC 61360 at least in English.
func DataSpecificationIEC61360sHaveDefinitionAtLeastInEnglish(
	embeddedDataSpecifications []aastypes.IEmbeddedDataSpecification) bool {
	for _, eds := range embeddedDataSpecifications {
		content := eds.DataSpecificationContent()

		ok := aastypes.IsDataSpecificationIEC61360(content)
		if !ok {
			continue
		}
		iec61360 := content.(aastypes.IDataSpecificationIEC61360)

		definition := iec61360.Definition()
		if definition == nil {
			return false
		}

		noEnglish := true
		for _, langString := range definition {
			if IsBCP47ForEnglish(langString.Language()) {
				noEnglish = false
				break
			}
		}

		if noEnglish {
			return false
		}
	}
	return true
}
