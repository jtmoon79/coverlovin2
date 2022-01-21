# CoverLovin2

[![Build Status](https://travis-ci.com/jtmoon79/coverlovin2.svg?branch=master)](https://app.travis-ci.com/github/jtmoon79/coverlovin2/)
[![CircleCI](https://circleci.com/gh/jtmoon79/coverlovin2.svg?style=svg)](https://circleci.com/gh/jtmoon79/coverlovin2)
[![codecov](https://codecov.io/gh/jtmoon79/coverlovin2/branch/master/graph/badge.svg)](https://codecov.io/gh/jtmoon79/coverlovin2)
[![Coveralls Coverage Status](https://coveralls.io/repos/github/jtmoon79/coverlovin2/badge.svg?branch=master)](https://coveralls.io/github/jtmoon79/coverlovin2?branch=master)
[![PyPI version](https://badge.fury.io/py/CoverLovin2.svg)](https://badge.fury.io/py/CoverLovin2)
[![Python versions](https://img.shields.io/pypi/pyversions/coverlovin2.svg?longCache=True)](https://pypi.org/pypi/coverlovin2/)
[![Commits since](https://img.shields.io/github/commits-since/jtmoon79/coverlovin2/latest.svg)](https://img.shields.io/github/commits-since/jtmoon79/coverlovin2/latest.svg)
[![Requirements Status](https://requires.io/github/jtmoon79/coverlovin2/requirements.svg?branch=master)](https://requires.io/github/jtmoon79/coverlovin2/requirements/?branch=master)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

*CoverLovin2* (Cover Loving, too!), Python name *coverlovin2*, is a Python
script for downloading album cover art images, either via local searching and
copying, or via downloading from various online services.
A common use-case is creating "`cover.jpg`" files for a large collection of
ripped Compact Disc albums.

----

<!-- TOC auto-updated by VS Code -->
- [CoverLovin2](#coverlovin2)
  - [Script Usage](#script-usage)
    - [Common Media Player expectations](#common-media-player-expectations)
  - [Installation](#installation)
    - [Invocation](#invocation)
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
  - [Other Miscellaneous Notes](#other-miscellaneous-notes)
    - [Issues‼  🐛 🐵](#issues---)
    - [Run Phases](#run-phases)

## Script Usage

To see what it will do without changing any files

    coverlovin2 -s- --test /path/to/music/library

The verbose `--help` message

```Text
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

## Installation

- Using `pip` from pypi:

      python -m pip install coverlovin2

- Using `pip` from source:

      python -m pip install mutagen musicbrainzngs Pillow tabulate discogs-client attrs
      python -m pip install https://github.com/jtmoon79/coverlovin2/archive/master.zip

### Invocation

As a program:

    coverlovin2 --version

As a module:

    python -m coverlovin2 --version

Using `pip-run`:

    pip-run --use-pep517 --quiet git+https://github.com/jtmoon79/coverlovin2@feature/runpy-invoke -- -m coverlovin2 --version

<br />
*coverlovin2* depends on non-standard libraries [mutagen](https://pypi.org/project/mutagen/),
[musicbrainzngs](https://pypi.org/project/musicbrainzngs/), [Pillow](https://pypi.org/project/Pillow/), [Tabulate](https://pypi.org/project/tabulate/), and [attrs](https://pypi.org/project/attrs/).

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

This will install more non-standard libraries. See the [Pipfile](./Pipfile).

#### Using `pip`

Install `pip` and `virtualenv`.

Create a virtual environment and install the dependencies:

    cd coverlovin2
    python -m virtualenv --copies .venv
    .venv/Scripts/activate.ps1
    python -m pip install --upgrade pip wheel setuptools
    python -m pip install -e ".[dev]"

This will install more non-standard libraries. See the [setup.py](./setup.py).

### Subsequent development sessions

#### Using `pipenv`

##### pipenv

Start the `pipenv` shell (bash)

    ./tools/pipenv-shell.sh

(Powershell)

    .\tools\pipenv-shell.ps1

##### pipenv update

Update `Pipfile.lock` with the latest libraries

    pipenv update
    git add Pipfile.lock Pipfile
    git commit -v -m "pipenv update"

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

## Other Miscellaneous Notes

coverlovin2 requires Python version 3.7 or greater.

coverlovin2 is inspired by [coverlovin](https://github.com/amorphic/coverlovin).

coverlovin2 is a practice project for sake of the author catching up to changes
in the Python Universe and the github Universe.<br/>
Some things the author explored:

- project badges (are fun _and useful_)!
- online services
  - CI Services
    - [Travis CI](https://travis-ci.com/jtmoon79/coverlovin2)
    - [Circle CI](https://circleci.com/gh/jtmoon79/coverlovin2)
    - [codecov.io](https://codecov.io/gh/jtmoon79/coverlovin2)
    - [Requires.io](https://requires.io/github/jtmoon79/coverlovin2)
    - ☹ landscape.io ([had too many problems](https://github.com/landscapeio/landscape-issues/issues))
  - package distribution service [pypi](https://pypi.org/project/CoverLovin2/)
- [pytests](./coverlovin2/test)!
  - pytest [code coverage](https://pypi.org/project/pytest-cov/)!
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

<br/>

----

<a href="https://stackexchange.com/users/216253/jamesthomasmoon1979"><img src="https://stackexchange.com/users/flair/216253.png" width="208" height="58" alt="profile for JamesThomasMoon1979 on Stack Exchange, a network of free, community-driven Q&amp;A sites" title="profile for JamesThomasMoon1979 on Stack Exchange, a network of free, community-driven Q&amp;A sites" /></a>
