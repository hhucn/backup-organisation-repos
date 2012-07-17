#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile
import unittest

import bu_orga_repos


def _test_basic_dvcs(dvcs):
    tmpDir = tempfile.mkdtemp('', 'test_bor_' + dvcs)
    try:
        repoDir = os.path.join(tmpDir, 'repo')
        repoUrl = 'file://' + repoDir
        mirrorDir = os.path.join(tmpDir, 'mirror')
        os.mkdir(mirrorDir)

        # Initialize
        os.mkdir(repoDir)
        with open(os.path.join(repoDir, 'testfile'), 'w') as testf:
            testf.write('original')
        subprocess.check_call([dvcs, 'init', '--quiet'], cwd=repoDir)
        subprocess.check_call([dvcs, 'add', 'testfile'], cwd=repoDir)
        subprocess.check_call([dvcs, 'commit', '-m', 'initial commit', '--quiet'], cwd=repoDir)
        localPath = bu_orga_repos.clone_or_update(dvcs, repoUrl, mirrorDir)
        assert 'file:' not in localPath

        # Check that the checked out repository is functional
        checkOut1 = os.path.join(tmpDir, 'checkout1')
        subprocess.check_call([dvcs, 'clone', 'file://' + localPath, checkOut1, '--quiet'])
        with open(os.path.join(checkOut1, 'testfile')) as testf:
            assert testf.read() == 'original'

        # Check that updating works
        with open(os.path.join(repoDir, 'testfile'), 'w') as testf:
            testf.write('changed')
        if dvcs == 'git':
            subprocess.check_call([dvcs, 'add', 'testfile'], cwd=repoDir)
        subprocess.check_call([dvcs, 'commit', '-m', 'new commit', '--quiet'], cwd=repoDir)
        localPath2 = bu_orga_repos.clone_or_update(dvcs, repoUrl, mirrorDir)
        assert localPath == localPath2
        checkOut2 = os.path.join(tmpDir, 'checkout2')
        subprocess.check_call([dvcs, 'clone', 'file://' + localPath, checkOut2, '--quiet'])
        with open(os.path.join(checkOut2, 'testfile')) as testf:
            assert testf.read() == 'changed'
    finally:
        shutil.rmtree(tmpDir)


class TestBackup(unittest.TestCase):
    def test_git(self):
        """ Test cloning and updating git repositories """
        _test_basic_dvcs('git')

    def test_mercurial(self):
        """ Test cloning and updating hg repositories """
        _test_basic_dvcs('hg')

if __name__ == '__main__':
    unittest.main()
