-- Disposable-only PostgreSQL balance read projection (W01), not a bank authority.
-- Database name must be exactly bf_projection; loopback port 55442 only.
-- Source remains the independent bf_legacy PostgreSQL database on port 55438.
CREATE SCHEMA projection;
CREATE TABLE projection.meta (
  id SMALLINT PRIMARY KEY CHECK (id=1),
  watermark BIGINT NOT NULL CHECK (watermark >= 0),
  source_digest TEXT CHECK (source_digest IS NULL OR source_digest ~ '^[0-9a-f]{64}$'),
  refreshed_at TIMESTAMPTZ
);
CREATE TABLE projection.accounts (
  account_no INTEGER PRIMARY KEY,
  booked_minor BIGINT NOT NULL CHECK (booked_minor >= 0),
  source_revision BIGINT NOT NULL CHECK (source_revision >= 0)
);
INSERT INTO projection.meta(id, watermark, source_digest) VALUES (1, 0, NULL);
