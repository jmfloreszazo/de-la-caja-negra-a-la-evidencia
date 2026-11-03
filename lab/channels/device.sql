CREATE TABLE fixture_meta(name text PRIMARY KEY);
INSERT INTO fixture_meta VALUES ('channels-synthetic-v1');
CREATE TABLE inventory(terminal text PRIMARY KEY,remaining bigint NOT NULL CHECK(remaining>=0));
CREATE TABLE device_commands(
 command_id text PRIMARY KEY, op uuid NOT NULL UNIQUE, terminal text NOT NULL REFERENCES inventory(terminal),
 requested bigint NOT NULL CHECK(requested>0),dispensed bigint NOT NULL CHECK(dispensed>=0 AND dispensed<=requested),
 fingerprint text NOT NULL,state text NOT NULL CHECK(state='FINAL'),created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE FUNCTION keep_device_outcome() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Final synthetic device records are immutable'; END;
$$;
CREATE TRIGGER device_outcome_immutable BEFORE UPDATE OR DELETE ON device_commands FOR EACH ROW EXECUTE FUNCTION keep_device_outcome();
