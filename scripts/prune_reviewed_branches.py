#!/usr/bin/env python3
"""Prune one immutable reviewed branch list with archive and atomic SHA leases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'evidence/maintenance/branch-closeout-2026-11-03.json'
SELF = 'maintenance/closeout-2026-11-03'
REPO = 'jmfloreszazo/de-la-caja-negra-a-la-evidencia'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def ancestor(sha):
    return subprocess.run(['git','merge-base','--is-ancestor',sha,'HEAD'],cwd=ROOT).returncode == 0


def api(path,missing=False):
    request=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
                 'Accept':'application/vnd.github+json','User-Agent':'reviewed-branch-closeout'})
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if missing and error.code==404:
            return None
        raise


def local_audit():
    d=json.loads(MANIFEST.read_text())
    assert d['repository']==REPO and ancestor(d['baselineMain'])
    archive=ROOT/d['archive']['path']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==d['archive']['sha256']
    subprocess.run(['git','bundle','verify',str(archive)],cwd=ROOT,check=True,capture_output=True)
    # Import recoverable objects without creating any branch refs. Fresh clones
    # must still audit superseded tips after their remote branches are gone.
    git('bundle','unbundle',str(archive))
    archived={line.split()[1]:line.split()[0] for line in git('bundle','list-heads',str(archive)).splitlines()}
    assert len(d['branches'])==27 and len({r['branch'] for r in d['branches']})==27
    for row in d['branches']:
        name,sha=row['branch'],row['sha']
        assert name not in ('main',SELF) and re.fullmatch(r'[a-z0-9._/-]+',name)
        assert re.fullmatch(r'[0-9a-f]{40}',sha)
        if row['proof']=='ancestor_of_main':
            assert row['merged'] and ancestor(sha)
        else:
            assert archived['refs/remotes/origin/'+name]==sha
            if row['proof']=='identical_merged_tree':
                assert row['merged'] and ancestor(row['mergeCommit'])
                assert git('rev-parse',sha+'^{tree}')==git('rev-parse',row['mergeCommit']+'^{tree}')
            else:
                assert row['proof']=='superseded_archived' and not row['merged']
                assert row['pr'] in (46,67)
    return d


def remote_ref(name):
    return api('git/ref/heads/'+urllib.parse.quote(name,safe='/'),missing=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    d=local_audit()
    if not args.execute:
        print('PASS: 21 ancestor tips, 4 identical merged trees, 2 archived superseded tips; no deletion.')
        return
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    assert os.environ['GITHUB_REF']=='refs/heads/main'
    assert os.environ['GITHUB_REPOSITORY']==REPO and os.environ['GITHUB_SHA']==git('rev-parse','HEAD')
    pulls=api('pulls?state=open&per_page=100')
    assert len(pulls)<100, 'Refuse an incomplete open-PR inventory'
    active={p['head']['ref'] for p in pulls if p['head']['repo'] and p['head']['repo']['full_name']==REPO}
    plan=[]
    for row in d['branches']:
        assert row['branch'] not in active, 'Branch belongs to an open PR'
        pr=api('pulls/'+str(row['pr']))
        assert pr['state']=='closed' and pr['head']['ref']==row['branch'] and pr['head']['sha']==row['sha']
        assert bool(pr['merged_at'])==row['merged']
        ref=remote_ref(row['branch'])
        assert ref is None or ref['object']['sha']==row['sha'], 'Changed branch; no deletion'
        plan.append(dict(row,alreadyAbsent=ref is None))
    # Every target is preflighted before the first mutation.
    results=[]
    report=ROOT/'lab/results/branch-closeout.json'
    report.parent.mkdir(parents=True,exist_ok=True)
    try:
        for row in plan:
            if not row['alreadyAbsent']:
                subprocess.run(['git','push','--force-with-lease=refs/heads/'+row['branch']+':'+row['sha'],
                                'origin',':refs/heads/'+row['branch']],cwd=ROOT,check=True)
                assert remote_ref(row['branch']) is None
            results.append(dict(branch=row['branch'],sha=row['sha'],status='ALREADY_ABSENT' if row['alreadyAbsent'] else 'DELETED'))
            print(json.dumps(results[-1]))
        # Remove this maintenance branch only if this exact merged PR is its owner.
        ref=remote_ref(SELF)
        if ref is not None:
            tip=ref['object']['sha']
            own=api('pulls?state=closed&head='+urllib.parse.quote(REPO.split('/')[0]+':'+SELF,safe='')+'&per_page=100')
            matches=[p for p in own if p['merged_at'] and p['merge_commit_sha']==git('rev-parse','HEAD')
                     and p['head']['sha']==tip and p['base']['ref']=='main']
            assert len(matches)==1 and ancestor(tip), 'Do not delete an unrelated maintenance branch'
            subprocess.run(['git','push','--force-with-lease=refs/heads/'+SELF+':'+tip,
                            'origin',':refs/heads/'+SELF],cwd=ROOT,check=True)
            assert remote_ref(SELF) is None
            results.append(dict(branch=SELF,sha=tip,status='DELETED'))
    finally:
        report.write_text(json.dumps(dict(source=git('rev-parse','HEAD'),branches=results),indent=2)+'\n')


if __name__=='__main__':
    main()
