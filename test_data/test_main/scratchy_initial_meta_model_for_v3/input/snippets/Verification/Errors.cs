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
    public readonly List<Error> Errors;

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
        Errors = new List<Error>(Capacity);
    }

    /// <summary>
    /// Add the error to the container if the capacity has not been reached.
    /// </summary>
    public void Add(Error error)
    {
        if(Errors.Count <= Capacity)
        {
            Errors.Add(error);
        }
    }

    /// <summary>
    /// True if the capacity has been reached.
    /// </summary>
    public boolean Full()
    {
        return Errors.Count == Capacity;
    }
}
