package aas_core.aas3_0.generation;

import aas_core.aas3_0.types.enums.*;
import aas_core.aas3_0.types.impl.*;
import aas_core.aas3_0.types.model.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Builder for the EventPayload type.
 */
public class EventpayloadBuilder {
  /**
   * Reference to the source event element, including identification of
   * {@link AssetAdministrationShell}, {@link Submodel},
   * {@link ISubmodelElement}'s.
   */
  private IReference source;

  /**
   * {@link IHasSemantics#getSemanticId semanticId} of the source event element, if available
   *
   * <p>It is recommended to use a global reference.
   */
  private IReference sourceSemanticId;

  /**
   * Reference to the referable, which defines the scope of the event.
   *
   * <p>Can be {@link AssetAdministrationShell}, {@link Submodel} or
   * {@link ISubmodelElement}.
   */
  private IReference observableReference;

  /**
   * {@link IHasSemantics#getSemanticId semanticId} of the referable which defines the scope of
   * the event, if available.
   *
   * <p>It is recommended to use a global reference.
   */
  private IReference observableSemanticId;

  /**
   * Information for the outer message infrastructure for scheduling the event to
   * the respective communication channel.
   */
  private String topic;

  /**
   * Subject, who/which initiated the creation.
   *
   * <p>This is an external reference.
   */
  private IReference subjectId;

  /**
   * Timestamp in UTC, when this event was triggered.
   */
  private String timeStamp;

  /**
   * Event specific payload.
   */
  private byte[] payload;

  public EventpayloadBuilder(
    IReference source,
    IReference observableReference,
    String timeStamp) {
    this.source = Objects.requireNonNull(
      source,
      "Argument \"source\" must be non-null.");
    this.observableReference = Objects.requireNonNull(
      observableReference,
      "Argument \"observableReference\" must be non-null.");
    this.timeStamp = Objects.requireNonNull(
      timeStamp,
      "Argument \"timeStamp\" must be non-null.");
  }

  public EventpayloadBuilder setSourcesemanticid(IReference sourceSemanticId) {
    this.sourceSemanticId = sourceSemanticId;
    return this;
  }

  public EventpayloadBuilder setObservablesemanticid(IReference observableSemanticId) {
    this.observableSemanticId = observableSemanticId;
    return this;
  }

  public EventpayloadBuilder setTopic(String topic) {
    this.topic = topic;
    return this;
  }

  public EventpayloadBuilder setSubjectid(IReference subjectId) {
    this.subjectId = subjectId;
    return this;
  }

  public EventpayloadBuilder setPayload(byte[] payload) {
    this.payload = payload;
    return this;
  }

  public EventPayload build() {
    return new EventPayload(
      this.source,
      this.observableReference,
      this.timeStamp,
      this.sourceSemanticId,
      this.observableSemanticId,
      this.topic,
      this.subjectId,
      this.payload);
  }
}
