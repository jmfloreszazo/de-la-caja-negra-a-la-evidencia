"""Pack or unpack only the explicit, recorded inputs for an E4 candidate replay."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

FILES = (
    "attempt/candidate.json", "attempt/request.json", "attempt/response.json",
    "legacy/summary.json", "legacy/none-observations.json",
)
MAX_FILE_BYTES = 2 * 1024 * 1024


def validate(documents):
    payload = json.loads(documents["attempt/candidate.json"])
    request = json.loads(documents["attempt/request.json"])
    response = json.loads(documents["attempt/response.json"])
    if request.get("status") != "RECEIVED":
        raise ValueError("Replay requires a recorded successful model response")
    if payload != json.loads(response["choices"][0]["message"]["content"]):
        raise ValueError("Candidate differs from the recorded model response")
    if request.get("usage") != response.get("usage") or not response.get("usage"):
        raise ValueError("Recorded model usage differs from the response")
    if json.loads(documents["legacy/summary.json"]).get("status") != "PASS":
        raise ValueError("Actual successful legacy observations are required")


def pack(attempt, legacy, output):
    sources = {name: (attempt if name.startswith("attempt/") else legacy) / Path(name).name
               for name in FILES}
    documents = {}
    for name, path in sources.items():
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("Replay inputs must be bounded regular JSON files")
        documents[name] = path.read_bytes()
    validate(documents)
    with tarfile.open(output, "x") as archive:
        for name, path in sources.items():
            archive.add(path, arcname=name, recursive=False)
    return {"archiveSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "files": {name: hashlib.sha256(data).hexdigest() for name, data in documents.items()},
            "classification": "RECORDED_MODEL_RESPONSE_REPLAY_NOT_NEW_INFERENCE"}


def unpack(archive_path, output):
    documents = {}
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        if len(members) != len(FILES) or {member.name for member in members} != set(FILES):
            raise ValueError("Replay archive must contain exactly the five allowed inputs")
        for member in members:
            if not member.isfile() or not 0 < member.size <= MAX_FILE_BYTES:
                raise ValueError("Replay archive links, directories and oversized files are forbidden")
            documents[member.name] = archive.extractfile(member).read()
    validate(documents)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in documents.items():
        target = output / name
        target.parent.mkdir(exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("pack")
    create.add_argument("--attempt", type=Path, required=True)
    create.add_argument("--legacy", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    extract = commands.add_parser("unpack")
    extract.add_argument("--archive", type=Path, required=True)
    extract.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "pack":
        print(json.dumps(pack(args.attempt, args.legacy, args.output), indent=2))
    else:
        unpack(args.archive, args.output)


if __name__ == "__main__":
    main()
