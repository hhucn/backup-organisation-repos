Installation
============

Apart from Python 3 (3.2+ recommended), the backup script requires git and hg to be installed. On debian/Ubuntu, run:

    sudo apt-get install python3 git-core mercurial

Check out the script with:

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

