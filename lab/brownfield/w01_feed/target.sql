-- Completely separate synthetic incremental read store in bf_projection.
-- Never a source-of-truth, spendable balance or bank authorization ledger.
CREATE TABLE projection.feed_state (
    singleton SMALLINT PRIMARY KEY CHECK (singleton = 1),
    source_watermark BIGINT NOT NULL CHECK (source_watermark >= 0),
    last_hash CHAR(64) NOT NULL CHECK (last_hash ~ '^[0-9a-f]{64}$'),
    snapshot_digest CHAR(64) NOT NULL CHECK (snapshot_digest ~ '^[0-9a-f]{64}$')
);
CREATE TABLE projection.feed_accounts (
    account_no INTEGER PRIMARY KEY CHECK (account_no BETWEEN 1 AND 16),
    booked_minor BIGINT NOT NULL CHECK (booked_minor >= 0),
    source_revision BIGINT NOT NULL CHECK (source_revision >= 0)
);
