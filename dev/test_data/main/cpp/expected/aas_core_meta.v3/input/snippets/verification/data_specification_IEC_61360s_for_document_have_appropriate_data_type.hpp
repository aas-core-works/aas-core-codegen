/// \brief Check that the types::IDataSpecificationIec61360::data_type is defined
/// appropriately for all data specifications whose content is given as IEC 61360.
bool DataSpecificationIec61360sForDocumentHaveAppropriateDataType(
  const std::vector<
    std::shared_ptr<types::IEmbeddedDataSpecification>
  >& embedded_data_specifications
);