"""Fixed disposable fixture access; no external DSN overrides."""
import os
import psycopg
from psycopg.rows import dict_row

DSNS = {name: f'host=127.0.0.1 port={port} dbname=channelslab_{name} user=postgres password=channelslocal gssencmode=disable'
        for name, port in [('core', 55442), ('device', 55443)]}

def connect(name, probe=True):
    if os.environ.get('CHANNELS_DISPOSABLE') != 'YES':
        raise RuntimeError('Explicit disposable channel fixture required')
    db = psycopg.connect(DSNS[name], row_factory=dict_row)
    if probe:
        rows = db.execute('SELECT current_database() AS db,name FROM fixture_meta').fetchall()
        if rows != [{'db': 'channelslab_' + name, 'name': 'channels-synthetic-v1'}]:
            db.close()
            raise RuntimeError('Unknown disposable fixture identity')
    return db

def snapshot():
    result = {}
    for name, tables in [('core', ['accounts', 'operations', 'holds', 'postings', 'outbox']),
                         ('device', ['inventory', 'device_commands'])]:
        with connect(name) as db:
            result[name] = {table: db.execute('SELECT * FROM ' + table + ' ORDER BY 1').fetchall() for table in tables}
    return result
