// Clean-room functional prototype. In-memory only: NO durable commit, HA, or authorization proof.
// The independent expected results live in contracts/cap007_cap005_synthetic.json.
using System.Text.Json;
using System.Text.Json.Serialization;

if (args.Length != 1)
{
    Console.Error.WriteLine("Usage: dotnet run --project lab/greenfield/Greenfield.csproj -- <synthetic-contract.json>");
    return 2;
}

try
{
    using var document = JsonDocument.Parse(File.ReadAllText(args[0]));
    var root = document.RootElement;
    if (root.GetProperty("schemaVersion").GetInt32() != 1 ||
        root.GetProperty("classification").GetString() != "SYNTHETIC_UNAPPROVED_CAPABILITY_CONTRACT")
        throw new InvalidDataException("Only explicit synthetic contract v1 is supported.");

    var initial = root.GetProperty("initialBalances");
    var balances = new SortedDictionary<string, long>(StringComparer.Ordinal);
    foreach (var account in initial.EnumerateObject())
    {
        if (account.Value.GetInt64() < 0 || string.IsNullOrWhiteSpace(account.Name))
            throw new InvalidDataException("Invalid initial account.");
        balances.Add(account.Name, account.Value.GetInt64());
    }
    if (balances.Count < 2) throw new InvalidDataException("At least two accounts required.");

    var projection = new SortedDictionary<string, long>(balances, StringComparer.Ordinal);
    var operations = new Dictionary<string, (string Source, string Target, long Amount, bool Authorized)>(StringComparer.Ordinal);
    var postings = new List<Posting>();
    var outbox = new List<string>();
    var results = new List<StepResult>();
    long version = 0, projectionVersion = 0;

    foreach (var step in root.GetProperty("steps").EnumerateArray())
    {
        var kind = step.GetProperty("type").GetString();
        switch (kind)
        {
            case "transfer":
            {
                var id = step.GetProperty("operationId").GetString() ?? "";
                var source = step.GetProperty("source").GetString() ?? "";
                var target = step.GetProperty("target").GetString() ?? "";
                long amount = step.GetProperty("amount").GetInt64();
                bool authorized = step.GetProperty("authorized").GetBoolean();
                var reply = step.GetProperty("reply").GetString() ?? "";
                if (string.IsNullOrWhiteSpace(id) || !balances.ContainsKey(source) ||
                    !balances.ContainsKey(target) || source == target || amount <= 0 ||
                    (reply != "received" && reply != "lost-after-apply"))
                    throw new InvalidDataException("Invalid transfer contract input.");
                if (operations.TryGetValue(id, out var previous))
                {
                    var same = previous.Source == source && previous.Target == target &&
                               previous.Amount == amount && previous.Authorized == authorized;
                    results.Add(new(same ? "DUPLICATE_APPLIED" : "ID_CONFLICT", null, version));
                    break;
                }
                if (!authorized)
                {
                    results.Add(new("REJECTED_UNAUTHORIZED", null, version));
                    break;
                }
                if (balances[source] < amount)
                {
                    results.Add(new("REJECTED_INSUFFICIENT", null, version));
                    break;
                }
                checked
                {
                    balances[source] -= amount;
                    balances[target] += amount;
                }
                operations.Add(id, (source, target, amount, authorized));
                postings.Add(new(id, source, -amount));
                postings.Add(new(id, target, amount));
                outbox.Add(id);
                version++;
                results.Add(new(reply == "received" ? "APPLIED" : "UNKNOWN_AFTER_APPLY", null, version));
                break;
            }
            case "project":
                projection = new SortedDictionary<string, long>(balances, StringComparer.Ordinal);
                projectionVersion = version;
                results.Add(new("PROJECTED", null, projectionVersion));
                break;
            case "balance":
            {
                var account = step.GetProperty("account").GetString() ?? "";
                var source = step.GetProperty("source").GetString() ?? "";
                long minimumVersion = step.GetProperty("minimumVersion").GetInt64();
                if (!balances.ContainsKey(account) || minimumVersion < 0)
                    throw new InvalidDataException("Invalid balance request.");
                if (source == "authoritative")
                {
                    results.Add(version < minimumVersion
                        ? new("UNAVAILABLE_VERSION", null, version)
                        : new("BOOKED", balances[account], version));
                }
                else if (source == "projection")
                {
                    results.Add(projectionVersion < minimumVersion
                        ? new("STALE_PROJECTION", null, projectionVersion)
                        : new("PROJECTED_BALANCE", projection[account], projectionVersion));
                }
                else throw new InvalidDataException("Unknown balance source.");
                break;
            }
            default:
                throw new InvalidDataException("Unsupported synthetic step type.");
        }
    }

    var output = new Output("SYNTHETIC_IN_MEMORY_ONLY", results, balances, version,
                            projectionVersion, postings, outbox);
    Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    }));
    return 0;
}
catch (Exception exception) when (exception is IOException or InvalidDataException or
                                 JsonException or ArgumentException or OverflowException)
{
    Console.Error.WriteLine($"INVALID_SYNTHETIC_CONTRACT: {exception.Message}");
    return 2;
}

sealed record StepResult(string Status, long? Balance, long Version);
sealed record Posting(string OperationId, string Account, long Delta);
sealed record Output(string Status, List<StepResult> Results,
                     SortedDictionary<string, long> Balances, long Version,
                     long ProjectionVersion, List<Posting> Postings, List<string> Outbox);
