"""Negative preservation controls and an actual stale deletion-lease test."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import prune_reviewed_branches as subject


class CloseoutTests(unittest.TestCase):
    def test_archive_corruption_main_target_and_wrong_merge_tree_fail(self):
        original=json.loads(subject.MANIFEST.read_text())
        mutations=[]
        d=copy.deepcopy(original);d['archive']['sha256']='0'*64;mutations.append(d)
        d=copy.deepcopy(original);d['branches'][0]['branch']='main';mutations.append(d)
        d=copy.deepcopy(original)
        row=next(r for r in d['branches'] if r['proof']=='identical_merged_tree')
        row['mergeCommit']=d['baselineMain'];mutations.append(d)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'manifest.json'
            for d in mutations:
                path.write_text(json.dumps(d))
                with self.subTest(),patch.object(subject,'MANIFEST',path):
                    with self.assertRaises(AssertionError):
                        subject.local_audit()

    def test_atomic_lease_preserves_a_branch_that_advanced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);remote=root/'remote.git';work=root/'work'
            def run(*args,check=True):
                return subprocess.run(['git',*map(str,args)],cwd=work if work.exists() else root,
                    check=check,text=True,capture_output=True)
            run('init','--bare',remote);run('init',work)
            run('config','user.name','Closeout test');run('config','user.email','closeout@example.invalid')
            run('commit','--allow-empty','-m','first')
            old=run('rev-parse','HEAD').stdout.strip()
            run('remote','add','origin',remote)
            run('push','origin','HEAD:refs/heads/reviewed')
            run('commit','--allow-empty','-m','new work')
            new=run('rev-parse','HEAD').stdout.strip()
            run('push','origin','HEAD:refs/heads/reviewed')
            attempted=run('push','--force-with-lease=refs/heads/reviewed:'+old,
                          'origin',':refs/heads/reviewed',check=False)
            self.assertNotEqual(attempted.returncode,0)
            self.assertEqual(run('--git-dir',remote,'rev-parse','refs/heads/reviewed').stdout.strip(),new)


if __name__=='__main__':
    unittest.main()
