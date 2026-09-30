public static bool SubmodelElementIsOfType(
    Our.ISubmodelElement element,
    Our.AasSubmodelElements expectedType
)
{
    switch (expectedType)
    {
        case Our.AasSubmodelElements.AnnotatedRelationshipElement:
            return element is Our.IAnnotatedRelationshipElement;

        case Our.AasSubmodelElements.BasicEventElement:
            return element is Our.IBasicEventElement;

        case Our.AasSubmodelElements.Blob:
            return element is Our.IBlob;

        case Our.AasSubmodelElements.Capability:
            return element is Our.ICapability;

        case Our.AasSubmodelElements.DataElement:
            return element is Our.IDataElement;

        case Our.AasSubmodelElements.Entity:
            return element is Our.IEntity;

        case Our.AasSubmodelElements.EventElement:
            return element is Our.IEventElement;

        case Our.AasSubmodelElements.File:
            return element is Our.IFile;

        case Our.AasSubmodelElements.MultiLanguageProperty:
            return element is Our.IMultiLanguageProperty;

        case Our.AasSubmodelElements.Operation:
            return element is Our.IOperation;

        case Our.AasSubmodelElements.Property:
            return element is Our.IProperty;

        case Our.AasSubmodelElements.Range:
            return element is Our.IRange;

        case Our.AasSubmodelElements.ReferenceElement:
            return element is Our.IReferenceElement;

        case Our.AasSubmodelElements.RelationshipElement:
            return element is Our.IRelationshipElement;

        case Our.AasSubmodelElements.SubmodelElement:
            // ReSharper disable once IsExpressionAlwaysTrue
            // ReSharper disable once ConvertTypeCheckToNullCheck
            return element is Our.ISubmodelElement;

        case Our.AasSubmodelElements.SubmodelElementList:
            return element is Our.ISubmodelElementList;

        case Our.AasSubmodelElements.SubmodelElementCollection:
            return element is Our.ISubmodelElementCollection;

        default:
            throw new System.ArgumentException(
                $"expectedType is not a valid AasSubmodelElements: {expectedType}"
            );
    }
}
