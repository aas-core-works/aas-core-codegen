/**
 * @returns {@link kind} if set or the default value otherwise.
 */
kindOrDefault(): QualifierKind {
    return (this.kind !== null)
        ? this.kind
        : QualifierKind.ConceptQualifier;
}
