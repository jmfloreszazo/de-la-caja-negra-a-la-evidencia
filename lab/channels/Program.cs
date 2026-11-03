using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Npgsql;

Guard.Check();
var builder=WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://127.0.0.1:55444");
var app=builder.Build();
app.MapGet("/health",async()=> { await Guard.Probe(); return Results.Ok(new {status="READY"}); });
app.MapGet("/operations/{id:guid}",async(Guid id)=> {
    var op=await Ledger.Read(id);
    return op is null ? Results.NotFound(new {status="UNSEEN"}) : Results.Ok(op.Reply(false));
});
foreach(var route in new[]{"authorize","prepare","settle","expire","transfer"}) {
    var action=route;
    app.MapPost("/"+route,async(Command command,HttpContext http)=> {
        try {
            var reply=await Ledger.Perform(action,command);
            Console.WriteLine(JsonSerializer.Serialize(new {action,command.OperationId,reply.State,reply.Status,reply.PostedCents}));
            if(command.Fault=="drop-response") { http.Abort(); return Results.Empty; }
            return reply.Status=="ID_CONFLICT" ? Results.Conflict(reply) : Results.Ok(reply);
        } catch(ArgumentException error) {
            return Results.BadRequest(new {status="INVALID",error=error.Message});
        }
    });
}
await app.RunAsync();

record Command(Guid OperationId,string Channel,long SourceId,long TargetId,long AmountCents,
               string TerminalId="",int TtlSeconds=60,string Fault="");
record Decision(Guid OperationId,string State,string Status,long RequestedCents,long PostedCents,string? CommandId,bool Duplicate);
record Stored(Guid Id,string Fingerprint,string State,long Requested,long Posted,string? CommandId,DateTime Expiry) {
    public Decision Reply(bool duplicate)=>new(Id,State,State=="DISPENSE_PENDING"?"UNKNOWN":State,Requested,Posted,CommandId,duplicate);
}

static class Guard {
    public const string Core="Host=127.0.0.1;Port=55442;Database=channelslab_core;Username=postgres;Password=channelslocal;Pooling=true;Maximum Pool Size=16;GSS Encryption Mode=Disable";
    public const string Device="Host=127.0.0.1;Port=55443;Database=channelslab_device;Username=postgres;Password=channelslocal;Pooling=true;Maximum Pool Size=16;GSS Encryption Mode=Disable";
    public static void Check() {
        if(Environment.GetEnvironmentVariable("CHANNELS_DISPOSABLE")!="YES")
            throw new InvalidOperationException("Explicit disposable channel fixture required");
    }
    public static async Task Probe() {
        foreach(var pair in new[]{(Core,"channelslab_core"),(Device,"channelslab_device")}) {
            await using var db=new NpgsqlConnection(pair.Item1);await db.OpenAsync();
            await using var q=new NpgsqlCommand("SELECT current_database(),name FROM fixture_meta",db);
            await using var r=await q.ExecuteReaderAsync();
            if(!await r.ReadAsync()||r.GetString(0)!=pair.Item2||r.GetString(1)!="channels-synthetic-v1"||await r.ReadAsync())
                throw new InvalidOperationException("Unknown disposable fixture identity");
        }
    }
}

static class Ledger {
    static async Task<int> Sql(NpgsqlConnection db,NpgsqlTransaction tx,string sql,params (string,object)[] values) {
        await using var q=new NpgsqlCommand(sql,db,tx);
        foreach(var (key,value) in values) q.Parameters.AddWithValue(key,value);
        return await q.ExecuteNonQueryAsync();
    }
    static async Task<T> Scalar<T>(NpgsqlConnection db,NpgsqlTransaction tx,string sql,params (string,object)[] values) {
        await using var q=new NpgsqlCommand(sql,db,tx);
        foreach(var (key,value) in values) q.Parameters.AddWithValue(key,value);
        return (T)(await q.ExecuteScalarAsync()??throw new InvalidOperationException("Missing fixture row"));
    }
    static async Task<Stored?> Get(NpgsqlConnection db,NpgsqlTransaction? tx,Guid id,bool locked=false) {
        await using var q=new NpgsqlCommand("SELECT id,fingerprint,state,requested,posted,command_id,expires_at FROM operations WHERE id=@id"+(locked?" FOR UPDATE":""),db,tx);
        q.Parameters.AddWithValue("id",id);
        await using var r=await q.ExecuteReaderAsync();
        return await r.ReadAsync()?new(r.GetGuid(0),r.GetString(1),r.GetString(2),r.GetInt64(3),r.GetInt64(4),r.IsDBNull(5)?null:r.GetString(5),r.GetDateTime(6)):null;
    }
    public static async Task<Stored?> Read(Guid id) {
        Guard.Check();await using var db=new NpgsqlConnection(Guard.Core);await db.OpenAsync();return await Get(db,null,id);
    }
    public static string Fingerprint(string kind,Command c) {
        var text=string.Join('|',kind,c.Channel,c.SourceId.ToString(CultureInfo.InvariantCulture),
            c.TargetId.ToString(CultureInfo.InvariantCulture),c.AmountCents.ToString(CultureInfo.InvariantCulture),c.TerminalId);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text)));
    }
    static void Validate(string kind,Command c) {
        Guard.Check();
        if(c.OperationId==Guid.Empty||c.SourceId is not (1 or 2)||c.AmountCents<=0||c.AmountCents>100000000||c.TtlSeconds<1||c.TtlSeconds>120)
            throw new ArgumentException("Invalid synthetic operation bounds");
        if(kind=="WITHDRAWAL"&&(c.Channel!="atm"||c.TargetId!=3||c.TerminalId!="ATM-001"))
            throw new ArgumentException("Withdrawal needs the declared fixture terminal and cash-control account");
        if(kind=="TRANSFER"&&(c.Channel is not ("web" or "mobile")||c.TargetId is not (1 or 2)||c.TargetId==c.SourceId||c.TerminalId!=""))
            throw new ArgumentException("Invalid digital fixture route");
        if(c.Fault is not ("" or "drop-response" or "hold-before-commit"))
            throw new ArgumentException("Unknown diagnostic fault");
    }
    static Decision Conflict(Stored op)=>new(op.Id,op.State,"ID_CONFLICT",op.Requested,op.Posted,op.CommandId,true);
    static async Task Seal(NpgsqlTransaction tx,Command c) {
        if(c.Fault=="hold-before-commit") {
            var folder=Path.GetFullPath("lab/results/channels");Directory.CreateDirectory(folder);
            await File.WriteAllTextAsync(Path.Combine(folder,"before-commit.json"),JsonSerializer.Serialize(new {operationId=c.OperationId,stage="BEFORE_COMMIT"}));
            var deadline=DateTime.UtcNow.AddSeconds(45);
            while(!File.Exists(Path.Combine(folder,"release-commit"))) {
                if(DateTime.UtcNow>deadline) throw new TimeoutException("Unreleased diagnostic commit barrier");
                await Task.Delay(50);
            }
        }
        await tx.CommitAsync();
    }
    static async Task Post(NpgsqlConnection db,NpgsqlTransaction tx,Command c,long amount,string eventName) {
        await Sql(db,tx,"UPDATE accounts SET balance=balance-@amount WHERE id=@source",("amount",amount),("source",c.SourceId));
        await Sql(db,tx,"UPDATE accounts SET balance=balance+@amount WHERE id=@target",("amount",amount),("target",c.TargetId));
        await Sql(db,tx,"INSERT INTO postings VALUES (@id,@source,@debit),(@id,@target,@credit)",
            ("id",c.OperationId),("source",c.SourceId),("target",c.TargetId),("debit",-amount),("credit",amount));
        await Sql(db,tx,"INSERT INTO outbox VALUES (@id,@event,@amount)",("id",c.OperationId),("event",eventName),("amount",amount));
    }
    public static async Task<Decision> Perform(string action,Command c) {
        var kind=action=="transfer"?"TRANSFER":"WITHDRAWAL";Validate(kind,c);var fingerprint=Fingerprint(kind,c);
        try {
            await using var db=new NpgsqlConnection(Guard.Core);await db.OpenAsync();
            await using var tx=await db.BeginTransactionAsync();
            foreach(var id in new[]{c.SourceId,c.TargetId}.Distinct().Order())
                await Scalar<long>(db,tx,"SELECT id FROM accounts WHERE id=@id FOR UPDATE",("id",id));
            var op=await Get(db,tx,c.OperationId,true);
            if(op is not null&&op.Fingerprint!=fingerprint) return Conflict(op);
            if(action is "authorize" or "transfer") {
                if(op is not null)return op.Reply(true);
                var available=await Scalar<long>(db,tx,"SELECT balance-COALESCE((SELECT SUM(amount)::bigint FROM holds WHERE account=@source AND active),0) FROM accounts WHERE id=@source",("source",c.SourceId));
                var state=available<c.AmountCents?"DECLINED":action=="transfer"?"COMMITTED":"AUTHORIZED";
                await Sql(db,tx,"INSERT INTO operations(id,kind,channel,source,target,requested,terminal,fingerprint,state,posted,expires_at) VALUES (@id,@kind,@channel,@source,@target,@amount,@terminal,@fp,@state,@posted,clock_timestamp()+make_interval(secs=>@ttl))",
                    ("id",c.OperationId),("kind",kind),("channel",c.Channel),("source",c.SourceId),("target",c.TargetId),
                    ("amount",c.AmountCents),("terminal",c.TerminalId),("fp",fingerprint),("state",state),
                    ("posted",state=="COMMITTED"?c.AmountCents:0L),("ttl",c.TtlSeconds));
                if(state=="AUTHORIZED")await Sql(db,tx,"INSERT INTO holds VALUES (@id,@source,@amount,true)",("id",c.OperationId),("source",c.SourceId),("amount",c.AmountCents));
                if(state=="COMMITTED")await Post(db,tx,c,c.AmountCents,"DigitalTransferCommitted");
                op=await Get(db,tx,c.OperationId);await Seal(tx,c);return op!.Reply(false);
            }
            if(op is null)throw new ArgumentException("No prior authorization");
            if(op.State is "DECLINED" or "POSTED" or "CANCELLED" or "EXPIRED")return op.Reply(true);
            if(action is "prepare" or "expire") {
                if(op.State=="AUTHORIZED") {
                    var expired=await Scalar<bool>(db,tx,"SELECT expires_at<=clock_timestamp() FROM operations WHERE id=@id",("id",c.OperationId));
                    if(expired) {
                        await Sql(db,tx,"UPDATE operations SET state='EXPIRED' WHERE id=@id",("id",c.OperationId));
                        await Sql(db,tx,"UPDATE holds SET active=false WHERE op=@id",("id",c.OperationId));
                    } else if(action=="prepare")await Sql(db,tx,"UPDATE operations SET state='DISPENSE_PENDING',command_id=@command WHERE id=@id",("id",c.OperationId),("command","cash/"+c.OperationId.ToString("D")));
                    op=await Get(db,tx,c.OperationId);await Seal(tx,c);return op!.Reply(false);
                }
                return op.Reply(true); // Pending device work never expires automatically.
            }
            if(action!="settle"||op.State!="DISPENSE_PENDING")return op.Reply(true);
            long? dispensed=null;
            await using(var device=new NpgsqlConnection(Guard.Device)) {
                await device.OpenAsync();
                await using var q=new NpgsqlCommand("SELECT op,terminal,requested,dispensed,fingerprint,state FROM device_commands WHERE command_id=@command",device);
                q.Parameters.AddWithValue("command",op.CommandId!);
                await using var r=await q.ExecuteReaderAsync();
                if(await r.ReadAsync()) {
                    if(r.GetGuid(0)!=c.OperationId||r.GetString(1)!=c.TerminalId||r.GetInt64(2)!=c.AmountCents||r.GetString(4)!=fingerprint||r.GetString(5)!="FINAL")
                        throw new InvalidOperationException("Device journal conflicts with the authorized intent");
                    dispensed=r.GetInt64(3);
                }
            }
            if(dispensed is null)return op.Reply(false); // Missing evidence is UNKNOWN, not zero.
            if(dispensed<0||dispensed>c.AmountCents)throw new InvalidOperationException("Invalid final device amount");
            if(dispensed>0)await Post(db,tx,c,dispensed.Value,"CashWithdrawalPosted");
            await Sql(db,tx,"UPDATE holds SET active=false WHERE op=@id",("id",c.OperationId));
            await Sql(db,tx,"UPDATE operations SET state=@state,posted=@posted WHERE id=@id",("id",c.OperationId),
                ("state",dispensed>0?"POSTED":"CANCELLED"),("posted",dispensed.Value));
            op=await Get(db,tx,c.OperationId);await Seal(tx,c);return op!.Reply(false);
        } catch(PostgresException error) when(error.SqlState=="23505") {
            var existing=await Read(c.OperationId);
            if(existing is null)throw;
            return existing.Fingerprint==fingerprint?existing.Reply(true):Conflict(existing);
        }
    }
}
