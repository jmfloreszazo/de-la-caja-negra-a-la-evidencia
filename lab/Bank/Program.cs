using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.RegularExpressions;

// Linux tutorial using the real SQLite engine. One writer at a time, not row-level locking.
// No remote broker, replication, multi-node consensus or production authorization.
if(args.Length<2) return 4;
var mode=args[0];var path=args[1];
try {
 if(mode=="version") {using var db=new Db(path);Console.WriteLine(db.Rows("SELECT sqlite_version() AS v")[0]["v"]);return 0;}
 if(mode=="init") {
  var n=args.Length>2?int.Parse(args[2]):16; if(n<2||n>10000) return 4;
  using var db=new Db(path);db.Exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; BEGIN IMMEDIATE;");
  db.Exec("CREATE TABLE accounts(id INTEGER PRIMARY KEY,balance INTEGER NOT NULL CHECK(balance>=0));"+
   "CREATE TABLE operations(id TEXT PRIMARY KEY,src INTEGER NOT NULL,dst INTEGER NOT NULL,amount INTEGER NOT NULL CHECK(amount>0),status TEXT NOT NULL);"+
   "CREATE TABLE postings(op TEXT REFERENCES operations(id),account INTEGER REFERENCES accounts(id),delta INTEGER NOT NULL CHECK(delta<>0),PRIMARY KEY(op,account));"+
   "CREATE TABLE outbox(op TEXT PRIMARY KEY REFERENCES operations(id),event TEXT NOT NULL);");
  for(int i=1;i<=n;i++) db.Exec($"INSERT INTO accounts VALUES({i},100000);");
  db.Exec("COMMIT"); Console.WriteLine("initialized");return 0;
 }
 if(mode=="transfer") {
  if(args.Length<6)return 4;
  var r=Transfer(path,args[2],int.Parse(args[3]),int.Parse(args[4]),long.Parse(args[5]),args.Length>6?args[6]:"none");
  Console.WriteLine(JsonSerializer.Serialize(r));return r.status=="RETRY_EXHAUSTED"?7:0;
 }
 if(mode=="worker") {
  var worker=int.Parse(args[2]);var count=int.Parse(args[3]);var hot=args[4]=="hot";var prefix=args[5];
  var results=new List<Outcome>();
  for(int i=0;i<count;i++) {
   int src=hot?1:1+(worker*count+i)%16;
   int dst=hot?2:1+src%16;
   results.Add(Transfer(path,$"{prefix}-{worker}-{i}",src,dst,1,"none"));
  }
  Console.WriteLine(JsonSerializer.Serialize(results)); return results.Any(x=>x.status=="RETRY_EXHAUSTED")?7:0;
 }
 return 4;
} catch(Exception e) { Console.Error.WriteLine(e.Message);return 5; }

static Outcome Transfer(string path,string id,int src,int dst,long amount,string fault) {
 if(!Regex.IsMatch(id,"^[A-Za-z0-9-]{1,80}$")||src<=0||dst<=0||src==dst||amount<=0||amount>1000000000000)
  throw new ArgumentException("Invalid transfer");
 if(!new[]{"none","throw-after-debit","crash-after-debit","lost-response"}.Contains(fault))throw new ArgumentException("Invalid fault");
 var clock=Stopwatch.StartNew(); int retries=0;
 using var db=new Db(path);
 for(int attempt=0;attempt<12;attempt++) {
  bool begun=false;
  try {
   db.Exec("BEGIN IMMEDIATE");begun=true;
   var existing=db.Rows($"SELECT src,dst,amount,status FROM operations WHERE id='{id}'");
   if(existing.Count>0) {
    var e=existing[0];
    var same=e["src"]==src.ToString()&&e["dst"]==dst.ToString()&&e["amount"]==amount.ToString();
    db.Exec("COMMIT");begun=false;
    return new(same?"DUPLICATE_"+e["status"]:"ID_CONFLICT",retries,clock.Elapsed.TotalMilliseconds);
   }
   if(db.Number($"SELECT COUNT(*) FROM accounts WHERE id IN ({src},{dst})")!=2)throw new InvalidOperationException("Missing account");
   db.Exec($"UPDATE accounts SET balance=balance-{amount} WHERE id={src} AND balance>={amount}");
   var approved=db.Changes==1;
   if(approved) {
    if(fault=="crash-after-debit")Environment.Exit(91);
    if(fault=="throw-after-debit")throw new InvalidOperationException("Injected failure after debit");
    db.Exec($"UPDATE accounts SET balance=balance+{amount} WHERE id={dst}");
   }
   var status=approved?"COMMITTED":"REJECTED";
   db.Exec($"INSERT INTO operations VALUES('{id}',{src},{dst},{amount},'{status}')");
   if(approved) db.Exec($"INSERT INTO postings VALUES('{id}',{src},-{amount}),('{id}',{dst},{amount}); INSERT INTO outbox VALUES('{id}','TransferCommitted');");
   db.Exec("COMMIT");begun=false;
   if(fault=="lost-response")Environment.Exit(92);
   return new(status,retries,clock.Elapsed.TotalMilliseconds);
  } catch(SqlFailure e) when(e.Code==5||e.Code==6) {
   if(begun)db.Exec("ROLLBACK");retries++;
   Thread.Sleep(Math.Min(50,2*(attempt+1))+Random.Shared.Next(1,8));
  } catch {if(begun)db.Exec("ROLLBACK");throw;}
 }
 return new("RETRY_EXHAUSTED",retries,clock.Elapsed.TotalMilliseconds);
}
record Outcome(string status,int retries,double elapsedMs);
sealed class SqlFailure(int code,string message):Exception(message){public int Code=code;}
sealed class Db:IDisposable {
 IntPtr handle;
 [UnmanagedFunctionPointer(CallingConvention.Cdecl)]delegate int Callback(IntPtr arg,int count,IntPtr values,IntPtr names);
 [DllImport("libsqlite3.so.0",CallingConvention=CallingConvention.Cdecl)]static extern int sqlite3_open([MarshalAs(UnmanagedType.LPUTF8Str)]string file,out IntPtr db);
 [DllImport("libsqlite3.so.0",CallingConvention=CallingConvention.Cdecl)]static extern int sqlite3_close(IntPtr db);
 [DllImport("libsqlite3.so.0",CallingConvention=CallingConvention.Cdecl)]static extern int sqlite3_exec(IntPtr db,[MarshalAs(UnmanagedType.LPUTF8Str)]string sql,Callback? cb,IntPtr arg,out IntPtr error);
 [DllImport("libsqlite3.so.0",CallingConvention=CallingConvention.Cdecl)]static extern void sqlite3_free(IntPtr memory);
 [DllImport("libsqlite3.so.0",CallingConvention=CallingConvention.Cdecl)]static extern int sqlite3_busy_timeout(IntPtr db,int ms);
 [DllImport("libsqlite3.so.0",CallingConvention=CallingConvention.Cdecl)]static extern int sqlite3_changes(IntPtr db);
 public Db(string path){var rc=sqlite3_open(path,out handle);if(rc!=0)throw new SqlFailure(rc,"Open failed");sqlite3_busy_timeout(handle,100);Exec("PRAGMA foreign_keys=ON; PRAGMA synchronous=FULL;");}
 public int Changes=>sqlite3_changes(handle);
 public List<Dictionary<string,string>> Rows(string sql) {
  var rows=new List<Dictionary<string,string>>();
  Callback cb=(arg,count,values,names)=>{var row=new Dictionary<string,string>();for(int i=0;i<count;i++){
   var name=Marshal.PtrToStringUTF8(Marshal.ReadIntPtr(names,i*IntPtr.Size))!;
   var value=Marshal.PtrToStringUTF8(Marshal.ReadIntPtr(values,i*IntPtr.Size))??"";row[name]=value;
  }rows.Add(row);return 0;};
  var rc=sqlite3_exec(handle,sql,cb,IntPtr.Zero,out var error);GC.KeepAlive(cb);
  if(rc!=0){var msg=Marshal.PtrToStringUTF8(error)??"SQL error";sqlite3_free(error);throw new SqlFailure(rc,msg);}return rows;
 }
 public void Exec(string sql){var rc=sqlite3_exec(handle,sql,null,IntPtr.Zero,out var error);if(rc!=0){var msg=Marshal.PtrToStringUTF8(error)??"SQL error";sqlite3_free(error);throw new SqlFailure(rc,msg);}}
 public long Number(string sql)=>long.Parse(Rows(sql)[0].Values.First());
 public void Dispose(){sqlite3_close(handle);}
}
