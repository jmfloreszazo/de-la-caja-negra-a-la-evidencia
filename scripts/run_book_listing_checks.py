#!/usr/bin/env python3
"""Compile exact selected book code with bounded fixtures; preserve raw results."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from audit_book_listings import ROOT,inventory,source,sqlite_checks

OUT=ROOT/'lab/results/book-listings'


def run(name,command,**kwargs):
    r=subprocess.run(command,capture_output=True,text=True,timeout=180,**kwargs)
    (OUT/(name+'.stdout.txt')).write_text(r.stdout)
    (OUT/(name+'.stderr.txt')).write_text(r.stderr)
    assert r.returncode==0,(name,r.returncode)
    return r.stdout


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report=dict(status='FAIL',sourceHeadSha=os.environ['SOURCE_HEAD_SHA'],
                runId=os.environ['GITHUB_RUN_ID'],completeBookCompilationEstablished=False,
                crossPlatformEstablished=False,listingLabelsPromoted=False)
    try:
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        assert actual==report['sourceHeadSha']
        inv=inventory()
        paths={r[lang]['path'] for r in inv['listings'] for lang in ('english','spanish')}
        paths.update(['scripts/audit_book_listings.py','scripts/run_book_listing_checks.py',
                      'scripts/check_language_policy.py','lab/contracts/cases.json',
                      'lab/contracts/cases.sha256','lab/legacy/fee.cob',
                      '.github/workflows/book-listings.yml'])
        report['sourceHashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)}
        report['pairedFences']=inv['pairedFences'];report['canonicalExecutableFences']=inv['canonicalExecutableFences']
        report['sqlite']=sqlite_checks()
        report['tools']={key:run(key,cmd).strip() for key,cmd in {
            'dotnet':['dotnet','--version'],'gnucobol':['cobc','--version'],
            'python':['python3','--version']}.items()}
        with tempfile.TemporaryDirectory(prefix='book-listings-') as temporary:
            root=Path(temporary)
            cobol=root/'fee.cob';cobol.write_text(source('26.1'))
            run('cobol-build',['cobc','-x','-free','-o',str(root/'fee'),str(cobol)])
            cases=(ROOT/'lab/contracts/cases.json').read_bytes()
            assert hashlib.sha256(cases).hexdigest()==(ROOT/'lab/contracts/cases.sha256').read_text().split()[0]
            outcomes=[]
            for case in json.loads(cases):
                observed=run('cobol-'+case['id'],[str(root/'fee')],input=case['input']+'\n').strip()
                outcomes.append(dict(id=case['id'],input=case['input'],expected=case['expected'],actual=observed))
            report['cobol']=dict(listing='26.1',cases=outcomes,passed=sum(r['actual']==r['expected'] for r in outcomes))
            assert len(outcomes)==58 and report['cobol']['passed']==58
            expressions='\n'.join(line.split('//')[0] for line in source('12.2').splitlines()).split(';')
            expressions=[x.strip() for x in expressions if x.strip()]
            assert len(expressions)==4
            project=root/'native';project.mkdir()
            (project/'ListingChecks.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup></Project>')
            program='''using System;
using System.Linq;
static class Program {
    static void Main() {
        decimal[] rounding = { ROUNDING_EXPRESSIONS };
        if (!rounding.SequenceEqual(new decimal[]{0m,2m,1m,1m})) throw new Exception("Rounding mismatch");
        (byte[] Bytes,int Scale,decimal Expected)[] good = {
            (new byte[]{0x12,0x3C},2,1.23m),(new byte[]{0x12,0x3D},2,-1.23m),
            (new byte[]{0x12,0x3F},2,1.23m),(new byte[]{0x12,0x3A},2,1.23m),
            (new byte[]{0x12,0x3B},2,-1.23m),(new byte[]{0x12,0x3E},2,1.23m),
            (new byte[]{0x0D},0,0m),(new byte[]{0x1C},18,0.000000000000000001m),
            (new byte[]{0x99,0x9C},0,999m)
        };
        foreach(var c in good) if(DecodePacked(c.Bytes,c.Scale)!=c.Expected) throw new Exception("Packed mismatch");
        Reject<ArgumentException>(()=>DecodePacked(Array.Empty<byte>(),0));
        Reject<ArgumentException>(()=>DecodePacked(new byte[]{0x1C},-1));
        Reject<ArgumentException>(()=>DecodePacked(new byte[]{0x1C},19));
        Reject<FormatException>(()=>DecodePacked(new byte[]{0xFA,0x1C},0));
        Reject<FormatException>(()=>DecodePacked(new byte[]{0x12,0x37},0));
        Reject<OverflowException>(()=>DecodePacked(new byte[]{0x99,0x99,0x99,0x99,0x99,0x99,0x99,0x99,0x99,0x9C},0));
        Console.WriteLine("PASS: 4 rounding expressions; 9 packed-decimal values; 6 negative controls");
    }
    static void Reject<T>(Action action) where T:Exception {
        try { action(); } catch(T) { return; }
        throw new Exception("Expected rejection "+typeof(T).Name);
    }
    PACKED_SOURCE
}
'''.replace('ROUNDING_EXPRESSIONS',','.join(expressions)).replace('PACKED_SOURCE',source('15.1'))
            (project/'Program.cs').write_text(program)
            run('csharp',['dotnet','run','--project',str(project/'ListingChecks.csproj'),'-c','Release'])
            report['csharp']=dict(roundListing='12.2',roundExpressions=4,packedListing='15.1',
                                  packedValues=9,packedNegativeControls=6,scope='Exact expressions/method in an isolated harness; no application integration')
        report['status']='PASS_BOUNDED_LISTING_CHECKS'
    except Exception as error:
        report['error']=repr(error)
        raise
    finally:
        (OUT/'listing-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('sourceHashes','cobol')},indent=2))


if __name__=='__main__':
    main()
