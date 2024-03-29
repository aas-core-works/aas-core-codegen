/*
 * This code has been automatically generated by aas-core-codegen.
 * Do NOT edit or append.
 */

using Aas = dummyNamespace;  // renamed
using EnumMemberAttribute = System.Runtime.Serialization.EnumMemberAttribute;

using System.Collections.Generic;  // can't alias

namespace dummyNamespace
{
    /// <summary>
    /// Represent a general class of an AAS model.
    /// </summary>
    public interface IClass
    {
        /// <summary>
        /// Iterate over all the class instances referenced from this instance
        /// without further recursion.
        /// </summary>
        public IEnumerable<IClass> DescendOnce();

        /// <summary>
        /// Iterate recursively over all the class instances referenced from this instance.
        /// </summary>
        public IEnumerable<IClass> Descend();

        /// <summary>
        /// Accept the <paramref name="visitor" /> to visit this instance
        /// for double dispatch.
        /// </summary>
        public void Accept(Visitation.IVisitor visitor);

        /// <summary>
        /// Accept the visitor to visit this instance for double dispatch
        /// with the <paramref name="context" />.
        /// </summary>
        public void Accept<TContext>(
            Visitation.IVisitorWithContext<TContext> visitor,
            TContext context);

        /// <summary>
        /// Accept the <paramref name="transformer" /> to transform this instance
        /// for double dispatch.
        /// </summary>
        public T Transform<T>(Visitation.ITransformer<T> transformer);

        /// <summary>
        /// Accept the <paramref name="transformer" /> to visit this instance
        /// for double dispatch with the <paramref name="context" />.
        /// </summary>
        public T Transform<TContext, T>(
            Visitation.ITransformerWithContext<TContext, T> transformer,
            TContext context);
    }

    public interface ISomething : IClass
    {
        // Intentionally empty.
    }

    public class Something : ISomething
    {
        /// <summary>
        /// Iterate over all the class instances referenced from this instance
        /// without further recursion.
        /// </summary>
        public IEnumerable<IClass> DescendOnce()
        {
            // No descendable properties
            yield break;
        }

        /// <summary>
        /// Iterate recursively over all the class instances referenced from this instance.
        /// </summary>
        public IEnumerable<IClass> Descend()
        {
            // No descendable properties
            yield break;
        }

        /// <summary>
        /// Accept the <paramref name="visitor" /> to visit this instance
        /// for double dispatch.
        /// </summary>
        public void Accept(Visitation.IVisitor visitor)
        {
            visitor.VisitSomething(this);
        }

        /// <summary>
        /// Accept the visitor to visit this instance for double dispatch
        /// with the <paramref name="context" />.
        /// </summary>
        public void Accept<TContext>(
            Visitation.IVisitorWithContext<TContext> visitor,
            TContext context)
        {
            visitor.VisitSomething(this, context);
        }

        /// <summary>
        /// Accept the <paramref name="transformer" /> to transform this instance
        /// for double dispatch.
        /// </summary>
        public T Transform<T>(Visitation.ITransformer<T> transformer)
        {
            return transformer.TransformSomething(this);
        }

        /// <summary>
        /// Accept the <paramref name="transformer" /> to visit this instance
        /// for double dispatch with the <paramref name="context" />.
        /// </summary>
        public T Transform<TContext, T>(
            Visitation.ITransformerWithContext<TContext, T> transformer,
            TContext context)
        {
            return transformer.TransformSomething(this, context);
        }
    }
}  // namespace dummyNamespace

/*
 * This code has been automatically generated by aas-core-codegen.
 * Do NOT edit or append.
 */
