bool DataSpecificationIec61360sHaveDefinitionAtLeastInEnglish(
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
        std::vector<
          std::shared_ptr<types::ILangStringDefinitionTypeIec61360>
        >
      >& maybe_definition = iec61360->definition();

      if (!maybe_definition.has_value()) {
        return false;
      }

      const std::vector<
        std::shared_ptr<types::ILangStringDefinitionTypeIec61360>
      >& definition = *maybe_definition;

      bool no_definition_in_english = true;
      for (const auto& lang_string : definition) {
        if (IsBcp47ForEnglish(lang_string->language())) {
          no_definition_in_english = false;
          break;
        }
      }

      if (no_definition_in_english) {
      	return false;
      }
    }
  }

  return true;
}
