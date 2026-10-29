-- Educational SQL Server / Azure SQL design sketch: not a deployment migration.
-- Demonstrates where transactional durability SHOULD live; it is not invoked by the demo.
-- Money amounts use DECIMAL(19,4) here; real scale/currency rules require domain approval.
CREATE TABLE dbo.Accounts
(
    AccountId nvarchar(64) NOT NULL PRIMARY KEY,
    Balance decimal(19,4) NOT NULL,
    RowVer rowversion NOT NULL
);
GO
CREATE TABLE dbo.Operations
(
    OperationId uniqueidentifier NOT NULL PRIMARY KEY,
    RecordedUtc datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
    OperationType varchar(16) NOT NULL
);
GO
CREATE TABLE dbo.LedgerEntries
(
    EntryId bigint IDENTITY PRIMARY KEY,
    OperationId uniqueidentifier NOT NULL REFERENCES dbo.Operations(OperationId),
    AccountId nvarchar(64) NOT NULL REFERENCES dbo.Accounts(AccountId),
    SignedAmount decimal(19,4) NOT NULL
);
GO
CREATE TABLE dbo.Outbox
(
    Id bigint IDENTITY PRIMARY KEY,
    OperationId uniqueidentifier NOT NULL REFERENCES dbo.Operations(OperationId),
    Payload nvarchar(max) NOT NULL,
    CreatedUtc datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
    PublishedUtc datetime2 NULL
);
GO
-- Transfer pseudocode contract (implement in one database transaction):
-- 1. Check OperationId idempotency under concurrency.
-- 2. Debit source only if Balance >= amount (atomic conditional UPDATE).
-- 3. Credit destination and insert matching debit/credit ledger entries.
-- 4. Insert an outbox notification in this same transaction.
-- 5. COMMIT; publish outbox later and deduplicate in the receiver.
-- 6. Enforce currency, limit, and lifecycle invariants explicitly.
-- 7. Test crash before/after COMMIT, duplicate key, deadlock and replay.
-- A SQL DDL sketch is NOT proof of double-entry bookkeeping across currencies.
