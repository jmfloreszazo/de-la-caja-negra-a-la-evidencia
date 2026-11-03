#!/usr/bin/env python3
"""Validate a bounded source catalog; no vendor runtime or migration is certified."""
import argparse
import copy
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'research/platform-contracts/catalog.json'


def validate(data):
    def require(condition, message):
        if not condition: raise ValueError(message)
    require(data['schema_version']==1,'Unknown schema version')
    require(data['native_platform_execution']=='NOT_EXECUTED' and data['business_approval']=='NOT_OBTAINED','Seed scope inflation')
    sources={s['id']:s for s in data['sources']}
    require(len(sources)==len(data['sources']),'Duplicate source ID')
    for source in sources.values():
        require(source['url'].startswith(('https://www.ibm.com/','https://www.support.unisys.com/')),'Non-primary source')
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',source['accessed_on']) is not None,'Missing source access date')
        require(source['version_scope'] and source['retrieval'] in {'FULL_TEXT','SEARCH_INDEX','SEARCH_INDEX_DIRECT_403'},'Missing source scope/retrieval')
    ids=set()
    risk_text=(ROOT/'book/en/annexes/annex-e-catalog-of-one-hundred-risks.md').read_text()
    for row in data['capabilities']:
        require(row['id'] not in ids,'Duplicate capability ID');ids.add(row['id'])
        for field in ['vendor','platform','version_scope','original_contract','candidate_application','candidate_infrastructure_data','semantic_gap','failure_control','test_oracle']:
            require(isinstance(row.get(field),str) and row[field].strip(),'Missing '+field)
        require(row['layer'] in {'INFRA','APP','DATA','SECURITY','OPS','CROSS_LAYER'},'Unknown layer')
        require(row['strategy'] in {'REHOST','REPLATFORM','REFACTOR','REPLACE','RETAIN','HYBRID_COEXIST'},'Unknown strategy')
        require(row['source_status']=='DOCUMENTED' and row['native_evidence']=='NOT_EXECUTED' and row['migration_evidence']=='NOT_VERIFIED','Unsupported evidence status')
        require(row['availability']=='NOT_ASSESSED' and row['equivalence_claim'] is False,'Unproved availability/equivalence')
        require(row['customer_measurements'] and all(isinstance(m,str) and m.strip() for m in row['customer_measurements']),'Missing customer measurements')
        require(row['source_ids'] and all(s in sources and sources[s]['vendor']==row['vendor'] for s in row['source_ids']),'Missing/misattributed source')
        require(row['risk_ids'] and all(re.search(r'\| '+re.escape(r)+r'\b',risk_text) for r in row['risk_ids']),'Unknown risk mapping')
    for row in data['discovery']+data['adjacent_platforms']:
        require(row['status']=='NOT_VERIFIED' and row['reason'],'Unknown platform became an absence/parity claim')
    require(len(ids)==10,'Bounded seed inventory changed; review scope explicitly')


def self_test(data):
    controls=[('equivalence',lambda d:d['capabilities'][0].update(equivalence_claim=True)),
              ('missing failure',lambda d:d['capabilities'][0].update(failure_control='')),
              ('missing oracle',lambda d:d['capabilities'][0].update(test_oracle='')),
              ('unknown evidence',lambda d:d['capabilities'][0].update(migration_evidence='PASS')),
              ('wrong vendor source',lambda d:d['capabilities'][-1].update(source_ids=['S51'])),
              ('false absence',lambda d:d['discovery'][0].update(status='UNSUPPORTED'))]
    for name,mutate in controls:
        mutant=copy.deepcopy(data);mutate(mutant)
        try:validate(mutant)
        except ValueError:continue
        raise AssertionError('Catalog mutation escaped: '+name)
    return len(controls)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    data=json.loads(CATALOG.read_text());validate(data)
    rejected=self_test(data) if args.self_test else 0
    print(json.dumps({'status':'PASS','documented_capabilities':len(data['capabilities']),'sources':len(data['sources']),
                      'rejected_catalog_mutants':rejected,'native_platform_execution':'NOT_EXECUTED','migration_verified':False}))

if __name__=='__main__':main()
