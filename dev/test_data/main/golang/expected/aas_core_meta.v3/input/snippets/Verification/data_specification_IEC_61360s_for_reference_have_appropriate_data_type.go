// Check that [ourtypes.DataSpecificationIec61360.DataType]
// is defined appropriately for all data specifications whose content is given as
// IEC 61360.
func DataSpecificationIEC61360sForReferenceHaveAppropriateDataType(
	embeddedDataSpecifications []ourtypes.IEmbeddedDataSpecification) bool {
	for _, eds := range embeddedDataSpecifications {
		content := eds.DataSpecificationContent()

		ok := ourtypes.IsDataSpecificationIEC61360(content)
		if !ok {
			continue
		}
		iec61360 := content.(ourtypes.IDataSpecificationIEC61360)

		dt := iec61360.DataType()
		if dt == nil ||
			!ourcommon.MapContains(ourconstants.DataTypeIEC61360ForReference, *dt) {
			return false
		}
	}
	return true
}
