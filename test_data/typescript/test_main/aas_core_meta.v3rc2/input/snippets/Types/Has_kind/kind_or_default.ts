/**
 * @returns {@link kind} if set or the default value otherwise.
 */
kindOrDefault(): ModelingKind {
    return (this.kind !== null)
        ? this.kind
        : ModelingKind.Instance;
}
