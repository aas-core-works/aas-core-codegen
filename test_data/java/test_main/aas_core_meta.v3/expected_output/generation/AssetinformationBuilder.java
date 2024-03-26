package aas_core.aas3_0.generation;

import aas_core.aas3_0.types.enums.*;
import aas_core.aas3_0.types.impl.*;
import aas_core.aas3_0.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the AssetInformation type.
 */
public class AssetinformationBuilder {
  /**
   * Denotes whether the Asset is of kind {@link AssetKind#TYPE} or
   * {@link AssetKind#INSTANCE}.
   */
  private AssetKind assetKind;

  /**
   * Global identifier of the asset the AAS is representing.
   *
   * <p>This attribute is required as soon as the AAS is exchanged via partners in the life
   * cycle of the asset. In a first phase of the life cycle the asset might not yet have
   * a global ID but already an internal identifier. The internal identifier would be
   * modelled via {@link AssetInformation#getSpecificAssetIds specificAssetIds}.
   *
   * <p>This is a global reference.
   */
  private String globalAssetId;

  /**
   * Additional domain-specific, typically proprietary identifier for the asset like
   * e.g., serial number etc.
   */
  private List<ISpecificAssetId> specificAssetIds;

  /**
   * In case {@link AssetInformation#getAssetKind assetKind} is applicable the {@link AssetInformation#getAssetType assetType} is the asset ID
   * of the type asset of the asset under consideration
   * as identified by {@link AssetInformation#getGlobalAssetId globalAssetId}.
   *
   * <p>In case {@link AssetInformation#getAssetKind assetKind} is "Instance" than the {@link AssetInformation#getAssetType assetType} denotes
   * which "Type" the asset is of. But it is also possible
   * to have an {@link AssetInformation#getAssetType assetType} of an asset of kind "Type".
   */
  private String assetType;

  /**
   * Thumbnail of the asset represented by the Asset Administration Shell.
   *
   * <p>Used as default.
   */
  private IResource defaultThumbnail;

  public AssetinformationBuilder(AssetKind assetKind) {
    this.assetKind = Objects.requireNonNull(
      assetKind,
      "Argument \"assetKind\" must be non-null.");
  }

  public AssetinformationBuilder setGlobalassetid(String globalAssetId) {
    this.globalAssetId = globalAssetId;
    return this;
  }

  public AssetinformationBuilder setSpecificassetids(List<ISpecificAssetId> specificAssetIds) {
    this.specificAssetIds = specificAssetIds;
    return this;
  }

  public AssetinformationBuilder setAssettype(String assetType) {
    this.assetType = assetType;
    return this;
  }

  public AssetinformationBuilder setDefaultthumbnail(IResource defaultThumbnail) {
    this.defaultThumbnail = defaultThumbnail;
    return this;
  }

  public AssetInformation build() {
    return new AssetInformation(
      this.assetKind,
      this.globalAssetId,
      this.specificAssetIds,
      this.assetType,
      this.defaultThumbnail);
  }
}
