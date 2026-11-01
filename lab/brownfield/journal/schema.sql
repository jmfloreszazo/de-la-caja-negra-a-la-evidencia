-- Separate disposable coordinator. No customer credentials or real mandates.
-- Execute ONLY after confirming current_database() = 'bf_control'.
CREATE SCHEMA controller;
CREATE TABLE controller.authority (
    singleton SMALLINT PRIMARY KEY CHECK (singleton = 1),
    writer TEXT NOT NULL CHECK (writer IN ('legacy','candidate')),
    epoch BIGINT NOT NULL CHECK (epoch > 0)
);
INSERT INTO controller.authority VALUES (1,'legacy',1);
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
