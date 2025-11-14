bool PropertiesOrRangesHaveValueType(
  const std::vector<
    std::shared_ptr<types::ISubmodelElement>
  >& elements,
  types::DataTypeDefXsd value_type
) {
  for (const std::shared_ptr<types::ISubmodelElement>& element : elements) {
    // NOTE (mristin):
    // Dynamic casts are necessary here due to virtual inheritance.

    switch (element->model_type()) {
      case types::ModelType::kProperty: {
        types::IProperty* casted = dynamic_cast<types::IProperty*>(
          element.get()
        );

        if (casted->value_type() != value_type) {
          return false;
        }
        break;
      }
      case types::ModelType::kRange: {
        types::IRange* casted = dynamic_cast<types::IRange*>(
          element.get()
        );

        if (casted->value_type() != value_type) {
          return false;
        }
        break;
      }
    }
  }

  return true;
}
