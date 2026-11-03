"""Synthetic device journal. Its SQL atomicity does not model physical cash atomicity."""
import argparse
import json
import time
from pathlib import Path
from fixture import connect


def dispense(command, actual):
    with connect('core') as core:
        op = core.execute('SELECT * FROM operations WHERE id=%s', (command['operationId'],)).fetchone()
        if not op or op['state'] != 'DISPENSE_PENDING' or op['command_id'] != command['commandId']:
            raise ValueError('Device command lacks a prepared core intent')
    if not 0 <= actual <= op['requested']:
        raise ValueError('Invalid synthetic dispense amount')
    with connect('device') as db:
        stock = db.execute('SELECT remaining FROM inventory WHERE terminal=%s FOR UPDATE', (op['terminal'],)).fetchone()
        old = db.execute('SELECT * FROM device_commands WHERE command_id=%s', (command['commandId'],)).fetchone()
        if old:
            if str(old['op']) != command['operationId'] or old['fingerprint'] != op['fingerprint']:
                raise ValueError('Device command identity conflict')
            return old
        if not stock or stock['remaining'] < actual:
            raise ValueError('Insufficient synthetic device stock')
        db.execute('UPDATE inventory SET remaining=remaining-%s WHERE terminal=%s', (actual, op['terminal']))
        row = db.execute('INSERT INTO device_commands(command_id,op,terminal,requested,dispensed,fingerprint,state) '
                         "VALUES (%s,%s,%s,%s,%s,%s,'FINAL') RETURNING *",
                         (command['commandId'], op['id'], op['terminal'], op['requested'], actual, op['fingerprint'])).fetchone()
    return row

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    parser.add_argument('actual', type=int)
    parser.add_argument('--lose-response', action='store_true')
    args = parser.parse_args()
    row = dispense(json.loads(args.command), args.actual)
    if args.lose_response:
        Path('lab/results/channels/device-committed.json').write_text(json.dumps(row, default=str))
        time.sleep(45)  # The campaign kills this process after observing the durable marker.
        raise RuntimeError('Expected external SIGKILL did not arrive')
    print(json.dumps(row, default=str))
