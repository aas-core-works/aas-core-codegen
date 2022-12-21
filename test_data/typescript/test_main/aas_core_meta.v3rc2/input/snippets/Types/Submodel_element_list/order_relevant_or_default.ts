/**
 * @returns {@link orderRelevant} if set or the default value otherwise.
 */
orderRelevantOrDefault(): boolean {
    return (this.orderRelevant !== null)
        ? this.orderRelevant
        : true;
}
