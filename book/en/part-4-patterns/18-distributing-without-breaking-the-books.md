**English** · [Español](../../es/parte-4-patrones/18-distribuir-sin-romper-la-contabilidad.md)

[← Chapter 17 · From mainframe locks to explicit concurrency control](17-from-mainframe-locks-to-explicit-concurrency-control.md) · [Contents](../README.md) · [Chapter 19 · Actors: a great tool, a poor universal substitute →](19-actors-a-great-tool-a-poor-universal-substitute.md)

# Chapter 18 · Distributing without breaking the books

> [!IMPORTANT]
> **Chapter thesis.** Keeping a strong transactional boundary can simplify a great deal. If we distribute it, compensation has business meaning, publishing requires an outbox and a stale owner must be rejected by the target, not out of courtesy.

## Keeping a strong boundary can simplify a great deal

My first option for a capability that needs atomicity would be to study whether its writes can remain in a transaction on a single engine. The application can have several instances and the accounting core can still concentrate the commit decision. That limits one kind of scalability and avoids another kind of distributed coordination.

A modular monolith can be a reasonable initial target. It lets us recover internal boundaries before multiplying network hops and data owners. I would not choose it out of nostalgia or discard it for carrying an old label. I would evaluate it against the load, the expected changes and the required guarantees.

If the original unit commits several resources, we must decide whether to keep compatible distributed coordination or redesign the protocol. Db2 documents two-phase coordination for certain participants [20]. Replacing it with a saga changes the consistency model and must go through the business authority.

## Compensating has a business meaning

A saga organizes steps and compensating actions. It does not turn those steps into an invisible rollback. An observed transfer, a notification sent or a conversion applied may require specific handling. During compensation there is a state other participants could observe.

A reservation protocol can protect the available balance before completing the movement. It must define expiry, confirmation, release, recovery and who can resolve a doubtful operation. The reservation also becomes a resource that consumes capacity and needs reconciliation.

If the contract requires debit and credit to be immediately atomic for the relevant observers, I would not accept a saga for the convenience of deploying two services. I would look for a data boundary or a transactional mechanism that preserves that property.

## Publishing after the commit without losing the event

The outbox lets us store the intent to publish together with the business change in a single local transaction. A later publisher delivers the event and records its progress. That avoids the window in which we confirm the operation and forget to generate the notification, always within the resources really included in that transaction.

Even so, the publisher can send the message and fail before marking it as sent. The consumer must tolerate a repetition. Microsoft describes this pattern with at-least-once delivery and idempotency in the consumer [21]. Broker deduplication can help within its limits; the business identity must survive the retention window and the recovery we have agreed.

![Figure 18.1 · Outbox with at-least-once delivery: the publisher may repeat, the consumer deduplicates by business identity.](../../figures/en/outbox_seq.png)

*Figure 18.1 · Outbox with at-least-once delivery: the publisher may repeat, the consumer deduplicates by business identity.*

In the lab we check that each confirmed transfer generates its outbox row atomically. We do not run a remote publisher or prove delivery to a broker. That extension requires another test: crashing before and after sending, repeating messages and reconciling reception with applied effects.

## Protecting ourselves from a stale owner

When a process holds a temporary permission and loses connectivity, another can take over the work. The old one can come back and keep trying to write. Relying only on everyone respecting an in-memory marker is not enough.

One technique is to associate an increasing epoch or token with ownership and require the resource to reject writes from previous owners. Its usefulness depends on the store that receives the change really checking that token. A distributed lock consulted by the application does not automatically change the guarantees of the database.

This is one of the decisions I would put in an ADR: where write authority lives, what happens when it expires and what evidence shows that a stale owner cannot commit effects.

The epoch technique is easier to understand in two statements. The target is the one that enforces it: a batch that lost its lease may still be alive, but its writes are no longer committed.

**Listing 18.1 · Fencing: the store rejects writes from a stale owner** — *Illustrative*

```sql
-- Taking ownership: the epoch grows and is only granted if the previous lease expired.
UPDATE dbo.PartitionLeases
   SET Owner = @Worker, Epoch = Epoch + 1,
       ExpiresUtc = DATEADD(second, 30, SYSUTCDATETIME())
OUTPUT inserted.Epoch
 WHERE PartitionId = @Partition AND ExpiresUtc < SYSUTCDATETIME();

-- Every write carries the epoch obtained. HOLDLOCK prevents the takeover
-- from committing while this write is in progress.
INSERT dbo.BatchResults (PartitionId, Epoch, AccountId, Amount)
SELECT @Partition, @Epoch, @AccountId, @Amount
 WHERE EXISTS (SELECT 1 FROM dbo.PartitionLeases WITH (HOLDLOCK)
                WHERE PartitionId = @Partition AND Epoch = @Epoch);
-- 0 rows inserted: this worker is no longer the owner. It must stop, not retry.
```

![Figure 18.2 · Fencing: a stale owner may still be alive, but the store stops committing its writes.](../../figures/en/fencing_seq.png)

*Figure 18.2 · Fencing: a stale owner may still be alive, but the store stops committing its writes.*

> **A saga is not an invisible rollback. If the contract requires immediate atomicity, it is not traded for deployment convenience.**

---

[← Chapter 17 · From mainframe locks to explicit concurrency control](17-from-mainframe-locks-to-explicit-concurrency-control.md) · [Contents](../README.md) · [Chapter 19 · Actors: a great tool, a poor universal substitute →](19-actors-a-great-tool-a-poor-universal-substitute.md)
