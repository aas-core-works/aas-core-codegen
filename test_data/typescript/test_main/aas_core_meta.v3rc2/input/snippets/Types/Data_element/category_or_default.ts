/**
 * @returns {@link category} if set or the default value otherwise.
 */
categoryOrDefault(): string {
    return (this.category !== null)
        ? this.category
        : "VARIABLE";
}
