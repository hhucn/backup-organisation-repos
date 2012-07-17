#!/usr/bin/env python3

import base64
import itertools
import json
import optparse
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

def saneName(rurl):
    m = re.match(r'^(?:[a-z]+:///?)[a-z0-9.]*?(?P<domain>[a-z]+)(?:\.com|\.org|)/(?P<path>.*)$', rurl)
    if not m:
        raise ValueError('Invalid URL: ' + rurl)
    res = (m.group('domain') + '_' + m.group('path'))
    res = re.sub(r'\.git$', '', res)
    res = res.replace('/', '_')
    return res

def clone_or_update(rtype, rurl, localBasePath, verbose=False):
    sn = saneName(rurl)
    localPath = os.path.join(localBasePath, os.path.basename(sn))
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
        print(sn + '$ ' + subprocess.list2cmdline(cmd))
        sys.stdout.flush()
    stdout = sys.stdout.fileno() if verbose else _SUBPROCESS_DEV_NULL
    stderr = stdout
    subprocess.check_call(cmd, cwd=cwd, stdout=stdout, stderr=stderr)

    return localPath

_SERVICES = [BackupBitbucket, BackupGithub]
_SERVICES_MAP = {s.__name__.replace('Backup', '').lower(): s for s in _SERVICES}


def main():
    parser = optparse.OptionParser(description='Backup all the repositories of all members of all organizations.')
    parser.add_option('-d', '--backup-dir', metavar='dir', help='Directory where the repositories should be written to', default='./repo-backups-data/')
    parser.add_option('-a', '--auth-file', metavar='file', help='File to read authentication (= configuration) data from', default='./auth.json')
    parser.add_option('-t', '--test', help='Do not actually checkout or update anything, but test that everything will work', action='store_true')
    parser.add_option('-q', '--quiet', help='Silence output except for errors', action='store_true')
    parser.add_option('--list', help='Do not actually checkout or update anything, but list all repositories as JSON (implies -q)', action='store_true')
    args,params = parser.parse_args()

    if params:
        parser.error('Not expecting any parameters. Use options.')

    if args.list:
        args.quiet = True

    with open(args.auth_file) as authf:
        authData = json.load(authf)

    if args.test:
        if not os.access(args.backup_dir, os.W_OK):
            raise OSError('Backup directory is not writable!')

    for svcname, ad in authData.items():
        s = _SERVICES_MAP[svcname](ad)

        if not args.quiet:
            sys.stdout.write('Assembling ' + svcname + ' repository information ...')
            sys.stdout.flush()
        repos = s.getRepoUrls()
        if not args.quiet:
            sys.stdout.write(' .\n')
            sys.stdout.flush()

        if args.list:
            srepos = sorted(list(repos), key=lambda r: (r[1],r[0]))
            repoList = [{'rtype': rtype, 'url': rurl} for rtype, rurl in srepos]
            json.dump(repoList, sys.stdout, indent=4)
        else:
            for rtype, rurl in repos:
                if args.test:
                    subprocess.check_call([rtype, '--version'], stdout=_SUBPROCESS_DEV_NULL, stderr=_SUBPROCESS_DEV_NULL)
                else:
                    clone_or_update(rtype, rurl, args.backup_dir, not args.quiet)


if __name__ == '__main__':
    main()
