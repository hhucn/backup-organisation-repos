#!/usr/bin/env python3

import argparse
import base64
import itertools
import json
import os.path
import re
import subprocess
import sys
import urllib.request

class BackupBitbucket(object):
    def __init__(self, authData):
        self._authData = authData

    def getRepoUrls(self):
        return []

class BackupGithub(object):
    def __init__(self, authData):
        self._authData = authData

    def _request(self, url):
        req = urllib.request.Request(url)
        authStr = self._authData['user'] + ':' + self._authData['password']
        authb64 = base64.b64encode(authStr.encode('utf-8'))
        req.add_header('Authorization', 'Basic ' + authb64.decode('utf-8'))
        req.add_header('User-Agent', 'bu_orga_repos <hagemeister@cs.uni-duesseldorf.de>')
        with urllib.request.urlopen(req) as uf:
            gh_res = uf.read()
        return json.loads(gh_res.decode('utf-8'))

    def getRepoUrls(self):
        orgs = [o['url'] for o in self._request('https://api.github.com/user/orgs')]

        users = set(orgs)
        for o in orgs:
            users.update(u['url'] for u in self._request(o + '/members'))

        repos = set()
        for u in users:
            repos.update(('git', r['git_url']) for r in self._request(u + '/repos'))
        return repos


_SERVICES = [BackupBitbucket, BackupGithub]
_SERVICES_MAP = {s.__name__.replace('Backup', '').lower() : s for s in _SERVICES}

def main():
    parser = argparse.ArgumentParser(description='Backup all the repositories of all members of all organizations.')
    parser.add_argument('-d', '--backup-dir', metavar='dir', help='Directory where the repositories should be written to', default='./repo-backups-data/')
    parser.add_argument('-a', '--auth-file', metavar='file', help='File to read authentication (= configuration) data from', default='./auth.json')
    args = parser.parse_args()

    with open(args.auth_file) as authf:
        authData = json.load(authf)

    for svcname,ad in authData.items():
        s = _SERVICES_MAP[svcname](ad)
        repos = s.getRepoUrls()
        for rtype,rurl in repos:
            saneName = re.sub(r'^(?:[a-z]+://)[a-z0-9.]*?([a-z]+)(?:\.com|\.org|)/', r'\1_', rurl).replace('/', '_').replace('.git', '')
            localPath = os.path.join(args.backup_dir, os.path.basename(saneName))
            if rtype == 'git':
                cwd = None
                if os.path.exists(localPath):
                    cmd = ['git', 'remote', 'update']
                    cwd = localPath
                else:
                    cmd = ['git', 'clone', '--mirror', rurl, localPath]
                print(saneName + '$ ' + subprocess.list2cmdline(cmd))
                sys.stdout.flush()
                subprocess.check_call(cmd, cwd=cwd, stderr=sys.stdout.fileno())
            else:
                assert False


if __name__ == '__main__':
    main()
