"""Summarize the Azure TODM replay without promoting technical checks to approval.

    python3 scripts/evidence/summarize_todm_azure.py [--campaign lab/results/azure-e1-e4-20261108]

Re-derives evidence/runs/todm-azure-2026-11-08.json from the raw downloaded validation and
qualification outputs and compares parsed JSON values, not byte-identical serialization.
Verification is read-only by default; --write-summary creates a missing summary only.
Snapshot, binding and recovered-file counts are historical constants, not recounted here."""
import argparse
import hashlib,json
from pathlib import Path
from _checks import compare_summary, require
ROOT=Path(__file__).resolve().parents[2]
_p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
_p.add_argument("--campaign",type=Path,default=ROOT/"lab/results/azure-e1-e4-20261108")
_p.add_argument('--write-summary',action='store_true',help='Create a missing summary; never overwrite an existing record')
args=_p.parse_args()
HERE=args.campaign.resolve()
if not HERE.is_dir(): raise SystemExit(f"Campaign folder not found: {HERE} (see docs/DIST_MANIFEST.md)")
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
raw=HERE/'todm-azure-02-evidence'
v=load(raw/'validation.json'); q=load(raw/'qualification/qualification.json')
require(v['evaluationVerdict']=='PASS' and v['releaseOutcome']=='BLOCK', "v['evaluationVerdict']=='PASS' and v['releaseOutcome']=='BLOCK'")
require(v['methodologyVerdict']=='INCONCLUSIVE', "v['methodologyVerdict']=='INCONCLUSIVE'")
require(q['passed'] and q['caseCount']==8 and q['syntheticGovernanceCases']==12, "q['passed'] and q['caseCount']==8 and q['syntheticGovernanceCases']==12")
require({e['experiment'] for e in v['experiments']}=={'E1','E2','E3','E4'}, "{e['experiment'] for e in v['experiments']}=={'E1','E2','E3','E4'}")
require(all(e['evaluationVerdict']=='PASS' and e['releaseOutcome']=='BLOCK' for e in v['experiments']), "all(e['evaluationVerdict']=='PASS' and e['releaseOutcome']=='BLOCK' for e in v['experiments'])")
require(load(raw/'completion.json')['exitCode']==0, "load(raw/'completion.json')['exitCode']==0")
instance=load(raw/'azure-instance.json')['compute']
require(instance['name']=='bookev1107-runner' and instance['location']=='northeurope', "instance['name']=='bookev1107-runner' and instance['location']=='northeurope'")
state=load(HERE/'deployment/status.json')
require(any(s['code']=='PowerState/deallocated' for s in state['runner']['instanceView']['statuses']), "any(s['code']=='PowerState/deallocated' for s in state['runner']['instanceView']['statuses'])")
require(state['model']['sku']['capacity']==0, "state['model']['sku']['capacity']==0")
report={
 'schemaVersion':1,'classification':'EXECUTED_AZURE_TODM_ADAPTER_NOT_PRODUCTION_APPROVAL',
 'methodRepository':'https://github.com/jmfloreszazo/TODM',
 'methodCommit':'61354abc03e73fbf258b6e8d66e35678da134ef8',
 'sourceCommit':load(ROOT/'evidence/runs/azure-e1-e4-2026-11-08.json')['sourceCommit'],
 'inputArchiveSha256':sha(HERE/'todm-actual-03.tar.gz'),
 'rawArchiveSha256':sha(HERE/'todm-azure-02-evidence.tar.gz'),
 'validationSha256':sha(raw/'validation.json'),'qualificationSha256':sha(raw/'qualification/qualification.json'),
 'evaluationVerdict':v['evaluationVerdict'],'methodologyVerdict':v['methodologyVerdict'],
 'releaseOutcome':v['releaseOutcome'],'experiments':[
  {k:e[k] for k in ('experiment','oracleVerdict','qualificationVerdict','evaluationVerdict','releaseOutcome')}
  for e in v['experiments']],
 'actualInputNegativeControls':8,'upstreamSyntheticMandateCases':12,
 'verifiedSnapshotFiles':134,'artifactBindings':108,
 'azure':{'vmId':instance['vmId'],'name':instance['name'],'location':instance['location'],
          'runId':'todm-azure-20261108-02'},
 'recoveredOriginalRuntimeFiles':16,
 'retainedFailures':[
  'Incomplete original E3 artifact bundle rejected; exact original runtime bytes retrieved by hash, not rebuilt.',
  'First Azure qualification output path was outside its supported bundle root; validation passed but qualification failed. Separate supported-path retry passed.'
 ],
 'finalState':{'runner':'DEALLOCATED','workerCapacity':0,'residualCosts':'Disk, NAT, public IP and storage remain billable.'},
 'githubActions':'NOT_EXECUTED','ciRunId':None,
 'limitations':[
  'Local adapter of pinned TODM demonstration semantics, not certified TODM or full OMG engines.',
  'SHA256 manifests are not trusted signatures or accountable human approval.',
  'G2/G6 lack independent trusted business/release authority; production release stays BLOCK.',
  'Negative cases qualify these checks, not organizational independence or comparative superiority.',
  'E1-E4 are bounded single-VM demonstrations with the original experiment limitations.'
 ]}
p=ROOT/'evidence/runs/todm-azure-2026-11-08.json'
compare_summary(p,report,write_summary=args.write_summary)
print(json.dumps({'summary':str(p),'experiments':report['experiments'],'release':'BLOCK'},indent=2))
