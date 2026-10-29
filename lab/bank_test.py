"""Runs real .NET processes against one SQLite WAL database; validates from Python."""
import json,os,pathlib,sqlite3,subprocess,time,concurrent.futures,hashlib,platform
ROOT=pathlib.Path(__file__).resolve().parent;os.chdir(ROOT)
DOTNET=os.environ.get('DOTNET','dotnet');DLL='Bank/bin/Release/net10.0/Bank.dll'
OUT=ROOT/'results'/'bank';OUT.mkdir(parents=True,exist_ok=True)
def cmd(*args):return [DOTNET,DLL,*map(str,args)]
def run(*args):return subprocess.run(cmd(*args),capture_output=True,text=True,timeout=30)
def check(p,code=0):
 assert p.returncode==code,(p.returncode,p.stdout,p.stderr)
 return json.loads(p.stdout) if p.stdout.strip().startswith(('{','[')) else p.stdout.strip()
def init(name,n=16):
 p=OUT/(name+'.db')
 for suffix in ['','-wal','-shm']:(pathlib.Path(str(p)+suffix)).unlink(missing_ok=True)
 check(run('init',p,n));return p
def scalar(db,sql):
 with sqlite3.connect(db) as c:return c.execute(sql).fetchone()[0]
def invariant(db):
 with sqlite3.connect(db) as c:
  def s(q):return c.execute(q).fetchone()[0]
  tests={
   'nonnegative':s('SELECT MIN(balance) FROM accounts')>=0,
   'conserved':s('SELECT SUM(balance) FROM accounts')==s('SELECT COUNT(*)*100000 FROM accounts'),
   'balancedPostings':s('SELECT COUNT(*) FROM (SELECT op FROM postings GROUP BY op HAVING SUM(delta)<>0 OR COUNT(*)<>2)')==0,
   'twoPostingsPerCommit':s("SELECT COUNT(*) FROM operations o WHERE status='COMMITTED' AND (SELECT COUNT(*) FROM postings p WHERE p.op=o.id)<>2")==0,
   'outboxAtomic':s("SELECT COUNT(*) FROM operations o WHERE status='COMMITTED' AND NOT EXISTS(SELECT 1 FROM outbox b WHERE b.op=o.id)")==0 and s("SELECT COUNT(*) FROM outbox b JOIN operations o ON b.op=o.id WHERE o.status<>'COMMITTED'")==0,
   'projectionAgrees':s('SELECT COUNT(*) FROM accounts a WHERE balance<>100000+COALESCE((SELECT SUM(delta) FROM postings p WHERE p.account=a.id),0)')==0,
  }
 assert all(tests.values()),tests
 return tests
build=subprocess.run([DOTNET,'build','Bank','-c','Release','-m:1','--disable-build-servers'],capture_output=True,text=True,timeout=120)
(OUT/'build.txt').write_text(build.stdout+build.stderr);assert build.returncode==0,build.stdout+build.stderr
controls={};db=init('acceptance')
# Concurrency: only one of two independent processes may withdraw 70000 from 100000.
with concurrent.futures.ThreadPoolExecutor(2) as ex:
 rows=list(ex.map(lambda i:check(run('transfer',db,f'race-{i}',1,2,70000)),range(2)))
assert sorted(r['status'] for r in rows)==['COMMITTED','REJECTED'];controls['overdraftRace']='PASS'
# Concurrent duplicate submissions, followed by a conflicting reuse of the ID.
with concurrent.futures.ThreadPoolExecutor(8) as ex:
 rows=list(ex.map(lambda _:check(run('transfer',db,'same-id',2,1,100)),range(8)))
assert sum(r['status']=='COMMITTED' for r in rows)==1
assert sum(r['status']=='DUPLICATE_COMMITTED' for r in rows)==7
assert check(run('transfer',db,'same-id',2,1,101))['status']=='ID_CONFLICT';controls['duplicateAndConflict']='PASS'
before=scalar(db,'SELECT balance FROM accounts WHERE id=2')
check(run('transfer',db,'abort',2,1,100,'throw-after-debit'),5)
assert scalar(db,'SELECT balance FROM accounts WHERE id=2')==before
assert scalar(db,"SELECT COUNT(*) FROM operations WHERE id='abort'")==0;controls['exceptionRollback']='PASS'
check(run('transfer',db,'crash',2,1,100,'crash-after-debit'),91)
assert scalar(db,'SELECT balance FROM accounts WHERE id=2')==before
assert scalar(db,"SELECT COUNT(*) FROM operations WHERE id='crash'")==0;controls['processCrashRecovery']='PASS'
check(run('transfer',db,'lost',2,1,100,'lost-response'),92)
assert check(run('transfer',db,'lost',2,1,100))['status']=='DUPLICATE_COMMITTED';controls['commitWithoutResponse']='PASS'
# Force real lock contention and release it while the second process retries.
holder=sqlite3.connect(db);holder.execute('BEGIN IMMEDIATE')
p=subprocess.Popen(cmd('transfer',db,'blocked',2,1,1),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
time.sleep(.45);holder.rollback();holder.close();stdout,stderr=p.communicate(timeout=15)
assert p.returncode==0,(stdout,stderr);r=json.loads(stdout);assert r['retries']>0,r
controls['lockWaitAndRetry']='PASS'
# No liveness claim after retry exhaustion: report failure, preserve balances.
holder=sqlite3.connect(db);holder.execute('BEGIN IMMEDIATE')
p=run('transfer',db,'exhausted',2,1,1);holder.rollback();holder.close()
assert p.returncode==7,p.stdout;assert json.loads(p.stdout)['status']=='RETRY_EXHAUSTED'
assert scalar(db,"SELECT COUNT(*) FROM operations WHERE id='exhausted'")==0;controls['boundedRetries']='PASS'
controls['accountingInvariants']=invariant(db)
# Seed invalid persisted evidence by deleting a posting. The oracle MUST detect it.
corrupt=OUT/'negative-control.db'
with sqlite3.connect(db) as source,sqlite3.connect(corrupt) as target:source.backup(target)
with sqlite3.connect(corrupt) as c:c.execute('DELETE FROM postings WHERE rowid=(SELECT MIN(rowid) FROM postings)');c.commit()
try:invariant(corrupt)
except AssertionError:controls['oracleRejectsCorruptLedger']='PASS'
else:raise AssertionError('Oracle accepted corrupt ledger')
# Closed-loop multiprocess observations, includes launch and initialization overhead.
measurements=[]
for pattern in ['uniform','hot']:
 for workers in [1,2,4,8]:
  db=init(f'load-{pattern}-{workers}')
  begin=time.perf_counter()
  processes=[subprocess.Popen(cmd('worker',db,w,32,pattern,'load'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for w in range(workers)]
  results=[]
  for p in processes:
   out,err=p.communicate(timeout=45);assert p.returncode==0,(out,err);results.extend(json.loads(out))
  duration=time.perf_counter()-begin;lat=sorted(x['elapsedMs'] for x in results)
  pct=lambda p:lat[min(len(lat)-1,int((len(lat)-1)*p))]
  invariant(db)
  measurements.append({'pattern':pattern,'workers':workers,'operations':len(results),'committed':sum(x['status']=='COMMITTED' for x in results),'elapsedSeconds':round(duration,4),'attemptsPerSecondIncludingProcessLaunch':round(len(results)/duration,2),'operationP50Ms':round(pct(.50),3),'operationP95Ms':round(pct(.95),3),'operationP99Ms':round(pct(.99),3),'busyRetries':sum(x['retries'] for x in results)})
summary={'status':'PASS','controls':controls,'measurements':measurements,'environment':platform.platform(),'dotnet':subprocess.check_output([DOTNET,'--version'],text=True).strip(),'sqlitePythonVerifier':sqlite3.sqlite_version,'sqliteNativeDotnet':check(run('version',db)),'sourceSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'Bank/Program.cs',ROOT/'Bank/Bank.csproj',ROOT/'bank_test.py']},'limits':'Synthetic SQLite single-writer Linux lab. Closed-loop local measurements; no mainframe baseline, no Azure measurement, no DB row deadlock/failover/2PC test, no power-loss durability test, no external message delivery.'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
