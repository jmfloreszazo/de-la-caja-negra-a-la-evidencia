-- Separate disposable coordinator. No customer credentials or real mandates.
-- Execute ONLY after confirming current_database() = 'bf_control'.
CREATE SCHEMA controller;
CREATE TABLE controller.authority (
    singleton SMALLINT PRIMARY KEY CHECK (singleton = 1),
    writer TEXT NOT NULL CHECK (writer IN ('legacy','candidate')),
    epoch BIGINT NOT NULL CHECK (epoch > 0),
    mode TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (mode IN ('ACTIVE','SWITCHING'))
);
INSERT INTO controller.authority(singleton,writer,epoch) VALUES (1,'legacy',1);
-- A durable freeze precedes either authority change. Recovery moves forward
-- only after independent SQL reconciliation; this is not distributed COMMIT.
CREATE TABLE controller.writer_transition (
    transition_id BIGSERIAL PRIMARY KEY,
    from_writer TEXT NOT NULL CHECK (from_writer IN ('legacy','candidate')),
    from_epoch BIGINT NOT NULL CHECK (from_epoch > 0),
    to_writer TEXT NOT NULL CHECK (to_writer IN ('legacy','candidate')),
    to_epoch BIGINT NOT NULL CHECK (to_epoch = from_epoch + 1),
    state TEXT NOT NULL CHECK (state IN ('PREPARED','COMPLETED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    completed_at TIMESTAMPTZ,
    CHECK (from_writer <> to_writer),
    UNIQUE (from_epoch)
);
CREATE UNIQUE INDEX one_prepared_transition ON controller.writer_transition(state)
    WHERE state = 'PREPARED';
CREATE TABLE controller.admission (
    operation_id TEXT PRIMARY KEY CHECK (operation_id ~ '^[A-Za-z0-9-]{1,80}$'),
    request_hash CHAR(64) NOT NULL CHECK (request_hash ~ '^[0-9a-f]{64}$'),
    capability_id TEXT NOT NULL CHECK (capability_id = 'CAP-007'),
    tenant_scope TEXT NOT NULL CHECK (tenant_scope = 'SYNTHETIC'),
    actor_ref TEXT NOT NULL CHECK (actor_ref = 'UNVERIFIED_FIXTURE_ACTOR'),
    mandate_ref TEXT NOT NULL CHECK (mandate_ref = 'UNVERIFIED_FIXTURE_MANDATE'),
    writer TEXT NOT NULL CHECK (writer IN ('legacy','candidate')),
    epoch BIGINT NOT NULL CHECK (epoch > 0),
    source_account INTEGER NOT NULL,
    destination_account INTEGER NOT NULL,
    amount_minor BIGINT NOT NULL CHECK (amount_minor > 0),
    state TEXT NOT NULL CHECK (state IN (
        'ADMITTED','DISPATCHING','UNKNOWN','COMMITTED','REJECTED','RECONCILIATION_REQUIRED'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX admission_unresolved ON controller.admission(state)
    WHERE state NOT IN ('COMMITTED','REJECTED');
