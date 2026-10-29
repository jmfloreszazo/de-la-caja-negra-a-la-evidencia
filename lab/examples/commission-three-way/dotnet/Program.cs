using System.Globalization;
using System.Text.Json;

// Synthetic financial commission example, not a banking ledger or production code.
var inv = CultureInfo.InvariantCulture;
if (args.Contains("--race", StringComparer.Ordinal))
{
    await ConcurrencyExample.RunAsync();
    return;
}
var mutant = args.Contains("--mutant", StringComparer.Ordinal);
var input = Console.ReadLine() ?? throw new InvalidOperationException("Missing CSV input");
var fields = input.Split(',');
if (fields.Length != 2) throw new FormatException("Expected amount,rate");
var amount = decimal.Parse(fields[0], NumberStyles.Number, inv);
var rate = decimal.Parse(fields[1], NumberStyles.Number, inv);
if (amount < 0 || amount > 99_999_999.99m || rate < 0 || rate > 999.99m)
    throw new ArgumentOutOfRangeException(nameof(input), "Outside synthetic COBOL fixture range");
var raw = amount * rate / 100m;
var result = decimal.Round(raw, 2,
    mutant ? MidpointRounding.ToEven : MidpointRounding.AwayFromZero);
Console.WriteLine(result.ToString("0.00", inv));

static class ConcurrencyExample
{
    // Only an in-process demonstration. Not durable, not valid across instances.
    public static async Task RunAsync()
    {
        var naiveBalance = 1000m;
        async Task<bool> NaiveWithdraw()
        {
            var snapshot = naiveBalance;
            await Task.Delay(30); // Force a scheduling window after reading.
            if (snapshot < 600m) return false;
            naiveBalance = snapshot - 600m;
            return true;
        }
        var naive = await Task.WhenAll(NaiveWithdraw(), NaiveWithdraw());
        var safeBalance = 1000m;
        using var gate = new SemaphoreSlim(1, 1);
        async Task<bool> LockedWithdraw()
        {
            await gate.WaitAsync();
            try
            {
                var snapshot = safeBalance;
                await Task.Delay(30);
                if (snapshot < 600m) return false;
                safeBalance = snapshot - 600m;
                return true;
            }
            finally { gate.Release(); }
        }
        var safe = await Task.WhenAll(LockedWithdraw(), LockedWithdraw());
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            NaiveApproved = naive.Count(x => x),
            NaiveFinalBalance = naiveBalance,
            SafeApproved = safe.Count(x => x),
            SafeFinalBalance = safeBalance,
            Warning = "SemaphoreSlim is local to one process; use database ACID or an appropriate distributed protocol"
        }));
    }
}
