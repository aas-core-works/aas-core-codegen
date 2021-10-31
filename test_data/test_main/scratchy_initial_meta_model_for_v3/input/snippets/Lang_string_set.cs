public class LangStringSet : IEntity {
    public IEnumerable<IEntity> DescendOnce()
    {
        throw new System.NotImplementedException("TODO");
    }

    public IEnumerable<IEntity> Descend()
    {
        throw new System.NotImplementedException("TODO");
    }

    public void Accept(Visitation.IVisitor visitor)
    {
        throw new System.NotImplementedException("TODO");
    }

    public void Accept<C>(Visitation.IVisitorWithContext<C> visitor, C context)
    {
        throw new System.NotImplementedException("TODO");
    }

    public T Transform<T>(Visitation.ITransformer<T> transformer)
    {
        throw new System.NotImplementedException("TODO");
    }

    public T Transform<C, T>(Visitation.ITransformerWithContext<C, T> transformer, C context)
    {
        throw new System.NotImplementedException("TODO");
    }


}
