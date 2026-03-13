bool DataSpecificationIec61360sHaveValue(
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
	  const common::optional<std::wstring>& maybe_value(
        iec61360->value()
      );

      if (!maybe_value.has_value()) {
        return false;
      }
    }
  }

  return true;
}