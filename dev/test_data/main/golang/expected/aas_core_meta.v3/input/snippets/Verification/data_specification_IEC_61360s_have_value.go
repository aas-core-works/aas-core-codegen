// Check that [ourtypes.DataSpecificationIec61360.Value]
// is defined for all data specifications whose content is given as
// IEC 61360.
func DataSpecificationIEC61360sHaveValue(
	embeddedDataSpecifications []ourtypes.IEmbeddedDataSpecification) bool {
	for _, eds := range embeddedDataSpecifications {
		content := eds.DataSpecificationContent()

		ok := ourtypes.IsDataSpecificationIEC61360(content)
		if !ok {
			continue
		}
		iec61360 := content.(ourtypes.IDataSpecificationIEC61360)

		v := iec61360.Value()
		if v == nil {
			return false
		}
	}
	return true
}
