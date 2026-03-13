/**
 * @returns {@link kind} if set or the default value otherwise.
 */
kindOrDefault(): ModellingKind {
    return (this.kind !== null)
        ? this.kind
        : ModellingKind.Instance;
}
