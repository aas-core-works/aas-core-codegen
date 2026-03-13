std::map<
  types::AasSubmodelElements,
  std::function<bool(const std::shared_ptr<types::ISubmodelElement>&)>
> ConstructAasSubmodelElementToIs() {
  std::map<
    types::AasSubmodelElements,
    std::function<bool(const std::shared_ptr<types::ISubmodelElement>&)>
  > result = {
    {
      types::AasSubmodelElements::kAnnotatedRelationshipElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsAnnotatedRelationshipElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kBasicEventElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsBasicEventElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kBlob,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsBlob(*element);
      }
    },
    {
      types::AasSubmodelElements::kCapability,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsCapability(*element);
      }
    },
    {
      types::AasSubmodelElements::kDataElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsDataElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kEntity,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsEntity(*element);
      }
    },
    {
      types::AasSubmodelElements::kEventElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsEventElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kFile,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsFile(*element);
      }
    },
    {
      types::AasSubmodelElements::kMultiLanguageProperty,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsMultiLanguageProperty(*element);
      }
    },
    {
      types::AasSubmodelElements::kOperation,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsOperation(*element);
      }
    },
    {
      types::AasSubmodelElements::kProperty,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsProperty(*element);
      }
    },
    {
      types::AasSubmodelElements::kRange,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsRange(*element);
      }
    },
    {
      types::AasSubmodelElements::kReferenceElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsReferenceElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kRelationshipElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsRelationshipElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kSubmodelElement,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsSubmodelElement(*element);
      }
    },
    {
      types::AasSubmodelElements::kSubmodelElementList,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsSubmodelElementList(*element);
      }
    },
    {
      types::AasSubmodelElements::kSubmodelElementCollection,
      [](const std::shared_ptr<types::ISubmodelElement>& element) {
        return types::IsSubmodelElementCollection(*element);
      }
    }
  };

  #ifdef DEBUG
  for (types::AasSubmodelElements literal : iteration::kOverAasSubmodelElements) {
    const auto it = result.find(literal);
    if (it == result.end()) {
      throw std::logic_error(
        common::Concat(
          "The enumeration literal ",
          std::to_string(static_cast<std::uint32_t>(literal)),
          " of types::AasSubmodelElements "
          " is not covered in ConstructAasSubmodelElementToIs"
        )
      );
    }
  }
  #endif

  return result;
}

const std::map<
  types::AasSubmodelElements,
  std::function<bool(const std::shared_ptr<types::ISubmodelElement>&)>
> kAasSubmodelElementToIs = ConstructAasSubmodelElementToIs();

bool SubmodelElementIsOfType(
  const std::shared_ptr<types::ISubmodelElement>& element,
  types::AasSubmodelElements element_type
) {
  const auto it = kAasSubmodelElementToIs.find(element_type);
  if (it == kAasSubmodelElementToIs.end()) {
    throw std::invalid_argument(
      common::Concat(
        "Unexpected element type: ",
        std::to_string(static_cast<uint32_t>(element_type))
      )
    );
  }

  const std::function<
    bool(const std::shared_ptr<types::ISubmodelElement>&)
  >& is_function(
    it->second
  );

  return is_function(element);
}
