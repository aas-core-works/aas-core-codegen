public class LangStringSetJsonConverter :
    System.Text.Json.Serialization.JsonConverter<Aas.LangStringSet>
{
    public override Aas.LangStringSet Read(
        ref System.Text.Json.Utf8JsonReader reader,
        System.Type typeToConvert,
        System.Text.Json.JsonSerializerOptions options)
    {
        throw new System.NotImplementedException("TODO");
    }

    public override void Write(
        System.Text.Json.Utf8JsonWriter writer,
        Aas.LangStringSet value,
        System.Text.Json.JsonSerializerOptions options)
    {
        throw new System.NotImplementedException("TODO");
    }
}
