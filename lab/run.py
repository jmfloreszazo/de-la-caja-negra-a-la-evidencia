"""Python orchestrates actual COBOL and .NET processes; acceptance runs in .NET."""
import hashlib, json, os, pathlib, platform, shutil, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parent
os.chdir(ROOT)
DOTNET=os.environ.get('DOTNET','dotnet')
COBC=os.environ.get('COBC','cobc')
RESULTS=ROOT/'results'; RESULTS.mkdir(exist_ok=True)
def run(cmd,**kw):
    return subprocess.run(cmd,text=True,capture_output=True,timeout=120,**kw)
def checked(cmd,**kw):
    p=run(cmd,**kw)
    if p.returncode: raise RuntimeError(f'{cmd}: {p.stdout}\n{p.stderr}')
    return p.stdout.strip()
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def gate(name,rows,authority='demo-authorized',digest=None):
    path=RESULTS/(name+'-observations.json')
    path.write_text(json.dumps(rows,indent=2)+'\n')
    p=run([DOTNET,'Gate/bin/Release/net10.0/Gate.dll','contracts/cases.json',digest or anchor,str(path),authority])
    report=json.loads(p.stdout); report['exitCode']=p.returncode
    (RESULTS/(name+'-gate.json')).write_text(json.dumps(report,indent=2)+'\n')
    return report
start=time.time()
try:
    sdk=checked([DOTNET,'--version']); compiler=checked([COBC,'-V']).splitlines()[0]
    for project in ['Candidate','Gate']:
        log=checked([DOTNET,'build',project,'-c','Release','-m:1','--disable-build-servers'])
        (RESULTS/(project+'-build.txt')).write_text(log+'\n')
    checked([COBC,'-x','-free','-o','legacy/fee','legacy/fee.cob'])
    cases=json.loads(pathlib.Path('contracts/cases.json').read_text())
    anchor=pathlib.Path('contracts/cases.sha256').read_text().strip()
    if sha('contracts/cases.json')!=anchor:raise RuntimeError('Baseline changed before execution')
    legacy=[checked([str(ROOT/'legacy/fee')],input=c['input']+'\n') for c in cases]
    reports={};good=[]
    for mode in ['none','round-even','wrong-threshold','approve-inactive']:
        output=checked([DOTNET,'Candidate/bin/Release/net10.0/Candidate.dll',mode],input='\n'.join(c['input'] for c in cases)+'\n').splitlines()
        if len(output)!=len(cases):raise RuntimeError('Candidate output count mismatch')
        rows=[{'id':c['id'],'legacy':l,'candidate':a} for c,l,a in zip(cases,legacy,output)]
        reports[mode]=gate(mode,rows)
        if mode=='none':good=rows
    missing=[dict(x) for x in good];missing[0].pop('candidate')
    reports['missing-evidence']=gate('missing-evidence',missing)
    reports['missing-case']=gate('missing-case',good[1:])
    reports['duplicate-case']=gate('duplicate-case',good+[good[0]])
    reports['invalid-anchor']=gate('invalid-anchor',good,digest='0'*64)
    reports['no-mandate']=gate('no-mandate',good,authority='none')
    # Equal outputs can be equally wrong; the third, normative expectation catches this.
    equal_wrong=[dict(x) for x in good]
    equal_wrong[2]['legacy']=equal_wrong[2]['candidate']='APPROVE|00000000'
    reports['equal-but-wrong']=gate('equal-but-wrong',equal_wrong)
    expected={'none':('PASS',0),'round-even':('FAIL',2),'wrong-threshold':('FAIL',2),
      'approve-inactive':('FAIL',2),'missing-evidence':('INCONCLUSIVE',3),
      'missing-case':('INCONCLUSIVE',3),'duplicate-case':('INCONCLUSIVE',3),
      'invalid-anchor':('INCONCLUSIVE',3),'no-mandate':('PASS',4),'equal-but-wrong':('FAIL',2)}
    for k,(v,code) in expected.items():
        assert reports[k]['verdict']==v and reports[k]['exitCode']==code,(k,reports[k])
        assert reports[k]['release']==('SIMULATED_ALLOW' if k=='none' else 'BLOCK'),k
    sources={str(p):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix in ['.cs','.csproj','.cob','.py','.json','.sha256'] and not any(x in ['obj','bin','results'] for x in p.relative_to(ROOT).parts)}
    sources={str(pathlib.Path(p).relative_to(ROOT)):h for p,h in sources.items()}
    summary={'status':'PASS','scope':'Synthetic fixed-record fee service; not an industrial equivalence proof',
      'cases':len(cases),'gateControls':len(reports),'sdk':sdk,'compiler':compiler,'platform':platform.platform(),
      'elapsedSeconds':round(time.time()-start,2),'baselineSha256':anchor,'sourceSha256':sources,
      'reports':{k:{'verdict':v['verdict'],'release':v['release'],'exitCode':v['exitCode'],'findingCount':len(v['findings'])} for k,v in reports.items()}}
    (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
except Exception as exc:
    (RESULTS/'run-failure.txt').write_text(str(exc)+'\n')
    print(str(exc),file=sys.stderr);sys.exit(1)
