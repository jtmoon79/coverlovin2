#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# setup.py

"""
Python setup for coverlovin2 package.

Based on sample https://github.com/pypa/sampleproject/blob/master/setup.py
and instructions at
https://setuptools.pypa.io/en/latest/userguide/keywords.html
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation

Run this `setup.py` with:

    python -m pip install --editable .
    python -m pip install --editable ".[dev]"

"""

import os
from pathlib import Path
from setuptools import setup
from setuptools import find_packages
import sys

# https://pypi.org/project/py2exe/
try:
    import py2exe
except ImportError:
    # not needed for typical builds, fails to install on non-Windows Python
    pass

# HACK: workaround for `module not found`
sys.path.append(str(Path(__file__).resolve().parent))

from coverlovin2 import (
    __version__,
    __author__,
    __url__,
    __app_name__,
)

# Get the long description from the README.md file
__here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(__here, "README.md"), encoding="utf-8") as f_:
    long_description = f_.read()

setup(
    name=__app_name__,
    version=__version__,
    author=__author__,
    url=__url__,
    description="Download music album cover art for a music collection.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache License 2.0 (Apache-2.0)",
    install_requires=[
        # this should match `Pipfile [packages]`
        "attrs == 23.1.0",
        #"discogs-client == 2.3.0",
        "requests == 2.31.0",
        "musicbrainzngs == 0.7.1",
        "mutagen == 1.47.0",
        "Pillow == 10.1.0",
        "tabulate == 0.9.0",
        "typing-extensions == 4.8.0",
    ],
    setup_requires=["wheel"],
    extras_require={
        # this should match `Pipfile [dev-packages]`
        "dev": [
            "codecov",
            "coveralls",
            "exceptiongroup",
            "mypy",
            "pip-run",
            "pipenv",
            "pluggy",
            "pytest",
            "pytest-cov",
            "pytest-dependency",
            "pyyaml>=4.2b1",
            "setuptools",
            "twine",
            "types-requests == 2.31.0.10",
            "types-setuptools",
            "types-tabulate == 0.9.0.3",
            "wheel",
            "yamllint",
        ]
    },
    # see https://pypi.org/classifiers/ (https://archive.ph/70Qce)
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        # XXX: as of 2019/02/07, the Apache-2.0 License is an OSI approved
        #      license: https://opensource.org/licenses/alphabetical
        #      However the listed classifier string is not listed at
        #      https://pypi.org/classifiers/
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    keywords="audio image music",
    python_requires=">=3.8",
    # XXX: should Pipfile* also be distributed???
    packages=find_packages(
        exclude=("coverlovin2.test",),
        include=("coverlovin2",),
    ),
    #scripts=["coverlovin2/app.py"],
    py_modules=["coverlovin2.__main__"],  # enables `python -m coverlovin2`
    entry_points={
        # see
        # https://setuptools.pypa.io/en/latest/userguide/entry_point.html#console-scripts
        # https://packaging.python.org/en/latest/specifications/entry-points/#use-for-scripts
        "console_scripts": [
            "coverlovin2=coverlovin2.app:main",
        ],
    },
    project_urls={  # Optional
        "Source": __url__,
        "Bug Reports": "https://github.com/jtmoon79/coverlovin2/issues",
    },
    # for py2exe
    # see https://www.py2exe.org/index.cgi/Tutorial
    options={
        # build this option with command:
        #    python setup.py py2exe
        "py2exe": {
            "compressed": True,
            "optimize": 2,
            "bundle_files": 3,
        },
    },
    console=["coverlovin2/app.py"],
)
