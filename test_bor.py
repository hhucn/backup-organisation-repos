#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
import unittest

import bu_orga_repos

class TestBackup(unittest.TestCase):
    def test_git(self):
        """ Test cloning and updating git repositories """
        tmpDir = tempfile.mkdtemp('tmp', 'test_bor_git')
        try:
            repoDir = os.path.join(tmpDir, 'repo')
            repoUrl = 'file://' + repoDir
            mirrorDir = os.path.join(tmpDir, 'mirror')

            # Initialize
            os.mkdir(repoDir)
            with open(os.path.join(repoDir, 'testfile'), 'w') as testf:
                testf.write('original')
            subprocess.check_call(['git', 'init', '--quiet'], cwd=repoDir)
            subprocess.check_call(['git', 'add', 'testfile'], cwd=repoDir)
            subprocess.check_call(['git', 'commit', '-m', 'initial commit', '--quiet'], cwd=repoDir)
            localPath = bu_orga_repos.clone_or_update('git', repoUrl, mirrorDir)
            assert 'file:' not in localPath

            # Check that the checked out repository is functional
            checkOut1 = os.path.join(tmpDir, 'checkout1')
            subprocess.check_call(['git', 'clone', 'file://' + localPath, checkOut1, '--quiet'])
            with open(os.path.join(checkOut1, 'testfile')) as testf:
                assert testf.read() == 'original'

            # Check that updating works
            with open(os.path.join(repoDir, 'testfile'), 'w') as testf:
                testf.write('changed')
            subprocess.check_call(['git', 'commit', '-a', '-m', 'new commit', '--quiet'], cwd=repoDir)
            localPath2 = bu_orga_repos.clone_or_update('git', repoUrl, mirrorDir)
            assert localPath == localPath2
            checkOut2 = os.path.join(tmpDir, 'checkout2')
            subprocess.check_call(['git', 'clone', 'file://' + localPath, checkOut2, '--quiet'])
            with open(os.path.join(checkOut2, 'testfile')) as testf:
                assert testf.read() == 'changed'
        finally:
            shutil.rmtree(tmpDir)

if __name__ == '__main__':
    unittest.main()
