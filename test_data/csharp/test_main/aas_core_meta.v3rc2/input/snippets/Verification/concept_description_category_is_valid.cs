private static readonly HashSet<string> ConceptDescriptionCategories = new HashSet<string>
{
    "APPLICATION_CLASS",
    "CAPABILITY",
    "COLLECTION",
    "DOCUMENT",
    "ENTITY",
    "EVENT",
    "FUNCTION",
    "PROPERTY",
    "VALUE",
    "RANGE",
    "QUALIFIER_TYPE",
    "REFERENCE",
    "RELATIONSHIP"
};

/// <summary>
/// Check that <paramref name="category" /> is a valid
/// category of the concept description.
/// </summary>
public static bool ConceptDescriptionCategoryIsValid(
    string category
)
{
    return ConceptDescriptionCategories.Contains(
        category);
}
