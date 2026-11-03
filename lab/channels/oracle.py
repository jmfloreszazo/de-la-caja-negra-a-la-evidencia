"""Read-only assertions over both stores; independent of the candidate implementation."""
import hashlib
from collections import defaultdict


def audit(data, offered):
    failures = defaultdict(list)
    def check(group, condition, message):
        if not condition:
            failures[group].append(message)
    core, device = data['core'], data['device']
    ops = {str(o['id']): o for o in core['operations']}
    posts = defaultdict(dict)
    for row in core['postings']:
        posts[str(row['op'])][row['account']] = row['delta']
    events = {str(r['op']): r for r in core['outbox']}
    holds = {str(r['op']): r for r in core['holds']}
    commands = {str(r['op']): r for r in device['device_commands']}
    balances = {r['id']: r['balance'] for r in core['accounts']}
    check('conservation', sum(balances.values()) == 20000, 'Closed-world sum differs')
    for account, initial in [(1, 10000), (2, 10000), (3, 0)]:
        expected = initial + sum(p.get(account, 0) for p in posts.values())
        check('projection', balances.get(account) == expected and expected >= 0, f'Account {account} projection')
        reserved = sum(h['amount'] for h in holds.values() if h['account'] == account and h['active'])
        check('holds', balances.get(account, -1) - reserved >= 0, f'Account {account} availability')
    for key, op in ops.items():
        intent = offered.get(key)
        check('identity', intent is not None, f'Unoffered operation {key}')
        if intent is None:
            continue
        kind = 'WITHDRAWAL' if intent['channel'] == 'atm' else 'TRANSFER'
        fields = [kind, intent['channel'], str(intent['sourceId']), str(intent['targetId']), str(intent['amountCents']), intent['terminalId']]
        fp = hashlib.sha256('|'.join(fields).encode()).hexdigest().upper()
        check('identity', op['fingerprint'] == fp and op['kind'] == kind and op['channel'] == intent['channel']
              and op['source'] == intent['sourceId'] and op['target'] == intent['targetId']
              and op['requested'] == intent['amountCents'] and op['terminal'] == intent['terminalId'], f'Intent {key}')
        final = op['state'] in ('POSTED', 'COMMITTED')
        amount = op['posted'] if final else 0
        check('postings', posts.get(key, {}) == ({op['source']: -amount, op['target']: amount} if final and amount > 0 else {}), f'Paired entries {key}')
        event = events.get(key)
        check('outbox', (event is not None and event['amount'] == amount and event['event'] == ('CashWithdrawalPosted' if kind == 'WITHDRAWAL' else 'DigitalTransferCommitted')) if final else event is None, f'Financial event {key}')
        hold = holds.get(key)
        pending = op['state'] in ('AUTHORIZED', 'DISPENSE_PENDING')
        check('holds', (hold is not None and hold['active'] and hold['amount'] == op['requested'] and hold['account'] == op['source']) if pending else (hold is None or not hold['active']), f'Hold state {key}')
        command = commands.get(key)
        if kind == 'TRANSFER':
            check('identity', op['state'] in ('COMMITTED', 'DECLINED') and op['posted'] == (op['requested'] if final else 0), f'Digital decision {key}')
        else:
            check('device', op['posted'] == (command['dispensed'] if op['state'] == 'POSTED' and command else 0), f'Cash amount {key}')
            check('device', op['state'] != 'POSTED' or (command is not None and command['dispensed'] > 0), f'Final cash proof {key}')
            check('device', op['state'] != 'CANCELLED' or (command is not None and command['dispensed'] == 0), f'Zero cash proof {key}')
            check('identity', op['command_id'] == ('cash/' + key) if op['state'] in ('DISPENSE_PENDING', 'POSTED', 'CANCELLED') else op['command_id'] is None, f'Stable command {key}')
        if command:
            check('device', command['command_id'] == op['command_id'] and command['fingerprint'] == fp and command['requested'] == op['requested'] and command['terminal'] == op['terminal'] and command['state'] == 'FINAL' and 0 <= command['dispensed'] <= op['requested'] and op['state'] in ('DISPENSE_PENDING', 'POSTED', 'CANCELLED'), f'Device intent {key}')
    check('device', set(commands) <= set(ops), 'Stray device command')
    check('postings', set(posts) <= set(ops), 'Stray posting')
    check('outbox', set(events) <= set(ops), 'Stray outbox')
    check('holds', set(holds) <= set(ops), 'Stray hold')
    check('device', len(device['inventory']) == 1 and device['inventory'][0]['remaining'] == 100000 - sum(c['dispensed'] for c in commands.values()), 'Cash stock reconciliation')
    groups = ['projection', 'conservation', 'identity', 'postings', 'outbox', 'holds', 'device']
    return {'status': 'FAIL' if failures else 'PASS', 'checks': {g: failures[g] for g in groups}}
