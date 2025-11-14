// Check that [aastypes.DataSpecificationIec61360.Value]
// is defined for all data specifications whose content is given as
// IEC 61360.
func DataSpecificationIEC61360sHaveValue(
	embeddedDataSpecifications []aastypes.IEmbeddedDataSpecification) bool {
	for _, eds := range embeddedDataSpecifications {
		content := eds.DataSpecificationContent()

		ok := aastypes.IsDataSpecificationIEC61360(content)
		if !ok {
			continue
		}
		iec61360 := content.(aastypes.IDataSpecificationIEC61360)

		v := iec61360.Value()
		if v == nil {
			return false
		}
	}
	return true
}
