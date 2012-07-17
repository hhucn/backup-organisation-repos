Installation
============

Apart from Python 3, the backup script requires git (`git-core` in debian) and hg(`mercurial` in debian) to be installed. Check it out

Checkout the script with

    git clone git://github.com/hhucn/backup-organisation-repos.git

Copy `auth.json.example` to `auth.json` and modify it with your account data. Then, simply run

    ./bu_orga_repos.py

For extended options, call it with the `--help` option.

Testing
=======

To test that everything works *locally*, execute

    python3 -m unittest

To test the live system (requires auth.json) etc., call

    ./bu_orga_repos.py --test --your-options-if-any-here

