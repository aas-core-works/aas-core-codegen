/// <summary>
/// Represent a verification error traceable to an entity or a property.
/// </summary>
public class Error
{
    /// <summary>
    /// JSON-like path to the related object (an entity or a property)
    /// </summary>
    public readonly string Path;

    /// <summary>
    /// Cause or description of the error
    /// </summary>
    public readonly string Message;

    public Error(string path, string message)
    {
        Path = path;
        Message = message;
    }
}
