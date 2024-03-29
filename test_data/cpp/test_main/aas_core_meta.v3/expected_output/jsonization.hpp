#ifndef AAS_CORE_AAS_3_0_JSONIZATION_GUARD_
#define AAS_CORE_AAS_3_0_JSONIZATION_GUARD_

// This code has been automatically generated by aas-core-codegen.
// Do NOT edit or append.

#include "aas_core/aas_3_0/common.hpp"
#include "aas_core/aas_3_0/iteration.hpp"
#include "aas_core/aas_3_0/types.hpp"

#pragma warning(push, 0)
#include <nlohmann/json.hpp>

#include <memory>
#include <string>
#include <utility>
#pragma warning(pop)

namespace aas_core {
namespace aas_3_0 {

/**
 * \defgroup jsonization De/serialize instances from and to JSON.
 * @{
 */
namespace jsonization {

/**
 * Represent a segment of a JSON path to some value.
 */
class ISegment {
 public:
  /**
   * \brief Convert the segment to a string in a JSON path.
   */
  virtual std::wstring ToWstring() const = 0;

  virtual std::unique_ptr<ISegment> Clone() const = 0;

  virtual ~ISegment() = default;
};  // class ISegment

/**
 * Represent a property access on a JSON path.
 */
struct PropertySegment : public ISegment {
  /**
   * Name of the property in a JSON object
   */
  std::wstring name;

  PropertySegment(
    std::wstring a_name
  );

  std::wstring ToWstring() const override;

  std::unique_ptr<ISegment> Clone() const override;

  ~PropertySegment() override = default;
};  // struct PropertySegment

/**
 * Represent an index access on a JSON path.
 */
struct IndexSegment : public ISegment {
  /**
   * Index of the value in an array.
   */
  size_t index;

  explicit IndexSegment(
    size_t an_index
  );

  std::wstring ToWstring() const override;

  std::unique_ptr<ISegment> Clone() const override;

  ~IndexSegment() override = default;
};  // struct IndexSegment

/**
 * Represent a JSON path to some value.
 */
struct Path {
  std::deque<std::unique_ptr<ISegment> > segments;

  Path();
  Path(const Path& other);
  Path(Path&& other);
  Path& operator=(const Path& other);
  Path& operator=(Path&& other);

  std::wstring ToWstring() const;
};  // struct Path

// region De-serialization

/**
 * Represent a de-serialization error.
 */
struct DeserializationError {
  /**
   * Human-readable description of the error
   */
  std::wstring cause;

  /**
   * Path to the erroneous value
   */
  Path path;

  explicit DeserializationError(std::wstring a_cause);
  DeserializationError(std::wstring a_cause, Path a_path);
};  // struct DeserializationError

/**
 * \brief Deserialize \p json value to an instance
 * of types::IHasSemantics.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IHasSemantics>,
  DeserializationError
> HasSemanticsFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IExtension.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IExtension>,
  DeserializationError
> ExtensionFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IHasExtensions.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IHasExtensions>,
  DeserializationError
> HasExtensionsFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IReferable.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IReferable>,
  DeserializationError
> ReferableFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IIdentifiable.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IIdentifiable>,
  DeserializationError
> IdentifiableFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IHasKind.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IHasKind>,
  DeserializationError
> HasKindFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IHasDataSpecification.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IHasDataSpecification>,
  DeserializationError
> HasDataSpecificationFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IAdministrativeInformation.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IAdministrativeInformation>,
  DeserializationError
> AdministrativeInformationFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IQualifiable.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IQualifiable>,
  DeserializationError
> QualifiableFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IQualifier.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IQualifier>,
  DeserializationError
> QualifierFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IAssetAdministrationShell.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IAssetAdministrationShell>,
  DeserializationError
> AssetAdministrationShellFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IAssetInformation.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IAssetInformation>,
  DeserializationError
> AssetInformationFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IResource.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IResource>,
  DeserializationError
> ResourceFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ISpecificAssetId.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ISpecificAssetId>,
  DeserializationError
> SpecificAssetIdFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ISubmodel.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ISubmodel>,
  DeserializationError
> SubmodelFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ISubmodelElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ISubmodelElement>,
  DeserializationError
> SubmodelElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IRelationshipElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IRelationshipElement>,
  DeserializationError
> RelationshipElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ISubmodelElementList.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ISubmodelElementList>,
  DeserializationError
> SubmodelElementListFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ISubmodelElementCollection.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ISubmodelElementCollection>,
  DeserializationError
> SubmodelElementCollectionFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IDataElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IDataElement>,
  DeserializationError
> DataElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IProperty.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IProperty>,
  DeserializationError
> PropertyFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IMultiLanguageProperty.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IMultiLanguageProperty>,
  DeserializationError
> MultiLanguagePropertyFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IRange.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IRange>,
  DeserializationError
> RangeFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IReferenceElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IReferenceElement>,
  DeserializationError
> ReferenceElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IBlob.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IBlob>,
  DeserializationError
> BlobFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IFile.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IFile>,
  DeserializationError
> FileFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IAnnotatedRelationshipElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IAnnotatedRelationshipElement>,
  DeserializationError
> AnnotatedRelationshipElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IEntity.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IEntity>,
  DeserializationError
> EntityFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IEventPayload.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IEventPayload>,
  DeserializationError
> EventPayloadFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IEventElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IEventElement>,
  DeserializationError
> EventElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IBasicEventElement.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IBasicEventElement>,
  DeserializationError
> BasicEventElementFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IOperation.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IOperation>,
  DeserializationError
> OperationFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IOperationVariable.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IOperationVariable>,
  DeserializationError
> OperationVariableFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ICapability.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ICapability>,
  DeserializationError
> CapabilityFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IConceptDescription.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IConceptDescription>,
  DeserializationError
> ConceptDescriptionFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IReference.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IReference>,
  DeserializationError
> ReferenceFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IKey.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IKey>,
  DeserializationError
> KeyFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IAbstractLangString.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IAbstractLangString>,
  DeserializationError
> AbstractLangStringFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ILangStringNameType.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ILangStringNameType>,
  DeserializationError
> LangStringNameTypeFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ILangStringTextType.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ILangStringTextType>,
  DeserializationError
> LangStringTextTypeFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IEnvironment.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IEnvironment>,
  DeserializationError
> EnvironmentFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IDataSpecificationContent.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IDataSpecificationContent>,
  DeserializationError
> DataSpecificationContentFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IEmbeddedDataSpecification.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IEmbeddedDataSpecification>,
  DeserializationError
> EmbeddedDataSpecificationFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ILevelType.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ILevelType>,
  DeserializationError
> LevelTypeFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IValueReferencePair.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IValueReferencePair>,
  DeserializationError
> ValueReferencePairFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IValueList.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IValueList>,
  DeserializationError
> ValueListFrom(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ILangStringPreferredNameTypeIec61360.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ILangStringPreferredNameTypeIec61360>,
  DeserializationError
> LangStringPreferredNameTypeIec61360From(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ILangStringShortNameTypeIec61360.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ILangStringShortNameTypeIec61360>,
  DeserializationError
> LangStringShortNameTypeIec61360From(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::ILangStringDefinitionTypeIec61360.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::ILangStringDefinitionTypeIec61360>,
  DeserializationError
> LangStringDefinitionTypeIec61360From(
  const nlohmann::json& json,
  bool additional_properties = false
);

/**
 * \brief Deserialize \p json value to an instance
 * of types::IDataSpecificationIec61360.
 *
 * \param json value to be de-serialized
 * \param additional_properties if not set, check that \p json contains
 * no additional properties
 * \return The deserialized instance, or a de-serialization error, if any.
 */
common::expected<
  std::shared_ptr<types::IDataSpecificationIec61360>,
  DeserializationError
> DataSpecificationIec61360From(
  const nlohmann::json& json,
  bool additional_properties = false
);

// endregion Deserialization

// region Serialization

/**
 * Represent an error in the serialization of an instance to JSON.
 */
class SerializationException : public std::exception {
 public:
  SerializationException(
    std::wstring cause,
    iteration::Path path
  );

  const char* what() const noexcept override;

  const std::wstring& cause() const noexcept;
  const iteration::Path& path() const noexcept;

  ~SerializationException() noexcept override = default;

 private:
  const std::wstring cause_;
  const iteration::Path path_;
  const std::string msg_;
};  // class SerializationException

/**
 * \brief Serialize \p that instance to a JSON value.
 *
 * \param that instance to be serialized
 * \return The corresponding JSON value
 * \throw \ref SerializationException if a value within \p that instance
 * could not be serialized
 */
nlohmann::json Serialize(
  const types::IClass& that
);

// endregion Serialization

}  // namespace jsonization
/**@}*/

}  // namespace aas_3_0
}  // namespace aas_core

// This code has been automatically generated by aas-core-codegen.
// Do NOT edit or append.

#endif  // AAS_CORE_AAS_3_0_JSONIZATION_GUARD_
