using System.Text.RegularExpressions;
using Npgsql;

namespace E2.OrleansLab;

public sealed class PgDurableLedger(NpgsqlDataSource source) : IDurableLedger
{
    private static readonly HashSet<string> Retryable = ["40P01", "40001", "55P03", "23505"];
    private static readonly int MaxSyntheticAccount =
        Environment.GetEnvironmentVariable("E2_MAX_ACCOUNT_ID") == "1000" ? 1000 : 16;

    public static bool Valid(TransferCommand command) =>
        command.OperationId is not null &&
        Regex.IsMatch(command.OperationId, @"\A[A-Za-z0-9-]{1,80}\z") &&
        command.SourceAccountId >= 1 && command.SourceAccountId <= MaxSyntheticAccount &&
        command.TargetAccountId >= 1 && command.TargetAccountId <= MaxSyntheticAccount &&
        command.SourceAccountId != command.TargetAccountId &&
        command.AmountCents is > 0 and <= 1_000_000_000_000 &&
        command.Fault is "none" or "throw-after-debit" or "lost-response" or
        "kill-before-commit" or "kill-after-commit";

    public async Task<TransferResult> Transfer(TransferCommand command)
    {
        if (!Valid(command))
            return new TransferResult("INVALID", 0, [], "ledger");

        var errors = new List<string>();
        for (var attempt = 0; attempt < 6; ++attempt)
        {
            try
            {
                await using var db = await source.OpenConnectionAsync();
                await using var tx = await db.BeginTransactionAsync();
                await Execute(tx, "SET LOCAL lock_timeout = '750ms'");
                await Execute(tx, "SELECT pg_advisory_xact_lock(hashtextextended($1,0))",
                    command.OperationId);

                var previous = await Row(tx,
                    "SELECT src,dst,amount,status FROM operations WHERE id=$1",
                    command.OperationId);
                string verdict;
                if (previous is not null)
                {
                    var equal = Convert.ToInt32(previous[0]) == command.SourceAccountId &&
                                Convert.ToInt32(previous[1]) == command.TargetAccountId &&
                                Convert.ToInt64(previous[2]) == command.AmountCents;
                    verdict = equal ? "DUPLICATE_" + previous[3] : "ID_CONFLICT";
                }
                else
                {
                    foreach (var account in new[] {command.SourceAccountId, command.TargetAccountId}.Order())
                    {
                        if (await Scalar(tx,
                            "SELECT id FROM accounts WHERE id=$1 FOR UPDATE", account) is null)
                            throw new InvalidOperationException("Missing account row");
                    }

                    var affected = await Execute(tx,
                        "UPDATE accounts SET balance=balance-$1 WHERE id=$2 AND balance >= $1",
                        command.AmountCents, command.SourceAccountId);
                    if (affected == 1)
                    {
                        if (command.Fault == "throw-after-debit")
                            throw new InjectedRollbackException();
                        if (command.Fault == "kill-before-commit")
                        {
                            // Only run inside disposable E2 CI. Abrupt process
                            // death releases the DB session and rolls back
                            // the entire uncommitted transaction.
                            System.Diagnostics.Process.GetCurrentProcess().Kill();
                        }
                        await Execute(tx,
                            "UPDATE accounts SET balance=balance+$1 WHERE id=$2",
                            command.AmountCents, command.TargetAccountId);
                    }
                    verdict = affected == 1 ? "COMMITTED" : "REJECTED";
                    await Execute(tx,
                        "INSERT INTO operations(id,src,dst,amount,status) VALUES($1,$2,$3,$4,$5)",
                        command.OperationId, command.SourceAccountId,
                        command.TargetAccountId, command.AmountCents, verdict);
                    if (affected == 1)
                    {
                        await Execute(tx,
                            "INSERT INTO postings(op,account,delta) VALUES($1,$2,$3),($1,$4,$5)",
                            command.OperationId, command.SourceAccountId,
                            -command.AmountCents, command.TargetAccountId,
                            command.AmountCents);
                        await Execute(tx,
                            "INSERT INTO outbox(op,event) VALUES($1,$2)",
                            command.OperationId, "TransferCommitted");
                    }
                }
                await tx.CommitAsync();
                if (command.Fault == "kill-after-commit" && verdict == "COMMITTED")
                {
                    // Actual host process termination after SQL COMMIT.
                    // A fresh host must replay the stable operation ID.
                    System.Diagnostics.Process.GetCurrentProcess().Kill();
                }

                // The COMMIT is durable before the response is deliberately hidden.
                // A replay must resolve via the persisted operation ID.
                if (command.Fault == "lost-response" && verdict == "COMMITTED")
                    return new TransferResult("AMBIGUOUS_RESPONSE", errors.Count,
                        [..errors], "ledger");

                return new TransferResult(verdict, errors.Count, [..errors], "ledger");
            }
            catch (InjectedRollbackException)
            {
                return new TransferResult("INJECTED_ROLLBACK", errors.Count,
                    [..errors], "ledger");
            }
            catch (PostgresException ex) when (Retryable.Contains(ex.SqlState))
            {
                errors.Add(ex.SqlState);
                if (attempt < 5)
                    await Task.Delay(25 * (attempt + 1));
            }
        }
        return new TransferResult("RETRY_EXHAUSTED", errors.Count,
            [..errors], "ledger");
    }

    private static NpgsqlCommand Command(NpgsqlTransaction tx, string sql,
        params object[] parameters)
    {
        var command = new NpgsqlCommand(sql, tx.Connection, tx);
        foreach (var value in parameters)
            command.Parameters.Add(new NpgsqlParameter { Value = value });
        return command;
    }

    private static async Task<int> Execute(NpgsqlTransaction tx, string sql,
        params object[] parameters)
    {
        await using var command = Command(tx, sql, parameters);
        return await command.ExecuteNonQueryAsync();
    }

    private static async Task<object?> Scalar(NpgsqlTransaction tx, string sql,
        params object[] parameters)
    {
        await using var command = Command(tx, sql, parameters);
        return await command.ExecuteScalarAsync();
    }

    private static async Task<object[]?> Row(NpgsqlTransaction tx, string sql,
        params object[] parameters)
    {
        await using var command = Command(tx, sql, parameters);
        await using var reader = await command.ExecuteReaderAsync();
        if (!await reader.ReadAsync())
            return null;
        var result = new object[reader.FieldCount];
        reader.GetValues(result);
        return result;
    }

    private sealed class InjectedRollbackException : Exception { }
}
