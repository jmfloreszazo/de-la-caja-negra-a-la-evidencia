"""Deterministic simulation: why a closed-loop load test can hide a stall that an open-loop test reveals.

No network, no sleeping, no randomness: a single FIFO server with a fixed service time and one
stall (think of a long lock hold, a log flush or a GC pause). We measure the same server twice:

* closed loop: one client sends the next request only after the previous response arrives;
* open loop: requests are scheduled at a fixed arrival rate and latency is measured from the
  *scheduled* send time, so queueing during the stall is counted.

Usage: python3 tools/coordinated_omission_demo.py [--json]
"""
import argparse, json

SERVICE_MS = 1.0          # service time per request when the server is healthy
DURATION_MS = 10_000.0    # 10 simulated seconds
STALL_START_MS = 4_000.0  # the server stops serving at t = 4.0 s ...
STALL_MS = 500.0          # ... for 500 ms
OPEN_LOOP_RATE_PER_S = 500  # 50 % utilisation when healthy


def serve(arrival_ms, server_free_ms):
    """Return completion time for a request that arrives at arrival_ms (FIFO, one server)."""
    start = max(arrival_ms, server_free_ms)
    stall_end = STALL_START_MS + STALL_MS
    if STALL_START_MS <= start < stall_end or (start < STALL_START_MS < start + SERVICE_MS):
        start = max(start, stall_end)
    return start + SERVICE_MS


def percentile(sorted_values, p):
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, int(round((len(sorted_values) - 1) * p)))
    return sorted_values[index]


def summarise(name, latencies, elapsed_ms):
    lat = sorted(latencies)
    return {
        'mode': name,
        'requests': len(lat),
        'throughputPerSecond': round(len(lat) / (elapsed_ms / 1000.0), 1),
        'p50Ms': round(percentile(lat, 0.50), 2),
        'p95Ms': round(percentile(lat, 0.95), 2),
        'p99Ms': round(percentile(lat, 0.99), 2),
        'maxMs': round(lat[-1], 2),
        'requestsOver100Ms': sum(1 for x in lat if x > 100.0),
    }


def closed_loop():
    t, free, lat = 0.0, 0.0, []
    while t < DURATION_MS:
        done = serve(t, free)
        lat.append(done - t)
        free = t = done          # the client waits, so it stops offering load during the stall
    return summarise('closed-loop (1 client)', lat, t), lat


def open_loop():
    interval = 1000.0 / OPEN_LOOP_RATE_PER_S
    free, lat, n, last = 0.0, [], 0, 0.0
    while n * interval < DURATION_MS:
        scheduled = n * interval
        done = serve(scheduled, free)
        lat.append(done - scheduled)   # measured from the intended send time
        free, last = done, done
        n += 1
    return summarise(f'open-loop ({OPEN_LOOP_RATE_PER_S}/s)', lat, last), lat


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true', help='print raw JSON only')
    args = parser.parse_args()
    closed, _ = closed_loop()
    opened, _ = open_loop()
    if args.json:
        print(json.dumps([closed, opened], indent=2))
    else:
        print(f'Same server, one {STALL_MS:.0f} ms stall at t={STALL_START_MS / 1000:.1f}s, '
              f'{SERVICE_MS:.0f} ms service time.\n')
        header = f"{'mode':26}{'req':>7}{'req/s':>9}{'p50':>8}{'p95':>8}{'p99':>9}{'max':>9}{'>100ms':>8}"
        print(header)
        print('-' * len(header))
        for r in (closed, opened):
            print(f"{r['mode']:26}{r['requests']:>7}{r['throughputPerSecond']:>9}{r['p50Ms']:>8}"
                  f"{r['p95Ms']:>8}{r['p99Ms']:>9}{r['maxMs']:>9}{r['requestsOver100Ms']:>8}")
        print('\nThe closed loop records the stall once, because its only client was waiting.'
              '\nThe open loop keeps offering load, so every request that queued behind the stall counts.')
