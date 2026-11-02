-- Disposable-only synthetic CAP-007/CAP-005 reference schema.
-- Use an isolated PostgreSQL 16 database named bf_lab; never run on E1/E2 or customer data.
CREATE SCHEMA IF NOT EXISTS brownfield;

CREATE TABLE IF NOT EXISTS brownfield.authority (
  id SMALLINT PRIMARY KEY CHECK (id = 1),
  writer TEXT NOT NULL CHECK (writer IN ('legacy', 'candidate')),
  epoch BIGINT NOT NULL CHECK (epoch > 0),
  controller_required BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS brownfield.commit_clock (
  id SMALLINT PRIMARY KEY CHECK (id = 1),
  watermark BIGINT NOT NULL DEFAULT 0 CHECK (watermark >= 0)
);

CREATE TABLE IF NOT EXISTS brownfield.accounts (
  id INTEGER PRIMARY KEY,
  balance BIGINT NOT NULL CHECK (balance >= 0),
  version BIGINT NOT NULL DEFAULT 0 CHECK (version >= 0)
);

CREATE TABLE IF NOT EXISTS brownfield.operations (
  id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 80),
  fingerprint TEXT NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
  writer TEXT NOT NULL CHECK (writer IN ('legacy', 'candidate')),
  epoch BIGINT NOT NULL CHECK (epoch > 0),
  src INTEGER NOT NULL REFERENCES brownfield.accounts(id),
  dst INTEGER NOT NULL REFERENCES brownfield.accounts(id),
  amount BIGINT NOT NULL CHECK (amount > 0),
  status TEXT NOT NULL CHECK (status IN ('COMMITTED', 'REJECTED')),
  CHECK (src <> dst)
);

CREATE TABLE IF NOT EXISTS brownfield.postings (
  operation_id TEXT NOT NULL REFERENCES brownfield.operations(id),
  account_id INTEGER NOT NULL REFERENCES brownfield.accounts(id),
  delta BIGINT NOT NULL CHECK (delta <> 0),
  PRIMARY KEY (operation_id, account_id)
);

CREATE TABLE IF NOT EXISTS brownfield.outbox (
  operation_id TEXT PRIMARY KEY REFERENCES brownfield.operations(id),
  event_type TEXT NOT NULL CHECK (event_type = 'TransferCommitted')
);

-- Idempotent first-time bootstrapping does not reset or overwrite any existing state.
INSERT INTO brownfield.authority(id, writer, epoch)
VALUES (1, 'legacy', 1) ON CONFLICT (id) DO NOTHING;
INSERT INTO brownfield.commit_clock(id, watermark)
VALUES (1, 0) ON CONFLICT (id) DO NOTHING;
INSERT INTO brownfield.accounts(id, balance)
SELECT n, 100000 FROM generate_series(1, 16) AS n WHERE TRUE
ON CONFLICT (id) DO NOTHING;
