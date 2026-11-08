"""Exercise replay supervision with fake host tools; never modify a real user manager."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


@unittest.skipUnless(sys.platform == "linux", "Shell supervision requires Linux/WSL")
class ReplayRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = os.environ | {"PATH": str(self.bin) + ":" + os.environ["PATH"],
                                 "FIXTURE": str(self.root), "SOURCE_HEAD_SHA": "a" * 40,
                                 "SOURCE_ARCHIVE_SHA256": "b" * 64, "SOURCE_WORKTREE_DIRTY": "true"}
        for name in ("e4_agents", "Candidate", "Gate", "contracts", "legacy"):
            path = self.root / "lab" / name
            path.mkdir(parents=True)
            (path / "fixture.txt").write_text("fixture")
        for folder, files in (("attempt", ("candidate", "request", "response")),
                              ("legacy-input", ("summary", "none-observations"))):
            path = self.root / folder
            path.mkdir()
            for name in files:
                (path / (name + ".json")).write_text("{}")
        self.env["E4_ATTEMPT_DIRECTORY"] = str(self.root / "attempt")
        self.env["E4_LEGACY_RESULTS"] = str(self.root / "legacy-input")
        self.evidence = self.root / "evidence"
        self.evidence.mkdir()
        script = (HERE / "run-e4-replay.sh").read_text()
        script = script.replace('/var/tmp/book-e4-replay-XXXXXXXX', str(self.root / 'work-XXXXXXXX'))
        script = script.replace('test -S "/run/user/$uid/bus"', ':')
        (self.root / "runner.sh").write_text(script)
        self.tool("id", 'if test "$#" = 1; then echo 0; else echo 1000; fi')
        self.tool("getent", 'echo "laboperator:x:1000:1000:fixture:/tmp:/bin/bash"')
        self.tool("stat", 'echo cgroup2fs')
        self.tool("grep", 'echo "laboperator:100000:65536"')
        for name in ("newuidmap", "newgidmap", "loginctl", "systemctl", "chown"):
            self.tool(name, 'exit 0')
        self.tool("runuser", '''
case "$PWD" in "$FIXTURE"/work-*/source) ;; *) exit 99 ;; esac
if [[ "$*" == *"qualify.py"* ]]; then
    mkdir -p lab/results/qualification
    echo '{}' > lab/results/qualification/result.json
fi
if [[ "$*" == *"live.py evaluate"* ]]; then
    mkdir -p lab/results/evaluation
    echo '{}' > lab/results/evaluation/result.json
    exit "${FAIL_EVALUATE:-0}"
fi
''')
        self.tool("cp", '''
if [[ "${FAIL_COLLECT:-0}" = 1 && "$*" == *"e4-results"* ]]; then exit 41; fi
exec /bin/cp "$@"
''')

    def tool(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o700)

    def run_case(self):
        return subprocess.run(["bash", str(self.root / "runner.sh"), str(self.evidence)],
                              cwd=self.root, env=self.env, capture_output=True, text=True, timeout=20)

    def test_user_commands_start_from_accessible_copy_and_results_are_collected(self):
        result = self.run_case()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.evidence / "e4-results/evaluation/result.json").exists())
        self.assertFalse(list(self.root.glob("work-*")))

    def test_evaluation_failure_preserves_results_and_original_exit(self):
        self.env["FAIL_EVALUATE"] = "29"
        result = self.run_case()
        self.assertEqual(result.returncode, 29, result.stderr)
        self.assertTrue((self.evidence / "e4-results/evaluation/result.json").exists())
        self.assertFalse(list(self.root.glob("work-*")))

    def test_failed_collection_retains_original_work_directory(self):
        self.env["FAIL_COLLECT"] = "1"
        result = self.run_case()
        self.assertEqual(result.returncode, 41, result.stderr)
        self.assertIn("original evidence retained", result.stderr)
        self.assertEqual(len(list(self.root.glob("work-*/source/lab/results/evaluation/result.json"))), 1)


if __name__ == "__main__":
    unittest.main()
