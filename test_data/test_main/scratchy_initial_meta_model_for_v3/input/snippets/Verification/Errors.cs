/// <summary>
/// Contain multiple errors observed during a verification.
/// </summary>
public class Errors
{
    /// <summary>
    /// The maximum capacity of the container
    /// </summary>
    public readonly int Capacity;

    /// <summary>
    /// Contained error items
    /// </summary>
    private readonly List<Verification.Error> _entries;

    /// <summary>
    /// Initialize the container with the given <paramref name="capacity" />.
    /// </summary>
    public Errors(int capacity)
    {
        if (capacity <= 0)
        {
            throw new ArgumentException(
                $"Expected a strictly positive capacity, but got: {capacity}");
        }

        Capacity = capacity;
        _entries = new List<Verification.Error>(Capacity);
    }

    /// <summary>
    /// Add the error to the container if the capacity has not been reached.
    /// </summary>
    public void Add(Verification.Error error)
    {
        if(_entries.Count <= Capacity)
        {
            _entries.Add(error);
        }
    }

    /// <summary>
    /// True if the capacity has been reached.
    /// </summary>
    public bool Full()
    {
        return _entries.Count == Capacity;
    }

    /// <summary>
    /// Retrieve the contained error entries.
    /// </summary>
    /// <remarks>
    /// If you want to add a new error, use <see cref="Add" />.
    /// </remarks>
    public ReadOnlyCollection<Verification.Error> Entries()
    {
        var result = this._entries.AsReadOnly();
        if (result.Count > Capacity)
        {
            throw new InvalidOperationException(
                $"Post-condition violated: " +
                $"result.Count (== {result.Count}) > Capacity (== {Capacity})");
        }
        return result;
    }
}
