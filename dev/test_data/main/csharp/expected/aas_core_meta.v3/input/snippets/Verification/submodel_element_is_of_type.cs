public static bool SubmodelElementIsOfType(
    Aas.ISubmodelElement element,
    Aas.AasSubmodelElements expectedType
)
{
    switch (expectedType)
    {
        case Aas.AasSubmodelElements.AnnotatedRelationshipElement:
            return element is Aas.IAnnotatedRelationshipElement;

        case Aas.AasSubmodelElements.BasicEventElement:
            return element is Aas.IBasicEventElement;

        case Aas.AasSubmodelElements.Blob:
            return element is Aas.IBlob;

        case Aas.AasSubmodelElements.Capability:
            return element is Aas.ICapability;

        case Aas.AasSubmodelElements.DataElement:
            return element is Aas.IDataElement;

        case Aas.AasSubmodelElements.Entity:
            return element is Aas.IEntity;

        case Aas.AasSubmodelElements.EventElement:
            return element is Aas.IEventElement;

        case Aas.AasSubmodelElements.File:
            return element is Aas.IFile;

        case Aas.AasSubmodelElements.MultiLanguageProperty:
            return element is Aas.IMultiLanguageProperty;

        case Aas.AasSubmodelElements.Operation:
            return element is Aas.IOperation;

        case Aas.AasSubmodelElements.Property:
            return element is Aas.IProperty;

        case Aas.AasSubmodelElements.Range:
            return element is Aas.IRange;

        case Aas.AasSubmodelElements.ReferenceElement:
            return element is Aas.IReferenceElement;

        case Aas.AasSubmodelElements.RelationshipElement:
            return element is Aas.IRelationshipElement;

        case Aas.AasSubmodelElements.SubmodelElement:
            // ReSharper disable once IsExpressionAlwaysTrue
            // ReSharper disable once ConvertTypeCheckToNullCheck
            return element is Aas.ISubmodelElement;

        case Aas.AasSubmodelElements.SubmodelElementList:
            return element is Aas.ISubmodelElementList;

        case Aas.AasSubmodelElements.SubmodelElementCollection:
            return element is Aas.ISubmodelElementCollection;

        default:
            throw new System.ArgumentException(
                $"expectedType is not a valid AasSubmodelElements: {expectedType}"
            );
    }
}
