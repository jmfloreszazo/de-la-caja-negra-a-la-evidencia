-- E1 PostgreSQL evidence-only schema; no mainframe performance claims.
DROP TABLE IF EXISTS postings, outbox, operations, accounts, duty CASCADE;
CREATE TABLE accounts (
 id INTEGER PRIMARY KEY,
 balance BIGINT NOT NULL CHECK (balance >= 0)
);
CREATE TABLE operations (
 id TEXT PRIMARY KEY,
 src INTEGER NOT NULL REFERENCES accounts(id),
 dst INTEGER NOT NULL REFERENCES accounts(id),
 amount BIGINT NOT NULL CHECK (amount > 0),
 status TEXT NOT NULL CHECK (status IN ('COMMITTED','REJECTED')),
 CHECK (src <> dst)
);
CREATE TABLE postings (
 op TEXT NOT NULL REFERENCES operations(id),
 account INTEGER NOT NULL REFERENCES accounts(id),
 delta BIGINT NOT NULL CHECK (delta <> 0),
 PRIMARY KEY (op, account)
);
CREATE TABLE outbox (
 op TEXT PRIMARY KEY REFERENCES operations(id),
 event TEXT NOT NULL
);
CREATE TABLE duty (
 id INTEGER PRIMARY KEY,
 active BOOLEAN NOT NULL
);
INSERT INTO accounts (id, balance) SELECT n, 100000 FROM generate_series(1,16) AS n;
INSERT INTO duty (id, active) VALUES (1,TRUE),(2,TRUE);
