-- Synthetic legacy banking contract with deliberately different storage names.
-- Only in the disposable PostgreSQL database named exactly bf_legacy.
CREATE SCHEMA legacy;
CREATE TABLE legacy.accounts (
  account_no INTEGER PRIMARY KEY,
  ledger_minor BIGINT NOT NULL CHECK (ledger_minor >= 0),
  revision BIGINT NOT NULL DEFAULT 0 CHECK (revision >= 0)
);
CREATE TABLE legacy.transactions (
  request_id TEXT PRIMARY KEY,
  request_hash TEXT NOT NULL CHECK (request_hash ~ '^[0-9a-f]{64}$'),
  source_no INTEGER NOT NULL REFERENCES legacy.accounts(account_no),
  destination_no INTEGER NOT NULL REFERENCES legacy.accounts(account_no),
  value_minor BIGINT NOT NULL CHECK (value_minor > 0),
  decision TEXT NOT NULL CHECK (decision IN ('COMMITTED','REJECTED')),
  authority_epoch BIGINT NOT NULL CHECK (authority_epoch > 0),
  CHECK (source_no <> destination_no)
);
CREATE TABLE legacy.entries (
  request_id TEXT NOT NULL REFERENCES legacy.transactions(request_id),
  account_no INTEGER NOT NULL REFERENCES legacy.accounts(account_no),
  amount_minor BIGINT NOT NULL CHECK (amount_minor <> 0),
  PRIMARY KEY (request_id,account_no)
);
CREATE TABLE legacy.notices (
  request_id TEXT PRIMARY KEY REFERENCES legacy.transactions(request_id),
  kind TEXT NOT NULL CHECK (kind = 'TransferCommitted')
);
CREATE TABLE legacy.clock (
  singleton INTEGER PRIMARY KEY CHECK (singleton=1),
  sequence_no BIGINT NOT NULL CHECK (sequence_no >= 0)
);
INSERT INTO legacy.clock(singleton,sequence_no) VALUES (1,0);
INSERT INTO legacy.accounts(account_no,ledger_minor)
SELECT n,100000 FROM generate_series(1,16) AS n;
