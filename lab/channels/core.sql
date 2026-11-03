CREATE TABLE fixture_meta(name text PRIMARY KEY);
INSERT INTO fixture_meta VALUES ('channels-synthetic-v1');
CREATE TABLE accounts(id bigint PRIMARY KEY, balance bigint NOT NULL CHECK(balance>=0));
CREATE TABLE operations(
 id uuid PRIMARY KEY, kind text NOT NULL CHECK(kind IN ('WITHDRAWAL','TRANSFER')),
 channel text NOT NULL, source bigint NOT NULL REFERENCES accounts(id),
 target bigint NOT NULL REFERENCES accounts(id), requested bigint NOT NULL CHECK(requested>0),
 terminal text NOT NULL, fingerprint text NOT NULL,
 state text NOT NULL CHECK(state IN ('AUTHORIZED','DISPENSE_PENDING','POSTED','CANCELLED','DECLINED','COMMITTED','EXPIRED')),
 posted bigint NOT NULL DEFAULT 0 CHECK(posted>=0 AND posted<=requested),
 command_id text UNIQUE, expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK(source<>target)
);
CREATE TABLE holds(op uuid PRIMARY KEY REFERENCES operations(id),account bigint NOT NULL REFERENCES accounts(id),amount bigint NOT NULL CHECK(amount>0),active boolean NOT NULL);
CREATE TABLE postings(op uuid NOT NULL REFERENCES operations(id),account bigint NOT NULL REFERENCES accounts(id),delta bigint NOT NULL CHECK(delta<>0),PRIMARY KEY(op,account));
CREATE TABLE outbox(op uuid PRIMARY KEY REFERENCES operations(id),event text NOT NULL,amount bigint NOT NULL CHECK(amount>0));
