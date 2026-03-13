/// \brief Check that the types::IDataSpecificationIec61360::definition is defined
/// for all data specifications whose content is given as IEC 61360 at least in English.
bool DataSpecificationIec61360sHaveDefinitionAtLeastInEnglish(
  const std::vector<
    std::shared_ptr<types::IEmbeddedDataSpecification>
  >& embedded_data_specifications
);