public static boolean SubmodelElementIsOfType(
        ISubmodelElement element,
        AasSubmodelElements expectedType
) {
    switch (expectedType) {
        case ANNOTATED_RELATIONSHIP_ELEMENT:
            return element instanceof IAnnotatedRelationshipElement;

        case BASIC_EVENT_ELEMENT:
            return element instanceof IBasicEventElement;

        case BLOB:
            return element instanceof IBlob;

        case CAPABILITY:
            return element instanceof ICapability;

        case DATA_ELEMENT:
            return element instanceof IDataElement;

        case ENTITY:
            return element instanceof IEntity;

        case EVENT_ELEMENT:
            return element instanceof IEventElement;

        case FILE:
            return element instanceof IFile;

        case MULTI_LANGUAGE_PROPERTY:
            return element instanceof IMultiLanguageProperty;

        case OPERATION:
            return element instanceof IOperation;

        case PROPERTY:
            return element instanceof IProperty;

        case RANGE:
            return element instanceof IRange;

        case REFERENCE_ELEMENT:
            return element instanceof IReferenceElement;

        case RELATIONSHIP_ELEMENT:
            return element instanceof IRelationshipElement;

        case SUBMODEL_ELEMENT:
            return element instanceof ISubmodelElement;

        case SUBMODEL_ELEMENT_LIST:
            return element instanceof ISubmodelElementList;

        case SUBMODEL_ELEMENT_COLLECTION:
            return element instanceof ISubmodelElementCollection;

        default:
            throw new IllegalArgumentException(
                    "expectedType is not a valid AasSubmodelElements: " + expectedType
            );
    }
}
