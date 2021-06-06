#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python setup for coverlovin2 package.

Based on sample https://github.com/pypa/sampleproject/blob/master/setup.py
and instructions at
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation
"""

import os

from setuptools import setup
from setuptools import find_packages

# https://pypi.org/project/py2exe/
try:
    import py2exe
    #import pdb; pdb.set_trace()
    from pathlib import Path
    import sys
    #venv_path = Path(sys.executable) + Path("..\Lib\site-packages")
    import site
    sitep = site.getsitepackages()
    import modulefinder
    for site_ in sitep:
        sp = Path(site_)
        sp = sp / Path("PIL")
        if sp.exists():
            print(f"Add {sp}")
            modulefinder.AddPackagePath("PIL", sp)
        modulefinder.AddPackagePath("bz2", 'C:\\Python\\python.org.3.9.0\\lib\\bz2.py')
        modulefinder.AddPackagePath("_bz2", 'C:\\Python\\python.org.3.9.0\\DLLs\\_bz2.pyd')
    #import win32com
    #modulefinder.AddPackagePath("win32com", path)
except ImportError:
    # not needed for typical builds, fails to install on non-Windows Python
    pass

from coverlovin2.coverlovin2 import __version__
from coverlovin2.coverlovin2 import __author__
from coverlovin2.coverlovin2 import __url__
from coverlovin2.coverlovin2 import __app_name__

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
        # XXX: this should match file Pipefile
        "attrs ~= 20.3",
        "discogs-client ~=2.3",
        "musicbrainzngs ~= 0.7",
        "mutagen ~= 1.45",
        "Pillow ~= 8.1",
        "tabulate == 0.8.7",
    ],
    setup_requires=["wheel"],
    # see https://pypi.org/classifiers/
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
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Sound/Audio"
    ],
    keywords="audio image music",
    python_requires=">=3.7",
    # XXX: should Pipfile* also be distributed???
    packages=find_packages(
        exclude=[
            "coverlovin2/test/",
            ],
        include=[
            "coverlovin2/"
        ]),
    scripts=["coverlovin2/coverlovin2.py"],
    entry_points={
        "console_scripts": [
            "coverlovin2=coverlovin2:main",
        ],
    },
    project_urls={  # Optional
        "Source": __url__,
        "Bug Reports": "https://github.com/jtmoon79/coverlovin2/issues",
    },
    options={
        # build this option with command:
        #    python setup.py py2exe
        # only builds on Windows platform
        # see https://py2exe.org/index.cgi/ListOfOptions
        "py2exe": {
            "compressed": False,
            "unbuffered": True,
            "xref": True,
            "optimize": 2,
            "bundle_files": 1,
            "includes": [
                "bz2",
                "_bz2",
                "encodings.bz2_codec",
                "cffi",
                "PIL",
                "PIL.Image",
            ],
            "dll_excludes": [
                "tk84.dll",
                "tcl84.dll",
                "_tkinter.pyd",
                "_imagingtk.pyd",
                "w9xpopen.exe",
                'msvcr71.dll',
                'win32ui.pyd',
                "MSVCP90.dll",
                # starting with Windows 7
                "kernelbase.dll",
                "mpr.dll",
                "powrprof.dll",
                "secur32.dll",
                "shfolder.dll",
                "API-MS-Win-Core-LocalRegistry-L1-1-0.dll",
                "API-MS-Win-Core-ProcessThreads-L1-1-0.dll",
                "API-MS-Win-Security-Base-L1-1-0.dll",
                # starting with Windows 10
                "CRYPT32.dll",
                "bcrypt.dll",
            ]
        },
    },
    # added for py2exe
    console=["coverlovin2/coverlovin2.py"],
)
