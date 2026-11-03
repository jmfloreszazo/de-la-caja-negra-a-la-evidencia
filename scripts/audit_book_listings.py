#!/usr/bin/env python3
"""Inventory canonical bilingual listings and check only declared feasible slices."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import yaml
from check_language_policy import FENCE,code_pair_errors

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'evidence/editorial/book-listings.json'


def inventory():
    rows=[]
    for english in sorted((ROOT/'book/en').rglob('*.md')):
        if english.name in ('README.md','diagrams.md'):
            continue
        text=english.read_text()
        counterpart=re.search(r'\]\(([^)]+\.md)\)',text.splitlines()[0])
        if not counterpart:
            continue
        spanish=(english.parent/counterpart[1]).resolve()
        translated=spanish.read_text()
        assert not code_pair_errors(text,translated),english
        for index,(en,es) in enumerate(zip(FENCE.finditer(text),FENCE.finditer(translated)),1):
            labels=re.findall(r'^\*\*Listing ([A-Za-z0-9.]+) · (.*?)\*\* — \*(.*?)\*',text[:en.start()],re.M)
            assert labels, (english,index,'missing explicit listing label')
            number,title,label=labels[-1]
            language=en[1]
            dependencies={
                'bash':'Bash syntax only here; real Podman/SDK/PowerShell and OS reproduction remain separate',
                'cobol':'GnuCOBOL for full 26.1; 3.1 requires CICS, declarations and an enterprise fixture; 12.1 is an excerpt',
                'csharp':'SDK .NET 10; 12.2 and 15.1 have isolated harnesses; other fragments need their application types/services',
                'json':'JSON documents only; examples do not establish approval, provenance or executable business semantics',
                'yaml':'YAML syntax only; mandate schema and GitHub workflow validity/execution are separate',
                'sql':'SQLite in-memory fixture for 28.1; T-SQL 17.1/18.1 needs SQL Server schema, parameters and transactional tests',
                'python':'Python syntax plus the four displayed 28.4 predicates in a disposable SQLite fixture; not the full seven-oracle suite',
                'text':'Narrative topology, file tree or historical output; not executable source',
                'markdown':'Illustrative evidence-sheet template; not an actual mandate or acceptance record',
            }[language]
            checks=[]
            if language=='json':
                decoder=json.JSONDecoder();remaining=en[2].strip();count=0
                while remaining:
                    _,end=decoder.raw_decode(remaining);count+=1;remaining=remaining[end:].lstrip()
                checks.append(dict(kind='JSON_SYNTAX',documents=count))
            elif language=='yaml':
                assert isinstance(yaml.safe_load(en[2]),dict)
                checks.append(dict(kind='YAML_SYNTAX',workflowExecutionEstablished=False))
            elif language=='bash':
                subprocess.run(['bash','-n'],input=en[2],text=True,check=True,capture_output=True)
                checks.append(dict(kind='BASH_SYNTAX',commandsExecuted=False))
            elif language=='python':
                ast.parse(en[2]);checks.append(dict(kind='PYTHON_SYNTAX',standaloneProgram=False))
            elif number=='26.1':
                assert en[2].strip()==(ROOT/'lab/legacy/fee.cob').read_text().strip()
                checks.append(dict(kind='EXACT_FULL_SOURCE_MATCH',path='lab/legacy/fee.cob'))
            rows.append(dict(id=number,title=title,publishedLabel=label,language=language,
                fenceIndex=index,english=dict(path=str(english.relative_to(ROOT)),line=text[:en.start()].count('\n')+1,
                    sha256=hashlib.sha256(en[2].encode()).hexdigest()),
                spanish=dict(path=str(spanish.relative_to(ROOT)),line=translated[:es.start()].count('\n')+1,
                    sha256=hashlib.sha256(es[2].encode()).hexdigest()),
                canonicalExecutableCode=language not in ('text','markdown'),sameBytes=en[2]==es[2],
                dependencies=dependencies,staticChecks=checks,completeIntegrationEstablished=False))
    assert len(rows)==32 and len({r['id'] for r in rows})==32
    assert sum(r['canonicalExecutableCode'] for r in rows)==27
    return dict(schema='BOOK_LISTINGS_V1',pairedFences=32,canonicalExecutableFences=27,
        language='English executable/config code in both editions',listings=rows,
        limitation='Static parsing and bounded helper tests do not establish complete integration, production safety or cross-platform execution.')


def source(number):
    row=next(r for r in inventory()['listings'] if r['id']==number)
    text=(ROOT/row['english']['path']).read_text()
    return list(FENCE.finditer(text))[row['fenceIndex']-1][2]


def sqlite_checks():
    with sqlite3.connect(':memory:') as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript(source('28.1'))
        db.executemany('INSERT INTO accounts VALUES (?,?)',[(1,99999),(2,100001)])
        db.execute("INSERT INTO operations VALUES ('op',1,2,1,'COMMITTED')")
        db.executemany('INSERT INTO postings VALUES (?,?,?)',[('op',1,-1),('op',2,1)])
        db.execute("INSERT INTO outbox VALUES ('op','TransferCommitted')")
        def observed():
            scope={'s':lambda q:db.execute(q).fetchone()[0]}
            exec(compile(source('28.4'),'listing-28.4','exec'),scope)
            assert len(scope['tests'])==4
            return scope['tests']
        good=observed();assert all(good.values())
        db.execute('UPDATE accounts SET balance=balance+1 WHERE id=1')
        bad_balance=observed();assert not bad_balance['conserved'] and not bad_balance['projectionAgrees']
        db.execute('UPDATE accounts SET balance=balance-1 WHERE id=1')
        db.execute("UPDATE postings SET delta=2 WHERE account=2")
        bad_postings=observed();assert not bad_postings['balancedPostings'] and not bad_postings['projectionAgrees']
        return dict(schemaListing='28.1',predicateListing='28.4',displayedPredicates=4,
                    positive=good,corruptedBalanceRejected=True,corruptedPostingsRejected=True,
                    fullSevenOracleAcceptance=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    current=inventory()
    if args.write:
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        TARGET.write_text(json.dumps(current,indent=2)+'\n')
    else:
        assert current==json.loads(TARGET.read_text()),'Regenerate the reviewed inventory with --write'
    print(json.dumps(dict(pairedFences=32,canonicalExecutableFences=27,sqlite=sqlite_checks()),indent=2))


if __name__=='__main__':
    main()
