-- Synthetic and disposable-only source-owned change journal.
-- Installed AFTER legacy_schema.sql in exactly bf_legacy.
-- The test-only source writer inserts this row in the same transaction as the
-- financial COMMIT, paired postings, outbox and legacy.clock update.
-- Hashes detect accidental drift within this fixture, NOT malicious source edits.
CREATE TABLE legacy.balance_feed (
    sequence_no BIGINT PRIMARY KEY CHECK (sequence_no > 0),
    request_id TEXT NOT NULL UNIQUE REFERENCES legacy.transactions(request_id),
    debit_account INTEGER NOT NULL REFERENCES legacy.accounts(account_no),
    credit_account INTEGER NOT NULL REFERENCES legacy.accounts(account_no),
    amount_minor BIGINT NOT NULL CHECK (amount_minor > 0),
    debit_before BIGINT NOT NULL CHECK (debit_before >= 0),
    debit_after BIGINT NOT NULL CHECK (debit_after >= 0),
    credit_before BIGINT NOT NULL CHECK (credit_before >= 0),
    credit_after BIGINT NOT NULL CHECK (credit_after >= 0),
    previous_hash CHAR(64) NOT NULL CHECK (previous_hash ~ '^[0-9a-f]{64}$'),
    event_hash CHAR(64) NOT NULL CHECK (event_hash ~ '^[0-9a-f]{64}$'),
    CHECK (debit_account <> credit_account),
    CHECK (debit_before - debit_after = amount_minor),
    CHECK (credit_after - credit_before = amount_minor)
);
