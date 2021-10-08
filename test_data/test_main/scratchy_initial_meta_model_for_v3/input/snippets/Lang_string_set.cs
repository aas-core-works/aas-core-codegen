public class LangStringSet : IEntity {
    public IEnumerable<IEntity> DescendOnce()
    {
        throw new NotImplementedException("TODO");
    }

    public IEnumerable<IEntity> Descend()
    {
        throw new NotImplementedException("TODO");
    }

    public void Accept(Visitation.IVisitor visitor)
    {
        throw new NotImplementedException("TODO");
    }

    public void Accept<C>(Visitation.IVisitorWithContext<C> visitor, C context)
    {
        throw new NotImplementedException("TODO");
    }

    public T Transform<T>(Visitation.ITransformer<T> transformer)
    {
        throw new NotImplementedException("TODO");
    }

    public T Transform<C, T>(Visitation.ITransformerWithContext<C, T> transformer, C context)
    {
        throw new NotImplementedException("TODO");
    }
}
