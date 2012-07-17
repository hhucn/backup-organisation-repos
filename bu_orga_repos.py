#!/usr/bin/env python3

import argparse
import base64
import itertools
import json
import os
import re
import subprocess
import sys
import urllib.request

try:
    _SUBPROCESS_DEV_NULL = subprocess.DEVNULL
except AttributeError:
    _SUBPROCESS_DEV_NULL = open(os.devnull, 'wb')


class BackupBitbucket(object):
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
        orgs = self._authData['orgs']

        users = set(orgs)
        for o in orgs:
            groups = self._request('https://api.bitbucket.org/1.0/groups/' + o + '/')
            for g in groups:
                users.update(u['username'] for u in g['members'])

        repos = set()
        for u in users:
            for r in self._request('https://api.bitbucket.org/1.0/users/' + u + '/')['repositories']:
                if r['scm'] == 'git':
                    rurl = 'https://bitbucket.org/' + u + '/' + r['slug'] + '.git'
                elif r['scm'] == 'hg':
                    rurl = 'https://bitbucket.org/' + u + '/' + r['slug']
                else:
                    assert False

                repos.add((r['scm'], rurl))

        return repos


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
        assert orgs

        users = set(orgs)
        for o in orgs:
            users.update(u['url'] for u in self._request(o + '/members'))

        repos = set()
        for u in users:
            repos.update(('git', r['git_url']) for r in self._request(u + '/repos'))
        return repos


def clone_or_update(rtype, rurl, localBasePath, verbose=False):
    m = re.match(r'^(?:[a-z]+:///?)[a-z0-9.]*?(?P<domain>[a-z]+)(?:\.com|\.org|)/(?P<path>.*)$', rurl)
    if not m:
        raise ValueError('Invalid URL: ' + rurl)
    saneName = (m.group('domain') + '_' + m.group('path')).replace('/', '_').replace('.git', '')
    localPath = os.path.join(localBasePath, os.path.basename(saneName))

    cwd = None

    if rtype == 'git':
        if os.path.exists(localPath):
            cmd = ['git', 'remote', 'update']
            cwd = localPath
        else:
            cmd = ['git', 'clone', '--mirror', rurl, localPath]
    elif rtype == 'hg':
        if os.path.exists(localPath):
            cmd = ['hg', 'pull']
            cwd = localPath
        else:
            cmd = ['hg', 'clone', rurl, localPath]
    else:
        assert False

    if verbose:
        print(saneName + '$ ' + subprocess.list2cmdline(cmd))
        sys.stdout.flush()
    stdout = sys.stdout.fileno() if verbose else _SUBPROCESS_DEV_NULL
    stderr = stdout
    subprocess.check_call(cmd, cwd=cwd, stdout=stdout, stderr=stderr)

    return localPath

_SERVICES = [BackupBitbucket, BackupGithub]
_SERVICES_MAP = {s.__name__.replace('Backup', '').lower(): s for s in _SERVICES}


def main():
    parser = argparse.ArgumentParser(description='Backup all the repositories of all members of all organizations.')
    parser.add_argument('-d', '--backup-dir', metavar='dir', help='Directory where the repositories should be written to', default='./repo-backups-data/')
    parser.add_argument('-a', '--auth-file', metavar='file', help='File to read authentication (= configuration) data from', default='./auth.json')
    args = parser.parse_args()

    with open(args.auth_file) as authf:
        authData = json.load(authf)

    for svcname, ad in authData.items():
        s = _SERVICES_MAP[svcname](ad)
        print('Assembling ' + svcname + ' repository information ...', end='')
        sys.stdout.flush()
        repos = s.getRepoUrls()
        print(' .')
        sys.stdout.flush()
        for rtype, rurl in repos:
            clone_or_update(rtype, rurl, args.backup_dir, True)


if __name__ == '__main__':
    main()
