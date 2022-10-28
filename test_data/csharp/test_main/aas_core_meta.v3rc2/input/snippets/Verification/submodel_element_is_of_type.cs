public static bool SubmodelElementIsOfType(
    Aas.ISubmodelElement element,
    Aas.AasSubmodelElements expectedType
)
{
    switch (expectedType)
    {
        case Aas.AasSubmodelElements.AnnotatedRelationshipElement:
            return element is Aas.AnnotatedRelationshipElement;

        case Aas.AasSubmodelElements.BasicEventElement:
            return element is Aas.BasicEventElement;

        case Aas.AasSubmodelElements.Blob:
            return element is Aas.Blob;

        case Aas.AasSubmodelElements.Capability:
            return element is Aas.Capability;

        case Aas.AasSubmodelElements.DataElement:
            return element is Aas.IDataElement;

        case Aas.AasSubmodelElements.Entity:
            return element is Aas.Entity;

        case Aas.AasSubmodelElements.EventElement:
            return element is Aas.IEventElement;

        case Aas.AasSubmodelElements.File:
            return element is Aas.File;

        case Aas.AasSubmodelElements.MultiLanguageProperty:
            return element is Aas.MultiLanguageProperty;

        case Aas.AasSubmodelElements.Operation:
            return element is Aas.Operation;

        case Aas.AasSubmodelElements.Property:
            return element is Aas.Property;

        case Aas.AasSubmodelElements.Range:
            return element is Aas.Range;

        case Aas.AasSubmodelElements.ReferenceElement:
            return element is Aas.ReferenceElement;

        case Aas.AasSubmodelElements.RelationshipElement:
            return element is Aas.IRelationshipElement;

        case Aas.AasSubmodelElements.SubmodelElement:
            // ReSharper disable once IsExpressionAlwaysTrue
            // ReSharper disable once ConvertTypeCheckToNullCheck
            return element is Aas.ISubmodelElement;

        case Aas.AasSubmodelElements.SubmodelElementList:
            return element is Aas.SubmodelElementList;

        case Aas.AasSubmodelElements.SubmodelElementCollection:
            return element is Aas.SubmodelElementCollection;

        default:
            throw new System.ArgumentException(
                $"expectedType is not a valid AasSubmodelElements: {expectedType}"
            );
    }
}
