bool DataSpecificationIec61360sForPropertyOrValueHaveAppropriateDataType(
  const std::vector<
    std::shared_ptr<types::IEmbeddedDataSpecification>
  >& embedded_data_specifications
) {
  for (const auto& embedded_data_specification : embedded_data_specifications) {
    const std::shared_ptr<
      types::IDataSpecificationContent
    >& content(
      embedded_data_specification->data_specification_content()
    );

	// NOTE (mristin):
	// We need to use dynamic cast due to virtual inheritance. Otherwise,
    // we would have used the model_type followed by a static cast.
	const types::IDataSpecificationIec61360* iec61360 = dynamic_cast<
	  const types::IDataSpecificationIec61360*
	>(content.get());

    if (iec61360 != nullptr) {
      const common::optional<
        types::DataTypeIec61360
      >& data_type(
        iec61360->data_type()
      );

      if (
        !data_type.has_value()
        || (
          constants::kDataTypeIec61360ForPropertyOrValue.find(*data_type)
          == constants::kDataTypeIec61360ForPropertyOrValue.end()
        )
      ) {
        return false;
      }
    }
  }

  return true;
}
