<!-- README.md -->

# CoverLovin2 <!-- omit in toc -->

[![CircleCI build](https://img.shields.io/circleci/build/gh/jtmoon79/coverlovin2.svg?logo=circleci&style=flat-square)](https://circleci.com/gh/jtmoon79/coverlovin2)
[![coveralls code coverage](https://img.shields.io/coveralls/github/jtmoon79/coverlovin2/branch?main&token=Q2OXTL7U02&style=flat-square&logo=coveralls)](https://coveralls.io/github/jtmoon79/coverlovin2)
[![PyPi version](https://img.shields.io/pypi/v/coverlovin2.svg?longCache=True&logo=pypi&color=blue&style=flat-square)](https://pypi.org/pypi/coverlovin2/)
[![PyPi Python versions](https://img.shields.io/pypi/pyversions/coverlovin2.svg?longCache=True&logo=pypi&style=flat-square)](https://pypi.org/pypi/coverlovin2/)
[![Commits since](https://img.shields.io/github/commits-since/jtmoon79/coverlovin2/latest.svg?color=yellow&style=flat-square)](https://img.shields.io/github/commits-since/jtmoon79/coverlovin2/latest.svg)
[![License](https://img.shields.io/pypi/l/coverlovin2?style=flat-square)](https://opensource.org/licenses/Apache-2.0)
<!--[![Travis build](https://img.shields.io/travis/com/jtmoon79/coverlovin2.svg?branch=master&style=flat-square&logo=travis)](https://app.travis-ci.com/github/jtmoon79/coverlovin2/)-->
<!--[![codecov.io code coverage](https://img.shields.io/codecov/c/github/jtmoon79/coverlovin2/branch?main&token=Q2OXTL7U02&style=flat-square&logo=codecov)](https://codecov.io/gh/jtmoon79/coverlovin2)-->

*CoverLovin2* (Cover Loving, too!), Python name *coverlovin2*, is a Python
script for downloading album cover art images, either via local searching and
copying, or via downloading from various online services.
A common use-case is creating "`cover.jpg`" files for a large collection of
ripped Compact Disc albums.

----

<!-- TOC updated by VS Code extention Markdown All In One -->
- [Script Usage](#script-usage)
  - [Quickstart](#quickstart)
  - [Recommended use](#recommended-use)
  - [`--help`](#--help)
  - [Common Media Player expectations](#common-media-player-expectations)
- [Installation](#installation)
- [Invocation](#invocation)
  - [Run Phases](#run-phases)
- [Development](#development)
  - [First development session](#first-development-session)
    - [Using `pipenv`](#using-pipenv)
    - [Using `pip`](#using-pip)
  - [Subsequent development sessions](#subsequent-development-sessions)
    - [Using `pipenv`](#using-pipenv-1)
      - [pipenv](#pipenv)
      - [pipenv update](#pipenv-update)
    - [Using `pip`](#using-pip-1)
    - [pytest](#pytest)
    - [build](#build)
    - [new release](#new-release)
- [Other Miscellaneous Notes](#other-miscellaneous-notes)
  - [Issues‼  🐛 🐵](#issues---)

## Script Usage

### Quickstart

To see what it will do without changing any files

    coverlovin2 -s- --test /path/to/music/library

### Recommended use

1. Get your own [Discogs Personal Access Token](https://www.discogs.com/settings/developers).
2. Install coverlovin2

       python -m pip install coverlovin2

3. Run once with the better searches (skip Google CSE; too complicated)

       coverlovin2 -d -sl -se -sm \
           -sd -dt "DISCOGS PERSONAL ACCESS TOKEN" \
           /path/to/music/library

   The prior will write `cover.jpg` files to each found Artist-Album directory.

4. Run again to copy the previously downloaded `cover.jpg` to `folder.jpg`.

       coverlovin2 -d -n "folder" -sl /path/to/music/library

### `--help`

The verbose `--help` message

```lang-text
usage: app.py [-h] [-n IMAGE_NAME] [-i {jpg,png,gif}]
              [-o] [-s*] [-s-] [-sl] [-se] [-sm]
              [-sg] [-sgz {small,medium,large}] [--sgid GID] [--sgkey GKEY]
              [-sd] [-dt DISCOGS_TOKEN] [-v] [-r REFERER] [-d] [--test]
              DIRS [DIRS ...]

This Python-based program is for automating downloading album cover art images.
A common use-case is creating a "cover.jpg" file for a collection of ripped
Compact Disc albums.

Given a list of directories, DIRS, recursively identify "album" directories.
"Album" directories have audio files, e.g. files with extensions like .mp3 or
.flac.  For each "album" directory, attempt to determine the Artist and Album.
Then find an album cover image file using the requested --search providers.  If
an album cover image file is found then write it to IMAGE_NAME.IMAGE_TYPE within
each "album" directory.

Audio files supported are .mp3, .m4a, .mp4, .flac, .ogg, .wma, .asf.

optional arguments:
  -h, --help            show this help message and exit

Required Arguments:
  DIRS                  directories to scan for audio files (Required)

Recommended:
  -n IMAGE_NAME, --image-name IMAGE_NAME
                        cover image file name IMAGE_NAME. This is the file name that will be created within passed DIRS. This will be appended with the preferred
                        image TYPE, e.g. "jpg", "png", etc. (default: "cover")
  -i {jpg,png,gif}, --image-type {jpg,png,gif}
                        image format IMAGE_TYPE (default: "jpg")
  -o, --overwrite       overwrite any previous file of the same file IMAGE_NAME and IMAGE_TYPE (default: False)

Search all:
  -s*, --search-all     Search for album cover images using all methods and services
  -s-, --search-all-no-init
                        Search for album cover images using all methods and services that do not require user initialization (e.g. no Google CSE, no Discogs).

Search the local directory for likely album cover images:
  -sl, --search-likely-cover
                        For any directory with audio media files but no file "IMAGE_NAME.IMAGE_TYPE", search the directory for files that are likely album cover
                        images. For example, given options: --name "cover" --type "jpg", and a directory of .mp3 files with a file "album.jpg", it is reasonable to
                        guess "album.jpg" is a an album cover image file. So copy file "album.jpg" to "cover.jpg" . This will skip an internet image lookup and
                        download and could be a more reliable way to retrieve the correct album cover image.

Search the local directory for an embedded album cover image:
  -se, --search-embedded
                        Search audio media files for embedded images. If found, attempt to extract the embedded image.

Search Musicbrainz NGS webservice:
  -sm, --search-musicbrainz
                        Search for album cover images using musicbrainz NGS webservice. MusicBrainz lookup is the most reliable web search method.

Search Google Custom Search Engine (CSE):
  -sg, --search-googlecse
                        Search for album cover images using Google CSE. Using the Google CSE requires an Engine ID and API Key. Google CSE reliability entirely
                        depends upon the added "Sites to search". The end of this help message has more advice around using Google CSE. Google CSE is the most
                        cumbersome search method.
  -sgz {small,medium,large}, --sgsize {small,medium,large}
                        Google CSE optional image file size (default: "large")
  --sgid GID            Google CSE ID (URL parameter "cx") typically looks like "009494817879853929660:efj39xwwkng". REQUIRED to use Google CSE.
  --sgkey GKEY          Google CSE API Key (URL parameter "key") typically looks like "KVEIA49cnkwoaaKZKGX_OSIxhatybxc9kd59Dst". REQUIRED to use Google CSE.

Search Discogs webservice:
  -sd, --search-discogs
                        Search for album cover images using Discogs webservice.
  -dt DISCOGS_TOKEN, --discogs-token DISCOGS_TOKEN
                        Discogs authentication Personal Access Token.

Debugging and Miscellanea:
  -v, --version         show program's version number and exit
  -r REFERER, --referer REFERER
                        Referer url used in HTTP GET requests (default: "https://github.com/jtmoon79/coverlovin2")
  -d, --debug           Print debugging messages. May be passed twice.
  --test                Only test, do not write any files

This program attempts to create album cover image files for the passed DIRS.  It
does this several ways, searching for album cover image files already present in
the directory (-sl).  If not found, it attempts to figure out the Artist and
Album for that directory then searches online services for an album cover image
(-sm or -sg).

Directories are searched recursively.  Any directory that contains one or more
with file name extension .mp3 or .m4a or .mp4 or .flac or .ogg or .wma or .asf
is presumed to be an album directory.  Given a directory of such files, file
contents will be read for the Artist name and Album name using embedded audio
tags (ID3, Windows Media, etc.).  If no embedded media tags are present then a
reasonable guess will be made about the Artist and Album based on the directory
name; specifically this will try to match a directory name with a pattern like
"Artist - Year - Album" or "Artist - Album".
From there, online search services are used to search for the required album
cover image. If found, it is written to the album directory to file name
IMAGE_NAME.IMAGE_TYPE (-n … -i …).

If option --search-googlecse is chosen then you must create your Google Custom
Search Engine (CSE).  This can be setup at https://cse.google.com/cse/all .  It
takes about 5 minutes.  This is where your own values for --sgid and --sgkey can
be created. --sgid is "Search engine ID" (URI parameter "cx") and --sgkey is
under the "Custom Search JSON API" from which you can generate an API Key (URI
parameter "key"). A key can be generated at
https://console.developers.google.com/apis/credentials.
Google CSE settings must have "Image search" as "ON"  and "Search the entire
web" as "OFF".

If option --search-discogs is chosen then you must pass a Discogs Personal
Access Token (PAT). A PAT is a forty character string generated at
https://www.discogs.com/settings/developers with the button "Generate new token".
Requires a discogs account.
Discogs does rate-limit throttling which this program will wait on. It significantly
increases the time to search for candidate album cover images.

Shortcomings:

- Does not handle Various Artist albums.

- --search-discogs can only retrieve jpg file no matter the --image-type passed.

- Multi-threading is only a rudimentary implementation. Does not efficiently queue
  non-overlapping tasks, i.e. the artist-album directory search phase must entirely
  finish before the album cover search phase begins, e.g. will not do HTTP searches
  as soon as possible.

PyPi project: https://pypi.org/project/CoverLovin2/
Source code: https://github.com/jtmoon79/coverlovin2

Inspired by the program coverlovin.
```

### Common Media Player expectations

_Sonos_ systems will use file `folder.jpg`.

_Windows Media Player_ will use file `folder.jpg` if media-embedded images are not available.

_VLC Media Player_ will use file `folder.jpg` if media-embedded images are not available.

_MusicBee_ will use file `cover.png` or `cover.jpg` within the _MUSIC_ library view, _Album and Tracks_ pane if media-embedded images are not available.

_Winamp_ will use file `cover.png` or `cover.jpg` if media-embedded images are not available.

_One Commander_ will use file `cover.jpg`, `folder.jpg`, `front.jpg`, or `background.jpg`.

## Installation

- Using `pip` from pypi:

      python -m pip install coverlovin2

- Using `pip` from source:

      python -m pip install -e "git+https://github.com/jtmoon79/coverlovin2.git@master#egg=CoverLovin2"

## Invocation

There are few ways to run coverlovin2.

As a module

    python -m coverlovin2 --version

As a standalone program

    coverlovin2 --version

As a [`pip-run`](https://pypi.org/project/pip-run/) program

    pip-run coverlovin2 -- -m coverlovin2 --version

or

    pip-run --use-pep517 --quiet \
      "git+https://github.com/jtmoon79/coverlovin2" \
      -- -m coverlovin2 --version

As a [`pipx`](https://pypi.org/project/pipx/) program

    pipx run coverlovin2

See script [execution-modes](./tools/execution-modes.sh).

### Run Phases

coverlovin2 runs in a few phases:

1. recursively search passed directory paths for "album" directories. An "album"
directory merely holds audio files of type `.mp3`, `.m4a`, `.mp4`, `.flac`,
`.ogg`, `.wma`, or `.asf`. (see [`coverlovin2/app.py::AUDIO_TYPES`](./coverlovin2/app.py)).
2. employ a few techniques for determining the artist and album for that
directory.  The most reliable technique is to read available embedded audio tags
within the directory. (see [`coverlovin2/app.py::process_dir`](./coverlovin2/app.py))
3. using user-passed search options, search for the album cover art image file.
4. if album cover art is found, create that image file into the "album"
directory. The name and type of image (`.jpg`, `.png`, `.gif`) is based on
user-passed options for the `IMAGE_NAME` and `IMAGE_TYPE`.

## Development

### First development session

Clone the repository:

    git clone git@github.com:jtmoon79/coverlovin2.git

#### Using `pipenv`

Install `pipenv`.

Start the Python virtual environment and install the dependencies:

    cd coverlovin2
    pipenv --python 3.9 shell
    pipenv install --dev

See the [Pipfile](./Pipfile).

#### Using `pip`

Install `pip` and `virtualenv`.

Create a virtual environment and install the dependencies:

    cd coverlovin2
    python -m virtualenv --copies .venv
    .venv/Scripts/activate.ps1
    python -m pip install --upgrade pip wheel setuptools
    python -m pip install -e ".[dev]"

See the [setup.py](./setup.py).

### Subsequent development sessions

#### Using `pipenv`

##### pipenv

Start the `pipenv` shell (bash)

    ./tools/pipenv-shell.sh

(Powershell)

    .\tools\pipenv-shell.ps1

##### pipenv update

Update `Pipfile.lock` with the latest libraries

1. force upgrade within pip virtual environment

       python -m pip install --upgrade \
         attrs \
         discogs-client \
         musicbrainzngs \
         mutagen \
         Pillow \
         tabulate

   The listing of packages should follow those found in `Pipfile`.

2. run pytests (they must pass)

       python -m pip install pytest pytest-dependency
       python -m pytest ./coverlovin2

3. manually note versions installed

       python -m pip list -v

4. tweak versions in `Pipfile` and `setup.py` the with `pip list` versions

5. update `Pipfile.lock`

       python -m pipenv update

6. commit changes

       git add Pipfile.lock Pipfile setup.py
       git commit -v -m "pipenv update"

`pipenv update` succeeds more often when run under Windows.

#### Using `pip`

    python -m pip install --upgrade -e ".[dev]"

#### pytest

If pytests can run then the development environment is ready.

Run `pytest` tests (bash)

    ./tools/pytest-run.sh

or (Powershell)

    .\tools\pytest-run.ps1

#### build

    python setup.py bdist_wheel

or use the helper script

    ./tools/build-install-test.sh

#### new release

See [Create A New Release](https://github.com/jtmoon79/goto_http_redirect_server/blob/master/tools/build-install-steps.md).

## Other Miscellaneous Notes

coverlovin2 requires Python version 3.7 or greater.

coverlovin2 is inspired by [coverlovin](https://github.com/amorphic/coverlovin).

coverlovin2 is a practice project for sake of the author catching up to changes
in the Python Universe and the github Universe.<br/>
Some things the author explored:

- project badges (are fun _and useful_)!
- online services
  - CI Services
    - ☹ _disabled as of November 2020_ <img height="10" width="10" src="https://api.iconify.design/simple-icons/travisci.svg?color=yellow"/> [Travis CI](https://travis-ci.com/jtmoon79/coverlovin2)
    - <img height="10" width="10" src="https://api.iconify.design/simple-icons/circleci.svg?color=white"/> [Circle CI](https://circleci.com/gh/jtmoon79/coverlovin2)
    - ☹ _disabled as of November 2023_ <img height="10" width="10" src="https://api.iconify.design/simple-icons/codecov.svg?color=red"/> [codecov.io](https://codecov.io/gh/jtmoon79/coverlovin2)
    - <!-- BUG: this SVG does not display from github.com --> <svg fill="#3F5767" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" height="10" width="10"><path d="M0 12v12h24V0H0zm13.195-6.187l1.167 3.515 2.255.005c1.238.005 2.916.019 3.727.037l1.472.028-2.968 2.152c-1.63 1.181-2.976 2.18-2.99 2.212-.01.033.487 1.627 1.106 3.54.619 1.917 1.12 3.487 1.116 3.492-.005.01-1.35-.947-2.986-2.119-1.636-1.177-3-2.147-3.033-2.161-.028-.01-1.411.947-3.07 2.138-1.655 1.185-3.02 2.151-3.024 2.142-.004-.005.497-1.575 1.116-3.492.619-1.913 1.115-3.507 1.106-3.54-.014-.032-1.36-1.03-2.99-2.212L2.23 9.398l1.472-.028c.811-.018 2.49-.032 3.727-.037l2.254-.005 1.168-3.515a512.54 512.54 0 011.171-3.516c.005 0 .53 1.58 1.172 3.516z"/></svg>
      [coveralls.io](https://coveralls.io/github/jtmoon79/coverlovin2)
    - ☹ _service was shutdown_ [Requires.io](https://requires.io/github/jtmoon79/coverlovin2)
    - ☹ _too buggy_ [landscape.io](https://github.com/landscapeio/landscape-issues/issues)
  - <img height="10" width="10" src="https://api.iconify.design/simple-icons/pypi.svg?color=yellow"/> package distribution service [pypi](https://pypi.org/project/CoverLovin2/)
- <img height="10" width="10" src="https://api.iconify.design/simple-icons/pytest.svg?color=yellow"/> [pytests](./coverlovin2/test)!
  - pytest [code coverage](https://pypi.org/project/pytest-cov/)!
- Rudimentary OAuth 1.0a authentication.
- type-hinting‼<br/>
coverlovin2 is very type-hinted code and could be even more so. The author
thinks type-hinting is a good idea but it still needs improvement. In it's
current form in Python 3.7, it feels clumsy to write and to grok. Also, PyCharm
and mypy seem to catch different type-hint warnings.
  - mypy (and [bugs](https://github.com/python/mypy/issues/6476)? ☹)
- Python 3.7 classes and programming (like `SimpleQueue` and `namedtuple`)
  - virtual environment manager `pipenv`.
- printing odd UTF-8 characters (for example, `\uFF5B`, `｛`) and coercing UTF8
mode (within a context without UTF8 support; MinGW bash on Windows)

### Issues‼  🐛 🐵

Other projects Bug Issues 🐛 and Feature Issues 🐵 the author created in the
course of writing this application:

🐵 [pypa/pipenv #3505](https://github.com/pypa/pipenv/issues/3505)

🐛 [pypa/pipenv #3521](https://github.com/pypa/pipenv/issues/3521)

🐛 [pypa/pipenv #3523](https://github.com/pypa/pipenv/issues/3523)

🐛 [pypa/pipenv #3529](https://github.com/pypa/pipenv/issues/3529)

🐛 [pypa/pipenv #3573](https://github.com/pypa/pipenv/issues/3573)

🐛 [pypa/pipenv #4906](https://github.com/pypa/pipenv/issues/4906)

🐛 [python/mypy #6476](https://github.com/python/mypy/issues/6476)

🐛 [python/mypy #6473](https://github.com/python/mypy/issues/6473)

🐛 [ant-druha/PowerShell #16](https://github.com/ant-druha/PowerShell/issues/16)

----

<a href="https://stackexchange.com/users/216253/"><img src="https://stackexchange.com/users/flair/216253.png" width="208" height="58" alt="profile for @JamesThomasMoon on Stack Exchange, a network of free, community-driven Q&amp;A sites" title="profile for @JamesThomasMoon on Stack Exchange, a network of free, community-driven Q&amp;A sites" /></a>
