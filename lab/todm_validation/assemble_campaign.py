"""Assemble explicit retained campaign evidence without changing original artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile

from lab.todm_validation.validate import PIN, SCOPES, safe_path, strict_json

RUNS = {"E1": "e1-azure-20261108-01", "E2": "e2-cluster-azure-20261108-01",
        "E3": "e3-azure-20261108-01", "E4": "e4-replay-azure-20261108-02"}
SECRET = re.compile(rb"(?:AccountKey=[A-Za-z0-9+/]{20}|SharedAccessSignature=sv=|-----BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{30}|sk-[A-Za-z0-9]{25})")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def assemble(root, output):
    output.mkdir(parents=True, exist_ok=False)
    runs = root / "lab" / "results" / "azure-e1-e4-20261108" / "runs"
    manifest = {"schemaVersion": 1, "kind": "TODM_EVIDENCE_BUNDLE", "upstreamCommit": PIN, "experiments": []}
    audit = {"classification": "LOCAL_RETAINED_EVIDENCE_ASSEMBLY_NOT_AZURE_EXECUTION_ATTESTATION", "runs": [], "missingArtifacts": [],
             "limitations": ["External instance/request/completion records are preserved, not authenticated cloud identity.",
                             "Source archives contain code and synthetic fixtures, not PostgreSQL dumps or runtime credentials.",
                             "Secret-pattern screening is a bounded precaution, not a formal guarantee.",
                             "E3 missing original runtime bytes must not be replaced with a rebuild."]}
    for experiment, run in RUNS.items():
        source = runs / run
        evidence = runs / (run + "-evidence")
        artifacts, documents, index, copied = [], {}, {}, {}
        def add_bytes(raw, relative, role, document=None, origin=None):
            if SECRET.search(raw):
                raise ValueError("Secret-like bytes rejected: " + relative)
            if relative in copied:
                item = copied[relative]
                if document:
                    item["document"] = document
                    documents[document] = strict_json(raw)
                return item
            target = safe_path(output.resolve(), relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
            item = {"id": experiment + "-" + str(len(artifacts)), "path": relative, "role": role, "sha256": sha(raw)}
            if document:
                item["document"] = document
                documents[document] = strict_json(raw)
            if origin:
                item["origin"] = origin
            artifacts.append(item)
            copied[relative] = item
            return item
        def add_file(path, relative, role, document=None):
            return add_bytes(path.read_bytes(), relative, role, document, str(path.relative_to(root)))
        prefix = "inputs/" + experiment
        for name in ("source.tar", "source.json", "request.json", "remote-run.sh"):
            add_file(source / name, prefix + "/provenance/" + name, "source" if name.endswith(("tar", "sh")) else "raw")
        for name in ("completion.json", "azure-instance.json", "bootstrap.sha256"):
            add_file(evidence / name, prefix + "/provenance/" + name, "raw")
        request = strict_json((source / "request.json").read_bytes())
        completion = strict_json((evidence / "completion.json").read_bytes())
        metadata = strict_json((source / "source.json").read_bytes())
        archive_digest = sha((source / "source.tar").read_bytes())
        with tarfile.open(source / "source.tar") as archive:
            for member in archive.getmembers():
                safe_path(output.resolve(), "archive-check/" + member.name)
                if not member.isfile():
                    raise ValueError("Non-file source archive member")
                raw = archive.extractfile(member).read()
                if SECRET.search(raw):
                    raise ValueError("Secret-like archive member: " + member.name)
                index.setdefault(sha(raw), []).append((raw, member.name))
            archive_checks = {"archiveDigestMatchesRequest": archive_digest == request["sourceSha256"],
                "archiveDigestMatchesCompletion": archive_digest == completion["sourceSha256"],
                "archiveDigestMatchesSourceManifest": archive_digest == metadata["archiveSha256"],
                "sourceCommitConsistent": request["commit"] == completion["sourceCommit"] == metadata["sourceCommit"],
                "workloadCompleted": completion["workloadExitCode"] == 0 and completion["artifactPreparationExitCode"] == 0,
                "everySourceManifestDigestInArchive": all(value in index for value in metadata["sourceSha256"].values())}
        if experiment == "E4":
            for name in ("e4-inputs.tar", "e4-inputs.json"):
                add_file(source / name, prefix + "/provenance/" + name, "raw")
            archive_checks["recordedModelInputArchiveMatchesRequest"] = sha((source / "e4-inputs.tar").read_bytes()) == request["e4InputSha256"]
            with tarfile.open(source / "e4-inputs.tar") as archive:
                for member in archive.getmembers():
                    safe_path(output.resolve(), "archive-check/" + member.name)
                    if not member.isfile():
                        raise ValueError("Non-file model input archive member")
                    raw = archive.extractfile(member).read()
                    add_bytes(raw, prefix + "/model-inputs/" + member.name, "raw", origin=run + "/e4-inputs.tar:" + member.name)
                    index.setdefault(sha(raw), []).append((raw, "model-inputs/" + member.name))
        if experiment in ("E1", "E2", "E3"):
            folder = evidence / "results" / experiment.lower()
            selected = {"E1": {"summary.json": "report", "oracle-vectors-summary.json": "qualification"},
                        "E2": {"e2-process-crash.json": "report"},
                        "E3": {"summary.json": "report", "ledger-snapshot.json": "ledger", "offers.json": "offers", "offers-planned.json": "planned"}}[experiment]
            # Include every explicit raw artifact referenced by the selected summary, plus its adapter inputs.
            report = strict_json((folder / next(k for k, v in selected.items() if v == "report")).read_bytes())
            names = set(selected) | set(report.get("artifactSha256", {}))
            if experiment == "E1":
                names.add("dotnet-build.txt")
            if experiment == "E2":
                names.add("e2-smoke.json")
            for name in sorted(names):
                add_file(folder / name, prefix + "/evidence/" + name, "report" if selected.get(name) == "report" else "qualification" if selected.get(name) == "qualification" else "raw", selected.get(name))
        else:
            folder = evidence / "e4-results"
            selection = {"evaluation/evaluation.json": "report", "evaluation/observations.json": "observations", "qualification/qualification.json": "qualification"}
            selection.update({"qualification/" + name + "-observations.json": "qualification." + name for name in ("none", "round-even", "wrong-threshold", "approve-inactive")})
            for name, document in selection.items():
                add_file(folder / name, prefix + "/evidence/" + name, "report" if document == "report" else "qualification" if document == "qualification" else "raw", document)
        claims = {}
        for doc in documents.values():
            if not isinstance(doc, dict):
                continue
            for key in ("sourceSha256", "protectedSha256", "legacyInputSha256", "runtimeArtifactSha256"):
                claims.update(doc.get(key, {}))
            for key in ("candidateSha256", "qualifierSha256", "binarySha256"):
                if key in doc:
                    claims[key] = doc[key]
            claims.update(doc.get("source", {}).get("fileSha256", {}))
        if experiment == "E3":
            recovered = runs.parent / "e3-runtime-originals"
            if (recovered / "retrieval.json").is_file():
                retrieval = strict_json((recovered / "retrieval.json").read_bytes())
                expected_runtime = documents["report"]["runtimeArtifactSha256"]
                if set(retrieval) != set(expected_runtime):
                    raise ValueError("Recovered runtime inventory differs from original E3 report")
                for name, digest in expected_runtime.items():
                    path = safe_path(recovered.resolve(), name)
                    if retrieval[name].get("sha256") != digest or sha(path.read_bytes()) != digest:
                        raise ValueError("Recovered original runtime digest mismatch: " + name)
                    add_file(path, prefix + "/runtime/" + name, "source")
                add_file(recovered / "retrieval.json", prefix + "/retrieval-supplement/retrieval.json", "raw")
                supplement = runs.parent / "e3-runtime-originals.tar.gz"
                add_file(supplement, prefix + "/retrieval-supplement/e3-runtime-originals.tar.gz", "raw")
                transport = runs.parent / "e3-runtime-retrieval.json"
                if transport.is_file():
                    add_file(transport, prefix + "/retrieval-supplement/e3-runtime-retrieval.json", "raw")
                archive_checks["recoveredOriginalRuntimeDigestsMatch"] = True
                archive_checks["recoveredOriginalRuntimeCount"] = len(expected_runtime)
        already = {item["sha256"] for item in artifacts}
        for name, digest in claims.items():
            if digest in already:
                continue
            role = "contract" if name.endswith(("schema.sql", "cases.json", "cases.sha256", "performance-contract.json")) or "protected" in name else "source"
            choices = index.get(digest, [])
            if choices:
                raw, archive_name = choices[0]
                relative = prefix + "/source/" + archive_name
                add_bytes(raw, relative, role, "cases" if experiment == "E4" and archive_name == "lab/contracts/cases.json" else None, run + "/source.tar:" + archive_name)
                already.add(digest)
            else:
                # Dependencies are reusable only when their exact bytes match the retained run's recorded digest.
                local = root / "lab" / "e3_capacity" / "E3Fixture" / "bin" / "Release" / "net10.0" / name
                if experiment == "E3" and local.is_file() and sha(local.read_bytes()) == digest:
                    add_file(local, prefix + "/runtime/" + name, role)
                    already.add(digest)
                else:
                    relative = prefix + "/missing-original-runtime/" + name
                    if digest not in {row["sha256"] for row in audit["missingArtifacts"]}:
                        row = {"experiment": experiment, "path": relative, "sha256": digest, "reason": "Original bytes absent; local rebuild differs or absent"}
                        audit["missingArtifacts"].append(row)
                        artifacts.append({"id": experiment + "-missing-" + str(len(artifacts)), "path": relative, "sha256": digest, "role": role})
        if not any(item["role"] == "contract" for item in artifacts):
            for values in index.values():
                for raw, name in values:
                    if name == "lab/e1_pg/schema.sql":
                        add_bytes(raw, prefix + "/source/" + name, "contract", origin=run + "/source.tar:" + name)
        audit["runs"].append({"experiment": experiment, "runId": run, "checks": archive_checks, "sourceArchiveSha256": archive_digest})
        manifest["experiments"].append({"experiment": experiment, "scope": SCOPES[experiment],
            "risk": "Bounded retained synthetic evidence; neither cloud identity nor production approval is inferred.",
            "limitations": documents["report"].get("limitations", ["Selected protocol slice, not full experiment acceptance"]),
            "provenance": {"runId": run, "sourceCommit": request["commit"], "ciRunId": None,
                "executionLocation": "External Azure instance metadata retained separately; adapter executes locally",
                "externalProvenanceDirectory": prefix + "/provenance"}, "artifacts": artifacts})
        if isinstance(manifest["experiments"][-1]["limitations"], str):
            manifest["experiments"][-1]["limitations"] = [manifest["experiments"][-1]["limitations"]]
    adapter = output / "adapter" / "lab" / "todm_validation"
    adapter.mkdir(parents=True)
    for source in (root / "lab" / "todm_validation").glob("*.py"):
        shutil.copyfile(source, adapter / source.name)
    shutil.copytree(root / "lab" / "todm_validation" / "vendor", adapter / "vendor")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "assembly-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assemble(args.root.resolve(), args.output.resolve())
    print(json.dumps({"missingArtifacts": result["missingArtifacts"], "runs": len(result["runs"])}))


if __name__ == "__main__":
    main()
