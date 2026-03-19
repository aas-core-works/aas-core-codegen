// Check that [aastypes.DataSpecificationIec61360.DataType]
// is defined for all data specifications whose content is given as
// IEC 61360.
func DataSpecificationIEC61360sHaveDataType(
	embeddedDataSpecifications []aastypes.IEmbeddedDataSpecification) bool {
	for _, eds := range embeddedDataSpecifications {
		content := eds.DataSpecificationContent()

		ok := aastypes.IsDataSpecificationIEC61360(content)
		if !ok {
			continue
		}
		iec61360 := content.(aastypes.IDataSpecificationIEC61360)

		dt := iec61360.DataType()
		if dt == nil {
			return false
		}
	}
	return true
}
